"""
This Util is intended to use only for development purposes. It can be ignored
while we port codes to a production server.
"""


def random_punch_in():
    import random
    from datetime import time
    from django.contrib.auth import get_user_model
    from irhrs.attendance.models import TimeSheet
    from irhrs.core.utils.common import combine_aware
    from django.utils import timezone
    from irhrs.attendance.constants import DEVICE

    for u in get_user_model().objects.filter(
        is_active=True,
        is_blocked=False,
        attendance_setting__isnull=False,
    ):
        for time_z in [
            time(
                random.randint(8, 11),
                random.randint(0, 59),
            ),
            time(
                random.randint(12, 13),
                random.randint(0, 30),
            ),
            time(
                random.randint(14, 15),
                random.randint(0, 30),
            ),
            time(
                random.randint(17, 20),
                random.randint(0, 59),
            ),
        ]:
            TimeSheet.objects.clock(
                u,
                combine_aware(
                    timezone.now().date(),
                    time_z
                ),
                DEVICE
            )
