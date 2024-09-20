import math

from django.contrib.auth import get_user_model
from django.db.models import Count, Q, F, Window, OuterRef, Subquery, \
    fields as dj_fields, Sum
from django.http import Http404
from rest_framework.fields import ReadOnlyField, SerializerMethodField
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from irhrs.attendance.api.v1.reports.views.mixins import \
    AttendanceReportPermissionMixin
from irhrs.attendance.constants import EARLY_IN, TIMELY_IN, LATE_IN, EARLY_OUT, \
    TIMELY_OUT, LATE_OUT, PUNCH_IN, PUNCH_OUT
from irhrs.attendance.models import TimeSheet
from irhrs.core.mixins.serializers import DummySerializer
from irhrs.core.mixins.viewset_mixins import OrganizationMixin, \
    ListViewSetMixin, DateRangeParserMixin, PastUserParamMixin, OrganizationCommonsMixin
from irhrs.core.utils.common import get_today, get_yesterday
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer, \
    UserFieldThinSerializer

USER = get_user_model()


class AttendanceCategoryCommon(PastUserParamMixin):
    category_mapper = {
        "early-in": EARLY_IN,
        "early-out": EARLY_OUT,
        "late-in": LATE_IN,
        "late-out": LATE_OUT,
        "timely-in": TIMELY_IN,
        "timely-out": TIMELY_OUT
    }
    queryset = TimeSheet.objects.all()

    def get_queryset(self):
        supervisor_id = self.request.query_params.get('supervisor')
        fil = dict()

        if supervisor_id:
            if supervisor_id == str(self.request.user.id):
                fil.update({
                    'timesheet_user_id__in':
                        self.request.user.subordinates_pks
                })
            else:
                # if supervisor does not match return none
                return super().get_queryset().none()

        qs = super().get_queryset().filter(**fil)
        if self.user_type == 'past':
            return qs.filter(
                ~Q(timesheet_user__user_experiences__is_current=True)
            )
        elif self.user_type == 'all':
            return qs
        return qs.filter(
            timesheet_user__user_experiences__is_current=True
        )

    def get_category_filter(self, date=None, category=None):
        if not category:
            _category = self.kwargs.get("category")
            category = _category.replace("-today", "").replace("-yesterday", "")

        date = date or self.get_date(category)
        method_name = f"get_{category.replace('-', '_')}_filter"
        method = getattr(self, method_name, None)
        if method:
            return method(date)
        raise Http404

    @staticmethod
    def get_date(category):
        today = get_today()
        yesterday = get_yesterday()

        if category.endswith('out'):
            return yesterday
        else:
            return today

    @staticmethod
    def get_suffix(category):
        if category.endswith('out'):
            return 'yesterday'
        else:
            return 'today'

    @staticmethod
    def get_date_filter(date):
        if isinstance(date, tuple):
            return {'timesheet_for__range': date}
        return {'timesheet_for': date}

    @staticmethod
    def get_early_in_filter(date):
        return {
            "timesheet_entries__entry_type": PUNCH_IN,
            "timesheet_entries__category": EARLY_IN,
            **AttendanceCategoryCommon.get_date_filter(date)
        }

    @staticmethod
    def get_early_out_filter(date):
        return {
            "timesheet_entries__entry_type": PUNCH_OUT,
            "timesheet_entries__category": EARLY_OUT,
            **AttendanceCategoryCommon.get_date_filter(date)
        }

    @staticmethod
    def get_late_in_filter(date):
        return {
            "timesheet_entries__entry_type": PUNCH_IN,
            "timesheet_entries__category": LATE_IN,
            **AttendanceCategoryCommon.get_date_filter(date)
        }

    @staticmethod
    def get_late_out_filter(date):
        return {
            "timesheet_entries__entry_type": PUNCH_OUT,
            "timesheet_entries__category": LATE_OUT,
            **AttendanceCategoryCommon.get_date_filter(date)
        }

    @staticmethod
    def get_timely_in_filter(date):
        return {
            "timesheet_entries__entry_type": PUNCH_IN,
            "timesheet_entries__category": TIMELY_IN,
            **AttendanceCategoryCommon.get_date_filter(date)
        }

    @staticmethod
    def get_timely_out_filter(date):
        return {
            "timesheet_entries__entry_type": PUNCH_OUT,
            "timesheet_entries__category": TIMELY_OUT,
            **AttendanceCategoryCommon.get_date_filter(date)
        }


class AttendanceByCategoryViewSet(
    AttendanceCategoryCommon,
    OrganizationMixin,
    AttendanceReportPermissionMixin,
    ListViewSetMixin,
):
    serializer_class = type(
        "AttendanceByCategorySerializer",
        (DummySerializer,),
        {
            "user": UserThinSerializer(
                source="timesheet_user",
                fields=('id', 'full_name', 'profile_picture', "cover_picture", "is_online", 'is_current', 'organization', "job_title")
            ),
            "punch_in": ReadOnlyField(),
            "punch_out": ReadOnlyField()
        }
    )
    filter_backends = [OrderingFilter]
    ordering_fields = [
        "timesheet_for",
        "punch_in",
        "punch_out"
    ]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(
            timesheet_user__detail__organization=self.get_organization()
        )

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset).filter(
            **self.get_category_filter()
        )
        return queryset.select_related('timesheet_user', 'timesheet_user__detail', "timesheet_user__detail__job_title")


