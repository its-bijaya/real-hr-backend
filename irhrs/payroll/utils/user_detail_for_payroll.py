"""
User related details to be shown in payroll collection detail and excel export
"""
from irhrs.core.utils.common import humanize_interval
from irhrs.organization.models import Organization
from irhrs.payroll.api.v1.serializers.payslip import HourlyAttendanceDetails, \
    PayslipAttendanceDetailsSerializer
from irhrs.payroll.models import EmployeePayroll, OrganizationPayrollConfig


def get_user_detail_for_payroll(employee_payroll: EmployeePayroll, organization: Organization):
    from irhrs.payroll.utils.generate import PayrollGenerator
    attendance_details = HourlyAttendanceDetails(
        employee_payroll.employee,
        context={
            'from_date': employee_payroll.payroll.from_date,
            'to_date': employee_payroll.payroll.to_date,
            'simulated_from': employee_payroll.payroll.simulated_from
        }
    )

    include_holiday_offday = False
    payroll_config = OrganizationPayrollConfig.objects.filter(
        organization=organization
    ).first()
    if payroll_config:
        include_holiday_offday = payroll_config.include_holiday_offday_in_calculation

    payslip_attendance_serializer = PayslipAttendanceDetailsSerializer(
        employee_payroll.employee,
        context={
            "from_date": employee_payroll.payroll.from_date,
            "to_date": employee_payroll.payroll.to_date,
            "simulated_from": employee_payroll.payroll.simulated_from,
            "include_holiday_offday": include_holiday_offday
        }
    )

    date_work, payroll_config = PayrollGenerator.get_FY(
        employee_payroll.payroll.organization.slug,
        employee_payroll.payroll.from_date,
        employee_payroll.payroll.to_date
    )
    appoint_date, dismiss_date, slots = (
        PayrollGenerator.get_user_experience_calculation_data(
            employee_payroll.employee,
            employee_payroll.payroll.from_date,
            employee_payroll.payroll.to_date,
            payroll_config
        )
    )
    package_name = " - ".join(getattr(slot.get('package'), 'name', '')
                              for slot in slots)
    res = {
        'package_name': package_name,
        'working_days': payslip_attendance_serializer.get_working_days(
            employee_payroll.employee
        ),
        'worked_days': payslip_attendance_serializer.get_worked_days(
            employee_payroll.employee
        ),
        'worked_hours': humanize_interval(
            attendance_details.hourly_details['total_worked_hours']),
        'overtime_hours': humanize_interval(
            attendance_details.hourly_details['actual_overtime_hours']),
        'absent_days': payslip_attendance_serializer.get_absent_days(employee_payroll.employee),
        'step': slots[-1]["current_step"]
    }
    return res, slots
