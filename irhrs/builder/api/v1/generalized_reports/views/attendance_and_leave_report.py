import itertools

from django.contrib.auth import get_user_model
from django.db.models import fields as dj_fields, Q, Sum, F, Value, Count, OuterRef, Subquery
from django.db.models.functions import Coalesce, Cast, Concat
from django.forms.utils import pretty_name
from django.utils import timezone
from django.utils.functional import cached_property
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField, ReadOnlyField
from rest_framework.filters import SearchFilter

from irhrs.attendance.constants import (
    WORKDAY, HOLIDAY, FULL_LEAVE, CONFIRMED, OFFDAY)
from irhrs.attendance.models import OvertimeEntry
from irhrs.builder.api.v1.generalized_reports.serializers.attendance_and_leave_report import \
    AttendanceAndLeaveReportSerializer, LeaveOnlyReportSerializer, ExportSerializerBase
from irhrs.builder.permissions import AttendanceAndLeavePermission
from irhrs.core.mixins.serializers import add_fields_to_serializer_class
from irhrs.core.mixins.viewset_mixins import ListViewSetMixin, \
    OrganizationMixin, DateRangeParserMixin, PastUserFilterMixin
from irhrs.core.utils import HumanizedDurationField
from irhrs.core.utils.common import get_today
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.export.mixins.export import BackgroundTableExportMixin
from irhrs.leave.constants.model_constants import APPROVED, TIME_OFF, HOURLY_LEAVE_CATEGORIES
from irhrs.leave.models import MasterSetting, LeaveType, LeaveAccountHistory
from irhrs.leave.models.request import LeaveSheet
from irhrs.permission.constants.permissions import ATTENDANCE_REPORTS_PERMISSION, LEAVE_REPORT_PERMISSION

USER = get_user_model()


