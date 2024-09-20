import types

import openpyxl as openpyxl
from django.core.files.base import ContentFile
from django.db.models import Count, Q, Sum, Prefetch, Exists, OuterRef, Subquery, F, \
    ExpressionWrapper, DurationField
from django.db.models.functions import Coalesce
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from openpyxl.cell import Cell
from openpyxl.styles import Font
from openpyxl.writer.excel import save_virtual_workbook
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from irhrs.attendance.api.v1.permissions import (
    OvertimeClaimPermission, AttendanceOvertimeSettingPermission
)
from irhrs.attendance.constants import REQUESTED, FORWARDED, APPROVED, DECLINED, \
    UNCLAIMED, CONFIRMED, STATUS_CHOICES, WORKDAY
from irhrs.attendance.models.overtime import OvertimeEntryDetailHistory
from irhrs.attendance.utils.attendance import humanize_interval
from irhrs.core.mixins.file_import_mixin import BackgroundFileImportMixin
from irhrs.core.mixins.serializers import DummySerializer
from irhrs.core.mixins.viewset_mixins import (
    OrganizationMixin, ListRetrieveUpdateViewSetMixin,
    ListRetrieveViewSetMixin, RetrieveUpdateViewSetMixin,
    CreateViewSetMixin, HRSOrderingFilter,
    PastUserGenericFilterMixin, ListViewSetMixin, UserMixin
)
from irhrs.core.utils import nested_getattr
from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.core.utils.subordinates import set_supervisor_permissions, find_immediate_subordinates
from irhrs.export.mixins.export import BackgroundExcelExportMixin
from irhrs.export.utils.export import ExcelExport
from irhrs.permission.constants.permissions import (
    ATTENDANCE_PERMISSION, ATTENDANCE_OVERTIME_CLAIM_PERMISSION,
    HAS_PERMISSION_FROM_METHOD)
from irhrs.permission.permission_classes import permission_factory
from irhrs.users.models import UserSupervisor
from ..reports.views.individual_attendance_report import OvertimeDetailExportSerializer, \
    OvertimeDetailExportMetaDataSerializer
from ..serializers.overtime import (
    OvertimeSettingSerializer, OvertimeClaimSerializer,
    OvertimeClaimHistorySerializer, OvertimeEntryDetailSerializer,
    OvertimeClaimBulkSerializer,
    OvertimeClaimEditHistorySerializer, BulkOvertimeUnExpireSerializer,
    OvertimeActionsPerformedSerializer, OverTimeClaimActionSerializer, OvertimeEntryImportSerializer)
from ....models import OvertimeSetting, OvertimeClaim, OvertimeClaimHistory, \
    IndividualAttendanceSetting


