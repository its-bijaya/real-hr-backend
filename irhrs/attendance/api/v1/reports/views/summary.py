from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Q, OuterRef, Exists, Count, F, FloatField, Avg, \
    Sum, Case, When, DurationField, \
    IntegerField, ExpressionWrapper, Subquery
from django.db.models.functions import Coalesce
from django.http import Http404
from django.utils import timezone
from django.utils.functional import cached_property
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from irhrs.attendance.api.v1.permissions import AttendanceReportPermission
from irhrs.attendance.api.v1.reports.serializers.summary import \
    UserAttendanceSummarySerializer
from irhrs.attendance.api.v1.reports.views.mixins import \
    AttendanceReportPermissionMixin
from irhrs.attendance.constants import OFFDAY, WORKDAY, NO_LEAVE, REQUESTED, \
    FORWARDED, APPROVED, CONFIRMED, UNCLAIMED, DECLINED, BREAK_IN, BREAK_OUT, \
    FIRST_HALF, SECOND_HALF, FULL_LEAVE, PUNCH_OUT, TIMESHEET_ENTRY_CATEGORIES, \
    PUNCH_IN, TIMESHEET_ENTRY_REMARKS
from irhrs.attendance.models import TimeSheet, IndividualUserShift
from irhrs.core.mixins.serializers import create_read_only_dummy_serializer
from irhrs.core.mixins.viewset_mixins import \
    OrganizationMixin, ListRetrieveViewSetMixin, DateRangeParserMixin, \
    SupervisorQuerysetMixin, UserMixin, RetrieveViewSetMixin, \
    PastUserFilterMixin, PastUserTimeSheetFilterMixin
from irhrs.core.utils import grouper
from irhrs.core.utils.common import get_today, get_yesterday
from irhrs.core.utils.filters import FilterMapBackend, get_applicable_filters, \
    OrderingFilterMap
from irhrs.organization.models import FiscalYear
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer, \
    UserFieldThinSerializer

USER = get_user_model()
ZERO_DURATION = timedelta(0)

class AttendanceSummaryInformation(
    PastUserFilterMixin,
    OrganizationMixin,
    AttendanceReportPermissionMixin,
    ListRetrieveViewSetMixin
):
    serializer_class = UserAttendanceSummarySerializer

    categories = (
        'present',
        'absent',
        'offday',
    )
    lookup_url_kwarg = "category"
    queryset = USER.objects.all()

    def get_queryset(self):
        # active users

        supervisor_id = self.request.query_params.get('supervisor')
        fil = dict(
            user_experiences__is_current=True,
            detail__organization=self.organization
        )

        if supervisor_id:
            if supervisor_id == str(self.request.user.id):
                fil.update({
                    'id__in':
                        self.request.user.subordinates_pks
                })
            else:
                # if supervisor does not match return none
                return USER.objects.none()

        return super().get_queryset().filter(**fil).select_related(
            'detail',
            'detail__employment_level',
            'detail__job_title',
            'detail__organization',
            'detail__division',
            'attendance_setting'
        )

    @staticmethod
    def get_present(qs):
        return qs.filter(
            timesheets__timesheet_for=get_today(),
            timesheets__is_present=True,
        ).distinct()

    def get_present_queryset(self):
        return self.get_present(self.filter_queryset(self.get_queryset()))
        # return self.filter_queryset(
        #     self.get_queryset()).filter(
        #     timesheets__timesheet_for=get_today(),
        #     timesheets__is_present=True,
        # ).distinct()

    @staticmethod
    def get_absent(qs):
        is_present = USER.objects.all().current().filter(
            id=OuterRef("id"),
            timesheets__timesheet_for=get_today(),
            timesheets__is_present=True,
            timesheets__coefficient=WORKDAY,
            timesheets__leave_coefficient=NO_LEAVE
        )
        return qs.annotate(
            is_present=Exists(is_present)
        ).filter(
            Q(is_present=False) and
            Q(
                timesheets__timesheet_for=get_today(),
                timesheets__coefficient=WORKDAY,
                timesheets__leave_coefficient=NO_LEAVE,
                timesheets__is_present=False
            )
        ).distinct()

    def get_absent_queryset(self):
        return self.get_absent(self.filter_queryset(self.get_queryset()))
        # is_present = USER.objects.all().current().filter(
        #     id=OuterRef("id"),
        #     timesheets__timesheet_for=get_today(),
        #     timesheets__is_present=True,
        #     timesheets__coefficient=WORKDAY,
        #     timesheets__leave_coefficient=NO_LEAVE
        # )
        # return self.filter_queryset(self.get_queryset()).annotate(
        #     is_present=Exists(is_present)
        # ).filter(
        #     Q(is_present=False) and
        #     Q(
        #         timesheets__timesheet_for=get_today(),
        #         timesheets__coefficient=WORKDAY,
        #         timesheets__leave_coefficient=NO_LEAVE,
        #         timesheets__is_present=False
        #     )
        # ).distinct()

    @staticmethod
    def get_offday(qs):
        has_timesheet = USER.objects.all().current().filter(
            id=OuterRef("id"),
            timesheets__timesheet_for=get_today()
        )
        return qs.annotate(
            no_timesheet=~Exists(has_timesheet)
        ).filter(
            Q(no_timesheet=True) |
            Q(
                timesheets__timesheet_for=get_today(),
                timesheets__coefficient=OFFDAY
            )
        ).distinct()

    def get_offday_queryset(self):
        return self.get_offday(self.filter_queryset(self.get_queryset()))
        # has_timesheet = USER.objects.all().current().filter(
        #     id=OuterRef("id"),
        #     timesheets__timesheet_for=get_today()
        # )
        # return self.filter_queryset(self.get_queryset()).annotate(
        #     no_timesheet=~Exists(has_timesheet)
        # ).filter(
        #     Q(no_timesheet=True) |
        #     Q(
        #         timesheets__timesheet_for=get_today(),
        #         timesheets__coefficient=OFFDAY
        #     )
        # ).distinct()

    def get_function(self, slug):
        return getattr(self, f"get_{slug.replace('-', '_')}_queryset")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        total = queryset.filter().distinct().count()

        results = [
            {
                "name": slug.replace("-", " ").title(),
                "slug": slug,
                "count": self.get_function(slug)().count()
            }
            for slug in self.categories
        ]
        data = {
            "total": total,
            "results": results
        }
        return Response(data)

    def get_object(self):
        slug = self.kwargs.get("category")
        if slug not in self.categories:
            raise Http404
        return self.get_function(slug)()

    def retrieve(self, request, *args, **kwargs):
        data = self.get_serializer(
            self.paginate_queryset(self.get_object()),
            many=True
        ).data
        return self.get_paginated_response(data=data)


