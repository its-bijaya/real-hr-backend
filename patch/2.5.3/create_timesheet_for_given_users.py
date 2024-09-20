from dateutil.parser import parse
from dateutil.rrule import rrule, DAILY
from django.contrib.auth import get_user_model
from django.db import DatabaseError, transaction

from irhrs.attendance.models import TimeSheet

USER_FILTERS = [
    {
        'email': 'prabin.acharya@aayulogic.com',
    },
    {
        'email': 'sanjeev.shrestha@aayulogic.com',
    },
    {
        'email': 'rohit.shrestha@aayulogic.com',
    },
    {
        'email': 'sumit.chhetri@aayulogic.com',
    },
    {
        'email': 'prahlad.shrestha@aayulogic.com',
    },
    {
        'email': 'raju.bhattarai@aayulogic.com',
    },

]

DATE_LIST_PARSED = list(
    rrule(
       freq=DAILY,
       dtstart=parse('2020-01-01'),
       until=parse('2020-03-18')
    )
)
USER = get_user_model()


def populate_time_sheet_for_given_dates():
    """
    Create time-sheet for individual user for given dates.
    :return:
    """
    for user_filter in USER_FILTERS:
        user = USER.objects.get(**user_filter)
        for _date in DATE_LIST_PARSED:
            (
                timesheets, created_count, updated_count, status
            ) =  TimeSheet.objects._create_or_update_timesheet_for_profile(
                user=user,
                date_=_date
            )
            print(user, 'Time Sheet creation for', _date, status)


with transaction.atomic():
    populate_time_sheet_for_given_dates()
