from django.db.models import F, Case, When, Value, Q
from django.db.models.functions import Concat

from irhrs.payroll.models.payroll import CONFIRMED, OrganizationPayrollConfig, EmployeePayroll, \
    ReportRowRecord, EXTRA_ADDITION, EXTRA_DEDUCTION, PackageHeading


def get_employee_payrolls_via_settings(qs, organization):
    payroll_config = OrganizationPayrollConfig.objects.filter(
        organization=organization
    ).first()
    if not (payroll_config and payroll_config.show_generated_payslip):
        return qs.filter(payroll__status=CONFIRMED)
    return qs


def get_extra_addition_and_deduction(payroll_employee: EmployeePayroll) -> dict:
    emp_extra_headings = {}
    for record in ReportRowRecord.objects.filter(
        employee_payroll=payroll_employee,
        heading__type__in=[EXTRA_ADDITION, EXTRA_DEDUCTION],
        amount__gt=0
    ):
        package_heading = record.package_heading
        if not package_heading:
            package_heading = PackageHeading.objects.filter(
                package=payroll_employee.package,
                heading=record.heading).first()
            if not package_heading:
                continue
        emp_extra_headings[str(record.heading_id)] = {
            'value': str(record.amount),
            'package_heading_id': package_heading.id
        }
    return emp_extra_headings


def get_filtered_employee_payrolls_from_query_params(payroll, query_params):
    # Ordering a/c to employee.
    allowed_employee_ordering = [
        'full_name', '-full_name',
        'employee_level_hierarchy', '-employee_level_hierarchy'
    ]
    ordering = query_params.get('ordering')
    payroll_employees = payroll.employee_payrolls.order_by(
        '-employee__detail__joined_date'
    )
    if ordering in allowed_employee_ordering:
        ord_map = {
            'full_name': [
                F('employee__first_name'),
                F('employee__middle_name'),
                F('employee__last_name'),
            ],
            '-full_name': [
                F('employee__first_name').desc(),
                F('employee__middle_name').desc(),
                F('employee__last_name').desc(),
            ],
            'employee_level_hierarchy': [F('employee__detail__employment_level__order_field')],
            '-employee_level_hierarchy': [F('employee__detail__employment_level__order_field').desc()]
        }
        payroll_employees = payroll_employees.order_by(
            *ord_map.get(ordering)
        )
    # Ordering a/c to employee.
    # Search Filter
    search = query_params.get('full_name')
    if search:
        search = search.strip()
        payroll_employees = payroll_employees.annotate(
            __full_name= Concat(
                'employee__first_name', Value(' '),
                Case(
                    When(
                        ~Q(employee__middle_name=''),
                        then=Concat(
                            'employee__middle_name', Value(' ')
                        )
                    ),
                    default=Value('')
                ),
                'employee__last_name', Value(' ')
            )
        ).filter(
            Q(__full_name__icontains=search)|Q(employee__username__icontains=search)
        )
    filter_mapper = {
        'job_title': 'employee__detail__job_title__slug',
        'division': 'employee__detail__division__slug',
        'employment_level': 'employee__detail__employment_level__slug',
        'employment_type': 'employee__detail__employment_status__slug',
        'branch': 'employee__detail__branch__slug',
        'bank': 'employee__userbank__bank__slug',
        'username': 'employee__username',
    }
    fil = {}
    for item in query_params.keys():
        if item in filter_mapper.keys():
            value = query_params.get(item)
            if value:
                fil[filter_mapper[item]] = value
    return payroll_employees.filter(**fil)
