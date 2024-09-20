from datetime import timedelta

import dateutil.parser as dateparser
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum, F, Subquery, OuterRef, Case, When, \
    fields as dj_fields, Value, Exists
from django.db.models.functions import Coalesce, Cast, Concat
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.functional import cached_property
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.response import Response

from irhrs.attendance.api.v1.permissions import AttendancePermission, \
    AttendanceReportPermission
from irhrs.attendance.api.v1.reports.serializers.individual_attendance_report import \
    IndividualAttendanceIrregularityReportSerializer
from irhrs.attendance.api.v1.reports.serializers.timesheet_entry_report import (
    TimeSheetEntryReportSerializer, TimeSheetEntryDetailSerializer,
    DepartmentLateInEarlyOutSerializer, DepartmentAbsentReportSerializer,
    AttendanceIrregularitiesSerializer,
    AttendanceIrregularitiesDetailSerializer)
from irhrs.attendance.api.v1.reports.views.mixins import \
    AttendanceReportPermissionMixin
from irhrs.attendance.constants import LATE_IN, EARLY_OUT, WORKDAY, BREAK_OUT, \
    TEA_BREAK, CLIENT_VISIT, LUNCH_BREAK, MEETING, OTHERS, FULL_LEAVE, PUNCH_IN, \
    PUNCH_OUT, NO_LEAVE, FIRST_HALF, SECOND_HALF, PERSONAL, BREAK_IN
from irhrs.attendance.models import TimeSheetEntry, TimeSheet, \
    IndividualUserShift
from irhrs.core.constants.user import MALE, FEMALE, OTHER
from irhrs.core.mixins.viewset_mixins import ListViewSetMixin, \
    OrganizationMixin, UserMixin, PastUserFilterMixin, \
    PastUserTimeSheetFilterMixin
from irhrs.core.utils.common import apply_filters, get_today, humanize_interval
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap, \
    get_applicable_filters
from irhrs.export.mixins.export import BackgroundExcelExportMixin
from irhrs.permission.constants.permissions import ATTENDANCE_REPORTS_PERMISSION
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer

USER = get_user_model()


