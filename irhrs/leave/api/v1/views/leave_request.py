# Django imports

from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Exists, OuterRef
# Rest_framework imports
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

# Project current app imports
from irhrs.core.constants.common import LEAVE_CANCEL_REQUEST_NOTIFICATION
from irhrs.core.mixins.file_import_mixin import BackgroundFileImportMixin
from irhrs.core.mixins.serializers import DummySerializer
from irhrs.core.mixins.viewset_mixins import OrganizationMixin, \
    CreateViewSetMixin, ModeFilterQuerysetMixin, GetStatisticsMixin, \
    ListRetrieveViewSetMixin, OrganizationCommonsMixin
from irhrs.core.utils.common import apply_filters, validate_permissions
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.core.utils.subordinates import set_supervisor_permissions
from irhrs.export.mixins.export import BackgroundExcelExportMixin
from irhrs.leave.api.v1.permissions import \
    LeaveRequestDeletePermission, LeaveRequestDeleteObjectPermission
from irhrs.leave.constants.model_constants import CREDIT_HOUR, REQUESTED, APPROVED, DENIED, \
    FORWARDED, SUPERVISOR, APPROVER, HALF_LEAVE_CHOICES, FULL_DAY, TIME_OFF
from irhrs.leave.models.request import LeaveRequestDeleteHistory
from irhrs.notification.utils import notify_organization, add_notification
from irhrs.permission.constants.permissions import LEAVE_PERMISSION, \
    HAS_OBJECT_PERMISSION, LEAVE_REQUEST_PERMISSION, OFFLINE_LEAVE_PERMISSION, \
    ASSIGN_LEAVE_PERMISSION, HAS_PERMISSION_FROM_METHOD
from irhrs.permission.permission_classes import permission_factory
from irhrs.users.api.v1.serializers.thin_serializers import \
    UserSupervisorDivisionSerializer
from irhrs.users.models import UserSupervisor
from ..serializers.leave_request import LeaveRequestSerializer, \
    AdminLeaveRequestSerializer, LeaveRequestHistorySerializer, \
    LeaveRequestDeleteHistorySerializer, \
    LeaveRequestDeleteStatusHistorySerializer, LeaveRequestActionSerializer, \
    LeaveRequestImportSerializer, LeaveRequestAlternateAccountsSerializer
from ....models import LeaveRequest, LeaveAccount, MasterSetting, LeaveType
from ....utils.leave_request import get_recipient


