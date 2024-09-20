import json

# from django.db.models import DateField
from django.contrib.auth import get_user_model

from irhrs.attendance.utils.payroll import (
    get_working_days_from_organization_calendar as gwdfoc,
    get_hours_of_work as ghow,
)
from irhrs.leave.utils.payroll import get_unpaid_leave_days as guld
from irhrs.organization.models import EmploymentLevel
# from irhrs.users.models import UserDetail
from irhrs.payroll.models import (
    Heading,
    ReportRowRecord,
    EmployeePayroll
)

Employee = get_user_model()
Designation = EmploymentLevel


class ReportRow(object):
    def __init__(self, **kwargs):
        self.fy_slot = kwargs.get('fy_slot')
        self.employee = kwargs.get('employee')
        self.from_date = kwargs.get('from_date')
        self.to_date = kwargs.get('to_date')
        self.heading = kwargs.get('heading')
        self.package_heading = kwargs.get('package_heading')
        self.package = kwargs.get('package')

        self.taxable = kwargs.get('taxable')
        self.benefit_type = kwargs.get(
            'benefit_type',
            'No Benefit'
        )
        self.type = kwargs.get('type')

        self.amount = round(kwargs.get('amount'), 2)
        # self.gross_remuneration_contributing_amount = kwargs.get(
        #     'gross_remuneration_contributing_amount',
        #     0
        # )
        self.cost_to_company = kwargs.get('cost_to_company')

    def record_to_model(self, payroll, datework):
        employee_payroll = EmployeePayroll.objects.get_or_create(
            employee=self.employee,
            payroll=payroll,
            package=self.package
        )[0]
        ReportRowRecord.objects.create(
            fy_slot=datework.date_class_to_ad(self.fy_slot[0]).year,
            employee_payroll=employee_payroll,
            from_date=datework.date_class_to_ad(self.from_date),
            to_date=datework.date_class_to_ad(self.to_date),
            heading=self.heading,
            package_heading=self.package_heading,
            # package = self.package,
            taxable=self.taxable,
            benefit_type=self.benefit_type,
            type=self.type,

            amount=self.amount,
            # gross_remuneration_contributing_amount=self.gross_remuneration_contributing_amount,
            cost_to_company=self.cost_to_company,
            # payroll=payroll
        )


