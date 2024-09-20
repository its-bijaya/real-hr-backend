"""

[#2818]
As a supervisor, I want to assign shifts(rooster) to employees so
that I can manage their shift timings.


{
    "metadata": {
        user_id: {
            "full_name": ""
        }
    },
    "data": {
        user_id: {
            1: "DS",
            2: "NS",
            .
            .
            .
            32: "O",
        }
    },
}
"""
from dateutil.rrule import DAILY, rrule
from django.contrib.auth import get_user_model
from django.db.models import Q
from irhrs.attendance.models.attendance import IndividualUserShift

from irhrs.attendance.models.shift_roster import TimeSheetRoster
from irhrs.attendance.utils.helpers import get_weekday
from irhrs.core.utils.common import get_today
from irhrs.notification.utils import add_notification, notify_organization
from irhrs.organization.models.fiscal_year import FiscalYearMonth
from irhrs.permission.constants.permissions import ATTENDANCE_TIMESHEET_ROSTER_PERMISSION

USER = get_user_model()


def annotate_current_shift(paginated_users):
    return {
        user.id: find_shift_timings(user)
        for user in paginated_users
    }


def find_work_shift(user, date):
    """Returns rooster shift for the user if exists, default: work shift for the day"""
    return user.attendance_setting.work_shift_for(date)


def find_shift_timings(user):
    fiscal_year_month = FiscalYearMonth.objects.filter(
        start_at__lte='2021-02-16'
    ).order_by('-end_at').first()
    date_generator = rrule(
        DAILY,
        dtstart=fiscal_year_month.start_at,
        until=fiscal_year_month.end_at
    )

    date_iterator = list(
        map(
            lambda dt: dt.date(),
            date_generator
        )
    )

    # def get_initials(name):
    #     return name #(name[0] + name[-1]).upper()

    def get_initials(n):
        return n.name if n else 'N/A'

    return {
        int(_date.strftime('%d')):
        get_initials(find_work_shift(user=user, date=_date))
        for _date in date_iterator
    }


def date_iterator(start, end):
    return map(
        lambda dt: dt.date(),
        rrule(
            DAILY,
            dtstart=start,
            until=end
        )
    )


def find_shift_timings_for_future(user, fym):
    shift_qs = user._attendance_setting._shift
    res = {
        str(_date): roster_shift_display(
            getattr(
                next(filter(lambda obj: obj.applicable_from <= _date <= obj._end_date, shift_qs), None),
                'shift', None
            )
        )
        for _date in date_iterator(fym.start_at, fym.end_at)
    }
    return res


def populate_shift_roster(user_qs, fiscal_month):
    dates = filter(
        lambda date_: date_ > get_today(),
        date_iterator(fiscal_month.start_at, fiscal_month.end_at)
    )
    # Remove Existing and re-create.
    TimeSheetRoster.objects.filter(
        user__in=user_qs,
        date__in=dates
    ).delete()


def roster_shift_display(shift):
    if not shift:
        return {}
    work_shift_legend = shift.work_shift_legend
    return {
        'id': shift.id,
        'name': shift.name,
        'legend_text': work_shift_legend.legend_text,
        'legend_color': work_shift_legend.legend_color
    }


def get_shift_for_user(user, date_):
    # if roster exists for date, pull shift from roster.
    roster = TimeSheetRoster.objects.filter(
        user=user,
        date=date_
    ).first()
    if roster:
        shift = roster.shift

        weekday = get_weekday(date_)
        work_day = shift.work_days.filter(
            day=weekday,
        ).filter(
            Q(
                applicable_from__lte=date_,
            ) & Q(
                Q(applicable_to__isnull=True) |
                Q(applicable_to__gte=date_)
            )
        ).first()

        # simulate prefetch_work_shift_for_date
        shift.days = [work_day] if work_day else []

        return shift
    user.attendance_setting.force_prefetch_for_work_shift = True
    user.attendance_setting.force_work_shift_for_date = date_
    shift = user.attendance_setting.work_shift
    return shift


def send_roster_notification(user, fiscal_month):
    text = 'Your roster for the month of %s has been updated.' % fiscal_month.display_name
    org_notification_text = 'TimeSheet Roster of %s for the month of %s has been updated' % (
        user.full_name,
        fiscal_month.display_name
    )
    roster_fe_url = '/user/attendance/reports/roster/?fiscal_month=%s' % fiscal_month.id
    roster_hr_url = '/admin/%s/attendance/reports/roster/?fiscal_month=%s' % (
        user.detail.organization.slug,
        fiscal_month.id
    )
    add_notification(
        text=text,
        recipient=user,
        action=user,
        url=roster_fe_url
    )
    notify_organization(
        text=org_notification_text,
        action=user,
        organization=user.detail.organization,
        url=roster_hr_url,
        permissions=[ATTENDANCE_TIMESHEET_ROSTER_PERMISSION]
    )


def segregate_roster_payload(roster_list, user, fiscal_month):
    base_qs = TimeSheetRoster.objects.filter(
        user=user,
        date__range=(fiscal_month.start_at, fiscal_month.end_at)
    )
    _extant = base_qs.filter(
        date__in=map(lambda payload: payload['date'], roster_list)
    )
    _obsolete = _extant.exclude(
        date__in=[
            payload_['date'] for payload_ in filter(lambda payload: payload['shift'], roster_list)
        ]
    )
    _extant_dates = _extant.values_list('date', flat=True)
    _new = filter(
        lambda payload: payload['date'] not in _extant_dates,
        roster_list
    )
    return _new, _extant, _obsolete


def get_shift_details(user, end, start):
    shift_exists_for_start = IndividualUserShift.objects.filter(
        individual_setting__user=user,
        applicable_from__lte=start
    ).filter(
        Q(
            applicable_to__isnull=True
        ) | Q(
            applicable_to__gte=start
        )
    ).first()
    shift_exists_for_end = IndividualUserShift.objects.filter(
        individual_setting__user=user,
        applicable_from__lte=end
    ).filter(
        Q(
            applicable_to__isnull=True
        ) | Q(
            applicable_to__gte=end
        )
    ).first()
    return shift_exists_for_end, shift_exists_for_start
