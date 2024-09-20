import datetime
import itertools
import logging
import multiprocessing

from django.core.cache import cache
from django.db import transaction
from django.contrib.auth import get_user_model
from django.db.models import Q, Func, Window, F, Subquery, OuterRef
from fast_map import fast_map_async
from rest_framework.exceptions import ValidationError

from config import settings
from irhrs.core.utils.common import get_today

from irhrs.notification.utils import notify_organization
from irhrs.organization.models import Organization, FY
from irhrs.payroll.api.v1.serializers.payroll_serializer import PayrollEmployeeSerializer
from irhrs.payroll.api.v1.serializers.payroll import PayrollCreateSerializer, \
    EmployeeFilterSerializer
from irhrs.payroll.api.v1.serializers.report.preparation_sheet import PreparationSheetOverview
from irhrs.payroll.models import Payroll, SalaryHolding, OrganizationPayrollConfig, FAILED, \
    COMPLETED, PROCESSING, PayrollGenerationHistory, QUEUED, AdvanceSalarySetting, \
    PayrollApprovalHistory, CONFIRMED, UserExperiencePackageSlot, ReportRowRecord, \
    UserVoluntaryRebate, CREATE_REQUEST, DELETE_REQUEST, UserVoluntaryRebateAction

from irhrs.payroll.models.advance_salary_request import AdvanceSalaryRepayment
from irhrs.payroll.models.payroll import GENERATED, APPROVAL_PENDING, APPROVED
from irhrs.payroll.utils import helpers
from irhrs.payroll.utils.calculator import EmployeeSalaryCalculator
from irhrs.payroll.utils.employee_payroll import get_extra_addition_and_deduction
from irhrs.payroll.utils.exceptions import CustomValidationError
from irhrs.payroll.utils.user_voluntary_rebate import update_rebate_settings_from_payroll_edit

# from irhrs.payroll.utils.helpers import InvalidVariableTypeOperation, get_appoint_date, \
#     get_dismiss_date
from irhrs.permission.constants.permissions import GENERATE_PAYROLL_PERMISSION

Employee = get_user_model()

logger = logging.getLogger(__name__)


def check_in_progress_payroll(organization):
    return PayrollGenerationHistory.objects.filter(
        organization=organization, status__in=[QUEUED, PROCESSING]
    ).exists()


