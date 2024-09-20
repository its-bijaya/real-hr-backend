from django.contrib.auth import get_user_model

from irhrs.attendance.models import IndividualAttendanceSetting


def create_attendance_setting_for_all_users():
    """
    Creates attendance setting for all users.
    """
    users_with_no_attendance_setting = get_user_model().objects.filter(
        attendance_setting__isnull=True
    )
    IndividualAttendanceSetting.objects.bulk_create(
        [
            IndividualAttendanceSetting(
                user=user
            ) for user in users_with_no_attendance_setting
        ]
    )