class LeaveRequestViewSet(
    BackgroundFileImportMixin,
    OrganizationMixin, ModelViewSet,
    BackgroundExcelExportMixin
):
    """
    create:
    ## Creates an instance of LeaveRequest

    list:

    ## Lists all the leave requests from employees.

    ## Available Filters
    * status
    * branch
    * division
    * employee_level
    * start
    * end

    retrieve:

    ## Displays an instance of LeaveRequest with all fields.

    update:

    # Updates an instance of LeaveRequest.
    ### A new field `supervisor_remarks` has been added. This char field
    accepts max of 150 characters. This is required on Denial, and optional
    for other statuses.
    ## Sample PUT request
    ```javascript
    {

    }
    ```

    partial_update:

    Updates  details partially.

    Accepts the same parameters as ```.update()``` but not all fields required.

    """
    export_type = "Leave Request Export"
    export_fields = {
        "Username": "user.username",
        "Employee": "user.full_name",
        "Leave Type": "leave_rule.leave_type.name",
        "Part of Day": "part_of_day",
        "Start Date": "start",
        "End Date": "end",
        "Duration": "balance",
        "Status": "status",
        "User remarks": "details"
    }
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    permission_classes = [permission_factory.build_permission(
        name='Leave Permission',
        allowed_to=[HAS_PERMISSION_FROM_METHOD],
        actions={
            'delete': [HAS_OBJECT_PERMISSION],
            'get_applicable_users': [HAS_PERMISSION_FROM_METHOD],
            'import_file': [
                LEAVE_PERMISSION,
                OFFLINE_LEAVE_PERMISSION
            ],
            'import_file_status': [
                LEAVE_PERMISSION,
                OFFLINE_LEAVE_PERMISSION
            ],
        },
        allowed_user_fields=['user']
    )]
    filter_backends = (
        filters.SearchFilter, FilterMapBackend, filters.OrderingFilter
    )
    search_fields = ('user__first_name', 'user__middle_name', 'user__last_name', 'user__username')
    filter_map = {
        'status': 'status',
        'username': 'leave_account__user__username',
        'branch':
            'user__detail__branch__slug',
        'division':
            'user__detail__division__slug',
        'employment_level':
            'user__detail__employment_level__slug',
        'start_time': 'start',
        'end_time': 'end',
        'recipient': 'recipient',
        'user': 'leave_account__user',
        'leave_type': 'leave_rule__leave_type',
        'start_date': 'end__date__gte',
        'end_date': 'start__date__lte'
    }

    # Import Fields Start
    permissions_description_for_notification = [
        LEAVE_PERMISSION,
        ASSIGN_LEAVE_PERMISSION,
        OFFLINE_LEAVE_PERMISSION
    ]
    import_serializer_class = LeaveRequestImportSerializer
    import_fields = [
        'USER',
        'LEAVE CATEGORY',
        'START DATE',
        'END DATE',
        # Might need this when we add support for credit leave. Not rn!
        # 'START TIME',
        # 'END TIME',
        'PART OF DAY',
        'DESCRIPTION'
    ]
    values = [
        'someone@example.com',
        '',
        '2020-02-22',
        '2020-02-22',
        FULL_DAY,
        'Require Leave'
    ]
    background_task_name = 'leave_requests'
    sample_file_name = 'leave-requests'
    non_mandatory_field_value = {}
    slug_field_for_sample = 'name'

    def get_success_url(self):
        success_url = f'/admin/{self.organization.slug}/leave/employees-request'
        return success_url

    def get_failed_url(self):
        failed_url = f'/admin/{self.organization.slug}/leave/import/leave-request?status=failed'
        return failed_url

    def get_queryset_fields_map(self):
        return {
            'leave_category': self.leave_type_queryset,
            'part_of_day': [val for val, _ in HALF_LEAVE_CHOICES],
        }

    # /Import Fields End

    @property
    def mode(self):
        mode = self.request.query_params.get('as')
        if mode in ['supervisor', 'hr', 'approver']:
            return mode
        return 'user'

    @property
    def leave_type_queryset(self):
        active_master_setting = MasterSetting.objects.filter(
            organization=self.organization
        ).active().first()
        leave_types = LeaveType.objects.filter(
            master_setting=active_master_setting
        )
        return leave_types

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['mode'] = self.mode
        ctx['organization'] = self.organization
        ctx['leave_type_queryset'] = self.leave_type_queryset
        return ctx

    def has_user_permission(self):
        if self.mode == "hr":
            is_hr = validate_permissions(
                self.request.user.get_hrs_permissions(self.get_organization()),
                LEAVE_REQUEST_PERMISSION,
                LEAVE_PERMISSION
            )
            # If not is_hr and mode is hr raise permission denied directly
            if not is_hr:
                return False

        if self.action == 'get_applicable_users':
            if self.mode == "hr":
                is_hr = validate_permissions(
                    self.request.user.get_hrs_permissions(self.get_organization()),
                    LEAVE_PERMISSION,
                    ASSIGN_LEAVE_PERMISSION,
                    OFFLINE_LEAVE_PERMISSION
                )
                if not is_hr:
                    return False

            elif self.mode == "supervisor":
                return True

        if self.action in ['bulk_action']:
            return self.mode in ['hr', 'supervisor', 'approver']

        return True

    def get_queryset(self):
        select_related = [
            'user',
            'user__detail',
            'user__detail__organization',
            'user__detail__division',
            'user__detail__branch',
            'user__detail__employment_status',
            'user__detail__employment_level',
            'user__detail__job_title',
            'created_by',
            'created_by__detail',
            'created_by__detail__organization',
            'created_by__detail__division',
            'created_by__detail__branch',
            'created_by__detail__employment_status',
            'created_by__detail__employment_level',
            'created_by__detail__job_title',
            'leave_account',
            'leave_account__rule__leave_type'
        ]
        qs = super().get_queryset().filter(
            user__detail__organization=self.organization
        )
        if self.mode == 'supervisor':
            qs = qs.filter(
                recipient=self.request.user,
                recipient_type=SUPERVISOR
            )
        elif self.mode == 'approver':
            qs = super().get_queryset().filter(
                recipient=self.request.user,
                recipient_type=APPROVER
            )
        elif self.mode == 'user':
            qs = qs.filter(
                Q(user=self.request.user)
            )

        # else HR
        return qs.select_related(
            *select_related
        )

    def get_counts(self):
        # temporarily disable `status` from filter_map
        self.filter_map.pop('status', None)
        stats = self.filter_queryset(
            self.get_queryset()
        ).aggregate(**{
            REQUESTED: Count('id', filter=Q(status=REQUESTED)),
            APPROVED: Count('id', filter=Q(status=APPROVED)),
            DENIED: Count('id', filter=Q(status=DENIED)),
            FORWARDED: Count('id', filter=Q(status=FORWARDED)),
            'All': Count('id')
        })
        self.filter_map['status'] = 'status'
        return stats

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data.update({'counts': self.get_counts()})
        return response

    def paginate_queryset(self, queryset):
        page = super().paginate_queryset(queryset)
        if self.action == 'list' and self.mode == 'supervisor':
            return set_supervisor_permissions(page, self.request.user.id, 'user')
        return page

    @action(methods=['get'], detail=False, url_path='counts')
    def counts(self, *args, **kwargs):
        return Response(self.get_counts())

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status != APPROVED:
            raise ValidationError({
                'detail': 'Only approved leave requests can be deleted.'
            })
        if instance.leave_account.is_archived:
            raise ValidationError({
                'detail': 'The action is not available for archived Leave '
                          'Account.'
            })
        data = dict(request.data)
        ctx = self.get_serializer_context()
        ctx.update({
            'leave_request': instance,
        })
        if self.mode == 'hr':
            if not validate_permissions(
                self.request.user.get_hrs_permissions(
                    self.get_organization()
                ),
                LEAVE_REQUEST_PERMISSION
            ):
                raise self.permission_denied(self.request)
            ctx.update({'mode': 'hr'})

        ser = LeaveRequestDeleteHistorySerializer(
            context=ctx,
            data=data
        )
        ser.is_valid(raise_exception=True)
        delete_instance = ser.save()
        supervisor = instance.user.first_level_supervisor
        if supervisor:
            delete_instance.recipient = supervisor
            delete_instance.save()

        if self.mode == 'hr':
            leave_request = delete_instance.leave_request
            recipient = leave_request.user
            suffix = f'{leave_request.start.date()}'
            if leave_request.start.date() != leave_request.end.date():
                suffix = f'{leave_request.start.date()} - {leave_request.end.date()}'
            notification_text = 'Your leave request for %s has been deleted by %s' % (
                suffix,
                self.request.user
            )
            add_notification(
                text=notification_text,
                actor=request.user,
                action=delete_instance,
                recipient=recipient,
                url=f"/user/leave/cancel-history"
            )
            notify_organization(
                text=f"{leave_request.user.full_name}'s leave request for {suffix} has "
                f"been deleted by {self.request.user.full_name}.",
                action=delete_instance,
                actor=request.user,
                organization=self.organization,
                permissions=[LEAVE_PERMISSION, LEAVE_REQUEST_PERMISSION],
                url=f"/admin/{self.organization.slug}/leave/cancel-request"
            )
        else:
            # for sending notification to the organization
            suffix = f'{instance.start.date()}'
            if instance.start.date() == instance.end.date():
                suffix = f'{instance.start.date()} - {instance.end.date()}'
            organization = instance.user.detail.organization

            notify_organization(
                text=f"{instance.user.full_name} wants to cancel leave request for {suffix}.",
                action=delete_instance,
                actor=instance.user,
                organization=organization,
                permissions=[
                    LEAVE_PERMISSION, LEAVE_REQUEST_PERMISSION
                ],
                url=f"/admin/{organization.slug}/leave/cancel-request"
            )
            add_notification(
                text=f"{instance.user.full_name} wants to cancel leave request for {suffix}.",
                actor=request.user,
                action=delete_instance,
                recipient=supervisor,
                url=f"/user/supervisor/leave/cancel-requests",
                is_interactive=True,
                interactive_type=LEAVE_CANCEL_REQUEST_NOTIFICATION,
                interactive_data={
                    "leave_request_cancel_id": delete_instance.id,
                    "organization": {
                        "name": instance.user.detail.organization.name,
                        "slug": instance.user.detail.organization.slug
                    }
                }
            )
        return Response(
            status=status.HTTP_200_OK,
            data=ser.data
        )

    @action(methods=['get'], detail=True, url_path='history',
            url_name='leave-balance-history')
    def get_leave_balance_history(self, *args, **kwargs):
        serializer = LeaveRequestHistorySerializer
        obj = self.get_object()
        page = self.paginate_queryset(obj.history.all())
        if page is not None:
            serializer = serializer(page, many=True)
            resp = self.get_paginated_response(serializer.data)
            return resp
        return Response

    @action(methods=['get'], detail=False, url_path='users')
    def get_applicable_users(self, request, *args, **kwargs):
        search = request.query_params.get('search')
        ordering = request.query_params.get('ordering')
        mode = request.query_params.get('as')
        qs = get_user_model().objects.all()

        if mode == "supervisor":
            subordinates = UserSupervisor.objects.filter(supervisor=self.request.user)
            subordinates_id = [subordinate.user.id for subordinate in subordinates]
            qs = qs.filter(id__in=subordinates_id)

        qs = qs.filter(
            leave_accounts__isnull=False
        ).annotate(
            has_account=Exists(
                LeaveAccount.objects.filter(
                    user_id=OuterRef('pk'),
                    is_archived=False
                )
            )
        ).filter(has_account=True).filter(
            attendance_setting__isnull=False,
            detail__organization=self.get_organization(), )

        qs = apply_filters(
            request.query_params,
            {
                'branch': 'detail__branch__slug',
                'division': 'detail__division__slug',
                'username': 'username'
            },
            qs
        )

        qs = qs.prefetch_related(
            'detail',
            'detail__organization',
            'detail__division',
            'detail__job_title',
            'detail__employment_status',
            'detail__employment_level'
        )
        if search:
            qs = qs.filter(
                Q(first_name__istartswith=search) |
                Q(middle_name__istartswith=search) |
                Q(last_name__istartswith=search)|
                Q(username=search)
            )
        if ordering:
            if ordering == 'full_name':
                qs = qs.order_by(
                    'first_name', 'middle_name', 'last_name'
                )
            elif ordering == '-full_name':
                qs = qs.order_by(
                    '-first_name', '-middle_name', '-last_name'
                )
        qs = qs.distinct()
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = UserSupervisorDivisionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = UserSupervisorDivisionSerializer(qs, many=True)
        return Response(serializer.data)

    @action(methods=['post'], detail=False, url_path='bulk-action',
            url_name='bulk-action', serializer_class=DummySerializer)
    def bulk_action(self, request, **kwargs):
        """
        BULK ACTION

        POST DATA -->

            [{
                "leave_request": leave_request_id,
                "action": "approve",
                "remark": "Approved"
            },...]

        `action` can be one of "approve", "deny" or "forward"
        """
        ctx = self.get_serializer_context()
        ctx['leave_requests'] = self.get_queryset()
        serializer = LeaveRequestActionSerializer(
            data=request.data,
            context=ctx,
            many=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Successfully applied actions.'})

    @action(methods=['post'], detail=False, url_path='alternate-leave-accounts-apply',
            url_name='alternate-leave-accounts-apply',
            serializer_class=LeaveRequestAlternateAccountsSerializer)
    def alternate_leave_accounts_apply(self, request, **kwargs):
        """
        Alternate leave accounts apply
       """
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Successfully requested leave.'})

    @staticmethod
    def prepare_export_object(obj, **kwargs):
        category = obj.leave_rule.leave_type.category
        if category in [CREDIT_HOUR, TIME_OFF]:
            hour = int(obj.balance / 60)
            minutes = int(obj.balance) % 60
            obj.balance = f"{hour}:{minutes} HH:MM"
        else:
            obj.balance = f"{obj.balance} day"

        obj.start = obj.start.date()
        obj.end = obj.end.date()
        return obj


class LeaveRequestDeleteViewSet(
    GetStatisticsMixin,
    OrganizationMixin,
    ModeFilterQuerysetMixin,
    ListRetrieveViewSetMixin
):
    """
    Display status above the heading as shown in mock-up.
    Status are

        All - Should display all leave request with total number of leave request delete count.

        Requested - Should display total number of requested leave delete count at heading.

        Clicking on it should display only deleted leave request with status requested.

        Approved - Should display total number of approved leave delete count at heading.

        Clicking on it should display only deleted leave request with status approved.

        Denied - Should display total number of denied leave delete count at heading.

        Clicking on it should display only deleted leave request with status denied.
    ```
        ?status=Denied|Approved|Requested|<blank>
    ```

    ## Table details

        Leave Type - Should display the leave type in list.
            leave_request.leave_type

        From Date - Should display from date of respective leave request.
            leave_request.start

        To Date - Should display to date of respective leave request.
            leave_request.end

        Part of Day - Should display the part of day.
            leave_request.part_of_day

        Requested Date - Should display the leave deleted date.
            created_at

        Status - Should display the leave delete status.
            status

    ## Action - Clicking on action should display "View Details".

    Clicking on view details should open bottom sheet which contains following information.

        Leave Request Deleted Date
            modified_at (Modification is allowed only once i.e. Approved or Declined.)

        Status
            status

        Leave Type
            leave_request.leave_type

        Part Of Day
            leave_request.part_of_day

        From Date
            leave_request.start

        To Date
            leave_requested.end

        Leave Requested Date
            leave_request.created_at

        Self Remarks
            requested_remarks

        HR Admin Remarks - Display HR Admin Remarks after HR responses on request.
            acted_remarks
    Cross icon to close bottom sheet.

    """
    queryset = LeaveRequestDeleteHistory.objects.filter()
    serializer_class = LeaveRequestDeleteHistorySerializer
    filter_backends = (
        FilterMapBackend, OrderingFilterMap, filters.SearchFilter
    )
    search_fields = (
        'leave_request__user__first_name',
        'leave_request__user__middle_name',
        'leave_request__user__last_name'
    )
    filter_map = {
        'status': 'status',
        'branch': 'leave_request__user__detail__branch__slug',
        'division': 'leave_request__user__detail__division__slug',
        'employment_level': 'leave_request__user__detail__employment_level__slug',
        'start_time': 'leave_request__start',
        'end_time': 'leave_request__end',
        'recipient': 'recipient',
        'user': 'leave_request__user',
        'leave_type': 'leave_request__leave_rule__leave_type',
        'start_date': 'leave_request__end__date__gte',
        'end_date': 'leave_request__start__date__lte'
    }
    ordering_fields_map = {
        'modified_at': 'modified_at',
        'created_at': 'created_at',
        'name': (
            'leave_request__user__first_name',
            'leave_request__user__middle_name',
            'leave_request__user__last_name'
        ),
        'start_date': 'leave_request__start',
        'end_date': 'leave_request__end',
    }
    statistics_field = 'status'
    permission_classes = [LeaveRequestDeletePermission, LeaveRequestDeleteObjectPermission]
    permission_to_check = [LEAVE_PERMISSION, LEAVE_REQUEST_PERMISSION]
    user_definition = 'leave_request__user'

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get('as') == 'supervisor':
            qs = qs.filter(recipient=self.request.user)
        return qs

    @action(
        methods=['post'],
        detail=True,
        url_path='(?P<action>(approve|deny|forward))',
        serializer_class=LeaveRequestDeleteHistorySerializer
    )
    def delete_leave_request(self, request, **kwargs):
        leave_request_delete_history = self.get_object()
        if leave_request_delete_history.status in [APPROVED, DENIED]:
            raise ValidationError({
                'detail': 'The cancel request has already been '
                          f'{leave_request_delete_history.get_status_display()}.'
            })

        if self.kwargs.get('action') == 'forward' and request.query_params.get('as') == 'hr':
            raise ValidationError({
                'detail': 'You can either approve or deny the leave cancel request.'
            })

        desired_status = {
            'request': REQUESTED,
            'approve': APPROVED,
            'forward': FORWARDED,
            'deny': DENIED,
        }.get(self.kwargs.get('action'))
        if not desired_status:
            raise ValidationError({
                'detail': 'Please select a valid action.'
            })

        if (
            leave_request_delete_history.leave_request.leave_account.is_archived
            and desired_status in [APPROVED, FORWARDED]
        ):
            raise ValidationError({
                'detail': 'The action is not available for archived Leave '
                          'Account. Please deny instead.'
            })

        # The past approved leave requests pass through here.
        data = {
            k: v for k, v in request.data.items()
        }
        data.update({
            'status': desired_status
        })
        ctx = self.get_serializer_context()
        ctx.update({
            'leave_request': leave_request_delete_history.leave_request
        })
        ser = LeaveRequestDeleteHistorySerializer(
            instance=leave_request_delete_history,
            data=data,
            context=ctx
        )
        ser.is_valid(raise_exception=True)
        ser.save()

        leave_request = leave_request_delete_history.leave_request
        recipient = leave_request.user
        suffix = f'{leave_request.start.date()}'
        if leave_request.start.date() == leave_request.end.date():
            suffix = f'{leave_request.start.date()} - {leave_request.end.date()}'
        # for sending notification to the user
        if desired_status != FORWARDED:
            add_notification(
                text=f"Your leave cancel request for {suffix} has been {desired_status}"
                     f" by {self.request.user.full_name}.",
                actor=request.user,
                action=leave_request_delete_history,
                recipient=recipient,
                url=f"/user/leave/cancel-history"
            )
            notify_organization(
                text=f"{leave_request.user.full_name} leave cancel request for {suffix} has "
                     f"been {desired_status} by {self.request.user.full_name}.",
                action=leave_request_delete_history,
                actor=request.user,
                organization=self.organization,
                permissions=[LEAVE_PERMISSION, LEAVE_REQUEST_PERMISSION],
                url=f"/admin/{self.organization.slug}/leave/cancel-request"
            )
        else:
            new_recipient = get_recipient(
                user=recipient,
                recipient=leave_request_delete_history.recipient,
                status=FORWARDED,
                recipient_type=SUPERVISOR
            )[0]
            if not new_recipient:
                raise ValidationError({
                    'detail': 'You are unable to forward this request.'
                })
            leave_request_delete_history.recipient = new_recipient
            leave_request_delete_history.save()
            organization = leave_request.user.detail.organization
            add_notification(
                text=f"{leave_request.user.full_name} leave cancel request for {suffix} has "
                     f"been {desired_status} by {self.request.user.full_name}.",
                actor=request.user,
                action=leave_request_delete_history,
                recipient=new_recipient,
                url=f"/user/supervisor/leave/cancel-requests",
                is_interactive=True,
                interactive_type=LEAVE_CANCEL_REQUEST_NOTIFICATION,
                interactive_data={
                    "leave_request_cancel_id": leave_request_delete_history.id,
                    "organization": {
                        "name": organization.name,
                        "slug": organization.slug
                    }
                }
            )
        return Response(ser.data)

    @action(
        methods=['get'],
        detail=True,
        url_path='status-history'
    )
    def get_status_history(self, request, **kwargs):
        leave_request_delete_history = self.get_object()
        qs = leave_request_delete_history.status_history.all()
        return Response(
            LeaveRequestDeleteStatusHistorySerializer(
                many=True,
                instance=qs,
                context=self.get_serializer_context()
            ).data
        )

    def list(self, request, *args, **kwargs):
        ret = super().list(request, *args, **kwargs)
        ret.data.update({
            'statistics': self.statistics
        })
        return ret


class AdminLeaveRequest(OrganizationMixin, CreateViewSetMixin):
    serializer_class = AdminLeaveRequestSerializer
    permission_classes = [permission_factory.build_permission(
        name='Offline Leave Permission',
        allowed_to=[HAS_PERMISSION_FROM_METHOD]
    )]

    @property
    def mode(self):
        mode = self.request.query_params.get('as')
        if mode in ['supervisor', 'hr']:
            return mode
        return 'user'

    def has_user_permission(self):
        if self.mode == 'hr':
            is_hr = validate_permissions(
                self.request.user.get_hrs_permissions(self.get_organization()),
                LEAVE_REQUEST_PERMISSION,
                LEAVE_PERMISSION,
                OFFLINE_LEAVE_PERMISSION
            )
            return is_hr
        return True

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx.update({
            'organization': self.get_organization(),
            'mode': self.mode,
            'bypass_validation': self.request.query_params.get('bypass_validation')
        })
        return ctx