class AttendanceAndLeaveViewSet(
    PastUserFilterMixin, OrganizationMixin, DateRangeParserMixin,
    BackgroundTableExportMixin, ListViewSetMixin
):
    """
    Attendance and leave combined report
    ====================================

    filters
    -------

    **date_filters**

        start_date, end_date

    **send leave types**

        send_leave_types=true

    **select leave types**

        leave_types=1,2,3

    **exclude attendance**

        exclude_attendance=true
    """
    serializer_class = AttendanceAndLeaveReportSerializer
    queryset = USER.objects.filter()
    filter_backends = [SearchFilter, FilterMapBackend, OrderingFilterMap]
    filter_map = {
        'division': 'detail__division__slug',
        'username': 'username',
    }
    search_fields = (
        'first_name', 'middle_name', 'last_name', 'username'
    )
    ordering_fields_map = {
        'full_name': ('first_name', 'middle_name', 'last_name'),
        'holidays': 'holidays',
        'working_days': 'working_days',
        'off_days': 'off_days',
        'present_days': 'present_days',
        'absent_days': 'absent_days',
        'total_lost': 'total_lost',
        'confirmed_time': 'confirmed_overtime'
    }
    permission_classes = [AttendanceAndLeavePermission]
    __selected_leave_types = None
    notification_permissions = [ATTENDANCE_REPORTS_PERMISSION, LEAVE_REPORT_PERMISSION]

    def get_export_description(self):
        lines = [
            self.get_export_type()
        ]
        start_date, end_date = self.get_parsed_dates()
        no_of_days = (end_date - start_date).days + 1
        lines.append(
            f"Date Range: {start_date} - {end_date}, Total Days: {no_of_days}"
        )
        return lines

    def get_export_type(self):
        exclude_attendance = self.request.query_params.get('exclude_attendance', 'false') == 'true'
        if exclude_attendance:
            return "Monthly Leave Report"
        return "Attendance and Leave Report"

    def get_export_fields(self):

        export_fields = [
            {
                "name": "user",
                "title": "User Details",
                "fields": [
                    {
                        "name": "id",
                        "title": "Id"
                    },
                    {
                        "name": "full_name",
                        "title": "Full Name"
                    },
                    {
                        "name": "username",
                        "title": "Username"
                    },
                ]
            }
        ]

        exclude_attendance = self.request.query_params.get('exclude_attendance', 'false') == 'true'

        attendance_fields = ['holidays', 'off_days', 'absent_days', 'total_lost', 'confirmed_overtime']
        leave_fields = ['working_days', 'present_days', 'total_leave']

        fields_in_order = ['holidays', 'working_days', 'off_days', 'total_leave', 'present_days', 'leave_types', 'absent_days',
                           'total_lost', 'confirmed_overtime']

        available_fields = leave_fields if exclude_attendance else attendance_fields + leave_fields

        for field in fields_in_order:
            if field in available_fields:
                export_fields.append(
                    {
                        "name": field,
                        "title": pretty_name(field)
                    }
                )
            elif field == 'leave_types':
                for lt in self.get_selected_leave_types():
                    export_fields.append(
                        {
                            "name": str(lt.id),
                            "title": pretty_name(str(lt.name)),
                            "fields": [
                                {
                                    "name": "used",
                                    "title": "Used Balance"
                                },
                                {
                                    "name": "balance",
                                    "title": "Remaining Balance"
                                }
                            ]
                        }
                    )
        return export_fields

    def get_serializer_context(self):
        _, end_date = self.get_parsed_dates()
        ctx = super().get_serializer_context()
        ctx['selected_leaves'] = self.get_selected_leave_types_ids()
        ctx['leavesheet_filter'] = self.get_leavesheet_filter()
        ctx['end_date_parsed'] = end_date
        return ctx

    def get_extra_export_data(self):
        start_date, end_date = self.get_parsed_dates()

        extra = super().get_extra_export_data()
        extra["serializer_context"] = {
            "selected_leaves": self.get_selected_leave_types_ids(),
            "leavesheet_filter": self.get_leavesheet_filter(),
            "end_date_parsed": end_date
        }

        extra['exclude_attendance'] = self.request.query_params.get('exclude_attendance', 'false') == 'true'
        extra['overtime_filter'] = {
            'timesheet__timesheet_for__range': [start_date, end_date]
        }


        return extra

    def get_serializer_class_params(self):
        exclude_attendance = self.request.query_params.get('exclude_attendance', 'false') == 'true'
        return {
            "args": [exclude_attendance, self.get_selected_leave_types_ids()],
            "kwargs": dict()
        }

    @classmethod
    def get_serializer_class_for_export(cls, exclude_attendance, selected_leave_types):
        attendance_fields = ['holidays', 'off_days', 'absent_days', 'total_lost', 'confirmed_overtime']
        leave_fields = ['working_days', 'present_days', 'total_leave']
        fields_type_map = {
            "total_lost": HumanizedDurationField(),
            "confirmed_overtime": HumanizedDurationField(),
            "total_leave": SerializerMethodField()
        }

        serializer_fields = dict()
        serializer_get_methods = dict()

        available_fields = leave_fields if exclude_attendance else itertools.chain(attendance_fields, leave_fields)
        for field in available_fields:
            serializer_fields.update({
                field: fields_type_map.get(field, ReadOnlyField())
            })

        for leave_type_id in selected_leave_types:
            serializer_fields.update({
                str(leave_type_id): SerializerMethodField()
            })
            serializer_get_methods.update({
                f"get_{leave_type_id}": lambda self, obj, lti=leave_type_id: self.get_details_for_leave_type(obj, lti)
            })

        return add_fields_to_serializer_class(serializer_class=ExportSerializerBase,
                                              fields=dict(**serializer_fields, **serializer_get_methods))

    def get_serializer_class(self):
        if self.request.query_params.get('exclude_attendance', 'false') == 'true' and self.action != 'export':
            return LeaveOnlyReportSerializer
        return super().get_serializer_class()

    def get_default_start_date(self):
        return timezone.now().date() - timezone.timedelta(days=30)

    def get_default_end_date(self):
        return get_today()

    @staticmethod
    def annoatate_total_lost(queryset, timesheet_filter):
        """Annotates total lost due to Absent, Late In and early Out"""
        fil = dict(timesheet_filter)
        fil.update({'timesheets__coefficient': WORKDAY})
        excludes = Q(timesheets__leave_coefficient=FULL_LEAVE)

        attendance_lost_annotates = {
            'lost_late_in': Coalesce(
                Sum(
                    'timesheets__punch_in_delta',
                    filter=Q(
                        timesheets__punch_in_delta__gt=timezone.timedelta(
                            minutes=0),
                        **fil
                    ) & ~excludes), timezone.timedelta(microseconds=0)
            ),
            'lost_early_out': Coalesce(
                Sum('timesheets__punch_out_delta',
                    filter=Q(
                        timesheets__punch_out_delta__lt=timezone.timedelta(
                            minutes=0),
                        **fil
                    ) & ~excludes), timezone.timedelta(microseconds=0)
            ),
            'sum_unpaid_breaks': Coalesce(
                Sum(
                    'timesheets__unpaid_break_hours',
                    filter=Q(
                        timesheets__unpaid_break_hours__isnull=False,
                        **fil
                    ) & ~excludes
                ), timezone.timedelta(microseconds=0)
            ),
            'lost_absent': Coalesce(
                Sum(
                    'timesheets__work_time__working_minutes',
                    filter=Q(
                        timesheets__is_present=False,
                        **fil
                    ) & ~excludes
                ), 0
            )
        }

        return queryset.annotate(**attendance_lost_annotates).annotate(
            _=Cast("lost_absent", dj_fields.CharField(max_length=255))
        ).annotate(
            __=Concat(F("_"), Value(" minutes"))
        ).annotate(
            ___=Cast(F('__'), output_field=dj_fields.DurationField())
        ).annotate(
            # early out is negative so (- -)= (+)
            total_lost=F('lost_late_in') - F('lost_early_out') + F('___') + F('sum_unpaid_breaks')
        )

    @staticmethod
    def annotate_overtime(queryset, overtime_filter):
        """Annotates total confirmed overtime(claimed) at given date range"""
        sq = OvertimeEntry.objects.filter(
            claim__status=CONFIRMED, **overtime_filter
        ).filter(user_id=OuterRef('pk')).order_by().values('user_id').annotate(
            claimed=Sum('overtime_detail__claimed_overtime')
        ).values('claimed')[:1]
        return queryset.annotate(confirmed_overtime=Coalesce(
            Subquery(sq, output_field=dj_fields.DurationField()), timezone.timedelta(0)))

    def annotate_attendance(self, queryset, timesheet_filter, overtime_filter):
        """
        Annotates attendance related fields
        """
        queryset = queryset.annotate(
            holidays=Count('timesheets', filter=Q(
                timesheets__coefficient=HOLIDAY,
                **timesheet_filter
            ), distinct=True),

            absent_days=Count('timesheets', filter=Q(
                Q(timesheets__is_present=False, timesheets__coefficient=WORKDAY, **timesheet_filter) &
                ~Q(timesheets__leave_coefficient=FULL_LEAVE)
            ), distinct=True),
        )
        queryset = self.annoatate_total_lost(queryset, timesheet_filter)

        if not self.action == 'export':
            queryset = self.annotate_overtime(queryset, overtime_filter)

        return queryset

    def annotate_total_leave(self, queryset):
        """
        Annotate total leaves taken in the interval
        Note: This method is not used not (Currently calculating from serializer) due to high CPU load
        """
        selected_leave_type_ids = self.get_selected_leave_types_ids()

        if not selected_leave_type_ids:
            return queryset.annotate(total_leave=Value(0, output_field=dj_fields.FloatField()))

        leavesheet_filter = {
            'request__leave_rule__leave_type_id__in': selected_leave_type_ids,
            'request__end__date__lte': get_today(),
            'leave_for__range': self.get_parsed_dates()
        }

        leave_balance = LeaveSheet.objects.filter(request__user_id=OuterRef('pk')).filter(
            request__status=APPROVED,
            **leavesheet_filter
        ).exclude(
            # exclude time off leave
            request__leave_rule__leave_type__category=TIME_OFF
        ).order_by().values('request__user_id').annotate(
            total_consumed=Sum('balance')
        ).values('total_consumed')[:1]

        return queryset.annotate(total_leave=Coalesce(Subquery(leave_balance, output_field=dj_fields.FloatField()), 0))

    def annotate_leave_types(self, queryset):
        """
        Annotate selected leave types' used and remaining balance at end of date range
        Note: This method is not used not (Currently calculating from serializer) due to high CPU load
        """
        leave_types = self.get_selected_leave_types()
        leavesheet_filter = self.get_leavesheet_filter()
        _, end_date = self.get_parsed_dates()

        annotates = dict()

        for lt in leave_types:
            annotates.update({
                f"{lt.id}_used": Coalesce(Subquery(
                    LeaveSheet.objects.filter(
                        request__user_id=OuterRef('pk'), request__leave_rule__leave_type_id=lt.id
                    ).filter(request__status=APPROVED, **leavesheet_filter).order_by().values(
                        'request__user_id').annotate(total_balance=Sum('balance')).values('total_balance')[:1],
                    output_field=dj_fields.FloatField()
                ), 0
                ),
                f"{lt.id}_balance": Coalesce(Subquery(
                    LeaveAccountHistory.objects.filter(
                        user_id=OuterRef('pk'), account__rule__leave_type_id=lt.id
                    ).filter(modified_at__date__lte=end_date).order_by('-modified_at').values('new_usable_balance')[:1],
                    output_field=dj_fields.FloatField()
                ), 0)
            })

        return queryset.annotate(**annotates)

    def get_queryset(self):
        timesheet_filter = {
            'timesheets__timesheet_for__range': self.get_parsed_dates()
            # date range filter
        }
        overtime_filter = {
            'timesheet__timesheet_for__range': self.get_parsed_dates()
        }

        qs = super().get_queryset().filter(
            detail__organization=self.get_organization()
        ).annotate(
            working_days=Count('timesheets', filter=Q(
                timesheets__coefficient=WORKDAY,
                **timesheet_filter
            ), distinct=True),

            present_days=Count('timesheets', filter=Q(
                timesheets__is_present=True,
                **timesheet_filter,
            ), distinct=True),

            off_days=Count('timesheets', filter=Q(
                timesheets__coefficient=OFFDAY,
                **timesheet_filter,
            ), distinct=True)
        )

        if not self.request.query_params.get('exclude_attendance', 'false') == 'true':
            qs = self.annotate_attendance(qs, timesheet_filter, overtime_filter)

        # Note: Not used not (Currently calculating from serializer) due to high CPU load
        # qs = self.annotate_total_leave(qs)
        # qs = self.annotate_leave_types(qs)
        return qs.select_essentials()

    def get_available_leave_types(self):
        """Available leave types for selecting"""
        # base = self.master_setting.leave_types.all()
        _, end_date = self.get_parsed_dates()
        base = LeaveType.objects.filter(
            master_setting__in=MasterSetting.objects.filter(
                organization=self.get_organization(),
            ).active_for_date(end_date)
        )
        hourly = self.request.query_params.get('hourly')
        if hourly:
            if hourly == 'true':
                base = base.filter(category__in=HOURLY_LEAVE_CATEGORIES)
            elif hourly == 'false':
                base = base.exclude(category__in=HOURLY_LEAVE_CATEGORIES)
        return base

    @cached_property
    def master_setting(self):
        """Active master setting for given date range"""
        _, end_date = self.get_parsed_dates()
        ms = MasterSetting.objects.filter(
            organization=self.get_organization()).active_for_date(end_date).first()
        if not ms:
            raise ValidationError("No active master setting for given end date.")
        return ms

    def get_extra_data(self):
        """Extra data added at the end of response data"""
        start, end = self.get_parsed_dates()
        ret = {"no_of_days": (end - start).days + 1}

        if self.request.query_params.get('send_leave_types', None) == 'true':
            ret.update({'leave_type': [
                {
                    'name': t.get('cname'),
                    'id': t.get('id')
                } for t in self.get_available_leave_types().annotate(
                    cname=Concat(F('name'), Value('--'), F('master_setting__name'))
                ).values('cname', 'id')
            ]
            })

        return ret

    def get_selected_leave_types_ids(self):
        """
        :return: Selected leave types from query params
        """
        selected_leave_str = self.request.query_params.get('leave_types')
        if not selected_leave_str:
            return []

        try:
            selected_leaves = {int(lt_id) for lt_id in selected_leave_str.split(',')}
        except ValueError:
            raise ValidationError('Invalid leave types sent')

        return selected_leaves

    def get_selected_leave_types(self):
        """Selected leave types queryset"""
        if not self.__selected_leave_types:
            self.__selected_leave_types = list(LeaveType.objects.filter(id__in=self.get_selected_leave_types_ids()))
        return self.__selected_leave_types

    def get_leavesheet_filter(self):
        """Filter for leave sheet"""
        return {
            'request__end__date__lte': get_today(),
            'leave_for__range': self.get_parsed_dates()
        }

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data.update(self.get_extra_data())
        return response

    @classmethod
    def get_exported_file_content(
        cls, data, title, columns, extra_content, description=None, **kwargs
    ):
        exclude_attendance = extra_content.get('exclude_attendance', False)
        overtime_fiter = extra_content.get('overtime_filter', {})

        if not exclude_attendance:
            data = cls.annotate_overtime(data, overtime_filter=overtime_fiter)

        return super().get_exported_file_content(data, title, columns, extra_content, description)

    def get_frontend_redirect_url(self):
        exclude_attendance = self.request.query_params.get('exclude_attendance', 'false') == 'true'
        if exclude_attendance:
            return f'/admin/{self.organization.slug}/leave/reports/basic/monthly-leave'
        return f'/admin/{self.organization.slug}/common/master-report/generalized/attendance-and-leave'