class OvertimeOverviewSerializer(serializers.Serializer):
    users = UserThinSerializer()
    count = serializers.ReadOnlyField()


class AttendanceOverviewViewSet(
    AttendanceReportPermissionMixin,
    PastUserFilterMixin,
    DateRangeParserMixin,
    OrganizationMixin,
    SupervisorQuerysetMixin,
    ListRetrieveViewSetMixin
):
    filter_backends = (
        OrderingFilterMap,
        FilterMapBackend
    )
    ordering_fields = ()
    lookup_url_kwarg = 'step'
    overview_reports = {
        'overtime': [
            'pending_approval',
            'hr_verification_pending',
            'unclaimed',
            'declined',
            'max_ots',
            'confirmed',
            'claimed'
        ],
        'most_breaks': [
            'break_frequency'
        ],
        'most_breaks_duration': [
            'break_duration'
        ],
        'most_punctual': [],
        'missed_entries': [
            'missed_punch_in',
            'missed_punch_out'
        ]
    }
    queryset = USER.objects.all()

    @cached_property
    def missed_annotates(self):
        yesterday, today = get_yesterday(), get_today()
        annotates = {
            'missed_punch_in': Exists(
                TimeSheet.objects.exclude(
                    leave_coefficient=FULL_LEAVE
                ).filter(
                    coefficient=WORKDAY,
                    timesheet_for=today,
                    punch_in__isnull=True,
                    timesheet_user=OuterRef('pk')
                )
            ),
            'missed_punch_out': Exists(
                TimeSheet.objects.filter(
                    timesheet_for=yesterday,
                    punch_in__isnull=False,
                    punch_out__isnull=True,
                    timesheet_user=OuterRef('pk')
                )
            )
        }
        return annotates

    @cached_property
    def overtime_annotates(self):
        date_filters = get_applicable_filters(
            self.request.query_params,
            filter_map={
                'start_date': 'overtime_entries__timesheet__timesheet_for__gte',
                'end_date': 'overtime_entries__timesheet__timesheet_for__lte',
            }
        )
        annotates = {
            'pending_approval': Count(
                'overtime_entries__claim',
                filter=Q(
                    overtime_entries__claim__status__in=[REQUESTED, FORWARDED]
                ) & Q(
                    **date_filters
                ),
            ),
            'hr_verification_pending': Count(
                'overtime_entries__claim',
                filter=Q(
                    Q(overtime_entries__claim__status=APPROVED) &
                    ~Q(overtime_entries__claim__status=CONFIRMED) & Q(
                        **date_filters
                    ),
                    ),
            ),
            'unclaimed': Count(
                'overtime_entries__claim',
                filter=Q(
                    Q(overtime_entries__claim__status=UNCLAIMED) &
                    Q(overtime_entries__claim__is_archived=False) & Q(
                        **date_filters
                    )
                )
            ),
            'declined': Count(
                'overtime_entries__claim',
                filter=Q(overtime_entries__claim__status=DECLINED) & Q(
                    **date_filters
                ),
            ),
            'max_ots': Count(
                'overtime_entries__claim',
                filter=~Q(
                    overtime_entries__claim__status=UNCLAIMED,
                ) & Q(
                    **date_filters
                ),
            ),
            'confirmed': Count(
                'overtime_entries__claim',
                filter=Q(overtime_entries__claim__status=CONFIRMED) & Q(
                    **date_filters
                ),
            ),
        }
        return annotates

    @cached_property
    def overtime_aggregates(self):
        aggregates = {
            'pending_approval': Count(
                'id',
                filter=Q(
                    overtime_entries__claim__status__in=[REQUESTED, FORWARDED]
                ),
                distinct=True
            ),
            'hr_verification_pending': Count(
                'id',
                filter=Q(
                    Q(overtime_entries__claim__status=APPROVED) &
                    ~Q(overtime_entries__claim__status=CONFIRMED),
                    ),
                distinct=True
            ),
            'unclaimed': Count(
                'id',
                filter=Q(
                    Q(overtime_entries__claim__status=UNCLAIMED) &
                    Q(overtime_entries__claim__is_archived=False)
                ),
                distinct=True
            ),
            'declined': Count(
                'id',
                filter=Q(overtime_entries__claim__status=DECLINED),
                distinct=True
            )
        }
        return aggregates

    @cached_property
    def base_queryset(self):
        return self.get_supervisor_filtered_queryset(
            super().get_queryset()
        )

    @cached_property
    def date_filters(self):
        filters = get_applicable_filters(
            self.request.query_params,
            filter_map={
                'start_date': 'timesheets__timesheet_for__gte',
                'end_date': 'timesheets__timesheet_for__lte',

            }
        )
        return filters

    @cached_property
    def break_annotates(self):
        annotates = {
            'break_frequency': Count(
                'timesheets__timesheet_entries',
                filter=Q(
                    timesheets__timesheet_entries__entry_type=BREAK_OUT,
                    **self.date_filters
                )
            )
        }
        return annotates

    @cached_property
    def break_aggregates(self):
        result = self.base_queryset.annotate(
            break_frequency=Count(
                'id',
                filter=Q(
                    timesheets__timesheet_entries__entry_type=BREAK_OUT,
                    **self.date_filters
                )
            )
        ).filter(
            break_frequency__gte=self.max
        ).count()
        return {
            'break_frequency': result
        }

    @cached_property
    def break_duration(self):
        users = self.base_queryset.select_related(
            'detail',
            'detail__employment_level',
            'detail__job_title',
            'detail__organization',
            'detail__division',
        )
        for user in users:
            st, ed = self.get_parsed_dates()
            time_out = 0
            for timesheet in user.timesheets.filter(
                    timesheet_for__gte=st,
                    timesheet_for__lte=ed,
            ).annotate(
                entries_count=Count(
                    'timesheet_entries',
                )
            ).filter(
                entries_count__gt=2
            ):
                entries = timesheet.timesheet_entries.filter(
                    entry_type__in=[BREAK_IN, BREAK_OUT, PUNCH_OUT],
                    is_deleted=False
                ).order_by(
                    'timestamp'
                )
                pairs = grouper(entries, n=2)
                for out_timestamp, in_timestamp in pairs:
                    time_out += (
                        (
                                in_timestamp.timestamp
                                - out_timestamp.timestamp
                        ).total_seconds() if in_timestamp else 0)
            total_time_out = round(time_out / 60, 2)
            setattr(user, 'total_out', total_time_out)
        ser = type(
            'xyz',
            (UserFieldThinSerializer,),
            {
                'total_out': serializers.ReadOnlyField()
            }
        )
        valid_users = list(filter(
            lambda user: user.total_out > 0,
            users
        ))[:10]
        sorted_users = sorted(
            valid_users,
            key=lambda user: user.total_out,
            reverse=True
        )
        return ser(sorted_users, many=True).data

    @cached_property
    def max(self):
        defined_max = self.request.query_params.get('max')
        defined_max = defined_max if defined_max and defined_max.isdigit(
        ) else 2
        return defined_max

    # Queryset Aggregators
    def get_overtime(self):
        defined_max = self.max
        max_ots = self.base_queryset.annotate(
            max_ots=Count(
                'id',
                filter=~Q(overtime_entries__claim__status=UNCLAIMED),
            )
        ).filter(
            max_ots__gt=defined_max
        ).count()
        qs = self.base_queryset.aggregate(
            **self.overtime_aggregates
        )
        qs.update({
            'max_ots': max_ots
        })
        return Response(qs)

    def get_most_breaks(self):
        # No aggregates will be served.
        # result = self.break_aggregates
        # return result
        raise Http404

    def get_most_breaks_duration(self):
        return Response(self.break_duration)

    def get_most_punctual(self):
        self.filter_map = {
            'start_date': 'timesheets__timesheet_for__gte',
            'end_date': 'timesheets__timesheet_for__lte',
            'division': 'detail__division__slug'
        }
        self.ordering_fields_map = dict(
            punctuality='punctuality',
            full_name=(
                'first_name', 'middle_name', 'last_name',
            )
        )

        valid_users_for_shift = IndividualUserShift.objects.filter(
            Q(applicable_to__isnull=True) |
            Q(applicable_to__gte=get_today())
        ).values('individual_setting__user')

        qs = self.base_queryset.filter(
            id__in=valid_users_for_shift
        ).distinct()

        start_date, end_date = self.get_parsed_dates()

        timesheets_filter = {
            'timesheets__coefficient': WORKDAY,
            'timesheets__timesheet_for__range': (
                start_date, end_date
            ),
            'timesheets__leave_coefficient__in': [
                NO_LEAVE, FIRST_HALF, SECOND_HALF
            ]
        }

        time_sheet_punctuality_subquery = TimeSheet.objects.filter(
            Q(coefficient=WORKDAY) &
            Q(timesheet_for__range=(start_date, end_date)) &
            ~Q(leave_coefficient=FULL_LEAVE)
        ).order_by().values('timesheet_user').annotate(
            avg_punctuality=Avg(Coalesce(F('punctuality'), 0.0), output_field=FloatField())
        ).filter(
            timesheet_user=OuterRef('pk')
        )
        qs = qs.annotate(
            punctuality=Subquery(
                time_sheet_punctuality_subquery.values('avg_punctuality'),
                output_field=FloatField()
            ),
        )
        # qs = qs.filter(
        #     **timesheets_filter
        # ).annotate(
        #     punctuality=Avg(
        #         Coalesce(F('timesheets__punctuality'), 0),
        #         filter=Q(**timesheets_filter),
        #         output_field=FloatField()
        #     )
        # )
        qs = self.filter_queryset(qs.select_essentials())
        serializer = type(
            'DynamicSerializer',
            (UserFieldThinSerializer,),
            {
                'punctuality': serializers.ReadOnlyField(),
            }
        )
        page = self.paginate_queryset(qs)
        response = self.get_paginated_response(serializer(page, many=True).data)
        return response

    def get_missed_entries(self):
        raise Http404

    # /Queryset Aggregators

    def get_serializer_class(self):
        step, sub_step = self.steps
        if sub_step:
            keys = {
                'overtime': self.overtime_annotates.keys(),
                'most_breaks': self.break_annotates.keys(),
                'missed_entries': self.missed_annotates.keys()
            }.get(step)
            class_mapping = {
                step: {
                    key: type(
                        'SER',
                        (UserFieldThinSerializer,),
                        {
                            key: serializers.ReadOnlyField()
                        }
                    )
                    for key in keys}
            }
            return class_mapping.get(step).get(sub_step)
        return

    def get_queryset(self):
        skip_below = self.request.query_params.get('skip_below')
        skip_below = skip_below if skip_below and skip_below.isdigit() else 1
        step, sub_step = self.steps
        annotate_with = {
            'overtime': self.overtime_annotates,
        }.get(step, {}).get(sub_step)
        queryset = self.base_queryset
        if step == 'overtime':
            queryset = queryset.annotate(
                **{sub_step: annotate_with}
            ).order_by(
                F(sub_step).desc()
            ).filter(
                **{
                    f'{sub_step}__gte': skip_below
                }
            )
        elif step == 'most_breaks':
            queryset = queryset.annotate(
                **self.break_annotates
            ).order_by(
                F(sub_step).desc()
            ).filter(
                **{
                    f'{sub_step}__gte': skip_below
                }
            )
        elif step == 'missed_entries':
            annotate_with = self.missed_annotates.get(sub_step)
            queryset = queryset.annotate(
                **{
                    sub_step: annotate_with
                }
            ).filter(
                **{
                    sub_step: True
                }
            )
        queryset = queryset.select_related(
            'detail',
            'detail__employment_level',
            'detail__job_title',
            'detail__organization',
            'detail__division',
        )
        return queryset

    def get_object(self):
        step, sub_step = self.steps
        func = getattr(self, f'get_{step}')
        return func()

    @cached_property
    def steps(self):
        step, sub_step = None, None
        step_kwarg = self.kwargs.get('steps')
        steps = step_kwarg.split('/')
        if len(steps) == 1:
            step = steps[0]
        elif len(steps) > 1:
            step = steps[0]
            sub_step = steps[1]
        if (
                step and step not in self.overview_reports
        ) or (
                sub_step and sub_step not in self.overview_reports.get(step)
        ):
            raise Http404
        return step, sub_step

    def retrieve(self, request, *args, **kwargs):
        step, sub_step = self.steps
        if sub_step:
            return self.list(request, *args, **kwargs)
        return self.get_object()