class AttendanceByCategorySummaryViewSet(
    AttendanceCategoryCommon,
    OrganizationMixin,
    AttendanceReportPermissionMixin,
    ListViewSetMixin
):
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        agg = {
            f"{category}-{self.get_suffix(category)}": Count('id', filter=Q(
                **self.get_category_filter(
                    category=category
                )), distinct=True)
            for category in self.category_mapper.keys()
        }

        return Response(queryset.aggregate(**agg))

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(
            timesheet_user__detail__organization=self.get_organization()
        )

class UserByAttendanceCategoryFrequencyViewSet(
    AttendanceCategoryCommon,
    DateRangeParserMixin,
    OrganizationMixin,
    AttendanceReportPermissionMixin,
    ListViewSetMixin
):
    """
    User with most categories

    valid categories "early-in", "early-out", "late-in", "late-out", "timely-in", "timely-out", "max-stayers"
    """
    serializer_class = type(
        "UserByAttendanceCategoryFrequencySerializer",
        (UserFieldThinSerializer,),
        {
            "count": ReadOnlyField()
        }
    )
    max_stayers_serializer_class = type(
        "UserByAttendanceCategoryFrequencySerializer",
        (UserFieldThinSerializer,),
        {
            "worked_hours": SerializerMethodField(),
            "get_worked_hours": lambda _, obj:
            math.floor(obj.work_duration.total_seconds(
            )/60/60) if obj.work_duration else None,
            "expected_work_hours": SerializerMethodField(),
            "get_expected_work_hours": lambda _, obj:
            math.floor(obj.expected_work_duration.total_seconds(
            )/60/60) if obj.expected_work_duration else None,
        }
    )

    def get_serializer(self, *args, **kwargs):
        kwargs.update({
            "user_fields": ['id', 'full_name', 'profile_picture', "cover_picture", "is_online", "job_title"]
        })
        return super().get_serializer(*args, **kwargs)

    def get_serializer_class(self):
        category = self.kwargs.get('category')

        if category == "max-stayers":
            return self.max_stayers_serializer_class

        return super().get_serializer_class()

    def get_queryset(self):
        queryset = USER.objects.all().current()
        supervisor_id = self.request.query_params.get('supervisor')
        fil = dict(
            detail__organization=self.get_organization()
        )

        if supervisor_id:
            if supervisor_id == str(self.request.user.id):
                fil.update({
                    'id__in':
                        self.request.user.subordinates_pks
                })
            else:
                # if supervisor does not match return none
                return queryset.none()

        return queryset.filter(**fil)

    def filter_queryset(self, queryset):
        category = self.kwargs.get('category')
        category_filter = self.get_category_filter(category=category)

        timesheets = TimeSheet.objects.filter(timesheet_user=OuterRef('pk')).filter(
            **category_filter
        )

        if category == "max-stayers":
            work_duration = timesheets.annotate(
                work_duration=Window(
                    expression=Sum(F('worked_hours')),
                    partition_by=[F('timesheet_user')]
                ),
                expected_work_duration=Window(
                    expression=Sum(
                        F('expected_punch_out') - F('expected_punch_in')
                    ),
                    partition_by=[F('timesheet_user')]
                ),
            )

            queryset = super().filter_queryset(queryset).annotate(
                work_duration=Subquery(
                    work_duration.values('work_duration')[:1],
                    output_field=dj_fields.DurationField()
                ),
                expected_work_duration=Subquery(
                    work_duration.values('expected_work_duration')[:1],
                    output_field=dj_fields.DurationField()
                )
            ).filter(work_duration__isnull=False).order_by('-work_duration')

        else:
            # to annotate count from subquery
            count = timesheets.annotate(
                count=Window(
                    expression=Count('pk'),
                    partition_by=[F('timesheet_user')]
                ),
            ).values('count')[:1]

            queryset = super().filter_queryset(queryset).annotate(
                count=Subquery(
                    count,
                    output_field=dj_fields.IntegerField(default=0)
                )
            ).filter(count__isnull=False).order_by('-count')

        return queryset.select_related('detail', "detail__job_title")

    def get_category_filter(self, date=None, category=None):
        """
        :param date: start_date, end_date
        :type date: tuple
        :param category: timesheet_category, default will be taken from request
        :return: filter dict
        """
        date = date or self.get_parsed_dates()

        category = category or self.kwargs.get('category')

        if category == "max-stayers":
            return dict(is_present=True, **self.get_date_filter(date))

        method_name = f"get_{category.replace('-', '_')}_filter"
        method = getattr(self, method_name, None)
        if method:
            return method(date)
        raise Http404
