### CORE MISSING OFFDAY FIX ###
from dateutil.parser import parse
from dateutil.rrule import rrule, DAILY
from django.forms.models import model_to_dict
from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from irhrs.attendance.constants import HOLIDAY, WORKDAY, OFFDAY
from irhrs.attendance.managers.utils import fix_entries_on_commit
from irhrs.attendance.models import IndividualUserShift, TimeSheet
from irhrs.core.utils.common import combine_aware

USER = get_user_model()
PROVIDED_EMAILS = [
    'shrijana.shrestha@rojgari.com',
    'shova.bakhu@rojgari.com',
    'shrijana.shrestha@rojgari.com',
    'shova.bakhu@rojgari.com',
    'madan.giri@rojgari.com',
    'ujwal.shrestha@merojob.com',
    'raju.bhattarai@aayulogic.com',
    'prahlad.shrestha@aayulogic.com',
    'sanjeev.shrestha@aayulogic.com',
    'rohit.shrestha@aayulogic.com',
    'prabin.acharya@aayulogic.com',
    'pujan.shrestha@aayulogic.com',
    'santosh.aryal@aayulogic.com',
    'umesh.chaudhary@aayulogic.com',
    'sumit.chhetri@aayulogic.com',
    'babin.subedi@merojob.com',
    'reza.khanal@merojob.com',
    'nisha.gyawali@merojob.com',
    'yagyashree.dahal@merojob.com',
    'priyanka.basnet@merojob.com',
    'rajesh.manandhar@merojob.com',
    'mukesh.ghising@merojob.com',
    'ajay.shrestha@aayulogic.com',
    'sandip.balami@rojgari.com',
    'sujan.chitrakar@merojob.com',
    'kamala.khanal@aayulogic.com',
    'shital.luitel@aayulogic.com',
    'niroj.maharjan@rojgari.com',
    'kritika.katwal@merojob.com',
    'sumit.dhital@rojgari.com',
]
DATE_START = '2020-03-01'
DATE_UNTIL = '2020-03-24'
date_iterator = list(
    map(
        lambda d: d.date(),
        rrule(freq=DAILY, dtstart=parse(DATE_START), until=parse(DATE_UNTIL))
    )
)
user_iterator = get_user_model().objects.filter(
    email__in=PROVIDED_EMAILS
)

for date in date_iterator:
    for user in user_iterator:
        timesheets, created_count, updated_count, status = TimeSheet.objects._create_or_update_timesheet_for_profile(
            user=user,
            date_=date
        )
        print(
            str(date),
            user.full_name.ljust(20)[:20],
            str(created_count).ljust(5),
            str(updated_count).ljust(5),
            str(status).ljust(5),
        )