class NormalUserAttendanceOverviewViewSet(
    PastUserTimeSheetFilterMixin,
    OrganizationMixin,
    UserMixin,
    RetrieveViewSetMixin
):
    """
    list:

    Normal user attendance overview
    ===============================

    Stats for overview section of normal user

    filters
    -------

        {
            "start_date": "2019-01-01",
            "end_date": "2020-01-01"
        }

    overview_detail:

    Overview Details
    ================

    Overview detail stats

    available slugs: behavior, break-out

    filters
    -------

        {
            "start_date": "2019-01-01",
            "end_date": "2020-01-01"
        }


    """
    queryset = TimeSheet.objects.all()
    permission_classes = [AttendanceReportPermission]
    filter_backends = (FilterMapBackend,)
    filter_map = {
        "start_date": "timesheet_for__gte",
        "end_date": "timesheet_for__lte"
    }
    detail_slug_method_map = {
        'behavior': 'get_attendance_behavior',
        'break-out': 'get_break_out_report'
    }
    lookup_url_kwarg = 'user_id'

    def get_queryset(self):
        return super().get_queryset().filter(
            timesheet_user__detail__organization=self.get_organization(),
            timesheet_user=self.user
        )

    def filter_queryset(self, queryset):
        if self.request.query_params.get('fiscal_year') and \
                self.request.query_params.get('fiscal_year').lower() == 'current':
            fiscal_year = FiscalYear.objects.current(
                organization=self.organization)
            fil = {}
            if not fiscal_year:
                today = get_today()
                fil.update({
                    'timesheet_for__year__gte': today.year,
                    'timesheet_for__month__gte': 1,
                    'timesheet_for__lte': today
                })
            else:
                fil.update({
                    'timesheet_for__gte': fiscal_year.applicable_from,
                    'timesheet_for__lte': get_today()
                })
            return super().filter_queryset(self.get_queryset()).filter(**fil)
        return super().filter_queryset(queryset)

    def get_serializer_class(self):
        fields = [
            'total_lost_minutes',
            'expected_minutes',
            'total_worked_minutes',
            'absent_days',
            'present_days',
            'working_days',
            'punctuality',
        ]
        if self.request.query_params.get('fiscal_year') and \
                self.request.query_params.get('fiscal_year').lower() == 'current':
            fields.append('overtime_claimed')
        return create_read_only_dummy_serializer(fields=fields)

    def has_user_permission(self):
        return self.user == self.request.user or self.is_supervisor

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        return self.get_summary(queryset, self.request)

    @action(detail=True, methods=['GET'],
            url_path=r'(?P<detail_slug>([\w\-]+))')
    def overview_detail(self, request, **kwargs):
        method = self.detail_slug_method_map.get(kwargs['detail_slug'])
        if not method:
            raise Http404
        return Response(
            getattr(self, method)(self.filter_queryset(self.get_queryset())))

    @staticmethod
    def get_summary(queryset, request) -> dict:
        """
        :return: summary information
        """
        agg_data = queryset.aggregate(
            total_worked=Coalesce(Sum(
                F('worked_hours')
            ), timezone.timedelta(0)),
            expected_work=Coalesce(Sum(
                Case(
                    When(
                        expected_punch_in__isnull=False,
                        expected_punch_out__isnull=False,
                        coefficient=WORKDAY,
                        then=F('work_time__working_minutes')
                    ),
                    default=0,
                    output_field=IntegerField()
                )
            ), 0),
            absent_days=Count('id',
                              filter=Q(is_present=False, coefficient=WORKDAY,
                                       leave_coefficient=NO_LEAVE)),
            present_days=Count('id', filter=Q(is_present=True)),
            working_days=Count('id', filter=Q(coefficient=WORKDAY)),
            punctuality=Avg(
                Coalesce(F('punctuality'), 0),
                filter=Q(coefficient=WORKDAY, leave_coefficient=NO_LEAVE),
                output_field=FloatField()
            ),
            overtime_claimed=Sum(
                'overtime__overtime_detail__claimed_overtime',
                filter=~Q(overtime__claim__status=UNCLAIMED),
                output_field=DurationField()
            ),
            total_lost_early=Sum(
                Case(
                    # pid/pod is actual-expected.
                    When(
                        punch_in_delta__gt=ZERO_DURATION,
                        is_present=True,
                        coefficient=WORKDAY,
                        leave_coefficient__in=[NO_LEAVE, FIRST_HALF, SECOND_HALF],
                        then=F('punch_in_delta'),
                    ),
                    default=ZERO_DURATION,
                    output_field=DurationField()
                )
            ),
            total_lost_late=Sum(
                Case(
                    # pid/pod is actual-expected.
                    When(
                        punch_out_delta__lt=ZERO_DURATION,
                        is_present=True,
                        coefficient=WORKDAY,
                        leave_coefficient__in=[NO_LEAVE, FIRST_HALF, SECOND_HALF],
                        then=F('punch_out_delta'),
                    ),
                    default=ZERO_DURATION,
                    output_field=DurationField()
                )
            ),
            total_lost_absent=Sum(
                ExpressionWrapper(
                    F('expected_punch_out') - F('expected_punch_in'),
                    output_field=DurationField()
                ),
                filter=Q(is_present=False,
                         coefficient=WORKDAY,
                         leave_coefficient__in=[NO_LEAVE, FIRST_HALF, SECOND_HALF])
            )
        )
        total_worked = agg_data.get('total_worked', ZERO_DURATION) or ZERO_DURATION
        expected_work = agg_data.get('expected_work', 0) or 0
        total_worked_minutes = total_worked.total_seconds() // 60
        agg_data["total_lost"] = expected_work - total_worked_minutes

        response = {
            'total_lost_minutes': agg_data["total_lost"],
            'expected_minutes': agg_data['expected_work'],
            'total_worked_minutes': total_worked_minutes,
            'absent_days': agg_data['absent_days'],
            'present_days': agg_data['present_days'],
            'working_days': agg_data['working_days'],
            'punctuality': round(agg_data['punctuality'] or 0.0, 2)
        }

        if request.query_params.get('fiscal_year') == 'current':
            response.update({
                'overtime_claimed': agg_data['overtime_claimed'].total_seconds(
                ) // 60 if agg_data['overtime_claimed'] else 0
            })
        return response

    @staticmethod
    def get_attendance_behavior(queryset) -> dict:
        return queryset.aggregate(
            **{
                cat: Count('id', filter=Q(
                    Q(timesheet_entries__category=cat,
                      timesheet_entries__entry_type__in=[PUNCH_IN, PUNCH_OUT],
                      coefficient=WORKDAY) & ~Q(leave_coefficient=FULL_LEAVE)
                ), distinct=True)
                for cat, _ in TIMESHEET_ENTRY_CATEGORIES
            }
        )

    @staticmethod
    def get_break_out_report(queryset) -> dict:
        remarks = filter(lambda x: x[0] not in [PUNCH_IN, PUNCH_OUT],
                         TIMESHEET_ENTRY_REMARKS)
        return queryset.aggregate(
            **{
                cat: Count('timesheet_entries__id',
                           filter=Q(
                               timesheet_entries__remark_category=cat,
                               timesheet_entries__entry_type=BREAK_OUT
                           ), distinct=True)
                for cat, _ in remarks
            }
        )
