from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum, Subquery, OuterRef, Min, Value, DurationField, \
    FloatField
from django_filters.rest_framework import DjangoFilterBackend
from django_q.tasks import async_task
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from irhrs.attendance.api.v1.serializers.breakout_penalty import BreakOutPenaltySettingSerializer, \
    TimeSheetUserPenaltySerializer, FiscalMonthSelectionSerializer, \
    BreakOutPenaltyBulkActionSerializer, TimeSheetUserPenaltyGroupByUserSerializer
from irhrs.attendance.constants import CONFIRMED, CANCELLED
from irhrs.attendance.models import BreakOutPenaltySetting
from irhrs.attendance.models.breakout_penalty import TimeSheetUserPenalty
from irhrs.attendance.utils.breakout_penalty_report import generate_penalty_report
from irhrs.core.mixins.viewset_mixins import (
    RetrieveUpdateViewSetMixin, OrganizationMixin, OrganizationCommonsMixin,
    DateRangeParserMixin, ListViewSetMixin, ModeFilterQuerysetMixin,
    ListRetrieveUpdateDestroyViewSetMixin, GetStatisticsMixin
)
from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.common_utils import get_users_list_from_permissions
from irhrs.core.utils.filters import OrderingFilterMap, FilterMapBackend
from irhrs.core.utils.subordinates import find_immediate_subordinates
from irhrs.export.mixins.export import BackgroundExcelExportMixin
from irhrs.permission.constants.permissions.attendance import \
    ATTENDANCE_BREAK_OUT_PENALTY_PERMISSION, ATTENDANCE_BREAK_OUT_PENALTY_SETTING_PERMISSION
from irhrs.permission.permission_classes import permission_factory

USER = get_user_model()


class BreakOutPenaltySettingView(
    OrganizationMixin,
    OrganizationCommonsMixin,
    ModelViewSet
):
    """
    * API: `http://localhost:8000/api/v1/attendance/aayu-bank-pvt-ltd/breakout-penalty-settings/`
    * Image: `dhub.aayulogic.io/hris-2985`
    * Nested Fields: `break_out_penalty_settings` and `rules`
    """
    filter_backends = (
        SearchFilter, OrderingFilterMap, DjangoFilterBackend
    )
    queryset = BreakOutPenaltySetting.objects.all()
    serializer_class = BreakOutPenaltySettingSerializer
    permission_classes = [
        permission_factory.build_permission(
            "BreakOutPenaltyPermission",
            allowed_to=[
                ATTENDANCE_BREAK_OUT_PENALTY_SETTING_PERMISSION
            ]
        )
    ]
    search_fields = 'title',
    ordering_map = {
        'title': 'title',
    }
    filter_fields = 'is_archived',


