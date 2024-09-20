"""Enable Web Attendance for all current users"""

from django.contrib.auth import get_user_model
from django.db import transaction

from irhrs.attendance.models.attendance import IndividualAttendanceSetting, WebAttendanceFilter

User = get_user_model()


def main():
    settings = IndividualAttendanceSetting.objects.filter(
        user__in=User.objects.all().current()
    )

    web_filters_to_create = [
        WebAttendanceFilter(
            setting=setting,
            allow=True,
            cidr='0.0.0.0/0'
        )
        for setting in settings
    ]

    with transaction.atomic():
        settings.update(web_attendance=True)

        # if attendance filter already exists, ignore them
        WebAttendanceFilter.objects.bulk_create(
            web_filters_to_create,
            ignore_conflicts=True
        )


if __name__ == "__main__":
    main()
