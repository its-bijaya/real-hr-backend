from django.contrib.auth import get_user_model
from django.db.models import Case, When, F, Sum, PositiveSmallIntegerField, \
    Q, Avg
from django.db.models.functions import Coalesce
from rest_framework.response import Response

from irhrs.attendance.constants import WORKDAY, PUNCH_IN, PUNCH_OUT, \
    NO_LEAVE, FULL_LEAVE, DECLINED
from irhrs.attendance.models import TimeSheet
from irhrs.attendance.utils.attendance import humanize_interval
from irhrs.core.mixins.viewset_mixins import ListViewSetMixin, DateRangeParserMixin
from irhrs.core.utils.common import get_today
from irhrs.permission.constants.permissions import ATTENDANCE_PERMISSION, \
    HAS_PERMISSION_FROM_METHOD
from irhrs.permission.permission_classes import permission_factory

User = get_user_model()


class AttendanceIssuesViewSet(DateRangeParserMixin, ListViewSetMixin):
    """
    list:

    Attendance Issues for a user

    pass `user=user_id` in params to see results for that user.

    ## UPDATE [APR-1-2019]
    * `yesterday` has been refactored as `last_valid_day`.
    * `last_valid_day` refers to last working day.
    * In case the user has punch in but no punch out in off day. It is shown.
    """

    serializer_class = None
    permission_classes = [permission_factory.build_permission(
        "AttendanceIssuePermission",
        allowed_to=[ATTENDANCE_PERMISSION, HAS_PERMISSION_FROM_METHOD]
    )]
    _user = ...

    def get_queryset(self):
        user = self.get_user()
        today = get_today()
        if not user:
            return TimeSheet.objects.none()
        else:
            fil = {}
            start_date, end_date = self.get_parsed_dates()
            if start_date and end_date:
                fil.update({
                    'timesheet_for__gte': start_date,
                    'timesheet_for__lte': end_date
                })
            else:
                fil.update({
                    'timesheet_for__year': today.year,
                    'timesheet_for__month': today.month,
                    'timesheet_for__lte': today
                })
            return TimeSheet.objects.filter(
                timesheet_user=user, **fil
            ).select_related(
                'timesheet_user'
            )

    def has_user_permission(self):
        supervisor = self.request.query_params.get('supervisor')
        if supervisor and supervisor == str(self.request.user.id):
            return True
        return self.request.user == self.get_user()

    def get_organization(self):
        # For permission related to organization
        user = self.get_user()
        if user:
            return user.detail.organization
        return None

    def get_user(self):
        if self._user is ...:
            try:
                user_id = int(self.request.query_params.get('user'))
                try:
                    self._user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    self._user = None
            except (TypeError, ValueError):
                self._user = None

        return self._user

    def get_today(self, qs):
        today = qs.filter(
            timesheet_for=get_today()
        ).first()
        if not today:
            return None
        first_entry = today.timesheet_entries.filter(
            entry_type=PUNCH_IN,
            is_deleted=False
        ).first()
        punch_in_category = first_entry.category if first_entry else None
        coefficient = today.get_leave_coefficient_display() if (
                today.leave_coefficient == FULL_LEAVE
        ) else today.get_coefficient_display()
        if today.expected_punch_out and today.expected_punch_in and (
            today.expected_punch_in == today.expected_punch_out
        ):
            coefficient = FULL_LEAVE
        return {
            'coefficient': coefficient,
            'punch_in': bool(today.punch_in),
            'punch_in_time': today.punch_in.astimezone() if today.punch_in
            else None,
            'punch_in_delta': humanize_interval(today.punch_in_delta),
            'punch_in_category': punch_in_category,
            'expected_punch_in': today.expected_punch_in,
            'expected_punch_out': today.expected_punch_out
        }

    def get_yesterday(self, qs):
        # ignore queryset. The filter for this month this year is not valid
        # for cases of first day of the month. Example: April 1st. For this,
        # the last workday is 31st March.
        today = get_today()
        yesterday = TimeSheet.objects.filter(
            timesheet_user=self.get_user(),
            timesheet_for__lt=today,  # filter TS greater than today.
        ).filter(
            Q(punch_in__isnull=False) |
            Q(coefficient=WORKDAY)  # last working day or last day worked.
        ).exclude(
            leave_coefficient=FULL_LEAVE,
            punch_in__isnull=True
        ).order_by('-timesheet_for').first()
        if not yesterday:
            return None
        punch_out = bool(yesterday.punch_out)
        punch_out_entry = yesterday.timesheet_entries.filter(
            entry_type=PUNCH_OUT,
            is_deleted=False
        ).last()
        remark = punch_out_entry.category if punch_out_entry else None
        return {
            'punch_out': punch_out,
            'punch_out_time': yesterday.punch_out.astimezone() if
            yesterday.punch_out else None,
            'punch_out_delta': humanize_interval(yesterday.punch_out_delta),
            'adjusted': yesterday.adjustment_requests.exclude(
                status=DECLINED
            ).filter(
                new_punch_out__isnull=False
            ).exists(),
            'punch_out_category': remark,
            'timesheet_for': yesterday.timesheet_for
        }

    def get_statistics(self, qs):
        agg = qs.annotate(
            worked_time=F('worked_hours'),
            absent_count=Case(
                When(
                    coefficient=WORKDAY,
                    leave_coefficient=NO_LEAVE,
                    is_present=False,
                    timesheet_for__lt=get_today(),
                    then=1,
                ),
                default=0,
                output_field=PositiveSmallIntegerField()
            )
        ).aggregate(
            worked_seconds=Sum(
                'worked_time',
                filter=Q(
                    timesheet_for__lt=get_today()
                )
            ),
            # TODO: Refactor this field, the field says leave but returns absent.
            leave_count=Sum('absent_count')
        )
        agg.update({
            'punctuality': qs.filter(
                coefficient=WORKDAY,
                work_shift__isnull=False,
                leave_coefficient=NO_LEAVE
            ).aggregate(
                punctuality=Avg(Coalesce(F('punctuality'), 0.0))
            ).get(
                'punctuality'
            ),
            'expected_work_time': (qs.filter(
                timesheet_for__lt=get_today()
            ).aggregate(wt=Sum(
                'work_time__working_minutes',
                filter=Q(
                    coefficient=WORKDAY
                )
            )).get('wt', 0.0) or 0.0) * 60
        })
        return agg

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(
            self.get_queryset()
        )
        fields = ['today', 'yesterday', 'statistics']
        results = dict()
        for field in fields:
            func = getattr(self, f'get_{field}')
            results[field] = func(qs)
        return Response(results)