class TimeSheetEntryReportViewSet(
    PastUserFilterMixin,
    OrganizationMixin,
    ListViewSetMixin
):
    queryset = USER.objects.all()
    filter_fields = (
        'detail__division__slug',
        'detail__branch__slug',
        'timesheets__timesheet_entries__remark_category'
    )
    serializer_class = TimeSheetEntryReportSerializer
    permission_classes = [AttendancePermission]

    def get_queryset(self):
        qs = self.filter_queryset(self.queryset).filter(
            detail__organization=self.get_organization()
        )
        qs = qs.annotate(
            punch_in_late_count=Count(
                'timesheets__timesheet_entries',
                filter=Q(
                    timesheets__timesheet_entries__category=LATE_IN)
            ),
            punch_out_early_count=Count(
                'timesheets__timesheet_entries',
                filter=Q(
                    timesheets__timesheet_entries__category=EARLY_OUT)
            ),
            lost_time_late=Sum(
                'timesheets__punch_in_delta',
                filter=Q(timesheets__punch_in_delta__gt=timezone.timedelta(
                    minutes=0))),
            lost_time_early=Sum(
                'timesheets__punch_out_delta',
                filter=Q(timesheets__punch_out_delta__lt=timezone.timedelta(
                    minutes=0)))
        )
        return qs

    @action(methods=['get'], detail=True, url_path='detail',
            url_name='timesheet-entry-detail')
    def get_detail(self, request, pk, organization_slug):
        try:
            user = get_object_or_404(USER, pk=pk)
        except (TypeError, ValueError):
            raise Http404
        filter_category = request.query_params.get('category')
        mapper = {
            'late_in': LATE_IN,
            'early_out': EARLY_OUT
        }
        filter_value = mapper.get(filter_category, EARLY_OUT)
        qs = TimeSheetEntry.objects.filter(
            timesheet__timesheet_user=user,
            category=filter_value,
            is_deleted=False,
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = TimeSheetEntryDetailSerializer(qs[:10], many=True)
            resp = self.get_paginated_response(serializer.data)
            return resp
        return Response

    @action(methods=['get'], detail=False, url_path='department-count',
            url_name='late-in-department-count')
    def get_department_count(self, request, *args, **kwargs):
        qs = TimeSheet.objects.values(
            'timesheet_user__detail__division'
        ).annotate(
            male_count_late=Count(
                'timesheet_user__detail__gender',
                filter=Q(
                    timesheet_user__detail__gender=MALE,
                    timesheet_entries__category=LATE_IN
                )
            ),
            female_count_late=Count(
                'timesheet_user__detail__gender',
                filter=Q(
                    timesheet_user__detail__gender=FEMALE,
                    timesheet_entries__category=LATE_IN
                )
            ),
            other_count_late=Count(
                'timesheet_user__detail__gender',
                filter=Q(
                    timesheet_user__detail__gender=OTHER,
                    timesheet_entries__category=LATE_IN
                )
            ),
            male_count_early=Count(
                'timesheet_user__detail__gender',
                filter=Q(
                    timesheet_user__detail__gender=MALE,
                    timesheet_entries__category=EARLY_OUT
                )
            ),
            female_count_early=Count(
                'timesheet_user__detail__gender',
                filter=Q(
                    timesheet_user__detail__gender=FEMALE,
                    timesheet_entries__category=EARLY_OUT
                )
            ),
            other_count_early=Count(
                'timesheet_user__detail__gender',
                filter=Q(
                    timesheet_user__detail__gender=OTHER,
                    timesheet_entries__category=EARLY_OUT
                )
            ),

            lost_time_late=Sum(
                'punch_in_delta',
                filter=Q(punch_in_delta__gt=timezone.timedelta(minutes=0))),
            lost_time_early=Sum(
                'punch_out_delta',
                filter=Q(punch_out_delta__lt=timezone.timedelta(minutes=0)))
        )
        return Response(DepartmentLateInEarlyOutSerializer(qs, many=True).data)

    @property
    def annotate_data(self):
        """
        Get User vs. LateIn/EarlyOut Count
        :return:
        """
        qs = self.get_queryset()
        return qs.values('timesheet__timesheet_user').annotate(
            late_in_count=Count(
                'category',
                filter=Q(category=LATE_IN)
            ),
            early_out_count=Count(
                'category',
                filter=Q(category=EARLY_OUT)
            )
        )


class DepartmentAbsentReportViewSet(
    PastUserTimeSheetFilterMixin,
    OrganizationMixin,
    ListViewSetMixin
):
    queryset = TimeSheet.objects.all()
    serializer_class = DepartmentAbsentReportSerializer
    permission_classes = [AttendancePermission]

    def get_queryset(self):
        qs = super().get_queryset().filter(
            timesheet_user__detail__organization=self.get_organization()
        )
        qs = qs.filter(is_present=False).values(
            'timesheet_user__detail__division'
        ).annotate(
            male_count_absent=Count(
                'timesheet_user__detail__gender',
                filter=Q(
                    timesheet_user__detail__gender=MALE
                )
            ),
            female_count_absent=Count(
                'timesheet_user__detail__gender',
                filter=Q(
                    timesheet_user__detail__gender=FEMALE
                )
            ),
            other_count_absent=Count(
                'timesheet_user__detail__gender',
                filter=Q(
                    timesheet_user__detail__gender=OTHER
                )
            ),
            lost_time=Sum(
                'work_time__working_minutes'
            )
        )
        return qs


def get_lost_late_in(obj, fmt=True):
    result = obj.lost_late_in
    return humanize_interval(result) if fmt else result if isinstance(
        result, timedelta
    ) else timedelta(
        seconds=abs(obj.lost_early_out.total_seconds())
    ) if obj.lost_early_out else timezone.timedelta(0)


def get_lost_absent(obj, fmt=True):
    result = obj.lost_absent
    return humanize_interval(result) if fmt else result if isinstance(
            result, timedelta
    ) else timedelta(
        seconds=abs(obj.lost_early_out.total_seconds())
    ) if obj.lost_early_out else timezone.timedelta(0)


def get_lost_early_out(obj, fmt=True):
    result = obj.lost_early_out
    return humanize_interval(result) if fmt else result if isinstance(
            result, timedelta
    ) else timedelta(
        seconds=abs(obj.lost_early_out.total_seconds())
    ) if obj.lost_early_out else timezone.timedelta(0)


def get_total_lost(obj):
    """Get total lost from annotated user"""
    return humanize_interval(
        abs(get_lost_late_in(obj, False))
        + abs(get_lost_early_out(obj, False))
        + abs(get_lost_absent(obj, False))
    )


def get_total_worked(obj):
    """Get total worked from annotated user"""
    return humanize_interval(obj.total_worked)


class AttendanceIrregularitiesViewSet(
    PastUserFilterMixin,
    BackgroundExcelExportMixin,
    OrganizationMixin,
    AttendanceReportPermissionMixin,
    ListViewSetMixin
):
    """
    filters -->
        work_shift: work_shift_id
    """
    serializer_class = AttendanceIrregularitiesSerializer
    search_fields = (
        'first_name',
        'middle_name',
        'last_name',
        'username'
    )
    ordering = ('first_name', 'middle_name', 'last_name')
    ordering_fields_map = {
        'full_name': ('first_name', 'middle_name', 'last_name'),
        'lost_late_in': 'lost_late_in',
        'lost_early_out': 'lost_early_out',
        'lost_absent': 'lost_absent',
        'late_in_count': 'late_in_count',
        'early_out_count': 'early_out_count',
        'absent_count': 'absent_count',
        'total_lost': 'total_lost',
        'total_worked': 'total_worked'
    }
    filter_backends = (
        DjangoFilterBackend,
        FilterMapBackend,
        filters.SearchFilter,
        OrderingFilterMap
    )
    filter_map = {
        'branch': 'detail__branch__slug',
        'division': 'detail__division__slug',
        'username': 'username',
    }
    queryset = USER.objects.all()
    export_type = "Attendance Irregularities"
    export_fields = {
        "User": "full_name",
        "Username": "username",
        "Job Title": "detail.job_title",
        "Division": "detail.division",
        "Branch": "detail.branch",
        "Employment Level": "detail.employment_level",
        "late_in_count": "late_in_count",
        "Lost Late In": get_lost_late_in,
        "early_out_count": "early_out_count",
        "Lost Early Out": get_lost_early_out,
        "absent_count": "absent_count",
        "lost_absent": get_lost_absent,
        "total_lost": get_total_lost,
        "total_worked": get_total_worked
    }
    notification_permissions = [ATTENDANCE_REPORTS_PERMISSION]
    export_description = ["Attendance Irregularity Report"]

    def get_queryset(self):

        attendance_with_shifts = IndividualUserShift.objects.filter(
            Q(applicable_to__isnull=True) |
            Q(applicable_to__gte=timezone.now().date())
        ).values('individual_setting')

        supervisor_id = self.request.query_params.get('supervisor')
        fil = dict(attendance_setting__isnull=False,
                   attendance_setting__in=attendance_with_shifts,
                   detail__organization=self.organization)

        if supervisor_id:
            if supervisor_id == str(self.request.user.id):
                fil.update({
                    'id__in':
                        self.request.user.subordinates_pks
                })
            else:
                # if supervisor does not match return none
                return USER.objects.none()

        queryset = super().get_queryset().filter(**fil)
        return queryset.select_related(
            'detail',
            'detail__organization',
            'detail__division',
            'detail__job_title',
            'detail__employment_level',
            'attendance_setting'
        )

    def filter_queryset(self, queryset):

        # WORK SHIFT FILTER
        work_shift_id = self.request.query_params.get('work_shift')
        if work_shift_id:
            try:
                work_shift_id = int(work_shift_id)
                queryset = self.annotate_shift_id(queryset).filter(
                    work_shift_id=work_shift_id)

            except (TypeError, ValueError):
                pass

        # used intentionally
        fil = get_applicable_filters(
            self.request.query_params,
            {
                'start_date': 'timesheets__timesheet_for__gte',
                'end_date': 'timesheets__timesheet_for__lte'
            }
        )
        fil.update({'timesheets__coefficient': WORKDAY})
        excludes = Q(timesheets__leave_coefficient=FULL_LEAVE)
        if 'timesheets__timesheet_for__lte' not in fil:
            fil.update({
                'timesheets__timesheet_for__lte': get_today()
            })
        break_out_on_unpaid_break = Q(
            Q(timesheets__timesheet_entries__entry_type=BREAK_OUT) &
            Q(timesheets__timesheet_entries__is_deleted=False) &
            Q(timesheets__timesheet_entries__remark_category__in=settings.UNPAID_BREAK_TYPES)
        )
        missing_punch_out = Q(
            Q(timesheets__punch_in__isnull=False) &
            Q(timesheets__punch_out__isnull=True)
        )
        annotates = {
            'lost_late_in': Coalesce(
                Sum(
                    'timesheets__punch_in_delta',
                    filter=Q(
                        timesheets__timesheet_entries__category=LATE_IN,
                        timesheets__timesheet_entries__is_deleted=False,
                        **fil
                    ) & ~excludes), timezone.timedelta(microseconds=0)
            ),
            'lost_early_out': Coalesce(
                Sum('timesheets__punch_out_delta',
                    filter=Q(
                        timesheets__timesheet_entries__category=EARLY_OUT,
                        timesheets__timesheet_entries__is_deleted=False,
                        **fil
                    ) & ~excludes), timezone.timedelta(microseconds=0)
            ),
            'lost_absent': Coalesce(
                Sum(
                    F(
                        'timesheets__expected_punch_out'
                    )-F(
                        'timesheets__expected_punch_in'
                    ),
                    filter=Q(
                        timesheets__is_present=False,
                        **fil
                    ) & ~excludes
                ), timedelta(0)
            ),
            'late_in_count': Count(
                'timesheets__id',
                filter=Q(
                    timesheets__timesheet_entries__category=LATE_IN,
                    **fil
                ) & ~excludes,
                distinct=True
            ),
            'early_out_count': Count(
                'timesheets__id',
                filter=Q(
                    timesheets__timesheet_entries__category=EARLY_OUT,
                    **fil
                ) & ~excludes,
                distinct=True
            ),
            'absent_count': Count(
                'timesheets__id',
                filter=Q(
                    timesheets__is_present=False,
                    **fil
                ) & ~excludes,
                distinct=True
            ),
            'unpaid_break_out_count': Count(
                'timesheets__id',
                filter=Q(
                    Q( missing_punch_out | break_out_on_unpaid_break),
                    **fil
                ) & ~excludes
            ),
        }

        queryset = queryset.annotate(**annotates).annotate(
            tmp_=Cast("lost_absent", dj_fields.CharField(max_length=255))
        ).annotate(
            tmp=Concat(F("tmp_"), Value(" minutes"))
        ).annotate(
            abs=Cast(F('tmp'), output_field=dj_fields.DurationField())
        ).annotate(
            total_unpaid_hours=Coalesce(
                Sum(
                    F(
                        'timesheets__unpaid_break_hours'
                    ),
                    filter=Q(
                        timesheets__timesheet_entries__entry_type=PUNCH_OUT,
                        timesheets__timesheet_entries__is_deleted=False,
                        **fil
                    ) & ~excludes
                ), timedelta(0)
            ),
        ).annotate(
            # early out is negative so (- -)= (+)
            total_lost=F('lost_late_in') - F('lost_early_out') + F('abs') + Coalesce(
                F('total_unpaid_hours'),
                Value(timedelta(0))
            )
        ).annotate(
            total_worked=Coalesce(
                Sum(
                    'timesheets__worked_hours',
                    filter=Q(
                        # @TODO: exclude timesheet_entries from annotation
                        timesheets__timesheet_entries__entry_type=PUNCH_OUT,
                        timesheets__timesheet_entries__is_deleted=False,
                        **fil
                    ) & ~excludes
                ), timedelta(0)
            ),
        )
        return super().filter_queryset(queryset)

    @staticmethod
    def annotate_shift_id(queryset):
        _date_time_for_work_shift = timezone.now()
        return queryset.annotate(
            # annotate queryset for workshift slug
            work_shift_id=Subquery(
                IndividualUserShift.objects.filter(
                    individual_setting__user_id=OuterRef('pk')
                ).filter(
                    Q(
                        applicable_from__lte=_date_time_for_work_shift) & Q(
                        Q(
                            applicable_to__gte=_date_time_for_work_shift
                        ) | Q(
                            applicable_to__isnull=True
                        )
                    )
                ).order_by().values('shift_id')[:1]
            )
        )

    @action(methods=['get'], detail=True, url_path='user',
            url_name='user-irregularity')
    def get_user_irregularity(self, request, *args, **kwargs):
        """
        ordering --> timesheet_for, total_lost
        """
        try:
            user = get_object_or_404(USER, pk=kwargs.get('pk'))
        except ValueError:
            raise Http404
        irregularity_type = request.query_params.get('type')

        qs = TimeSheet.objects.all()

        # ------------ supervisor filter section -------------------------------------#
        supervisor_id = self.request.query_params.get('supervisor')
        fil = dict(timesheet_user__detail__organization=self.get_organization())

        if supervisor_id:
            if supervisor_id == str(self.request.user.id):
                fil.update({
                    'timesheet_user_id__in':
                        self.request.user.subordinates_pks
                })
            else:
                # if supervisor does not match return none
                qs = qs.none()

        qs = qs.filter(**fil)
        # ------------ end of supervisor filter section -------------------------------------#

        qs = qs.filter(
            timesheet_user=user,
            coefficient=WORKDAY
        ).select_related(
            'timesheet_user',
            'timesheet_user__detail',
            'timesheet_user__detail__organization',
            'timesheet_user__detail__division',
            'timesheet_user__detail__job_title',
            'timesheet_user__detail__employment_level',
        )
        if not self.request.query_params.get('end_date'):
            qs = qs.filter(timesheet_for__lte=get_today())
        qs = apply_filters(
            qp=self.request.query_params,
            filter_map={
                'start_date': 'timesheet_for__gte',
                'end_date': 'timesheet_for__lte'
            },
            qs=qs
        )

        qs = qs.exclude(
            leave_coefficient=FULL_LEAVE
        )
        working_days = qs.count()
        user_shifts = user.timesheets.count()
        annotated_field = None

        if user_shifts < 1:
            return Response()  # empty response if no timesheets for user.
        if irregularity_type == 'absent':
            qs = qs.filter(
                is_present=False
            ).annotate(
                lost_absent=Coalesce(
                    F(
                        'expected_punch_out'
                    ) - F(
                        'expected_punch_in'
                    ),
                    timedelta(0)
                )
            )
            annotated_field = 'lost_absent'
        elif irregularity_type == 'late_in':
            qs = qs.filter(
                timesheet_entries__category=LATE_IN,
            ).annotate(
                lost_late_in=Sum(
                    'punch_in_delta',
                    filter=Q(
                        timesheet_entries__category=LATE_IN, 
                        timesheet_entries__is_deleted = False
                    )
                )
            )
            annotated_field = 'lost_late_in'

            # punctuality = (1 - qs.count() / user_shifts) * 100
        elif irregularity_type == 'early_out':
            qs = qs.filter(
                timesheet_entries__category=EARLY_OUT,
            ).annotate(
                lost_early_out=Sum(
                    'punch_out_delta',
                    filter=Q(
                        timesheet_entries__category=EARLY_OUT,
                        timesheet_entries__is_deleted = False
                    )
                )
            )
            annotated_field = 'lost_early_out'
            # punctuality = (1 - qs.count() / user_shifts) * 100
        elif irregularity_type == 'unpaid_breaks':
            break_out_on_unpaid_break = Q(
                Q(timesheet_entries__entry_type=BREAK_OUT) &
                Q(timesheet_entries__is_deleted=False) &
                Q(timesheet_entries__remark_category__in=settings.UNPAID_BREAK_TYPES)
            )
            missing_punch_out = Q(
                Q(punch_in__isnull=False) &
                Q(punch_out__isnull=True)
            )
            unpaid_breaks_filter = Q(
                break_out_on_unpaid_break |
                missing_punch_out
            )
            qs = qs.filter(
                # timesheet_entries__remark_category__in=settings.UNPAID_BREAK_TYPES,
            ).filter(unpaid_breaks_filter).annotate(
                unpaid_breaks=Sum(
                    'unpaid_break_hours',
                    filter=Q(
                        timesheet_entries__entry_type=PUNCH_OUT,
                        timesheet_entries__is_deleted=False,
                    )
                )
            )
            annotated_field = 'unpaid_breaks'
            # punctuality = (1 - qs.count() / user_shifts) * 100
        else:
            qs = qs.none()

        qs = self.order_user_irregularity(qs, annotated_field)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = AttendanceIrregularitiesDetailSerializer(
                page, many=True, context={'irregularity_type': irregularity_type}
            )
            resp = self.get_paginated_response(serializer.data)
            resp.data.update({
                "total_working_days": working_days,
            })
            return resp
        return Response

    def order_user_irregularity(self, qs, annotated_field):
        ordering = self.request.query_params.get("ordering")

        if ordering in ['timesheet_for', '-timesheet_for']:
            qs = qs.order_by(ordering)

        elif ordering in ['total_lost', '-total_lost']:
            if annotated_field:
                # this should not be the case but in case of bad data specially in absent case
                default_value = timezone.timedelta(
                    microseconds=0)

                # in case of early out timedelta is negative, so reverse ordering
                if annotated_field == "lost_early_out":
                    ordering = "-total_lost" if ordering == "total_lost" else "total_lost"

                qs = qs.annotate(
                    total_lost=Case(
                        When(**{f"{annotated_field}__isnull": False},
                             then=F(annotated_field)),
                        default=default_value,
                    )
                ).order_by(ordering)
        else:
            qs = qs.order_by('-timesheet_for')
        return qs

    def get_frontend_redirect_url(self):
        return f'/admin/{self.organization.slug}/attendance/reports/irregularity'


class TimeSheetEntryCategoryViewSet(OrganizationMixin, ListViewSetMixin,
                                    AttendanceReportPermissionMixin
                                    ):
    serializer_class = []
    filter_backends = (FilterMapBackend,)
    filter_map = {
        'start_date': 'timesheet__timesheet_for__gte',
        'end_date': 'timesheet__timesheet_for__lte',
        'timesheet_user': 'timesheet__timesheet_user',
        'category': 'remark_category'
    }
    queryset = TimeSheetEntry.objects.filter(is_deleted=False)
    lookup_url_kwarg = 'category'

    def get_queryset(self):
        supervisor_id = self.request.query_params.get('supervisor')
        fil = dict(
            timesheet__timesheet_user__detail__organization=self.organization
        )

        if supervisor_id:
            if supervisor_id == str(self.request.user.id):
                fil.update({
                    'timesheet__timesheet_user_id__in':
                        self.request.user.subordinates_pks
                })
            else:
                # if supervisor does not match return none
                return super().get_queryset().none()

        return super().get_queryset().filter(**fil)

    def list(self, request, *args, **kwargs):
        # UPDATE: show all breaks count instead of total users
        remarks = (
            TEA_BREAK, CLIENT_VISIT, LUNCH_BREAK, MEETING, PERSONAL, OTHERS
        )
        remarks_count = self.filter_queryset(
            self.get_queryset()
        ).aggregate(
            **{
                remark_category: Count(
                    'id',
                    filter=Q(
                        entry_type=BREAK_OUT,
                        remark_category=remark_category,
                        timesheet__timesheet_user__is_active=True,
                        timesheet__timesheet_user__is_blocked=False,
                    )
                )
                for remark_category in remarks},
            **{
                f'{remark_category} users': Count(
                    'timesheet__timesheet_user',
                    distinct=True,
                    filter=Q(
                        entry_type=BREAK_OUT,
                        remark_category=remark_category,
                        timesheet__timesheet_user__is_active=True,
                        timesheet__timesheet_user__is_blocked=False,
                    )
                )
                for remark_category in remarks}
        )
        result = []

        for remark in remarks:
            remark = remark
            count = remarks_count.get(remark)
            result.append({
                'category': remark,
                'count': count,
                'users': remarks_count.get(f'{remark} users')
            })
        return Response(result)

    def get_users_for_category(self, remark, limit_=5):
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        _filters = dict()
        try:
            _ = dateparser.parse(start_date)
            _ = dateparser.parse(end_date)
        except (TypeError, ValueError):
            start_date = None
            end_date = None
        _filters = {
            'timesheets__timesheet_for__range': (start_date, end_date)
        } if start_date and end_date else {
            'timesheets__timesheet_for__year': timezone.now().year,
            'timesheets__timesheet_for__month': timezone.now().month,
        }
        users = self.user_queryset.filter(
            timesheets__timesheet_entries__entry_type=BREAK_OUT,
            timesheets__timesheet_entries__remark_category=remark,
            **_filters
        ).distinct()
        return UserThinSerializer(
            users[:limit_], many=True
        ).data

    @cached_property
    def user_queryset(self):
        supervisor_id = self.request.query_params.get('supervisor')
        fil = dict()

        if supervisor_id:
            if supervisor_id == str(self.request.user.id):
                fil.update({
                    'id__in':
                        self.request.user.subordinates_pks
                })
            else:
                # if supervisor does not match return none
                return USER.objects.none()
        else:
            # only use organization filter if supervisor is not passed in
            # query params, else filter by subordinates
            fil.update({'detail__organization':
                            self.get_organization()})

        return USER.objects.all().current().filter(**fil).select_related(
            'detail',
            'detail__organization',
            'detail__employment_level',
            'detail__division',
            'detail__job_title').prefetch_related(
            'timesheets',
            'timesheets__timesheet_entries'
        )

    @action(detail=False, methods=['get'], )
    def users(self, *args, **kwargs):
        filter_map = {
            'category': 'timesheets__timesheet_entries__remark_category',
            'start_date': 'timesheets__timesheet_for__gte',
            'end_date': 'timesheets__timesheet_for__lte',
        }
        user_set = apply_filters(
            self.request.query_params,
            filter_map,
            USER.objects.filter(
                detail__organization=self.organization
            ).distinct().select_essentials()
        ).filter(
            # Filters users with given timesheet entry type.
            # The query time-outs.
            # timesheets__timesheet_entries__entry_type=BREAK_OUT,
        )
        page = self.paginate_queryset(user_set)
        serializer = UserThinSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class UserAttendanceIrregularityViewSet(
    OrganizationMixin,
    UserMixin,
    ListViewSetMixin
):
    """
    Normal User Attendance Irregularity
    ===================================

    filters
    -------

        start_date
        end_date

    ordering
    --------

        timesheet_for
        -timesheet_for

    """
    serializer_class = IndividualAttendanceIrregularityReportSerializer
    queryset = TimeSheet.objects.all()
    permission_classes = [AttendanceReportPermission]
    filter_backends = (FilterMapBackend, )
    filter_map = {
        "start_date": "timesheet_for__gte",
        "end_date": "timesheet_for__lte"
    }

    def has_user_permission(self):
        return self.user == self.request.user

    def get_queryset(self):
        return super().get_queryset().filter(
            timesheet_user=self.user,
            timesheet_user__detail__organization=self.get_organization()
        ).annotate(

            absent=Case(When(
                is_present=False,
                coefficient=WORKDAY,
                leave_coefficient__in=[FIRST_HALF, SECOND_HALF, NO_LEAVE],
                then=True
            ), default=False, output_field=dj_fields.BooleanField()),

            late_in=Exists(
                TimeSheetEntry.objects.filter(timesheet_id=OuterRef('pk'), is_deleted=False).filter(
                    Q(
                        category=LATE_IN,
                        entry_type=PUNCH_IN,
                        timesheet__coefficient=WORKDAY
                    ) & ~Q(
                        timesheet__leave_coefficient=FULL_LEAVE
                    )
                )),
            early_out=Exists(
                TimeSheetEntry.objects.filter(timesheet_id=OuterRef('pk'), is_deleted=False).filter(
                    Q(
                        category=EARLY_OUT, entry_type=PUNCH_OUT, timesheet__coefficient=WORKDAY
                    ) & ~Q(
                        timesheet__leave_coefficient=FULL_LEAVE
                    ),
                )
            )
        ).exclude(absent=False, late_in=False, early_out=False).annotate(

            lost_late_in=Case(When(
                late_in=True,
                then=F('punch_in_delta')
            ), default=None, output_field=dj_fields.DurationField(null=True)),

            lost_early_out=Case(When(
                early_out=True,
                then=-F('punch_out_delta')
            ), default=None, output_field=dj_fields.DurationField(null=True)),

            lost_absent=Case(When(
                absent=True,
                expected_punch_in__isnull=False,
                expected_punch_out__isnull=False,
                then=F('expected_punch_out') - F('expected_punch_in')
            ), When(
                absent=False,
                then=None
            ), default=timezone.timedelta(0), output_field=dj_fields.DurationField(null=True))

        ).annotate(
            total_lost=Coalesce(
                F('lost_late_in'), timezone.timedelta(0)) + Coalesce(
                F('lost_early_out'), timezone.timedelta(0)) + Coalesce(
                F('lost_absent'), timezone.timedelta(0)) + Coalesce(
                F('unpaid_break_hours'), timezone.timedelta(0))
        )

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        ordering = self.request.query_params.get('ordering', '-timesheet_for')

        if ordering in ['-timesheet_for', 'timesheet_for']:
            queryset = queryset.order_by(ordering, 'expected_punch_in')
        return queryset

    def list(self, request, *args, **kwargs):
        response = super(UserAttendanceIrregularityViewSet, self).list(request, *args, **kwargs)

        try:
            total_lost = round(self.filter_queryset(self.get_queryset()).order_by().values(
                'timesheet_user_id'
            ).annotate(
                total_lost_=Coalesce(
                    Sum('total_lost'), timezone.timedelta(0))
            )[0]['total_lost_'].total_seconds() / 60, 2)
        except (IndexError, KeyError):
            total_lost = 0.0

        response.data.update({'total_lost': total_lost})
        return response