class PayrollGenerator:

    @staticmethod
    def get_FY(organization_slug, from_date, to_date):
        # also used at irhrs/payroll/api/v1/views/payroll.py:553
        error_messages = dict()
        date_work = FY(
            Organization.objects.get(slug=organization_slug)
        )

        payroll_start_fiscal_year = OrganizationPayrollConfig.objects.filter(
            organization__slug=organization_slug
        ).first()

        if not (payroll_start_fiscal_year and payroll_start_fiscal_year.start_fiscal_year):
            error_messages['to_date'] = 'Setup payroll start fiscal year first'
        else:
            if from_date < payroll_start_fiscal_year.start_fiscal_year.applicable_from:
                error_messages[
                    'from_date'
                ] = 'From date cannot be less than payroll start fiscal year applicable from date.'
            else:
                fy_datas = date_work.get_fiscal_year_data_from_date_range(
                    from_date,
                    to_date
                )

                if len(fy_datas) > 1:
                    error_messages[
                        'to_date'] = 'Date range cannot be in multiple fiscal years.'
                elif not fy_datas:
                    error_messages[
                        'to_date'] = 'No fiscal entry found for given date range'
                else:
                    month_slots = date_work.get_months_data_from_date_range(
                        from_date,
                        from_date,
                        to_date
                    )
                    if not month_slots:
                        error_messages[
                            'to_date'] = 'No month slot entry found for given date range'

        if error_messages.keys():
            raise CustomValidationError(error_dict=error_messages)
        return date_work, payroll_start_fiscal_year

    @staticmethod
    def get_valid_employee_for_payroll(*request_data, **kwargs):
        return PayrollGenerator.get_valid_employee_for_payroll_generation(*request_data, **kwargs)

    @classmethod
    def get_user_experience_calculation_data(cls, employee, from_date,
                                             to_date, payroll_start_fiscal_year):
        # also used at irhrs/payroll/api/v1/views/payroll.py:557

        user_experience = employee.first_date_range_user_experiences(
            from_date,
            to_date
        )
        appoint_date = helpers.get_appoint_date(
            employee, payroll_start_fiscal_year)
        dismiss_date = helpers.get_dismiss_date(employee, user_experience)

        # appoint date or from_date whichever is later
        active_from_date = max(from_date, appoint_date)

        date_range_user_experiences = employee.date_range_user_experiences(
            from_date,
            to_date
        )
        package_slots = UserExperiencePackageSlot.objects.filter(
            user_experience__in=date_range_user_experiences,
        ).order_by('-active_from_date')

        salary_packages = list()
        _package_applicable_to_date = to_date

        for package_slot in package_slots:
            _from_date = max(package_slot.active_from_date, active_from_date)
            if _package_applicable_to_date - _from_date < datetime.timedelta(days=0):
                # if effective days lte 0, then do not add that slot
                continue

            salary_packages.append({
                "package": package_slot.package,
                "from_date": max(package_slot.active_from_date, active_from_date),
                "to_date": _package_applicable_to_date,
                "applicable_from": package_slot.active_from_date,
                "job_title": getattr(package_slot.user_experience.job_title, "title", ""),
                "current_step": package_slot.user_experience.current_step,
                "employment_status": getattr(
                    package_slot.user_experience.employment_status, "title", "")
            })
            _package_applicable_to_date = package_slot.active_from_date - \
                datetime.timedelta(days=1)

        # order by active from date
        salary_packages.reverse()
        return appoint_date, dismiss_date, salary_packages

    @staticmethod
    def repayments(employee, from_date, to_date):
        return AdvanceSalaryRepayment.objects.filter(
            request__employee=employee,
            paid=False,
            request__payslip_generation_date__lte=to_date
        ).order_by('request__payslip_generation_date', 'order')

    @classmethod
    def validate_advance_salary_settings(cls, employee, package_slot, from_date, to_date):
        """
        Validate user's package has heading to deduct advance salary
        """

        if cls.repayments(employee, from_date, to_date).exists():

            organization = employee.detail.organization
            advance_salary_settings = AdvanceSalarySetting.objects.filter(
                organization=organization).first()
            if not advance_salary_settings:
                return False, ["Advance salary setting not defined for the organization."]
            if not advance_salary_settings.deduction_heading:
                return False, [
                    "Advance salary deduction heading not defined for the organization."]
            if not package_slot:
                return False, [
                    "Package not found for given date range."]
            if not package_slot.package.package_headings.filter(
                heading=advance_salary_settings.deduction_heading
            ).exists():
                return False, [
                    "Advance salary deduction heading `{}` not found in package.".format(
                        advance_salary_settings.deduction_heading
                    )
                ]
        return True, None

    @classmethod
    def get_employee_payroll_eligibility(cls, employee, from_date,
                                         to_date, payroll_start_fiscal_year, timeframe_user_experiences, **kwargs):
        """
        :param employee:
        :param from_date:
        :param to_date:
        :param payroll_start_fiscal_year: Start FY from settings
        :return: <eligible_status : Boolean>,
            <arg_list: [<error_message: String>,
            <error_type: String('Pending Approval'| 'Never Paid'| 'Gap Or Overlap'| 'Holding')>,
            <data: Dictionary>]>
        """

        # todo @Ravi: add extra error types
        # timeframe doesnot belong to any userexperience perfectly

        package_slot = None

        # if len(timeframe_user_experiences) > 1:
        #     # valid case, may need to check for gaps
        #     return False, [
        #         'Date range must not contain multiple user experiences',
        #         'No Package', {}
        #     ]
        if not timeframe_user_experiences:
            return False, [
                'Timeframe doesnot belong to any specific user experience',
                'No Experience in timeframe', {}
            ]
        else:
            first_user_experience = timeframe_user_experiences[0]
            last_user_experience = timeframe_user_experiences.last()
            appoint_date = helpers.get_appoint_date(
                employee, payroll_start_fiscal_year)
            dismiss_date = helpers.get_dismiss_date(
                employee, last_user_experience)
            cutoff_date=kwargs.get('cutoff_date')
            if cutoff_date and dismiss_date and cutoff_date < dismiss_date < to_date:
                return False, [
                    'Last Working date lies between cutoff date and end date of payroll.',{}
                ]

            if ((
                first_user_experience.start_date > from_date and
                # appoint date handled in calculator
                first_user_experience.start_date != appoint_date
            ) or (
                last_user_experience.end_date
                and last_user_experience.end_date < to_date
                and last_user_experience.end_date != dismiss_date
            )):
                return False, [
                    'Timeframe belongs to user experience partially',
                    'No Experience in timeframe', {}
                ]
            fy_obj = FY(payroll_start_fiscal_year.organization)
            fiscal_year = fy_obj.fiscal_obj(from_date)
            has_rebate = UserVoluntaryRebate.objects.filter(
                user=employee,
                fiscal_year=fiscal_year
            ).annotate(
                status=Subquery(UserVoluntaryRebateAction.objects.filter(
                    user_voluntary_rebate=OuterRef('id')).values('action')[:1])
            ).filter(status__in=[CREATE_REQUEST, DELETE_REQUEST]).exists()
            if has_rebate:
                return False, [
                    f'{employee.full_name} have rebate in requested state.Please Approve/Deny Rebate request to continue.',
                    {}
                ]
            for user_experience in timeframe_user_experiences:

                user_experience_packages = (
                    user_experience.user_experience_packages.order_by(
                        'active_from_date'
                    )
                )

                if not user_experience_packages:
                    return False, [
                        f'User experience ({user_experience.job_title}) with given date range has '
                        'no packages',
                        'No Package', {}
                    ]
                else:
                    # date_range_packages_count = user_experience_packages.filter(
                    #     active_from_date__lt=to_date,
                    #     active_from_date__gte=from_date
                    # ).count()
                    package_slot = user_experience_packages.filter(
                        active_from_date__lte=from_date
                    ).last()

                    # if date_range_packages_count > 1:
                    #     return False, [
                    #         'Date range must not contain multiple user experience packages',
                    #         'No Package', {}
                    #     ]

        # START:Time frame contains not released holdings. that is fully or partially
        # sh_q = AvailabilityQueryHelper(
        #     from_date,
        #     to_date,
        #     'from_date',
        #     'to_date'
        # )
        # to_date_not_none_query_object = Q(
        #     ~Q(to_date=None) &
        #     Q(
        #         Q(sh_q.a & sh_q.b & sh_q.c & sh_q.d) |
        #         Q(sh_q.e & sh_q.f & sh_q.g & sh_q.h) |
        #         Q(sh_q.i & sh_q.j & sh_q.k & sh_q.l) |
        #         Q(sh_q.m & sh_q.n & sh_q.o & sh_q.p))
        # )

        # to_date_none_query_object = Q(
        #     Q(to_date=None) &
        #     Q(
        #         Q(from_date__gte=from_date) &
        #         Q(from_date__lte=to_date)
        #     )
        # )

        # if salary hold is present, block
        not_released_holding = SalaryHolding.objects.filter(
            released=False,
            employee=employee
        ).first()
        #     .filter(
        #     to_date_not_none_query_object |
        #     to_date_none_query_object
        # ).first()

        if not_released_holding:
            return False, [
                'Employee salary is on hold.',
                'Holding', {
                    'holding_id': not_released_holding.id
                }
            ]
        # END:Time frame contains not released holdings. that is fully or partially

        if dismiss_date:
            # --> removed this check to as to_date will be adjusted automatically by calculator
            # if from_date <= dismiss_date <= to_date:
            #     return False, [
            #         'Employee dismissed in between given date range. Dismissed on %s' % (
            #             str(dismiss_date)
            #         ),
            #         'Dismissed'
            #     ]
            if dismiss_date < from_date:
                return False, [
                    'Employee already dismissed. Dismissed on %s' % (
                        str(dismiss_date)),
                    'Dismissed'
                ]

        employee_last_payroll = Payroll.objects.filter(
            Q(
                employees__id=employee.id
            ) & ~Q(
                status='Rejected'
            )
        ).order_by('-to_date', '-id').first()

        if employee_last_payroll:

            paid_to_date = employee_last_payroll.to_date

            class Lead(Func):
                function = 'lead'
                window_compatible = True

            upcoming_experiences = employee.user_experiences.filter(
                Q(
                    Q(start_date__gte=paid_to_date) &
                    Q(start_date__lte=to_date)
                ) |
                Q(
                    Q(end_date__gte=paid_to_date) &
                    Q(end_date__lte=to_date)
                )
            ).annotate(
                next_start=Window(
                    expression=Lead('start_date'),
                    order_by=F('id').asc()
                )
            ).order_by(
                'start_date'
            ).distinct(
                'start_date'
            ).values(
                'start_date',
                'end_date',
                'next_start'
            )

            gaps = [
                {
                    'start_date': obj.get('end_date') + datetime.timedelta(
                        days=1),
                    'end_date': obj.get('next_start') - datetime.timedelta(
                        days=1)
                } for obj in upcoming_experiences if
                obj.get('end_date') and obj.get('next_start') and obj.get(
                    'next_start') != (
                    obj.get('end_date') + datetime.timedelta(days=1)
                )]

            # this should be continious
            not_released_salary_holdings_after_last_payroll = SalaryHolding.objects.filter(
                released=False,
                employee=employee,
                from_date__date__gt=paid_to_date,
                to_date__date__lt=from_date
            ).annotate(
                start_date=F('from_date'),
                end_date=F('to_date')
            ).order_by('-from_date').values(
                'start_date',
                'end_date'
            )

            # Sort this by start date
            gaps = sorted(
                itertools.chain(
                    gaps, not_released_salary_holdings_after_last_payroll),
                key=lambda x: x.get('start_date')
            )

            for gap in gaps:
                # TODO @Ravi: think of overlap (Applied on holding model)
                if gap.get('start_date') == paid_to_date + datetime.timedelta(
                        days=1):
                    paid_to_date = gap.get('end_date')
                else:
                    break

            # if not_released_salary_holding_just_after_last_payroll:
            #     paid_to_date = not_released_salary_holding_just_after_last_payroll.to_date

            if not from_date == paid_to_date + datetime.timedelta(
                days=1
            ):
                message = f'Pending approval of last payroll generated on {str(paid_to_date)}'
                if employee_last_payroll.status == CONFIRMED:
                    message = f'Payment date range cannot have gap or overlap with previous ' \
                              f'payroll date range. Last paid on {str(paid_to_date)}'
                return False, [
                    message,
                    'Gap Or Overlap',
                    {'payroll_id': employee_last_payroll.id}
                ]
            # fd <= f <= td

            if employee_last_payroll.status == 'Generated':
                return False, [
                    'Pending Approval of last payroll',
                    'Pending Approval',
                    {'payroll_id': employee_last_payroll.id}
                ]
            if employee_last_payroll.status == APPROVAL_PENDING:
                return False, [
                    'Pending Approval of forwarded payroll',
                    'Pending Approval',
                    {'payroll_id': employee_last_payroll.id}
                ]
            if employee_last_payroll.status == APPROVED:
                return False, [
                    'Pending confirmation of last payroll',
                    'Pending Approval',
                    {'payroll_id': employee_last_payroll.id}
                ]
        else:
            if appoint_date:
                if appoint_date > to_date:
                    return False, [
                        'Cannot generate salary for date before \
                            employee is appointed.Employee appointed on %s.' % (
                            str(appoint_date)), 'Never Paid']

                if appoint_date < from_date:
                    return False, [
                        'Employee should be paid from appoint date.Employee appointed on %s.' % (
                            str(appoint_date)), 'Never Paid']
            else:
                return False, [
                    'Employee has no payroll appoint date']

        # Add validation here
        valid, errors = cls.validate_advance_salary_settings(employee, package_slot,
                                                             from_date, to_date)
        if not valid:
            return False, errors

        return True, None

    @staticmethod
    def check_employee_eligibility(employee, from_date, to_date, payroll_start_fiscal_year, timeframe_user_experiences, **kwargs):
        eligible, reason_args = PayrollGenerator.get_employee_payroll_eligibility(
            employee, from_date, to_date, payroll_start_fiscal_year, timeframe_user_experiences, **kwargs)
        if not eligible:
            employee_serialized_data = PayrollEmployeeSerializer(
                instance=employee,
                many=False).data
            if timeframe_user_experiences:
                employee_serialized_data['designation_name'] = str(
                    timeframe_user_experiences.last().job_title
                )

            return {
                'employee': employee_serialized_data,
                'reason_args': reason_args
            }

    @staticmethod
    def validate_employees_without_multiprocessing(employees, from_date, to_date, payroll_start_fiscal_year, **kwargs):
        not_eligibles = []
        for employee in employees:
            timeframe_user_experiences = employee.date_range_user_experiences(
                from_date,
                to_date
            )
            not_eligible_employee = PayrollGenerator.check_employee_eligibility(
                employee,
                from_date, to_date,
                payroll_start_fiscal_year,
                timeframe_user_experiences,
                **kwargs
            )
            if not_eligible_employee:
                not_eligibles.append(not_eligible_employee)
        return not_eligibles

    @staticmethod
    def validate_employees_with_multiprocessing(employees, from_date, to_date, payroll_start_fiscal_year, **kwargs):
        manager = multiprocessing.Manager()
        shared_list = manager.list()

        def on_result(result):
            pass

        def on_done():
            print('Employee validation completed.')

        def _validate_employee(args):
            employee, timeframe_user_experiences = args
            not_eligible_employee = PayrollGenerator.check_employee_eligibility(
                employee,
                from_date, to_date,
                payroll_start_fiscal_year,
                timeframe_user_experiences,
                **kwargs
            )
            if not_eligible_employee:
                shared_list.append(not_eligible_employee)
        users = []
        for emp in employees:
            timeframe_user_experiences = emp.date_range_user_experiences(
                from_date,
                to_date
            )
            users.append((emp, timeframe_user_experiences))
        t = fast_map_async(_validate_employee, users, on_result=on_result,
                           on_done=on_done, threads_limit=settings.Q_CLUSTER_AFFINITY,
                           procs_limit=settings.Q_CLUSTER_AFFINITY)
        t.join()
        return list(shared_list)

    @staticmethod
    def check_employees_payroll_eligibility(employees, from_date,
                                            to_date, payroll_start_fiscal_year, **kwargs):
        if settings.USE_MULTIPROCESSING:
            return PayrollGenerator.validate_employees_with_multiprocessing(employees, from_date,
                                                                            to_date,
                                                                            payroll_start_fiscal_year,
                                                                            **kwargs)
        else:
            return PayrollGenerator.validate_employees_without_multiprocessing(employees,
                                                                               from_date,
                                                                               to_date,
                                                                               payroll_start_fiscal_year,
                                                                               **kwargs)

    @staticmethod
    def generate_payroll(employee,
                         from_date,
                         to_date,
                         initial_extra_headings,
                         extra_headings,
                         edited_general_headings,
                         datework,
                         payroll_start_fiscal_year,
                         cutoff_date=None):

        PAYROLL_MONTH_DAYS_SETTING = 'ORGANIZATION_CALENDAR'  # setting is base.py

        appoint_date, dismiss_date, salary_packages = \
            PayrollGenerator.get_user_experience_calculation_data(
                employee,
                from_date,
                to_date,
                payroll_start_fiscal_year
            )

        if not salary_packages:
            raise CustomValidationError(
                {
                    'non_field_errors': ['Employee has no assigned package for given range.'],
                    'employee_id': employee.id,
                    'package_id': None,
                    'package_heading_id': None
                }
            )

        try:
            calculation = EmployeeSalaryCalculator(
                employee,
                datework,
                from_date,
                to_date,
                salary_packages,
                appoint_date,
                dismiss_date,
                initial_extra_headings=initial_extra_headings,
                month_days_setting=PAYROLL_MONTH_DAYS_SETTING,
                extra_headings=extra_headings.get(str(employee.id), {}),
                edited_general_headings=edited_general_headings.get(
                    str(employee.id), {}
                ),
                edited_general_headings_difference_except_tax_heading=edited_general_headings.get(
                    str(employee.id)).get(
                    'incomeDifference') if edited_general_headings.get(
                    str(employee.id)) else 0,
                package_assigned_date=salary_packages[0]["applicable_from"],
                simulated_from=cutoff_date
            )
        except helpers.InvalidVariableTypeOperation as err:
            raise CustomValidationError(
                {
                    'non_field_errors': ['Invalid variable type operation occurred while'
                                         ' processing package'],
                    'employee_id': err.employee.id,
                    'package_id': err.package_heading.package.id,
                    'package_heading_id': err.package_heading.id
                }
            )

        return calculation

    @staticmethod
    def get_valid_employee_for_payroll_generation(
            employees,
            exclude_filter,
            exclude_not_eligible,
            from_date,
            payroll_start_fiscal_year,
            to_date,
            **kwargs):

        not_eligibles = PayrollGenerator.check_employees_payroll_eligibility(
            employees,
            from_date,
            to_date,
            payroll_start_fiscal_year,
            **kwargs
        )
        if not_eligibles and exclude_not_eligible:
            exclude_filter['id__in'] = [
                emp.get('employee').get('id') for emp in not_eligibles]
            employees = employees.exclude(**exclude_filter)
        if not_eligibles and not exclude_not_eligible:
            raise CustomValidationError(error_dict=not_eligibles)

        return employees

    @staticmethod
    def sync_validate(request_data):
        """
        Sync part of validation
        Validation to perform before starting task of payroll generation in background
        """
        error_messages = dict()
        serializer = PayrollCreateSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        title = data.get('title')
        from_date = data.get('from_date')
        to_date = data.get('to_date')
        organization_slug = data.get('organization_slug').slug
        exclude_not_eligible = data.get('exclude_not_eligible')
        save = data.get('save')
        datework, payroll_start_fiscal_year = PayrollGenerator.get_FY(
            organization_slug,
            from_date,
            to_date
        )
        employee_filter_from_ser = data.get('employees_filter', {})

        employee_filter, exclude_filter = EmployeeFilterSerializer.get_filter_and_excludes(
            employee_filter_from_ser
        )

        cutoff_date = data.get("cutoff_date", None)
        if not cutoff_date:
            cutoff_date = to_date + datetime.timedelta(days=1)
        if cutoff_date > get_today():
            cutoff_date = get_today()
        simulated_from = None
        if cutoff_date <= to_date:
            simulated_from = cutoff_date
        users = employee_filter.pop("id__in", [])
        employee_filter = Q(**employee_filter)

        if users:
            employee_filter = employee_filter | Q(id__in=users)

        employees = Employee.objects.filter(detail__organization__slug=organization_slug).filter(
            employee_filter).exclude(
            **exclude_filter).select_essentials()
        employee_filter = {"id__in": employees.values_list('id', flat=True)}
        preparation_sheet = PreparationSheetOverview(
            from_date,
            to_date,
            simulated_from,
            organization_slug,
            employee_filter,
            exclude_filter
        )
        include_past_employee = data.get('include_past_employee', False)
        if not include_past_employee:
            employees = employees.current()
        else:
            employees = employees.past()
        employee_with_clean_request = Employee.objects.none()
        valid_employees = Employee.objects.none()
        clean_valid_employees = Employee.objects.none()

        try:
            employee_with_clean_request = preparation_sheet.get_valid_employees_with_clean_request(
                employees, exclude_not_eligible, exclude_filter)
        except CustomValidationError as e:
            error_messages['preparation_sheet'] = e.error_dict

        # used to set values of not eligible employees in validate_generate_payroll
        # I think, we don't need to set this here, as it is not used elsewhere
        # TODO: @anurag verify whether this is needed to be passed from here and remove this
        not_eligible_employees = {}
        try:
            valid_employees = PayrollGenerator.get_valid_employee_for_payroll(
                employees, exclude_filter, exclude_not_eligible, from_date,
                payroll_start_fiscal_year, to_date, cutoff_date=cutoff_date)
        except CustomValidationError as e:
            error_messages['not_eligibles'] = e.error_dict

        if error_messages.keys():
            raise CustomValidationError(error_dict=error_messages)

        if employee_with_clean_request.count() > 0 and valid_employees.count() > 0:
            clean_valid_employees = employee_with_clean_request.intersection(
                valid_employees)
        if clean_valid_employees.count() == 0:
            raise ValidationError(
                'None of the employees were eligible for payroll generation.')

        full_data = (
            data, datework, clean_valid_employees, not_eligible_employees, exclude_not_eligible,
            from_date, organization_slug, payroll_start_fiscal_year, save, to_date, title
        )

        return (
            serializer,
            full_data
        )

    @staticmethod
    def update_payroll(
        payroll,
        initial_extra_headings=dict(),
        extra_headings=dict(),
        edited_general_headings=dict(),
        **kwargs
    ):
        # callable from staticmethod and transaction.atomic resulted into error in app-compile so
        # using context manager instead
        with transaction.atomic():
            # TODO @wrufesh centralize it
            employees = payroll.employees.all()
            emp_extra_data = dict()
            employees_email = kwargs.get('employees_email', [])
            if employees_email:
                employees = employees.filter(email__in=employees_email)

            cache.set("total_number_of_payroll_to_be_generated", len(employees))

            def _on_result(result):
                cache.set("payroll_generated_employee_name", result.get('full_name'))
                count = cache.get('payroll_generated_employee_count', 0)
                count = count + 1
                cache.set("payroll_generated_employee_count", count)
                cache.set(
                    "total_number_of_payroll_to_be_generated",
                    cache.get('total_number_of_payroll_to_be_generated', 0)
                )
                emp_extra_data.update(result)

            def _on_done():
                cache.delete('payroll_generated_employee_count')
                print('all done')

            def _calculation(args):
                with transaction.atomic():
                    PAYROLL_MONTH_DAYS_SETTING = 'ORGANIZATION_CALENDAR'

                    datework, payroll_start_fiscal_year = PayrollGenerator.get_FY(
                        payroll.organization.slug,
                        payroll.from_date,
                        payroll.to_date
                    )
                    simulated_from = payroll.simulated_from
                    employee = args
                    emp_initial_extra_headings = initial_extra_headings.get(
                        employee.email
                    ) or initial_extra_headings.get(
                        employee.id
                    ) or {}
                    emp_extra_headings = extra_headings.get(
                        employee.email
                    ) or extra_headings.get(
                        employee.id
                    ) or {}

                    emp_edited_general_headings = payroll.extra_data.get('edited_general_headings',
                                                                         {}).get(
                        str(employee.id)
                    ) or edited_general_headings.get(
                        employee.id
                    ) or {}

                    new_emp_edited_general_headings = edited_general_headings.get(
                        employee.email
                    ) or edited_general_headings.get(
                        employee.id
                    ) or {}

                    emp_edited_general_headings.update(
                        new_emp_edited_general_headings
                    )

                    emp_extra_data.update({
                        employee.id: emp_edited_general_headings
                    })

                    appoint_date, dismiss_date, salary_packages = \
                        PayrollGenerator.get_user_experience_calculation_data(
                            employee,
                            payroll.from_date,
                            payroll.to_date,
                            payroll_start_fiscal_year
                        )
                    payroll_employee = payroll.employee_payrolls.get(employee=employee)
                    update_rebate_settings_from_payroll_edit(
                        employee, emp_edited_general_headings, payroll.from_date, payroll.to_date,
                        payroll.organization, payroll_employee.package
                    )

                    if not emp_extra_headings:
                        emp_extra_headings = get_extra_addition_and_deduction(payroll_employee)
                    calculation = EmployeeSalaryCalculator(
                        employee,
                        datework,
                        payroll.from_date,
                        payroll.to_date,
                        payroll_employee.package,
                        appoint_date,
                        dismiss_date,
                        initial_extra_headings=emp_initial_extra_headings,
                        month_days_setting=PAYROLL_MONTH_DAYS_SETTING,
                        extra_headings=emp_extra_headings,
                        edited_general_headings=emp_edited_general_headings,
                        edited_general_headings_difference_except_tax_heading=0,
                        package_assigned_date=salary_packages[0]["applicable_from"],
                        simulated_from=simulated_from,
                    )

                    edits = dict()
                    try:
                        employee_payroll = payroll.employee_payrolls.select_for_update().get(
                            employee=employee)
                    except Exception as e:
                        print(e, "exception")
                    for old_record in ReportRowRecord.objects.select_related('heading').filter(
                        employee_payroll=employee_payroll
                    ):

                        if old_record.heading:
                            amount = calculation.payroll.get_heading_amount_from_heading(
                                old_record.heading
                            )
                            old_amount = getattr(old_record, 'amount', None)
                            edits[old_record.heading.id] = (old_amount, amount)

                    if calculation.payroll.backdated_calculations:
                        calculation.payroll.backdated_calculations.update(
                            adjusted_payroll=employee_payroll
                        )

                    helpers.create_payroll_edit_remarks(
                        employee_payroll=employee_payroll,
                        edited_packages=edits,
                        remarks=kwargs.get('remarks', "Excel update default remarks"),
                        created_by=kwargs.get('edit_log').created_by
                    )

                    calculation.payroll.record_to_model(
                        payroll,
                        instance=employee_payroll
                    )
                    return {
                        employee.id: emp_edited_general_headings
                    }

            employees_data_for_calculation = []
            for employee in employees:
                employees_data_for_calculation.append((employee))
            t = fast_map_async(_calculation, employees_data_for_calculation, on_result=_on_result,
                               on_done=_on_done, threads_limit=settings.Q_CLUSTER_AFFINITY,
                               procs_limit=settings.Q_CLUSTER_AFFINITY)
            t.join()


            cache.delete("payroll_generated_employee_name")
            cache.delete('total_number_of_payroll_to_be_generated')
            payroll.extra_data.update({
                "edited_general_headings": emp_extra_data
            })

            payroll.save()

            # TODO @wrufesh discuss about below comments
            # With current implementaion
            # if someone edits repayment heading repayment will not be calculated

            # Repayment cal be done using plugin

            return payroll

    @staticmethod
    def generate_payrolls(payroll_generation,
                          data,
                          datework,
                          employees,
                          exclude_filter,
                          exclude_not_eligible,
                          from_date,
                          organization_slug,
                          payroll_start_fiscal_year,
                          save,
                          to_date,
                          title,
                          payroll: Payroll = None
                          ):
        """Generate payrolls for multiple employees"""

        if not datework:
            datework = FY(payroll_generation.organization)

        logger.debug(f"Starting payroll generation of {payroll_generation.organization} with data "
                     f"{payroll_generation.data}")
        cls = PayrollGenerator

        initial_extra_headings = data.get('initial_extra_headings')

        extra_headings = data.get(
            'extra_headings',
            {}
        )
        edited_general_headings = data.get(
            'edited_general_headings',
            {}
        )

        cutoff_date = data.get("cutoff_date", None)
        if not cutoff_date:
            cutoff_date = to_date + datetime.timedelta(days=1)
        if cutoff_date > get_today():
            cutoff_date = get_today()

        count = 0

        simulated_from = None
        if cutoff_date and cutoff_date <= to_date:
            simulated_from = cutoff_date

        action = "Employee Added in payroll"
        employee_added = True
        if not payroll:
            payroll = Payroll.objects.create(
                organization=Organization.objects.get(
                    slug=organization_slug
                ),
                extra_data={
                    'initial_extra_headings': [h.id for h in initial_extra_headings],
                    'extra_headings': extra_headings,
                    'edited_general_headings': edited_general_headings
                },
                from_date=from_date,
                to_date=to_date,
                status=PROCESSING,
                simulated_from=simulated_from,
                title=title
            )
            action = "generated payroll"
            employee_added = False
        payroll_generation.status = PROCESSING
        payroll_generation.payroll = payroll
        payroll_generation.save()

        cache.set("total_number_of_payroll_to_be_generated", len(employees))

        def _on_result(result):
            cache.set("payroll_generated_employee_name", result.full_name)
            count = cache.get('payroll_generated_employee_count', 0)
            count = count + 1
            cache.set("payroll_generated_employee_count", count)
            cache.set(
                "total_number_of_payroll_to_be_generated",
                cache.get('total_number_of_payroll_to_be_generated', 0)
            )
            logger.debug(f"payroll_generated_employee_count {count}")

        def _on_done():
            print('all done')

        def _calculation(args):
            employee, \
                from_date, \
                to_date, \
                initial_extra_headings, \
                extra_headings, \
                edited_general_headings, \
                payroll_start_fiscal_year, \
                cutoff_date, payroll, payroll_generation = args
            try:
                print("calculation started for employee", employee, datetime.datetime.now())
                calculation = cls.generate_payroll(
                    employee,
                    from_date,
                    to_date,
                    initial_extra_headings,
                    extra_headings,
                    edited_general_headings,
                    datework,
                    payroll_start_fiscal_year,
                    cutoff_date=cutoff_date
                )
                employee_payroll = calculation.payroll.record_to_model(payroll)
                if calculation.settled_repayment:
                    repayment = calculation.settled_repayment
                    repayment.payroll_reference = employee_payroll
                    repayment.save()

            except CustomValidationError as e:
                if not employee_added:
                    payroll.delete()
                else:
                    payroll.employee_payrolls.filter(employee__in=employees).delete()
                return cls.raise_error(
                    payroll_generation,
                    e.error_dict
                )
            return employee

        employees_data_for_calculation = []
        for employee in employees:
            employees_data_for_calculation.append((employee,
                                                   from_date,
                                                   to_date,
                                                   initial_extra_headings,
                                                   extra_headings,
                                                   edited_general_headings,
                                                   payroll_start_fiscal_year,
                                                   cutoff_date, payroll, payroll_generation))
        t = fast_map_async(_calculation, employees_data_for_calculation, on_result=_on_result,
                           on_done=_on_done, threads_limit=settings.Q_CLUSTER_AFFINITY,
                           procs_limit=settings.Q_CLUSTER_AFFINITY)
        t.join()

        cache.delete("payroll_generated_employee_name")
        cache.delete('payroll_generated_employee_count')
        cache.delete('total_number_of_payroll_to_be_generated')

        payroll.status = GENERATED
        payroll.save()
        PayrollApprovalHistory.objects.create(
            actor=payroll_generation.created_by,
            action=action,
            payroll=payroll
        )

        return cls.send_success(payroll_generation, payroll)

    @staticmethod
    def raise_error(payroll_generation, error_dict):
        payroll_generation.status = FAILED
        payroll_generation.errors = error_dict
        payroll_generation.save()

        notify_organization(
            "Payroll generation failed.",
            organization=payroll_generation.organization,
            action=payroll_generation,
            permissions=[GENERATE_PAYROLL_PERMISSION],
            url=f'/admin/{payroll_generation.organization.slug}/payroll/generate?'
                f'log_id={payroll_generation.id}'
        )

    @staticmethod
    def send_success(payroll_generation, payroll):
        payroll_generation.payroll = payroll
        payroll_generation.status = COMPLETED
        payroll_generation.save()
        notify_organization(
            f"Payroll of {payroll_generation.organization} from {payroll.from_date} "
            f"{payroll.to_date} has been generated.",
            organization=payroll_generation.organization,
            action=payroll_generation,
            permissions=[GENERATE_PAYROLL_PERMISSION],
            url=f'/admin/{payroll.organization.slug}/payroll/collection/detail/{payroll.id}'
        )


def is_payroll_in_processing_or_generated_state(organization, sender=None, date=None):
    payroll_history_filter = {
        "organization": organization,
        "status": PROCESSING
    }
    payroll_filter = {
        "organization": organization,
        "status": GENERATED
    }
    payroll_exists = False
    if date:
        payroll_history_filter = {
            **payroll_history_filter,
            "payroll__from_date__lte": date,
            "payroll__to_date__gte": date
        }
        payroll_filter = {
            **payroll_filter,
            "from_date__lte": date,
            "to_date__gte": date
        }
        payroll_exists = Payroll.objects.filter(**payroll_filter, employees=sender).exists()

    return (
        PayrollGenerationHistory.objects.filter(**payroll_history_filter).exists()
        or payroll_exists
    )


def raise_validation_error_if_payroll_in_generated_or_processing_state(organization, sender=None,
                                                                       date=None):
    if is_payroll_in_processing_or_generated_state(organization, date=date, sender=sender):
        raise ValidationError("Payroll is either in generated or processing state.")


def validate_if_package_heading_updated_after_payroll_generated_previously(package):
    if package.is_used_package:
        raise ValidationError("Can not make changes in package once payroll is generated.")
