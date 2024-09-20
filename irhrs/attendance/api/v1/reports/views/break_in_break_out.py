from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db.models import Q, Count, Sum
from django.db.models.functions import Coalesce
import openpyxl
from django_q.tasks import async_task
from openpyxl import Workbook
from openpyxl.writer.excel import save_virtual_workbook
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404

from config import settings
from irhrs.attendance.api.v1.permissions import AttendanceReportPermission
from irhrs.attendance.api.v1.reports.serializers.break_in_break_out import \
    BreakInBreakOutDetailReportSerializer, BreakInBreakOutReportSerializer
from irhrs.attendance.api.v1.reports.views.mixins import \
    AttendanceReportPermissionMixin
from irhrs.attendance.constants import BREAK_OUT, BREAK_IN, PUNCH_OUT
from irhrs.attendance.models import IndividualUserShift, TimeSheetEntry
from irhrs.export.constants import ADMIN, SUPERVISOR, NORMAL_USER, QUEUED, FAILED, PROCESSING, \
    COMPLETED
from irhrs.attendance.utils.break_in_break_out import get_total_lost, get_total_paid_breaks,create_report_workbook
from irhrs.core.mixins.viewset_mixins import OrganizationMixin, \
    ListViewSetMixin, DateRangeParserMixin, PastUserParamMixin, \
    PastUserFilterMixin
from irhrs.core.utils.common import apply_filters, validate_permissions, get_complete_url
from irhrs.core.utils.filters import OrderingFilterMap, FilterMapBackend
from irhrs.export.models import Export
from irhrs.export.utils.helpers import get_latest_export, has_pending_export

USER = get_user_model()