class TaxCalculator(object):
    """
    Cases:
        1. appont_date in between fy_slot then annual_gross_salary
           from appoint_date to fy_slot.end_date
        2. when an employee leaves job in between
        3. when employee works for a short time
           (either in between a fiscal year or some in one fy and another in another fy)
           ............. the above conditions can be solved by the
           use of appoint date and dismiss date
        4. if what is salary is paused
        5. Need to see taxable adjustments too
    """

    def get_taxable_amount_from_entry(self, start_date, end_date):
        total_taxable_additions_records = ReportRowRecord.objects.filter(
            employee_payroll__employee=self.employee,
            type__in=['Extra Addition', 'Addition'],
            taxable=True,
            from_date__gte=self.datework.date_class_to_ad(start_date),
            to_date__lte=self.datework.date_class_to_ad(end_date),
            employee_payroll__payroll__status='Approved'
        ).order_by('-from_date')

        # To-Do assuming there is always an addition
        if total_taxable_additions_records:
            new_start_date = self.datework.ad_to_date_class(
                total_taxable_additions_records[0].to_date
            ) + self.datework.timedelta_class(days=1)
        else:
            new_start_date = start_date

        total_taxable_addition = sum(
            x.amount for x in total_taxable_additions_records
        )

        total_non_taxable_deductions_records = ReportRowRecord.objects.filter(
            employee_payroll__employee=self.employee,
            type='Deduction',
            taxable=False,
            from_date__gte=self.datework.date_class_to_ad(start_date),
            to_date__lte=self.datework.date_class_to_ad(end_date),
            employee_payroll__payroll__status='Approved'
        )
        total_non_taxable_deduction = sum(
            x.amount for x in total_non_taxable_deductions_records
        )
        """
        query taxable additions and non taxable deductions
        and additions - deductions
        Note: Also look for taxable additions and non_taxable
        deductions in adjustments in between the input date range
        :param start_date:   filter start date
        :param end_date: filter end date
        :return: (amount, upto_last paid_date + 1 ie new start)
        """
        taxable_amount = total_taxable_addition - total_non_taxable_deduction
        return taxable_amount, new_start_date

    def get_paid_tax_from_entry(self, start_date, end_date):
        total_paid_tax_records = ReportRowRecord.objects.filter(
            employee_payroll__employee=self.employee,
            heading__type='Tax Deduction',
            from_date__gte=self.datework.date_class_to_ad(start_date),
            to_date__lte=self.datework.date_class_to_ad(end_date),
            employee_payroll__payroll__status='Approved'
        )
        return sum(x.amount for x in total_paid_tax_records)

    def get_taxable_slots_in_fy(self, fy_start_date, fy_end_date):
        """
        gets the working time slots in between the fiscal year
        :param fy_start_date:
        :param fy_end_date:
        :return: list of working slots
        """
        start = fy_start_date
        end = fy_end_date
        if self.employee_appoint_date > fy_start_date:
            start = self.employee_appoint_date
        if self.employee_dismiss_date:
            if self.employee_dismiss_date < fy_end_date:
                end = self.employee_dismiss_date
        # To-Do can it have multiple start
        return start, end

    def get_annual_gross_salary(self, slot):
        amount = 0
        fy_data = self.datework.get_fiscal_year_data_from_date_range(
            slot.get('start'),
            slot.get('end')
        )[0]
        taxable_slot_in_fy = self.get_taxable_slots_in_fy(fy_data.get('fy_slot')[0],
                                                          fy_data.get('fy_slot')[1])
        amount, calculator_start_date = \
            self.get_taxable_amount_from_entry(
                taxable_slot_in_fy[0], taxable_slot_in_fy[1])

        if calculator_start_date < taxable_slot_in_fy[1]:
            amount += EmployeeSalaryCalculator(
                self.employee, self.datework, calculator_start_date,
                taxable_slot_in_fy[1],
                self.salary_package,
                self.appoint_date,
                self.dismiss_date,
                calculate_tax=False, **self.tax_kwargs
            ).total_taxable_amount()
        remaining_working_days_in_fy = self.get_range_working_days(
            calculator_start_date, taxable_slot_in_fy[1])
        paid_tax = self.get_paid_tax_from_entry(
            taxable_slot_in_fy[0],
            calculator_start_date - self.datework.timedelta_class(days=1)
        )
        amount = amount - self.edited_general_headings_difference_except_tax_heading

        return amount, paid_tax, remaining_working_days_in_fy

    def get_total_annual_tax(self, tax_deduction_obj, amount):
        self.set_global_var__annual_gross_salary(amount)
        total_tax = self.unit_amount(tax_deduction_obj)
        return total_tax

    def get_tax_amount(self, tax_deduction_heading_object, slot):

        # Below if condition is executed if tax_amount calculation is edited
        if str(
            tax_deduction_heading_object.heading.id
        ) in self.edited_general_headings.keys():
            return (int(
                self.edited_general_headings[
                    str(tax_deduction_heading_object.heading.id)
                ].get('currentValue')) / (
                self.get_range_working_days(self.from_date, self.to_date))
            ) * self.get_working_days(slot)[0]

        annual_gross_salary, paid_tax, remaining_working_days_in_fy = self.get_annual_gross_salary(
            slot
        )

        total_annual_tax = self.get_total_annual_tax(
            tax_deduction_heading_object, annual_gross_salary)

        remaining_tax_to_be_paid = total_annual_tax - paid_tax

        self.set_heading_variable(
            tax_deduction_heading_object.heading,
            total_annual_tax,
            '_UNIT_AMOUNT'
        )

        tax_amount = (remaining_tax_to_be_paid / remaining_working_days_in_fy) * (
            self.get_working_days(slot)[0])

        return tax_amount