class OvertimeSettingViewSet(OrganizationMixin, ModelViewSet):
    """
    create:

    ## Creates an overtime setting with the following fields.

    ## Data:

    ```javascript
    {
        "name": "Regular Overtime",
        "daily_overtime_limit": 600, //  minutes
        "off_day_overtime": true, //  allow overtime other than work days.
        "off_day_overtime_limit": 600, //  minutes
        "applicable_before": 15, // overtime begins after ? minutes of punchIn.
        "applicable_after": 15, // overtime begins after ? minutes of punchOut.
        "overtime_calculation": (Daily, Weekly), // how frequently generated?
        "paid_holiday_affect_overtime": false, // grant OT if sheet is holiday.
        "leave_affect_overtime": false // grant OT if sheet is leave.
        "rates": [ // the rates of overtime.
            "overtime_after": 6, // hours
            "rate": 2.5,
            "is_off_day": false // off day rate or work day rate.
        ]
    }
    ```

    list:

    ## lists all the overtime settings as a paginated response.

    ## Data:

    ```javascript
    {
        "count": 2,
        "next": null,
        "previous": null,
        "results": [
            {
                "organization": {
                    "name": "facebook",
                    "slug": "facebook"
                },
                "name": "setting",
                "daily_overtime_limit": 1200,
                "off_day_overtime": true,
                "off_day_overtime_limit": 1200,
                "applicable_before": 5,
                "applicable_after": 5,
                "overtime_calculation": 1,
                "paid_holiday_affect_overtime": true,
                "leave_affect_overtime": true,
                "rates": [
                    {
                        "overtime_after": 3,
                        "rate": 1.5,
                        "is_off_day": true,
                        "applicable_from": "2018-12-11",
                        "applicable_to": null
                    }
                ],
                "slug": "setting-2"
            },
            {
                "organization": {
                    "name": "facebook",
                    "slug": "facebook"
                },
                "name": "setting",
                "daily_overtime_limit": 1200,
                "off_day_overtime": true,
                "off_day_overtime_limit": 1200,
                "applicable_before": 5,
                "applicable_after": 5,
                "overtime_calculation": 1,
                "paid_holiday_affect_overtime": true,
                "leave_affect_overtime": true,
                "rates": [
                    {
                        "overtime_after": 3,
                        "rate": 1.5,
                        "is_off_day": true,
                        "applicable_from": "2018-12-11",
                        "applicable_to": null
                    }
                ],
                "slug": "setting"
            }
        ]
    }
    ```
    retrieve:

    ## retrieves an overtime setting with the following data.
    ### Data:

    ```javascript
    {
        "organization": {
            "name": "facebook",
            "slug": "facebook"
        },
        "name": "setting",
        "daily_overtime_limit": 1200,
        "off_day_overtime": true,
        "off_day_overtime_limit": 1200,
        "applicable_before": 5,
        "applicable_after": 5,
        "overtime_calculation": 1,
        "paid_holiday_affect_overtime": true,
        "leave_affect_overtime": true,
        "rates": [
            {
                "overtime_after": 3,
                "rate": 1.5,
                "is_off_day": true,
                "applicable_from": "2018-12-11",
                "applicable_to": null
            }
        ],
        "slug": "setting"
    }

    ```
    update:

    ## updates an overtime setting with the parameters defined in `create`.

    """
    serializer_class = OvertimeSettingSerializer
    queryset = OvertimeSetting.objects.all()
    lookup_field = 'slug'
    http_method_names = [
        'get', 'post', 'put', 'delete', 'head', 'options', 'trace'
    ]
    filter_backends = (
        filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend
    )
    search_fields = (
        'name',
    )
    ordering_fields = (
        'name', 'applicable_before', 'applicable_after'
    )
    filter_fields = (
        'is_archived',
    )
    permission_classes = [AttendanceOvertimeSettingPermission]

    def get_queryset(self):
        return self.queryset.filter(organization=self.get_organization())

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({
            'organization': self.get_organization()
        })
        return context

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # allow delete if the overtime setting is not assigned to anyone.
        editable = instance.editable
        if not editable:
            return Response(
                data={
                    "message":
                        "Cannot delete Overtime Setting as it has been used."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        # allow delete if the overtime setting is not assigned to anyone.
        editable = instance.editable
        if not editable:
            return Response(
                data={
                    "message":
                        "Cannot update Overtime Setting as it has been used."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().update(request, *args, **kwargs)


class OvertimeClaimViewSet(
    BackgroundFileImportMixin,
    PastUserGenericFilterMixin,
    HRSOrderingFilter,
    OrganizationMixin,
    ListRetrieveUpdateViewSetMixin
):
    queryset = OvertimeClaim.objects.filter()
    user_definition = 'overtime_entry__user'
    serializer_class = OvertimeClaimSerializer
    search_fields = (
        'overtime_entry__user__first_name',
        'overtime_entry__user__middle_name',
        'overtime_entry__user__last_name',
        'overtime_entry__user__username'
    )
    filter_backends = (
        filters.SearchFilter, filters.OrderingFilter, FilterMapBackend
    )
    permission_classes = [permission_factory.build_permission(
        "AttendanceReportPermission",
        limit_write_to=[HAS_PERMISSION_FROM_METHOD],
        actions={
            'import_file': [
                ATTENDANCE_PERMISSION, ATTENDANCE_OVERTIME_CLAIM_PERMISSION,
            ],
            'import_file_status': [
                ATTENDANCE_PERMISSION, ATTENDANCE_OVERTIME_CLAIM_PERMISSION,
            ],
        },
    )]
    filter_map = {
        'start_date': 'overtime_entry__timesheet__timesheet_for__gte',
        'end_date': 'overtime_entry__timesheet__timesheet_for__lte',
        'branch': 'overtime_entry__user__detail__branch__slug',
        'division': 'overtime_entry__user__detail__division__slug',
    }
    ordering_fields_map = {
        'date': 'overtime_entry__timesheet__timesheet_for',
        'claimed_overtime': 'overtime_entry__overtime_detail__claimed_overtime',
        'name': 'overtime_entry__user__first_name',
    }

    # Import Fields Start
    import_serializer_class = OvertimeEntryImportSerializer
    import_fields = [
        'user',
        'date',
        'punch_in_overtime',
        'punch_out_overtime',
        'description',
    ]
    values = [
        'someone@example.com',
        '2020-02-02',
        '00:00:00',
        '00:00:00',
        'Require OT'
    ]
    background_task_name = 'overtime'
    sample_file_name = 'overtime'
    non_mandatory_field_value = {}
    permissions_description_for_notification = [
        ATTENDANCE_PERMISSION, ATTENDANCE_OVERTIME_CLAIM_PERMISSION,
    ]

    def get_success_url(self):
        success_url = f'/admin/{self.organization.slug}/attendance/requests/overtime-claim'
        return success_url

    def get_failed_url(self):
        failed_url = f'/admin/{self.organization.slug}/attendance/import/overtime-claim?status=failed'
        return failed_url

    # /Import Fields End

    @property
    def mode(self):
        mode = self.request.query_params.get('as')
        if mode in ['supervisor', 'hr']:
            return mode
        return 'user'

    def check_permissions(self, request):
        if self.mode == "hr" and request.user and request.user.is_authenticated:
            is_hr = validate_permissions(
                self.request.user.get_hrs_permissions(self.get_organization()),
                ATTENDANCE_PERMISSION, ATTENDANCE_OVERTIME_CLAIM_PERMISSION,
            )
            # If not is_hr and mode is hr raise permission denied directly
            if not is_hr:
                raise PermissionDenied
        super().check_permissions(request)

    def has_user_permission(self):
        if self.mode == "hr":
            is_hr = validate_permissions(
                self.request.user.get_hrs_permissions(self.get_organization()),
                ATTENDANCE_PERMISSION, ATTENDANCE_OVERTIME_CLAIM_PERMISSION,
            )
            # If not is_hr and mode is hr raise permission denied directly
            if not is_hr:
                return False

        if self.action in ['unexpire', 'import']:
            return self.mode == 'hr'

        if self.request.method.upper() in ['PUT', 'PATCH']:
            return self.mode in ['hr', 'supervisor']

        return True

    def get_queryset(self):
        select_related = [
            'overtime_entry',
            'overtime_entry__overtime_detail',
            'overtime_entry__timesheet',
            'overtime_entry__timesheet__work_time',
            'overtime_entry__timesheet__work_shift',
            'overtime_entry__overtime_settings',
            'overtime_entry__user',
            'overtime_entry__user__detail',
            'overtime_entry__user__detail__organization',
            'overtime_entry__user__detail__division',
            'overtime_entry__user__detail__employment_status',
            'overtime_entry__user__detail__employment_level',
            'overtime_entry__user__detail__job_title',
        ]
        qs = super().get_queryset().annotate(
            edited=Exists(
                OvertimeEntryDetailHistory.objects.filter(
                    detail=OuterRef('overtime_entry__overtime_detail')
                ).only('id')
            )
        ).select_related(
            *select_related
        ).prefetch_related(
            Prefetch('overtime_entry__user__supervisors',
                     queryset=UserSupervisor.objects.filter(
                         authority_order=1
                     )
                     .select_related('supervisor',
                                     'supervisor__detail',
                                     'supervisor__detail__organization',
                                     'supervisor__detail__job_title',
                                     'supervisor__detail__division',
                                     'supervisor__detail__employment_level'),
                     to_attr='user_supervisors')
        )

        qs = qs.filter(
            overtime_entry__user__detail__organization=self.organization
        )

        if self.mode == 'hr':
            archived = self.request.query_params.get('expired')
            if archived and archived.lower() == 'true':
                return qs.filter(is_archived=True)
            return qs.filter(is_archived=False)
        # except for ATTENDANCE_PERMISSION, hide archived
        qs = qs.filter(is_archived=False)
        if self.mode == 'supervisor':
           # 'Unclaimed' status has ot entry user as recipient
            # so in order to act an action on behalf of subordinate we need immediate subordinate
            if self.request.query_params.get('status') == UNCLAIMED:
                immediate_subordinates_id = find_immediate_subordinates(self.request.user.id)
                immediate_subordinates_qs = qs.filter(
                    Q(overtime_entry__user__in=immediate_subordinates_id) 
                    | Q(recipient=self.request.user)).exclude(overtime_entry__user=self.request.user)
                if not immediate_subordinates_qs.exists():
                    qs = qs.filter(recipient=self.request.user).exclude(overtime_entry__user=self.request.user)
                else:
                    qs = immediate_subordinates_qs
            else:
                qs = qs.filter(recipient=self.request.user)
        else:
            qs = qs.filter(overtime_entry__user=self.request.user)
        return qs

    def filter_queryset(self, queryset):
        claimed_date = OvertimeClaimHistory.objects.filter(
            action_performed=REQUESTED,
            overtime=OuterRef('pk')
        ).order_by(
            'created_at'
        ).values('created_at')[:1]
        queryset = queryset.annotate(
            # update after pre-approval. There are high chances,
            # OT Claim was never requested.
            claimed_on=Coalesce(
                Subquery(claimed_date),
                F('created_at')
            )
        )
        return super().filter_queryset(queryset)

    def get_status_count(self, queryset):
        # additional filter applied for supervisor in order to resolve the count discrepency
        # when status is 'Unclaimed', then the qs filter will be for the 1st level subordinate
        # instead of recipient=self.request.user
        if self.mode == 'supervisor':
            queryset = queryset.filter(recipient=self.request.user).exclude(
                overtime_entry__user=self.request.user)
        counts = queryset.aggregate(
            Requested=Count('id', filter=Q(status=REQUESTED)),
            Forwarded=Count('id', filter=Q(status=FORWARDED)),
            Approved=Count('id', filter=Q(status=APPROVED)),
            Declined=Count('id', filter=Q(status=DECLINED)),
            Confirmed=Count('id', filter=Q(status=CONFIRMED)),
            Expired=Count('id', filter=Q(is_archived=True)),
            **({'Unclaimed': Count('id', filter=Q(status=UNCLAIMED))}
               if self.mode != 'supervisor' else
               {}),
        )
        # 'Unclaimed' status count removed from 'All' status
        # because logic behind the other status depends on recipient
        # but 'Unclaimed' status has ot entry user as recipient
        counts['All'] =  sum(counts.values()) - counts.get('Unclaimed', 0)
        if self.mode == 'supervisor':
            immediate_subordinates_id = find_immediate_subordinates(self.request.user.id)
            unclaimed_qs = OvertimeClaim.objects.filter(
                overtime_entry__user__in=immediate_subordinates_id,
                is_archived=False,
                status=UNCLAIMED,
                overtime_entry__user__detail__organization=self.organization,
            )
            unclaimed_count = self.filter_queryset(unclaimed_qs).count()
            counts['Unclaimed'] = unclaimed_count
        return counts

    def paginate_queryset(self, queryset):
        page = super().paginate_queryset(queryset)
        if self.action == 'list' and self.mode == 'supervisor':
            return set_supervisor_permissions(page, self.request.user.id, 'overtime_entry.user')
        return page

    def list(self, request, *args, **kwargs):
        # produce stats count without stats filter
        qs = self.filter_queryset(
            self.get_queryset()
        )
        stats = self.get_status_count(qs)
        status_ = self.request.query_params.getlist('status')
        if status_ and "" not in status_:
            queryset = qs.filter(status__in=status_)
        else:
            queryset = qs.exclude(status=UNCLAIMED)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            resp = self.get_paginated_response(serializer.data).data
        else:
            resp = dict()
        all_status_aggregator = {
            **{
                f'{value}_minutes'.lower(): Sum(
                    'overtime_entry__overtime_detail__claimed_overtime',
                    filter=Q(status=value)
                ) for value, _ in STATUS_CHOICES
            },
            **{
                f'{value}_normalized_minutes'.lower(): Sum(
                    'overtime_entry__overtime_detail__normalized_overtime',
                    filter=Q(status=value)
                ) for value, _ in STATUS_CHOICES
            },
        }
        aggregates = qs.aggregate(
            **all_status_aggregator,
        )
        humanized_aggregates = {
            i: humanize_interval(j) for i, j in aggregates.items()}
        resp.update({
            'counts': stats,
            **humanized_aggregates
        })
        return Response(resp)

    @action(methods=['GET'], detail=True)
    def normalization(self, *args, **kwargs):
        """
        Return the computation steps for normalization of overtime.
        The steps below are re-computed because the steps have not been stored.
        :param args:
        :param kwargs:
        :return:
        """
        overtime = self.get_object()
        overtime_detail = overtime.overtime_entry.overtime_detail
        return Response(
            overtime_detail.get_normalized_overtime_seconds(trail=True)
        )

    @action(methods=['POST'], detail=False)
    def unexpire(self, request, *args, **kwargs):
        serializer = BulkOvertimeUnExpireSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(methods=['GET'], detail=False)
    def performed(self, request, *args, **kwargs):
        status = request.query_params.get('status')
        queryset = OvertimeClaimHistory.objects.filter(
            action_performed_by=request.user,
        ).exclude(
            adjustment__overtime_entry__user=request.user
        )
        if status:
            queryset = queryset.filter(
                action_performed=status
            )
        page = self.paginate_queryset(queryset.select_related('adjustment'))
        if page is not None:
            serializer = OvertimeActionsPerformedSerializer(
                instance=queryset,
                many=True,
            )
            resp = self.get_paginated_response(serializer.data).data
        else:
            resp = {}
        return Response(resp)

    @action(methods=['GET'], detail=False)
    def summary(self, request, *args, **kwargs):
        """
        Summary information of all the subordinates' status counts.
        Could not use self.queryset() as it is designed to filter claims
        based on the recipient.
        :return:
        """
        queryset = self.queryset
        c_user = self.request.user
        if self.mode == 'supervisor':
            queryset = queryset.filter(
                overtime_entry__user_id__in=c_user.subordinates_pks,
                overtime_entry__user__detail__organization_id=self.organization.id
            )
        elif self.mode == 'hr':
            queryset = queryset.filter(
                overtime_entry__user__detail__organization_id=
                self.organization.id
            )
        else:
            queryset = queryset.none()
        aggregates = queryset.aggregate(
            **{
                display: Count(
                    'id',
                    filter=Q(status=value)
                )
                for display, value in STATUS_CHOICES
            }
        )
        return Response(aggregates)

    @action(methods=['POST'], detail=False, url_name='bulk-action',
            url_path='bulk-action', serializer_class=DummySerializer)
    def bulk_action(self, request, *args, **kwargs):
        """
        BULK ACTION

        POST DATA -->

            [{
                "overtime_claim": overtime_claim_id,
                "action": "approve",
                "remark": "Approved"
            },...]

        `action` can be one of "approve", "confirm", "deny" or "forward"
        """
        ctx = self.get_serializer_context()
        ctx["overtime_claims"] = self.get_queryset()
        ser = OverTimeClaimActionSerializer(
            data=request.data, many=True, context=ctx
        )
        ser.is_valid(raise_exception=True)
        ser.save()

        return Response({"message": _("Successfully Applied actions")})


class OvertimeClaimBulkUpdateViewSet(CreateViewSetMixin):
    serializer_class = OvertimeClaimBulkSerializer


class OvertimeClaimHistoryViewSet(OrganizationMixin, ListRetrieveViewSetMixin):
    """
    list:

    ## Lists all the instances of OvertimeClaimHistory with limited fields.
    ```javascript
    [
        {

        },
        {

        }
    ]
    ```
    retrieve:

    ## Displays an instance of OvertimeClaimHistory with all fields.

    ```javascript
    {

    }
    ```

    """
    queryset = OvertimeClaimHistory.objects.all()
    serializer_class = OvertimeClaimHistorySerializer
    filter_fields = ()
    search_fields = ()
    filter_backends = (filters.SearchFilter, filters.OrderingFilter,
                       DjangoFilterBackend)
    permission_classes = [OvertimeClaimPermission]

    def has_user_permission(self):
        accessing_user = self.request.user
        try:
            overtime_claim = get_object_or_404(
                OvertimeClaim, pk=self.kwargs.get('ot_claim_id')
            )
        except (TypeError, ValueError):
            raise Http404
        if self.request.method.upper() == 'GET':
            # there will be ot claim obj or will be 404.
            related_user = nested_getattr(
                overtime_claim,
                'overtime_entry.user'
            )
            if related_user:
                # check for self.
                is_self = related_user == accessing_user
                is_subordinate = related_user.id in accessing_user.subordinates_pks
                return is_self or is_subordinate
        return False

    def get_queryset(self):
        overtime = self.overtime
        return super().get_queryset().filter(
            overtime=overtime
        ).select_related(
            'action_performed_by__detail',
            'action_performed_by__detail__organization',
            'action_performed_by__detail__division',
            'action_performed_by__detail__job_title',
            'action_performed_by__detail__employment_status',
            'action_performed_by__detail__employment_level',
            'action_performed_to__detail',
            'action_performed_to__detail__organization',
            'action_performed_to__detail__division',
            'action_performed_to__detail__job_title',
            'action_performed_to__detail__employment_status',
            'action_performed_to__detail__employment_level',
        )

    @property
    def overtime(self):
        ot_claim_id = self.kwargs.get('ot_claim_id')
        return get_object_or_404(OvertimeClaim, pk=ot_claim_id)

    @action(methods=['GET'], detail=False)
    def edits(self, request, *args, **kwargs):
        self.serializer_class = OvertimeClaimEditHistorySerializer

        def get_queryset(self):
            claim = self.overtime
            histories = claim.overtime_entry.overtime_detail.histories.all(
            ).select_related(
                'actor',
                'actor__detail',
                'actor__detail__employment_level',
                'actor__detail__job_title',
                'actor__detail__organization',
                'actor__detail__division'
            )
            return histories

        self.get_queryset = types.MethodType(get_queryset, self)

        return super().list(request, *args, **kwargs)


class OvertimeClaimEditViewSet(OrganizationMixin, RetrieveUpdateViewSetMixin):
    queryset = OvertimeClaim.objects.all()
    serializer_class = OvertimeEntryDetailSerializer
    permission_classes = [OvertimeClaimPermission]

    def get_queryset(self):
        return self.queryset.filter(
            overtime_entry__user__detail__organization=self.get_organization()
        )

    def get_object(self):
        qs = self.filter_queryset(
            self.get_queryset()
        )
        try:
            obj = get_object_or_404(qs, pk=self.kwargs.get('claim'))
        except (TypeError, ValueError):
            raise Http404
        return obj.overtime_entry.overtime_detail
    
    @property
    def mode(self):
        mode = self.request.query_params.get('as')
        if mode in ['supervisor', 'hr']:
            return mode
        return 'user'

    def has_user_permission(self):
        user = self.request.user
        subordinates = find_immediate_subordinates(user.id)
        try:
            ot_claim = get_object_or_404(
                OvertimeClaim, pk=self.kwargs.get('claim')
            )
        except (TypeError, ValueError):
            raise Http404
        ot_user = ot_claim.overtime_entry.user
        if self.mode == 'user' and user == ot_user:
            return True
        if self.mode =='supervisor' and ot_user.id in subordinates:
            return True
        return  validate_permissions(
                user.get_hrs_permissions(self.get_organization()),
                ATTENDANCE_PERMISSION, ATTENDANCE_OVERTIME_CLAIM_PERMISSION,
            )


class IndividualOvertimeExportView(BackgroundExcelExportMixin, OrganizationMixin, UserMixin,
                                   ListViewSetMixin):
    export_type = 'Consolidated Overtime Report'
    export_fields = (
        "Requested Date",
        "Claim Date",
        "Shift Hours",
        "Punch In Overtime",
        "Punch Out Overtime",
        "Offday / Holiday Overtime",
        "Day",
        "Actual Overtime",
        "Confirmed Overtime",
        "Reason for Overtime",
        "Action By[1st Level]",
        "Action By[2nd Level]",
        "Action By[3rd Level]",
        "Confirmed By",
        "Confirmed Date",
    )

    permission_classes = [permission_factory.build_permission(
        'OvertimeExportPermission',
        allowed_to=[ATTENDANCE_PERMISSION, ATTENDANCE_OVERTIME_CLAIM_PERMISSION]
    )]
    filter_backends = [OrderingFilterMap, DjangoFilterBackend, FilterMapBackend]
    filter_map = {
        'start_date': 'overtime_entry__timesheet__timesheet_for__gte',
        'end_date': 'overtime_entry__timesheet__timesheet_for__lte',
    }
    ordering_map = {
        'date': 'overtime_entry__timesheet__timesheet_for',
    }
    serializer_class = OvertimeDetailExportSerializer
    queryset = OvertimeClaim.objects.filter(
        status__in=[APPROVED, CONFIRMED]
    )

    def get_queryset(self):
        qs = super().get_queryset().filter(
            overtime_entry__user=self.user
        )
        return qs

    @staticmethod
    def get_aggregates(queryset):
        return queryset.annotate(
            _worked_hours=ExpressionWrapper(
                F('overtime_entry__timesheet__punch_out') - F(
                    'overtime_entry__timesheet__punch_in'
                ), output_field=DurationField()
            )
        ).aggregate(
            worked_hours=Sum('_worked_hours'),
            punch_in_overtime=Sum(
                'overtime_entry__overtime_detail__punch_in_overtime',
                filter=Q(overtime_entry__timesheet__coefficient=WORKDAY)
            ),
            punch_out_overtime=Sum(
                'overtime_entry__overtime_detail__punch_out_overtime',
                filter=Q(overtime_entry__timesheet__coefficient=WORKDAY)
            ),
            actual=Sum(
                F('overtime_entry__overtime_detail__punch_in_overtime')
                + F('overtime_entry__overtime_detail__punch_out_overtime')
            ),
            offday_overtime=Sum(
                'overtime_entry__overtime_detail__punch_in_overtime',
                filter=~Q(overtime_entry__timesheet__coefficient=WORKDAY)
            ),
            claimed=Sum('overtime_entry__overtime_detail__claimed_overtime'),
            confirmed=Sum('overtime_entry__overtime_detail__claimed_overtime'),
        )

    def get_extra_export_data(self):
        return dict(
            user=self.user,
            organization=self.organization,
        )

    @classmethod
    def get_exported_file_content(cls, data, title, columns, extra_content, description=None,
                                  **kwargs):
        wb = openpyxl.Workbook()
        ws = wb.active

        ws.title = 'Consolidated Overtime Report - %s' % extra_content.get('user').full_name
        lines_used = ExcelExport.insert_org_info(ws, extra_content.get('organization'))

        # insert a blank line
        ws.append([])

        metadata = OvertimeDetailExportMetaDataSerializer(instance=extra_content.get('user')).data

        header_col, value_col = [], []
        for field in OvertimeDetailExportMetaDataSerializer.Meta.fields:
            header_col.append(
                OvertimeDetailExportMetaDataSerializer.Meta.fields_map.get(field)
            )
            value_col.append(metadata.get(field))

        ws.append(header_col)
        ws.append(value_col)
        ws.append([])

        ws.append(
            [
                OvertimeDetailExportSerializer.fields_map.get(field) for field in
                OvertimeDetailExportSerializer.fields_list
             ]
        )

        # Extra blank row after table heading not required.
        # ws.append([])

        for row in OvertimeDetailExportSerializer(
            instance=data, many=True
        ).data:
            container = []
            for field in OvertimeDetailExportSerializer.fields_list:
                container.append(
                    Cell(
                        worksheet=ws,
                        value=row.get(field),
                    )
                )
            ws.append(container)

        ws.append([])

        aggregates = cls.get_aggregates(data)
        footer = [
            '' if aggregates.get(field, ...) is ... else humanize_interval(aggregates.get(field))
            for field in OvertimeDetailExportSerializer.fields_list
        ]

        ws.append(['Total', *footer[1:]])

        # fixing fonts
        def bold_font(row_no):
            for cell in ws[row_no]:
                cell.font = Font(bold=True)
        bold_font(lines_used + 2)
        bold_font(lines_used + 5)
        bold_font(lines_used + 5 + data.count() + 2)
        return ContentFile(save_virtual_workbook(wb))

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            ret = self.get_paginated_response(serializer.data)
            ret.data.update({
                'aggregates': self.get_aggregates(queryset),
                'metadata': OvertimeDetailExportMetaDataSerializer(instance=self.user).data
            })
            return ret

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