class BreakInBreakOutReportView(
    PastUserFilterMixin, DateRangeParserMixin, OrganizationMixin,
    AttendanceReportPermissionMixin, ListViewSetMixin, PastUserParamMixin
):
    """
    filters -

        start_date
        end_date
        remark_category
        division
        branch

    ordering -

    in user list

        full_name

    in detail

        date

    """
    serializer_class = BreakInBreakOutReportSerializer
    search_fields = (
        'first_name', 'middle_name', 'last_name', 'username',
    )
    filter_backends = (
        filters.SearchFilter, OrderingFilterMap, FilterMapBackend
    )
    ordering_fields_map = {
        'full_name': ('first_name', 'middle_name', 'last_name'),
        'break_in_out_count': 'break_in_out_count'
    }
    filter_map = {
        'division': 'detail__division__slug',
        'branch': 'detail__branch__slug',
    }
    queryset = USER.objects.all()
    export_type = "Breakin Breakout"
    export_name = "breakin_breakout_report.xlsx"

    @property
    def mode(self):
        mode = self.request.query_params.get('as')
        if mode in ["supervisor", "hr"]:
            return mode
        return "user"

    @property
    def is_hr(self):
        if self.mode == "hr" and validate_permissions(
            self.request.user.get_hrs_permissions(self.get_organization()),
            AttendanceReportPermission
        ):
            return True
        return False

    def get_exported_as(self):
        if self.is_hr:
            return ADMIN
        elif self.mode == "supervisor":
            return SUPERVISOR
        return NORMAL_USER

    def _export_get(self):
        organization = self.get_organization()
        latest_export = get_latest_export(
            export_type=self.export_type,
            user=self.request.user,
            exported_as=self.get_exported_as(),
            organization=organization
        )

        if latest_export:
            return Response({
                'url': get_complete_url(latest_export.export_file.url),
                'created_on': latest_export.modified_at
            })
        else:
            return Response({
                'message': 'Previous Export file couldn\'t be found.',
                'url': ''
            }, status=status.HTTP_200_OK
            )

    def _export_post(self, *args, **kwargs):
        organization = self.get_organization()

        if has_pending_export(
            export_type=self.export_type,
            user=self.request.user,
            exported_as=self.get_exported_as(),
            organization=organization
        ):
            return Response({
                'message': 'Previous request for generating report is being '
                           'currently processed, Please try back later'},
                status=status.HTTP_202_ACCEPTED)

        export = Export.objects.create(
            user=self.request.user,
            name=self.export_name,
            exported_as=self.get_exported_as(),
            export_type=self.export_type,
            organization=organization,
            status=QUEUED,
            remarks=''
        )

        start = self.request.query_params["start_date"]
        end = self.request.query_params["end_date"]
        user = get_object_or_404(USER, pk=self.kwargs.get('pk'))
        break_details, qs = self.get_break_details(user=user)

        try:
            _ = async_task(
                create_report_workbook,
                start,
                end,
                break_details,
                qs,
                export,
                user,
                self.export_name
            )
        except Exception as e:
            import traceback

            export.status = FAILED
            export.message = "Could not start export."
            export.traceback = str(traceback.format_exc())
            export.save()
            if getattr(settings, 'DEBUG', False):
                raise e
            return Response({
                'message': 'The export could not be completed.'
            }, status=400)

        return Response({
            'message': 'Your request is being processed in the background . Please check back later'
        })

    @action(methods=['GET', 'POST'], detail=True, url_path="excel-report")
    def excel_report(self, *args, **kwargs):
        if self.request.method.upper() == 'GET':
            return self._export_get()
        else:
            return self._export_post()

    def has_user_permission(self):
        if self.kwargs.get('pk') == str(self.request.user.id):
            return True
        return super().has_user_permission()

    @staticmethod
    def get_default_end_date():
        return timezone.now() - timezone.timedelta(5)

    @staticmethod
    def get_default_start_date():
        return timezone.now() + timezone.timedelta(5)

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
                return super().get_queryset().none()

        date_range = self.get_parsed_dates()

        remark_category = self.request.query_params.get('remark_category')
        count_fil = {
            'timesheets__timesheet_entries__entry_type': BREAK_OUT,
            'timesheets__timesheet_for__range': date_range
        }
        if remark_category:
            count_fil.update({
                'timesheets__timesheet_entries__remark_category': remark_category})
        qs = super().get_queryset()

        return qs.filter(
            **fil
        ).annotate(
            break_in_out_count=Count(
                'timesheets__timesheet_entries',
                filter=Q(**count_fil))
        ).filter(break_in_out_count__gt=0).select_essentials()

    def get_break_details(self,*args,**kwargs):
        user = kwargs["user"]
        time_out_hours = get_total_lost(self.get_entries(user))
        zero_delta = timezone.timedelta(0)

        qs = user.timesheets.filter(
            timesheet_entries__entry_type__in=[BREAK_IN, BREAK_OUT],
            timesheet_entries__is_deleted=False,
        ).order_by().distinct('timesheet_for')

        # for date range filters
        qs = apply_filters(
            self.request.query_params,
            {
                'start_date': 'timesheet_for__gte',
                'end_date': 'timesheet_for__lte',
            },
            qs
        )

        unpaid_break_in_seconds = user.timesheets.filter(
            id__in=qs.values_list('id')
        ).filter().aggregate(
            total_unpaid_breaks=Coalesce(
                Sum(Coalesce('unpaid_break_hours', zero_delta)),
                zero_delta
            )
        ).get('total_unpaid_breaks').total_seconds() or 0
        if unpaid_break_in_seconds:
            unpaid_break_in_mins = unpaid_break_in_seconds // 60
        else:
            unpaid_break_in_mins = 0
        break_in_out_count = TimeSheetEntry.objects.filter(
            entry_type=BREAK_OUT,
            is_deleted=False,
            timesheet_id__in=qs.values_list('id', flat=True)
        ).count()
        total_paid_breaks = get_total_paid_breaks(self.get_entries(user))
        return  {
            'total_lost': time_out_hours,
            'total_paid_breaks': total_paid_breaks,
            'break_in_out_count': break_in_out_count,
            'total_unpaid_breaks': unpaid_break_in_mins,
        }, qs

    @action(detail=True, url_path='detail')
    def get_break_in_out_detail(self, *args, **kwargs):
        kwargs['user']=USER.objects.get(id=kwargs['pk'])

        break_details, qs = self.get_break_details(*args, **kwargs)

        ordering = self.request.query_params.get('ordering')
        if ordering == "date":
            qs = qs.order_by('timesheet_for')
        elif ordering == "-date":
            qs = qs.order_by('-timesheet_for')

        page = self.paginate_queryset(qs)
        ctx = self.get_serializer_context()
        ctx.update({
            'breakout_category': self.request.query_params.get(
                'remark_category'
            )
        })
        serializer = BreakInBreakOutDetailReportSerializer(
            page, many=True, context=ctx
        )
        resp = self.get_paginated_response(serializer.data)
        resp.data.update(break_details)
        return resp

    def get_entries(self, user):
        return apply_filters(
            self.request.query_params,
            {
                'start_date': 'timesheet__timesheet_for__gte',
                'end_date': 'timesheet__timesheet_for__lte',
                'remark_category': 'remark_category'
            },
            TimeSheetEntry.objects.select_related(
                'timesheet'
            ).filter(
                timesheet__timesheet_user=user,
                is_deleted=False
            ).filter(
                Q(
                    entry_type__in=[BREAK_IN, BREAK_OUT, PUNCH_OUT]
                )
            )
        )