class RuleMethod(object):
    def diff(self, from_date, to_date):
        return (to_date - from_date).days + self.datework.timedelta_class(days=1)


class HeadingCalculator(TaxCalculator, RuleMethod):

    def __init__(self):
        self.employee_global_variables = {}
        self.get_easy_global_variables()

    def get_easy_global_variables(self):
        # self.employee_global_variables['EMPLOYEE_MARITAL_STATUS'] = self.employee.marital_status
        # self.employee_global_variables['EMPLOYEE_GENDER'] = self.employee.sex
        # self.employee_global_variables['MALE'] = 'Male'
        # self.employee_global_variables['FEMALE'] = 'Female'
        # self.employee_global_variables['SINGLE'] = 'Single'
        # self.employee_global_variables['MARRIED'] = 'Married'
        #
        # self.employee_global_variables['EMPLOYEE_APPOINT_DATE'] = self.employee_appoint_date
        # self.employee_global_variables['EMPLOYEE_DISMISS_DATE'] = self.employee_dismiss_date

        # employee_adapter = EmployeeVariableAdapter()
        # designation_adapter = DesignationVariableAdapter()
        # employee_and_designation_common_field_adapter =
        # EmployeeAndDesignationCommonFieldAdapter()
        # self.employee_global_variables = merge_two_dicts(
        #     self.employee_global_variables,
        #     employee_adapter.generate(self.employee, self.datework)
        # )
        # self.employee_global_variables = merge_two_dicts(
        #     self.employee_global_variables,
        #     designation_adapter.generate(self.employee.employment_level,
        #                                  self.datework)
        # )
        # self.employee_global_variables = merge_two_dicts(
        #     self.employee_global_variables,
        #     employee_and_designation_common_field_adapter.generate(
        #         self.employee,
        #         self.employee.designation,
        #         self.datework
        #     )
        # )

        self.employee_global_variables['__PAYMENT_DATE_FROM__'] = self.from_date
        self.employee_global_variables['__PAYMENT_DATE_TO__'] = self.to_date

    def set_global_var__slot_variables(self, slot):
        self.employee_global_variables['__EMPLOYEE_WORKED_YEARS__'] = slot.get(
            'worked_years')
        self.employee_global_variables['__SLOT_START_DATE__'] = slot.get(
            'start')
        self.employee_global_variables['__SLOT_END_DATE__'] = slot.get('end')
        self.employee_global_variables['__SLOT_WORKING_DAYS__'] = self.get_working_days(slot)[
            0]
        self.employee_global_variables['__SLOT_WORKING_MONTH_DAYS__'] = self.get_worked_days(slot)[
            1]
        self.employee_global_variables['__SLOT_WORKED_DAYS_COUNT__'] = self.get_worked_days(slot)[
            0]
        self.employee_global_variables['__SLOT_DAYS_COUNT__'] = slot.get(
            'days_count')
        self.employee_global_variables['__SLOT_MONTH_DAYS__'] = slot.get(
            'month_days')

    def set_global_var__fiscal_year_data(self, fy_data):
        self.employee_global_variables['__CURRENT_FISCAL_YEAR_START_DATE__'] = fy_data.get('fy_slot')[
            0]
        self.employee_global_variables['__CURRENT_FISCAL_YEAR_END_DATE__'] = fy_data.get('fy_slot')[
            1]
        self.employee_global_variables['__CURRENT_FISCAL_YEAR_FROM_DATE__'] = fy_data.get(
            'date_range')[0]
        self.employee_global_variables['__CURRENT_FISCAL_YEAR_TO_DATE__'] = fy_data.get(
            'date_range')[1]

    def set_global_var__annual_gross_salary(self, amount):
        self.employee_global_variables['__ANNUAL_GROSS_SALARY__'] = amount

    def set_global_var__methods(self):
        self.employee_global_variables['__DATE_DIFFERENCE__'] = self.diff

    def evaluate_expression(self, expression):
        for key in self.employee_global_variables.keys():
            locals()[key] = self.employee_global_variables[key]
        return eval(expression)  # Expression is cleaned for security purpose

    def unit_amount(self, package_heading_obj):
        amount = 0
        if type(package_heading_obj.rules) == str:
            package_heading_obj.rules = json.loads(package_heading_obj.rules)
        if len(package_heading_obj.rules) > 1:
            for rule in package_heading_obj.rules:
                if self.evaluate_expression(rule.get('condition')):
                    amount += self.evaluate_expression(rule.get('rule'))
        elif len(package_heading_obj.rules) == 1:
            amount += self.evaluate_expression(
                package_heading_obj.rules[0].get('rule'))
        return amount

    def get_working_days_from_organization_calendar(self, slot):
        """
        :param slot:
        :return:
        """
        from_date = self.datework.date_class_to_ad(slot.get('start'))
        to_date = self.datework.date_class_to_ad(slot.get('end'))
        return gwdfoc(self.employee, from_date, to_date)
        # # To-Do
        # return 0

    def get_working_days(self, slot):
        """
        Returns days count and month days
        :param slot:
        :return: (working_days in a slot, working days in a month)
        """

        if type(self.month_days_setting) == int:
            if slot.get('days_count') == slot.get('month_days'):
                return self.month_days_setting, self.month_days_setting
            else:
                return (
                    self.month_days_setting *
                    (slot.get('days_count')/slot.get('month_days')),
                    self.month_days_setting
                )
        elif self.month_days_setting == 'DATE_CALENDAR':
            return (
                slot.get('days_count'),
                slot.get('month_days')
            )
        elif self.month_days_setting == 'ORGANIZATION_CALENDAR':
            return (
                self.get_working_days_from_organization_calendar(
                    slot.get('start'),
                    slot.get('end')
                ),
                self.get_working_days_from_organization_calendar(
                    self.datework.date_class(
                        slot.get('year'),
                        slot.get('month'),
                        1
                    ),
                    self.datework.date_class(
                        slot.get('year'),
                        slot.get('month'),
                        slot.get('month_days')
                    )
                )
            )

    def get_worked_days(self, slot, package_heading_obj=None):
        worked_days, month_days = self.get_working_days(slot)

        if package_heading_obj:
            if package_heading_obj.absent_days_impact:
                return (
                    worked_days - self.get_unpaid_leave_days(slot),
                    month_days
                )
            else:
                return worked_days, month_days
        else:
            return worked_days - self.get_unpaid_leave_days(slot), month_days

    def get_range_worked_days(self, from_date, to_date):
        month_slots = self.datework.get_months_data_from_date_range(
            self.employee_appoint_date,
            from_date,
            to_date
        )
        total_days = 0
        for slot in month_slots:
            total_days += self.get_worked_days(slot)[0]
        return total_days

    def get_range_working_days(
            self, from_date, to_date):
        month_slots = self.datework.get_months_data_from_date_range(
            self.employee_appoint_date,
            from_date,
            to_date
        )
        total_days = 0
        for slot in month_slots:
            total_days += self.get_working_days(slot)[0]
        return total_days

    def get_hours_of_work(self, slot, package_heading_obj):

        heading_name = package_heading_obj.heading.name
        from_date = self.datework.date_class_to_ad(slot.get('start'))
        to_date = self.datework.date_class_to_ad(slot.get('end'))

        return ghow(self.employee,from_date, to_date, heading_name)

    def get_unpaid_leave_days(self, slot):
        # To-Do get it from somewhere
        from_date = self.datework.date_class_to_ad(slot.get('start'))
        to_date = self.datework.date_class_to_ad(slot.get('end'))

        return guld(self.employee, from_date, to_date)

    def get_slot_gross_remuneration_amount(self, slot):
        gross_remunerations = list(filter(
            lambda x: x.from_date >= slot.get('start') and x.to_date <= slot.get(
                'end') and x.heading.type == 'Addition' and x.heading.payroll_setting_type not in [
                'Provident Fund Office Addition', 'Self CIT Office Addition'], self.report_rows))
        return sum(x.amount for x in gross_remunerations)

    def get_slot_basic_remuneration(self, slot):
        basic_remunerations = list(filter(
            lambda x: x.from_date >= slot.get('start') and x.to_date <= slot.get(
                'end') and x.heading.type == 'Addition' and x.heading.payroll_setting_type in [
                'Salary Structure'], self.report_rows))
        return sum(x.amount for x in basic_remunerations)

    def get_slot_amount(self, slot, package_heading_obj):
        working_days = self.get_working_days(slot)[0]
        worked_days = self.get_worked_days(slot, package_heading_obj)[0]
        month_days = self.get_working_days(slot)[1]

        # Below if condition is executed when particular heading general calculation value is edited
        # Ratio because there can be many slots and edition is for over all
        if str(package_heading_obj.heading.id) in self.edited_general_headings.keys():
            return (
                int(
                    self.edited_general_headings[str(
                        package_heading_obj.heading.id)].get('currentValue')
                ) /
                (
                    self.get_range_working_days(
                        self.from_date, self.to_date)
                )
            ) * self.get_working_days(slot)[0]

        duration_unit = package_heading_obj.duration_unit

        if duration_unit == 'Hourly':
            return self.get_hours_of_work(slot, package_heading_obj) * self.unit_amount(
                package_heading_obj)
        elif duration_unit == 'Daily':
            return worked_days * self.unit_amount(package_heading_obj)
        elif duration_unit == 'Weekly':
            return 0  # To-Do
        elif duration_unit == 'Monthly':
            return (self.unit_amount(package_heading_obj) * (
                worked_days)) / month_days
        elif duration_unit == 'Yearly':
            return 0  # To-Do

    def set_heading_variable(self, heading_obj, amount, *suffixes):
        var_name = '_'.join(heading_obj.name.upper().split(' '))
        suffix = ''.join(suffixes)
        var_name += suffix
        self.employee_global_variables['__' + var_name + '__'] = amount

    def create_extra_heading_report_row(self, fy_data, month_slot):
        for heading_id in self.extra_headings.keys():
            heading_obj = Heading.objects.get(id=heading_id)
            amount = int(self.extra_headings[heading_id].get('value'))

            type_ = heading_obj.type
            taxable = heading_obj.taxable
            benefit_type = heading_obj.benefit_type

            if type_ in ['Extra Addition', 'Extra Deduction']:

                if benefit_type in ['Monetary Benefit', 'Non Monetary Benefit']:
                    adjustment_ctc_amount = amount
                else:
                    adjustment_ctc_amount = 0
                adjustment_report_row = ReportRow(
                    fy_slot=fy_data.get('fy_slot'),
                    employee=self.employee,
                    from_date=month_slot.get('start'),
                    to_date=month_slot.get('end'),
                    heading=heading_obj,

                    package_heading=self.salary_package.package_headings.get(
                        heading=heading_obj),
                    package=self.salary_package,

                    taxable=taxable,
                    type=type_,
                    benefit_type=benefit_type,

                    amount=amount,
                    cost_to_company=adjustment_ctc_amount
                )
                self.report_rows.append(adjustment_report_row)
            else:
                raise TypeError(
                    "Only 'Extra Addition' and 'Extra Deduction' type heading are supported as extra headings")
        return True

    def create_month_slot_report_row(self, fy_data, month_slot):
        latest_tax_deduction_heading = self.employee_salary_package_headings.filter(
            type='Tax Deduction'
        )
        latest_tax_deduction_heading = latest_tax_deduction_heading.latest(
            '-order') if latest_tax_deduction_heading else None
        for index, package_heading_obj in enumerate(self.employee_salary_package_headings):
            if package_heading_obj.type == 'Tax Deduction' and self.calculate_tax:

                report_row = ReportRow(
                    fy_slot=fy_data.get('fy_slot'),
                    employee=self.employee,
                    from_date=month_slot.get('start'),
                    to_date=month_slot.get('end'),
                    heading=package_heading_obj.heading,
                    package_heading=package_heading_obj,
                    package=self.salary_package,

                    taxable=False,
                    type=package_heading_obj.type,

                    amount=self.get_tax_amount(
                        package_heading_obj, month_slot),
                    cost_to_company=0
                )
                self.report_rows.append(report_row)
                self.set_heading_variable(
                    report_row.heading, report_row.amount)

            elif package_heading_obj.type in ['Type1Cnst', 'Type2Cnst']:
                # To-Do variable with higher order than tax should be igonored when self.calculate_tax is false
                # Calculate tax when false indicates that it is inside tax calculation mode
                if latest_tax_deduction_heading:
                    if self.calculate_tax or latest_tax_deduction_heading.order > package_heading_obj.order:
                        if not self.heading_exists(
                            package_heading_obj.heading
                        ):
                            report_row = ReportRow(
                                fy_slot=fy_data.get('fy_slot'),
                                employee=self.employee,
                                from_date=month_slot.get('start'),
                                to_date=month_slot.get('end'),
                                heading=package_heading_obj.heading,
                                package_heading=package_heading_obj,
                                package=self.salary_package,

                                taxable=False,
                                type=package_heading_obj.type,

                                amount=self.unit_amount(package_heading_obj),
                                cost_to_company=0
                            )
                            self.report_rows.append(report_row)
                        self.set_heading_variable(
                            package_heading_obj.heading,
                            self.unit_amount(package_heading_obj)
                        )
                else:
                    if not self.heading_exists(
                        package_heading_obj.heading
                    ):
                        report_row = ReportRow(
                            fy_slot=fy_data.get('fy_slot'),
                            employee=self.employee,
                            from_date=month_slot.get('start'),
                            to_date=month_slot.get('end'),
                            heading=package_heading_obj.heading,
                            package_heading=package_heading_obj,
                            package=self.salary_package,

                            taxable=False,
                            type=package_heading_obj.type,

                            amount=self.unit_amount(package_heading_obj),
                            cost_to_company=0
                        )
                        self.report_rows.append(report_row)
                    self.set_heading_variable(package_heading_obj.heading,
                                              self.unit_amount(package_heading_obj))

                # print(self.unit_amount(package_heading_obj))
            elif package_heading_obj.type not in ['Tax Deduction', 'Type1Cnst', 'Type2Cnst', 'Extra Addition', 'Extra Deduction']:
                # To-Do assert error when  self.calculate_tax is false and order is greater than tax order
                if latest_tax_deduction_heading:
                    assert (
                        (self.calculate_tax) or (package_heading_obj.order <
                                                 latest_tax_deduction_heading.order)
                    ), 'Addition or deduction heading after tax'
                # below if is just test
                # if (package_heading_obj.heading.name == 'Provident Fund Allowance' and self.calculate_tax):
                #     print(self.employee_global_variables)
                # print(self.get_slot_amount(month_slot, package_heading_obj))
                # print(package_heading_obj.type)
                amount = self.get_slot_amount(month_slot, package_heading_obj)
                if package_heading_obj.benefit_type in ['Monetary Benefit', 'Non Monetary Benefit']:
                    ctc_amount = amount
                else:
                    ctc_amount = 0

                report_row_kwargs = dict(
                    fy_slot=fy_data.get('fy_slot'),
                    employee=self.employee,
                    from_date=month_slot.get('start'),
                    to_date=month_slot.get('end'),
                    taxable=package_heading_obj.taxable,
                    heading=package_heading_obj.heading,
                    package_heading=package_heading_obj,
                    package=self.salary_package,
                    type=package_heading_obj.type,
                    benefit_type=package_heading_obj.benefit_type,
                    amount=amount,
                    cost_to_company=ctc_amount
                )

                if package_heading_obj.benefit_type in ['Monetary Benefit', 'Non Monetary Benefit']:
                    # report_row_kwargs['gross_remuneration_contributing_amount'] = gross_amount
                    report_row_kwargs['cost_to_company'] = amount

                report_row = ReportRow(
                    **report_row_kwargs
                )

                self.report_rows.append(report_row)

                self.employee_global_variables[
                    '__TOTAL_GROSS_REMUNERATION__'] = self.get_slot_gross_remuneration_amount(month_slot)

                self.employee_global_variables[
                    '__BASIC_REMUNERATION__'] = self.get_slot_basic_remuneration(month_slot)

                # self.set_heading_variable(report_row.heading, report_row.amount, '_PAYABLE_AMOUNT')
                # self.set_heading_variable(report_row.heading, self.unit_amount(package_heading_obj), '_UNIT_AMOUNT')

                self.set_heading_variable(
                    report_row.heading, report_row.amount, '')


