import itertools
from collections import defaultdict
from datetime import date, timedelta
from typing import Union

from django.contrib.auth import get_user_model
from django.db import transaction

from irhrs.organization.models import FY
from irhrs.payroll.models import ReportRowRecord, Package, OrganizationPayrollConfig, \
    UserExperiencePackageSlot, EmployeePayroll, BackdatedCalculation, EXTRA_ADDITION, \
    EXTRA_DEDUCTION
from irhrs.payroll.utils.calculator import EmployeeSalaryCalculator
from irhrs.payroll.utils import helpers
from irhrs.payroll.utils.generate import PayrollGenerator

Employee = get_user_model()


def get_payroll_config(organization):
    return OrganizationPayrollConfig.objects.filter(
        organization=organization
    ).first()


def get_generated_report_rows(employee: Employee, from_date: date, to_date: date) -> list:
    """
    Fetches report rows of employee for given date range
    :param employee: Employee / User instance
    :param from_date: start_date
    :param to_date: end_date
    :return: list of report rows
    """
    return list(ReportRowRecord.objects.filter(
        employee_payroll__employee=employee,
        employee_payroll__payroll__from_date__lte=to_date,
        employee_payroll__payroll__to_date__gte=from_date
    ).distinct().order_by('employee_payroll__payroll__from_date'))


def generate_payroll(employee: Employee, from_date: date, to_date: date,
                     salary_package: Package) -> list:
    """
    Generate payroll using for user using given salary package
    """
    organization = employee.detail.organization
    datework = FY(organization)
    payroll_config = get_payroll_config(organization)

    if not payroll_config:
        return []
    appoint_date = helpers.get_appoint_date(employee, payroll_config)

    if not employee.current_experience:
        return []
    dismiss_date = helpers.get_dismiss_date(employee, employee.current_experience)

    calculator = EmployeeSalaryCalculator(
        employee,
        datework,
        from_date,
        to_date,
        salary_package,
        appoint_date,
        dismiss_date,
        True,  # calculate_tax
        month_days_setting='ORGANIZATION_CALENDAR'
    )

    return calculator.payroll.rows


def group_generated_report_rows(rows: list) -> dict:
    """
    Groups by heading and returns report row and sum of amounts
    :param rows: [<Basic Salary: 1000>, <Basic Salary: 2000>]
    :return: {<Basic Salary>: 3000}
    """
    result = defaultdict(int)
    for row in rows:
        result[row.heading] += row.amount
    return dict(result)


def calculate_back_dated_payroll_diff(employee: Employee, from_date: date, to_date: date,
                                      salary_package: Union[Package, list]) -> list:
    """
    :param employee:
    :param from_date:
    :param to_date:
    :param salary_package:
    :return:
    """
    generated_rows = group_generated_report_rows(
        get_generated_report_rows(employee, from_date, to_date)
    )
    new_rows = group_generated_report_rows(
        generate_payroll(employee, from_date, to_date, salary_package)
    )

    result = []

    for heading in set(itertools.chain(generated_rows, new_rows)):
        if heading.type in ["Addition", "Deduction", EXTRA_ADDITION, EXTRA_DEDUCTION]:
            result.append({
                "heading": heading,
                "previous_amount": generated_rows.get(heading),
                "current_amount": new_rows.get(heading)
            })
    return result


def get_arguments_for_calculate_back_dated_payroll_diff(
    package_slot: UserExperiencePackageSlot
) -> tuple:
    """
    Returns arguments to be passed in calculate_back_dated_payroll_diff
    :param package_slot: package slot to calculate backdated payroll
    :return: (employee, from_date, to_date, salary_packages)
    """

    if not package_slot.backdated_calculation_from:
        raise AssertionError("Package Slot must have backdated_calculation_from set")

    employee = package_slot.user_experience.user
    organization = employee.detail.organization

    payroll_start_date = EmployeePayroll.objects.filter(
        payroll__to_date__gte=package_slot.backdated_calculation_from,
        employee=employee
    ).order_by('payroll__from_date').values_list('payroll__from_date', flat=True).first()

    from_date = min(payroll_start_date, package_slot.backdated_calculation_from) \
        if payroll_start_date else package_slot.backdated_calculation_from
    to_date = package_slot.active_from_date - timedelta(days=1)

    payroll_config = get_payroll_config(organization)

    appoint_date, dismiss_date, salary_packages = \
        PayrollGenerator.get_user_experience_calculation_data(
            employee,
            from_date,
            to_date,
            payroll_config
        )

    from_date = max(appoint_date, from_date)
    to_date = min(dismiss_date, to_date) if dismiss_date else to_date

    applicable_salary_packages = list()

    for salary_package in salary_packages:
        if salary_package["to_date"] < package_slot.backdated_calculation_from:
            # directly append packages before our from date
            applicable_salary_packages.append(salary_package)
        elif salary_package["from_date"] < package_slot.backdated_calculation_from:
            # end partial applicable before our from date
            salary_package["to_date"] = package_slot.backdated_calculation_from - timedelta(days=1)
            applicable_salary_packages.append(salary_package)

    applicable_salary_packages.append({
        "package": package_slot.package,
        "from_date": package_slot.backdated_calculation_from,
        "to_date": to_date,
        "applicable_from": package_slot.active_from_date,
        "job_title": getattr(package_slot.user_experience.job_title, "title", ""),
        "current_step": package_slot.user_experience.current_step,
        "employment_status": getattr(package_slot.user_experience.employment_status, "title", "")
    })

    return (
        employee,
        from_date,
        to_date,
        applicable_salary_packages
    )


@transaction.atomic
def update_or_create_backdated_payroll(package_slot: UserExperiencePackageSlot) -> None:

    BackdatedCalculation.objects.filter(package_slot=package_slot).delete()
    if package_slot.backdated_calculation_from:

        args = get_arguments_for_calculate_back_dated_payroll_diff(package_slot)
        diffs = calculate_back_dated_payroll_diff(*args)

        calculations = [
            BackdatedCalculation(
                package_slot=package_slot,
                **diff
            )
            for diff in diffs
        ]
        if calculations:
            BackdatedCalculation.objects.bulk_create(calculations)
            # quick hack to disable signal
            UserExperiencePackageSlot.objects.filter(id=package_slot.id).update(
                backdated_calculation_generated=True)