class BreakoutPenaltyUserView(OrganizationMixin, ListViewSetMixin):
    serializer_class = TimeSheetUserPenaltyGroupByUserSerializer

    permission_to_check = ATTENDANCE_BREAK_OUT_PENALTY_PERMISSION

    filter_backends = (
        FilterMapBackend,
        OrderingFilterMap,
    )

    filter_map = {
        'user': 'id',
    }

    def get_queryset(self):
        status = self.request.query_params.get('status')
        status_fil = dict()
        user_fil = dict()
        if status in ('Generated', 'Confirmed', 'Cancelled'):
            status_fil.update({'status': status})
        if self.mode == 'user':
            user_fil.update({'id': self.request.user.id})
        if self.mode == 'supervisor':
            user_fil.update({'id__in': find_immediate_subordinates(self.request.user.id)})

        organization = self.get_organization()
        timesheet_penalty = TimeSheetUserPenalty.objects.filter(
            user=OuterRef('id'),
            fiscal_month=self.get_fiscal_month(),
            **status_fil
        ).values('user').order_by().annotate(
            loss_accumulated=Sum('loss_accumulated'),
            lost_days_count=Sum('lost_days_count'),
            penalty_accumulated=Sum('penalty_accumulated'),
        )
        qs = get_user_model().objects.filter(
                detail__organization=organization,
                **user_fil
            ).annotate(
                total_loss_accumulated=Subquery(
                    timesheet_penalty.values('loss_accumulated'),
                    output_field=DurationField()
                )
            ).annotate(
                total_lost_days_count=Subquery(
                    timesheet_penalty.values('lost_days_count'),
                    output_field=FloatField()
                )
            ).annotate(
                total_penalty_accumulated=Subquery(
                    timesheet_penalty.values('penalty_accumulated'),
                    output_field=FloatField()
                )
            ).filter(Q(total_loss_accumulated__gt=Value(timedelta(0)))
                     | Q(total_lost_days_count__gt=0)
                     | Q(total_penalty_accumulated__gt=0)
                     )
        return qs

    def get_fiscal_month(self):
        fiscal_month = self.request.query_params.get('fiscal_month', None)
        return fiscal_month if fiscal_month else None

    def list(self, request, *args, **kwargs):
        ret = super().list(request, *args, **kwargs)
        ret.data.update({
            'statistics': self.statistics
        })
        return ret

    @property
    def mode(self):
        mode = self.request.query_params.get('as')
        if mode in ['supervisor', 'hr']:
            return mode
        return 'user'

    @property
    def statistics(self):
        user_fil = dict()
        if self.mode == 'user':
            user_fil.update({'user': self.request.user.id})
        if self.mode == 'supervisor':
            user_fil.update({'user__in': find_immediate_subordinates(self.request.user.id)})
        stat = TimeSheetUserPenalty.objects.filter(
            fiscal_month=self.get_fiscal_month(),
            **user_fil
            ).aggregate(
                all=Count('user_id', distinct=True),
                generated=Count('user_id', filter=(Q(status='Generated')), distinct=True),
                confirmed=Count('user_id', filter=(Q(status='Confirmed')), distinct=True),
                cancelled=Count('user_id', filter=(Q(status='Cancelled')), distinct=True)
            )
        return stat