class EmployeeSalaryCalculator(HeadingCalculator):
    def __init__(
        self,
        employee,
        datework,
        from_date,
        to_date,
        salary_package,
        employee_appoint_date,
        employee_dismiss_date,
        calculate_tax=True,
        **kwargs
    ):
        self.employee = employee
        self.datework = datework

        self.salary_package = salary_package
        self.appoint_date = employee_appoint_date
        self.dismiss_date = employee_dismiss_date
        self.employee_appoint_date = self.datework.ad_to_date_class(
            employee_appoint_date)
        self.employee_dismiss_date = self.datework.ad_to_date_class(
            employee_dismiss_date) if employee_dismiss_date else None

        self.calculate_tax = calculate_tax

        self.tax_kwargs = kwargs
        self.extra_headings = kwargs.get('extra_headings', {})
        self.edited_general_headings_difference_except_tax_heading = kwargs.get(
            'edited_general_headings_difference_except_tax_heading',
            0
        )
        self.edited_general_headings = kwargs.get(
            'edited_general_headings', {})
        self.month_days_setting = kwargs.get(
            'month_days_setting',
            'DATE_CALENDAR'
        )  # is one of ['DATE_CALENDAR', 'ORGANIZATION_CALENDAR', FIXED_NUMBER like 28, 30]

        entriesToRemove = (
            'extra_headings',
            'edited_general_headings',
            'edited_general_headings_difference_except_tax_heading'
        )
        for k in entriesToRemove:
            self.tax_kwargs.pop(k, None)

        self.from_date = self.datework.ad_to_date_class(from_date) if type(
            from_date) != self.datework.date_class else from_date
        self.to_date = self.datework.ad_to_date_class(to_date) if type(
            to_date) != self.datework.date_class else to_date

        # if not self.calculate_tax:
        #     print(self.from_date, self.to_date)

        self.heading_payments = []

        self.report_rows = []

        self.fy_datas = self.datework.get_fiscal_year_data_from_date_range(
            self.from_date,
            self.to_date
        )

        self.employee_salary_package_headings = self.salary_package.package_headings.all(
        ).order_by('order')

        super().__init__()

        self.holdings = self.get_holdings()

        last_fy_data = self.fy_datas[-1]
        for fy_data in self.fy_datas:
            self.set_global_var__fiscal_year_data(fy_data)
            month_slots = self.datework.get_months_data_from_date_range(
                self.employee_appoint_date,
                fy_data.get(
                    'date_range'
                )[0],
                fy_data.get('date_range')[1]
            )
            for month_slot in month_slots:
                last_month_slot = month_slots[-1]
                self.set_global_var__slot_variables(month_slot)
                self.create_month_slot_report_row(fy_data, month_slot)

                if fy_data == last_fy_data and month_slot == last_month_slot:
                    self.create_extra_heading_report_row(fy_data, month_slot)

        # Notes
        # from_date => Payment from date (Either AD or BS)
        # to_date => Payment to date (Either AD or BS)
        # extra_heading_amount => Extra paid heading with amount (Other headings not specified in package headings)

        # Other on calculation variables
        #
        # __FIXED_SALARY
        # __DEARNESS_ALLOWANCE_AMOUNT
        # __CONVEYANCE_ALLOWANCE_AMOUNT
        # __FLEXIBILITY_ALLOWANCE_AMOUNT
        # __TECHNICAL_ALLOWANCE_AMOUNT
        # __COMMUNICATION_ALLOWANCE_AMOUNT
        # __OVERTIME_HOURLY_RATE
        # __LIFE_INSURANCE_DEDUCTION_AMOUNT
        #
        # EMPLOYEE_DAILY_WAGE
        # HOURLY_RATE

        # EMPLOYEE_MARITAL_STATUS
        # SINGLE
        # MARRIED
        # PAYMENT_DATE_RANGE_FROM
        # PAYMENT_DATE_RANGE_TO

        # UNIT_SLOT_FROM
        # UNIT_SLOT_TO
        #
        # EMPLOYEE_WORKED_YEARS
        # ANNUAL_GROSS_SALARY
        # OVERTIME_HOURS
        # BASIC_REMUNERATION

    def get_holdings(self):
        holdings = dict()
        holdings['salary_holdings'] = self.employee.salary_holdings.filter(
            from_date__lte=self.datework.date_class_to_ad(self.to_date))
        holdings['heading_holdings'] = self.employee.heading_holdings.filter(
            from_date__lte=self.datework.date_class_to_ad(self.to_date))
        return holdings

    def get_all_package_headings_amount(self):
        data = []
        for package_heading_obj in self.employee_salary_package_headings:
            amount = self.get_heading_amount(package_heading_obj)
            data.append(
                {
                    'package_heading_obj': package_heading_obj,
                    'amount': amount
                }
            )
        return data

    # this is only for variable
    def heading_exists(
        self,
        heading,
    ):
        # May be check heading of paricular slot
        headings = [x for x in self.report_rows if x.heading ==
                    heading]
        return len(headings) > 0

    def get_heading_amount(self, package_heading_obj):
        # import ipdb
        # ipdb.set_trace()
        package_heading_obj_rows = list(filter(
            lambda x: x.heading == package_heading_obj.heading, self.report_rows))

        return sum(x.amount for x in package_heading_obj_rows)

    def total_taxable_additions(self):
        # Added before tax
        total_taxable_additions_records = list(filter(
            lambda x: x.type in ['Extra Addition', 'Addition'] and x.taxable, self.report_rows))
        return sum(x.amount for x in total_taxable_additions_records)

    def total_non_taxable_additions(self):
        # Added after tax deduction
        total_non_taxable_additions_records = list(filter(
            lambda x: x.type in ['Extra Addition',
                                 'Addition'] and not x.taxable,
            self.report_rows))
        return sum(x.amount for x in total_non_taxable_additions_records)

    def total_non_taxable_deductions(self):
        # Deduced before tax deduction
        total_non_taxable_deductions_records = list(filter(
            lambda x: x.type == 'Deduction' and not x.taxable,
            self.report_rows))
        return sum(x.amount for x in total_non_taxable_deductions_records)

    def total_taxable_deductions(self):
        # Deduced after tax deduction
        total_taxable_deductions_records = list(filter(
            lambda x: x.heading.type == 'Deduction' and x.taxable, self.report_rows))
        return sum(x.amount for x in total_taxable_deductions_records)

    def total_taxable_amount(self):
        return self.total_taxable_additions() - self.total_non_taxable_deductions()

    def total_additions(self):
        return self.total_non_taxable_additions() + self.total_taxable_additions()

    def total_deductions(self):
        return self.total_non_taxable_deductions() + self.total_taxable_deductions()

    def cash_in_hand(self):
        return self.total_additions() - self.total_deductions() - self.get_heading_amount(
            self.employee_salary_package_headings.get(heading__name='Tax Deduction'))

    def amount_after_tax(self):
        return self.total_taxable_amount() - self.get_heading_amount(
            self.employee_salary_package_headings.get(heading__name='Tax Deduction'))

    def get_total_cost_to_company(self):
        return sum(x.cost_to_company for x in self.report_rows)

    def get_total_gross_remuneration(self):
        return sum(x.gross_remuneration_contributing_amount for x in self.report_rows)

    def record_report_rows(self):
        for report_row in self.report_rows:
            # if report_row.type == 'Tax Deduction':
            # print(report_row.amount)
            report_row.record_to_model()
