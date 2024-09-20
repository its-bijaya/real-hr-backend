from irhrs.attendance.api.v1.serializers.attendance import IndividualAttendanceSettingSerializer, \
    AttendanceUserMapSerializer
from irhrs.attendance.models import IndividualAttendanceSetting, AttendanceUserMap
from irhrs.hris.models import LeaveAccount, UserResultArea
from irhrs.leave.api.v1.serializers.account import LeaveAccountSerializer
from irhrs.payroll.models import EmployeePayroll, UserExperiencePackageSlot
from irhrs.hris.api.v1.serializers.supervisor_authority import UserSupervisorSerializer
from irhrs.users.models import UserSupervisor


def get_user_settings_overview(user_id, user, serializer_context):
    individual_attendance_settings = getattr(user, 'attendance_setting', None)
    if not individual_attendance_settings:
        return {
            "message": "No data available"
        }
    serialized_individual_attendance_settings = \
        IndividualAttendanceSettingSerializer(
            individual_attendance_settings, context=serializer_context
        ).data

    user_status = user.account_status
    has_current_experience = True if user.current_experience else False

    supervisors = UserSupervisor.objects.filter(user=user_id).order_by("authority_order")
    serialized_supervisors = UserSupervisorSerializer(
        supervisors, context=serializer_context, many=True
    ).data
    first_level_supervisor = user.first_level_supervisor
    supervisor_data = []
    for supervisor_ in serialized_supervisors:
        supervisor = supervisor_.get("supervisor")
        supervisor_data.append({
            "supervisor": {
                "id": supervisor.get('id'),
                "profile_picture": supervisor.get('profile_picture'),
                "cover_picture": supervisor.get('cover_picture'),
                "full_name": supervisor.get('full_name'),
                "job_title": supervisor.get('job_title'),
                "is_online": supervisor.get('is_online'),
            },
            "authority_order": supervisor_.get('authority_order'),
            "approve": supervisor_.get('approve'),
            "forward": supervisor_.get('forward'),
            "deny": supervisor_.get('deny')
        }
        ) if first_level_supervisor else supervisor_data

    work_shift = serialized_individual_attendance_settings.get('work_shift')
    overtime_settings = serialized_individual_attendance_settings.get('overtime_setting')
    credit_hour = serialized_individual_attendance_settings.get('credit_hour_setting')
    web_attendance_setting = serialized_individual_attendance_settings.get('web_attendance')
    late_in_email_notifications = serialized_individual_attendance_settings\
        .get('late_in_notification_email')
    absent_email_notifications = serialized_individual_attendance_settings\
        .get('absent_notification_email')
    weekly_attendance_report_email = serialized_individual_attendance_settings \
        .get('weekly_attendance_report_email')
    overtime_reminder_email_notifications = serialized_individual_attendance_settings\
        .get('overtime_remainder_email')

    device_bio_id_settings = AttendanceUserMap.objects.filter(
        setting__user=user_id
    ).values_list('bio_user_id', flat=True)

    leave_settings = LeaveAccount.objects.filter(
        user=user_id, is_archived=False
    ).values_list('rule__leave_type__name', flat=True)

    payroll_package = UserExperiencePackageSlot.objects.filter(
        user_experience__user_id=user_id
    ).order_by('-active_from_date').values_list('package__name', flat=True).first()

    ra_and_core_tasks_assigned = UserResultArea.objects.filter(user_experience__user_id=user_id)\
        .exists()

    return {
            "user_status": user_status,
            "has_current_experience": has_current_experience,
            "supervisors": supervisor_data,
            "work_shift": work_shift,
            "overtime_settings": overtime_settings,
            "credit_hour": credit_hour,
            "web_attendance_setting": web_attendance_setting,
            "device_bio_id_settings": device_bio_id_settings,
            "leave_settings": leave_settings,
            "payroll_package": payroll_package,
            "ra_and_core_tasks_assigned": ra_and_core_tasks_assigned,
            "email_notifications": {
                "late_in_notification_email": late_in_email_notifications,
                "absent_notification_email": absent_email_notifications,
                "weekly_attendance_report_email": weekly_attendance_report_email,
                "overtime_remainder_email": overtime_reminder_email_notifications
            }
        }