class BreakoutPenaltyView(
    GetStatisticsMixin,
    OrganizationMixin,
    ModeFilterQuerysetMixin,
    ListRetrieveUpdateDestroyViewSetMixin,
    BackgroundExcelExportMixin
):
    queryset = TimeSheetUserPenalty.objects.all()
    serializer_class = TimeSheetUserPenaltySerializer
    permission_to_check = ATTENDANCE_BREAK_OUT_PENALTY_PERMISSION
    filter_backends = (
        FilterMapBackend,
        OrderingFilterMap,
    )
    filter_map = {
        'user': 'user',
        'fiscal_month': 'fiscal_month',
        'status': 'status'
    }
    ordering_fields_map = {
        'loss_accumulated': 'loss_accumulated',
        'penalty_accumulated': 'penalty_accumulated',
        'user': (
            'user__first_name', 'user__middle_name', 'user__last_name'
        )
    }
    user_definition = 'user'
    statistics_field = 'status'

    def get_queryset(self):
        return super().get_queryset().filter(
            user__detail__organization=self.get_organization()
        ).select_related(
            'user',
            'user__detail',
            'user__detail__employment_level',
            'user__detail__job_title',
            'user__detail__organization',
            'user__detail__division',
            'fiscal_month',
            'fiscal_month__fiscal_year',
            'rule',
            'rule__penalty_setting'
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['organization'] = self.get_organization()
        return ctx

    # New Bulk Action created
    # @action(
    #     methods=['POST'],
    #     detail=True,
    #     serializer_class=BreakOutPenaltyActionSerializer,
    #     url_path=r'(?P<action_performed>(confirm|cancel))',
    # )
    # def perform_action(self, *args, **kwargs):
    #     obj = self.get_object()
    #     if not validate_permissions(
    #         self.request.user.get_hrs_permissions(self.organization),
    #         self.permission_to_check
    #     ):
    #         raise PermissionDenied
    #     action_performed = self.get_action_performed()
    #     serializer = self.serializer_class(
    #         data=self.request.data,
    #         instance=obj,
    #         context={'status': action_performed}
    #     )
    #     serializer.is_valid(raise_exception=True)
    #     serializer.update(obj, serializer.validated_data)
    #     # remarks = serializer.validated_data.get('remarks')
    #     # ser = TimeSheetUserPenaltySerializer(
    #     #     instance=obj,
    #     #     data={},
    #     #     context={
    #     #         **self.get_serializer_context(),
    #     #         'status': 'verified',
    #     #         'remarks': remarks
    #     #     }
    #     # )
    #     return Response(serializer.data)

    @action(
        methods=['POST'],
        detail=False,
        serializer_class=BreakOutPenaltyBulkActionSerializer,
        url_path='bulk-status-update'
    )
    def perform_bulk_action(self, *args, **kwargs):
        if not validate_permissions(
            self.request.user.get_hrs_permissions(self.organization),
            self.permission_to_check
        ):
            raise PermissionDenied

        organization = self.get_organization()
        hrs = get_users_list_from_permissions(
            [self.permission_to_check], organization=organization
        )
        
        serializer = BreakOutPenaltyBulkActionSerializer(
            data=self.request.data,
            many=True,
            context={**self.get_serializer_context(), 'hrs': hrs}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"message": "Successfully Applied actions"})

    @action(
        methods=['POST'],
        detail=False,
        url_path='generate',
        serializer_class=FiscalMonthSelectionSerializer
    )
    def generate_report(self, *args, **kwargs):
        ser = FiscalMonthSelectionSerializer(
            data=self.request.data,
            context=self.get_serializer_context(),
        )
        ser.is_valid(raise_exception=True)
        async_task(
            generate_penalty_report,
            self.get_organization(),
            ser.validated_data.get('fiscal_month')
        )
        return Response({
            "message": "The timesheet Penalty report is being generated."
        }, status=201)

    def get_action_performed(self):
        return {
            'confirm': CONFIRMED,
            'cancel': CANCELLED,
        }.get(self.kwargs.get('action_performed'))

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data['counts'] = self.statistics
        return response

    @property
    def mode(self):
        mode = self.request.query_params.get('as')
        if mode in ['supervisor', 'hr']:
            return mode
        return 'user'

    export_fields = {
        'S.N': '#SN',
        'User': 'user',
        'Rule': 'rule',
        'Start Date': 'start_date',
        'End Date': 'end_date',
        'Fiscal Month': 'fiscal_month.display_name',
        'Loss Accumulated': 'loss_accumulated',
        'Lost Days Count': 'lost_days_count',
        'Penalty Accumulated': 'penalty_accumulated',
        'Status': 'status',
        'Remarks': 'remarks'
    }

    export_type = "Penalty Report"

    def get_extra_export_data(self):
        extra_data = super().get_extra_export_data()
        fiscal_month = self.request.query_params.get('fiscal_month')
        user = self.request.query_params.get('user')
        status = self.request.query_params.get('status')
        status_fil = {}
        user_fil = {}
        if status in ('Generated', 'Confirmed', 'Cancelled'):
            status_fil.update({'status': status})
        if self.mode == 'user':
            user_fil.update({'user': self.request.user.id})
        elif user != '':
            user_fil.update({'user': user})
        if self.mode == 'supervisor':
            user_fil.update({'user__in': find_immediate_subordinates(self.request.user.id)})
        penalty_report = self.get_queryset().filter(
            fiscal_month=fiscal_month, **status_fil, **user_fil
        )
        extra_data.update({
            'penalty_report': penalty_report,
        })
        return extra_data

    @classmethod
    def get_exported_file_content(cls, data, title, columns, extra_content,
                                  description=None, **kwargs):
        penalty_report = extra_content.get('penalty_report')
        return super().get_exported_file_content(
            penalty_report, title, columns, extra_content, description=description, **kwargs
        )
