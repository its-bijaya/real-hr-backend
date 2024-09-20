from django.db.models import OuterRef, Subquery, Count, Sum
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import (
    GenericViewSet
)
from irhrs import organization, payroll
from irhrs.core.constants.organization import BIRTHDAY_EMAIL, REBATE_IS_APPROVED_DECLINED, \
    REBATE_IS_REQUESTED_BY_USER, REBATE_IS_REQUESTED_ON_BEHALF_USER_BY_HR, GLOBAL
from irhrs.core.mixins.file_import_mixin import BackgroundFileImportMixin

from irhrs.core.mixins.viewset_mixins import OrganizationMixin
from rest_framework import mixins
from rest_framework.decorators import action

from rest_framework import status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser

from rest_framework.filters import SearchFilter
from irhrs.core.utils.common_utils import get_users_list_from_permissions
from irhrs.core.utils.filters import OrderingFilterMap

from django_filters.rest_framework import (
    DjangoFilterBackend,
    FilterSet,
    MultipleChoiceFilter
)

from irhrs.export.mixins.export import BackgroundTableExportMixin
from irhrs.organization.models import FiscalYear
from irhrs.payroll.constants import MONTHLY
from irhrs.payroll.utils.generate import \
    raise_validation_error_if_payroll_in_generated_or_processing_state
from irhrs.payroll.utils.user_voluntary_rebate import get_all_payroll_generated_months, \
    revert_fiscal_months_amount_to_zero_when_rebate_is_archived, archive_old_rebate_entry
from irhrs.permission.constants.permissions import (
    PAYROLL_REBATE_PERMISSION
)
from irhrs.permission.constants.permissions.hrs_permissions import GENERATE_PAYROLL_PERMISSION


from irhrs.permission.permission_classes import permission_factory

from irhrs.notification.utils import (
    notify_organization,
    add_notification
)

from irhrs.payroll.models import (
    UserVoluntaryRebate,
    UserVoluntaryRebateAction,
    UserVoluntaryRebateDocument,
    CREATE_REQUEST,
    CREATED,
    CREATE_REJECTED,
    DELETE_REQUEST,
    DELETED,
    DELETE_REJECTED,
    VOLUNTARY_REBATE_ACTION_CHOICES, RebateSetting
)

from irhrs.payroll.api.v1.serializers.user_voluntary_rebate_requests import (
    UserVoluntaryRebateCreateSerializer,
    RequestUserVoluntaryRebateCreateSerializer,
    UserVoluntaryRebateListSerializer,
    RequestUserVoluntaryRebateListSerializer,
    RebateActionHistorySerializer,
    UserVoluntaryRebateActionRemarkSerializer, UserVoluntaryRebateImportSerializer
)
from irhrs.core.utils.email import send_email_as_per_settings


class UserVoluntaryRebateFilter(FilterSet):

    status = MultipleChoiceFilter(
        choices=VOLUNTARY_REBATE_ACTION_CHOICES,
        method='get_status_in'
    )

    def get_status_in(self, queryset, name, value):
        return queryset.filter(**{
            'status__in': value,
        })

    class Meta:
        model = UserVoluntaryRebate
        fields = ['status', 'user_id', 'fiscal_year_id']


class UserVoluntaryRebateStatFilter(FilterSet):
    class Meta:
        model = UserVoluntaryRebate
        fields = ['user_id', 'fiscal_year_id', 'rebate_id']


class UserVoluntaryRebateApiViewset(
    mixins.ListModelMixin,
    GenericViewSet,
    OrganizationMixin,
    BackgroundFileImportMixin,
    BackgroundTableExportMixin
):
    queryset = UserVoluntaryRebate.objects.all()
    filter_backends = (DjangoFilterBackend, OrderingFilterMap, SearchFilter)
    ordering_fields_map = {
        'full_name': (
            'user__first_name',
            'user__middle_name',
            'user__last_name'
        )
    }
    search_fields = ()
    filter_class = UserVoluntaryRebateFilter
    serializer_class = UserVoluntaryRebateListSerializer
    import_serializer_class = UserVoluntaryRebateImportSerializer
    import_fields = [
        "user",
        "rebate_type",
        "title",
        "fiscal_year",
        'amount',
        'description',
        'remarks'
    ]
    values = [
        "info@example.com",
        "rebate_type",
        "rebate for this year",
        "2078/89",
        "10000",
        "rebate confirmed",
        "rebate on bonus"
    ]
    serializer_field_map = {
        "user": "user",
        "rebate_type": "rebate_type",
        "title": "title",
        "fiscal_year": "fiscal_year",
        "amount": "amount",
        "description": "description",
        "remarks": "remarks"
    }
    non_mandatory_field_value = {}
    model_fields_map = {
        "user": "user",
        "rebate_type": "rebate_type",
        "title": "title",
        "fiscal_year": "fiscal_year",
        "amount": "amount",
        "description": "description",
        "remarks": "remarks"

    }
    background_task_name = 'user-rebate'
    sample_file_name = 'user-rebate-import'

    def get_success_url(self):
        success_url = f'/admin/{self.organization.slug}/payroll/rebate/'
        return success_url

    def get_failed_url(self):
        failed_url = f'/admin/{self.organization.slug}/payroll/rebate/?status=failed'
        return failed_url

    def get_queryset_fields_map(self):
        return {
            'fiscal_year': [fiscal_year.name for fiscal_year in FiscalYear.objects.filter(
                organization=self.organization, category=GLOBAL)],
            'rebate_type': [rebate_setting.title for rebate_setting in RebateSetting.objects.filter(
                organization=self.organization, is_archived=False)]
        }

    permission_classes = [
        permission_factory.build_permission(
            "VoluntaryRebatePermission",
            actions={
                'list': [PAYROLL_REBATE_PERMISSION],
                'create': [PAYROLL_REBATE_PERMISSION],
                'archive_rebate_entry':[PAYROLL_REBATE_PERMISSION],
                'accept_create_request': [PAYROLL_REBATE_PERMISSION],
                'reject_create_request': [PAYROLL_REBATE_PERMISSION],
                'accept_delete_request': [PAYROLL_REBATE_PERMISSION],
                'reject_delete_request': [PAYROLL_REBATE_PERMISSION],
                'rebate_action_history': [PAYROLL_REBATE_PERMISSION],
                'export': [PAYROLL_REBATE_PERMISSION]
            }
        )
    ]
    notification_permissions = [PAYROLL_REBATE_PERMISSION]

    @property
    def permissions_description_for_notification(self):
        return [PAYROLL_REBATE_PERMISSION]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserVoluntaryRebateCreateSerializer
        return super().get_serializer_class()

    @staticmethod
    def get_multipart_files(query_dict):
        file_keys = filter(lambda x: x.startswith('file'), query_dict.keys())

        return map(
            lambda key: query_dict.pop(key),
            list(file_keys)
        )

    @property
    def frontend_hr_rebate_list_url(self):
        return f'/admin/{self.get_organization().slug}/payroll/rebate'

    @property
    def frontend_user_rebate_list_url(self):
        return '/user/payroll/rebate'

    def _export_post(self):
        fiscal_year_id = self.request.query_params.get('fiscal_year_id', None)
        if not fiscal_year_id:
            raise ValidationError("Choose fiscal before generating excel file.")
        return super()._export_post()

    # Key is action request and value is current status requirement
    action_request_required_status = {
        CREATED: [CREATE_REQUEST],
        CREATE_REJECTED: [CREATE_REQUEST],
        DELETE_REQUEST: [CREATED, DELETE_REJECTED],
        DELETED: [DELETE_REQUEST],
        DELETE_REJECTED: [DELETE_REQUEST]
    }

    def add_voluntary_deduction_action(self, action):
        instance = self.get_object()

        if instance.status not in self.action_request_required_status[action]:
            return Response(
                dict(
                    non_fields_errors=[
                        (
                            f'{self.action_request_required_status[action]} '
                            f'is required for status to be {action}'
                        )
                    ]
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        if (action == DELETE_REQUEST) and (self.request.user != instance.user):
            return Response(
                dict(
                    non_fields_errors=['Only owner can send delete request']
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        if action == CREATED:
            archive_old_rebate_entry(instance)

        remark_serializer = UserVoluntaryRebateActionRemarkSerializer(
            data={
                'remarks': self.request.data.get('remarks')
            }
        )
        remark_serializer.is_valid(raise_exception=True)

        UserVoluntaryRebateAction.objects.create(
            user_voluntary_rebate=instance,
            action=action,
            remarks=self.request.data.get('remarks')
        )

        if action in [CREATED, CREATE_REJECTED, DELETED, DELETE_REJECTED]:
            add_notification(
                text=f"Your {instance.title} rebate entry has been {action}.",
                recipient=instance.user,
                action=instance,
                actor=self.request.user,
                url=self.frontend_user_rebate_list_url
            )
            send_email_as_per_settings(
                recipients=instance.user,
                subject="Rebate Status",
                email_text=f"Your {instance.title} rebate entry has been {action}.",
                email_type=REBATE_IS_REQUESTED_BY_USER
            )

        if action in [DELETE_REQUEST]:
            notify_organization(
                actor=self.request.user,
                text=f"{self.request.user} has sent request to Archive {instance.title} rebate.",
                action=instance,
                organization=self.get_organization(),
                url=self.frontend_hr_rebate_list_url,
                permissions=[PAYROLL_REBATE_PERMISSION]
            )
        if action in [DELETED, CREATE_REJECTED] and instance.rebate.duration_type == "Monthly":
            revert_fiscal_months_amount_to_zero_when_rebate_is_archived(
                instance)

        return Response(status=status.HTTP_200_OK)

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'user',
            'fiscal_year',
            'rebate'
        ).prefetch_related('documents')

        fiscal_year_id = self.request.query_params.get('fiscal_year_id')
        if fiscal_year_id:
            queryset = queryset.filter(fiscal_year_id=fiscal_year_id)
        action_based_filter = dict()

        if self.action == 'by_current_user':
            action_based_filter['user'] = self.request.user

        status_history_subquery = UserVoluntaryRebateAction.objects.filter(
            user_voluntary_rebate=OuterRef('pk')
        ).order_by('-created_at')

        return queryset.filter(
            user__detail__organization__slug=self.kwargs.get(
                'organization_slug'
            ),
            **action_based_filter
        ).annotate(
            status=Subquery(status_history_subquery.values('action')[:1])
        )

    def get_fiscal_months(self):
        fiscal_year_id = self.request.query_params.get('fiscal_year_id')
        fiscal_year = get_object_or_404(FiscalYear, id=fiscal_year_id)
        fiscal_months = fiscal_year.fiscal_months.values_list('display_name', flat=True)
        return fiscal_months

    def get_export_type(self):
        return 'Rebate'

    def get_frontend_redirect_url(self):
        return f'/admin/{self.organization.slug}/payroll/rebate'

    def get_export_fields(self):
        fields = [
            {
                'name': 'user.full_name',
                'title': 'Employee Name'
            },
            {
                'name': 'title',
                'title': 'title'
            },
            {
                'name': 'rebate.title',
                'title': 'Rebate Type'
            },
            {
                'name': 'amount',
                'title': 'Amount'
            },
            {
                'name': 'duration_unit',
                'title': 'Duration Type'
            },
            {
                'name': 'fiscal_year_name',
                'title': 'Fiscal Year'
            },
            {
                'name': 'fiscal_months_amount',
                'title': 'Fiscal Months Amount',
                'fields':
                    [{
                        'name': i,
                        'title': i
                    } for i in self.get_fiscal_months()]
            },
            {
                'name': 'status',
                'title': 'Status'
            }
        ]
        return fields

    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        self.filter_class = UserVoluntaryRebateStatFilter

        stats_list = self.filter_queryset(self.get_queryset()).order_by('status').values(
            'status'
        ).annotate(
            Count('status')
        )
        stats = dict()
        for item in stats_list:
            stats[item['status']] = item['status__count']
        response.data['stats'] = stats
        return response

    @action(
        methods=['GET'],
        detail=False,
        url_path='by-current-user',
        serializer_class=RequestUserVoluntaryRebateListSerializer
    )
    def by_current_user(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["organization"] = self.get_organization()
        ctx["hide_fiscal_months_amount"] = True
        return ctx

    def create_rebate(self, request, **kwargs):
        ''' Creates rebate by user or hr
        '''
        multipart_files_iter = UserVoluntaryRebateApiViewset.get_multipart_files(
            request.data
        )

        serializer = self.get_serializer(
            data=request.data,
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)

        remark_serializer = UserVoluntaryRebateActionRemarkSerializer(
            data={
                'remarks': kwargs.get('remarks')
            }
        )
        remark_serializer.is_valid(raise_exception=True)

        instance = serializer.save()

        invalidate_old_rebate_entry = kwargs.get(
            'invalidate_monthly_rebate_entry',
            False
        )

        if invalidate_old_rebate_entry:
            archive_old_rebate_entry(instance)

        UserVoluntaryRebateAction.objects.create(
            user_voluntary_rebate=instance,
            action=kwargs.get('action'),
            remarks=kwargs.get('remarks', 'Default remark')
        )

        UserVoluntaryRebateDocument.objects.bulk_create(
            [
                UserVoluntaryRebateDocument(
                    user_voluntary_rebate=instance,
                    file_name=blob[0].name,
                    file=blob[0]
                ) for blob in multipart_files_iter
            ]
        )

        if kwargs.get('action') == CREATE_REQUEST:
            notify_organization(
                actor=request.user,
                text=f"{request.user} has sent {instance.title} rebate request.",
                action=instance,
                organization=self.get_organization(),
                url=self.frontend_hr_rebate_list_url,
                permissions=[PAYROLL_REBATE_PERMISSION]
            )
            hrs=get_users_list_from_permissions(
                permission_list=[PAYROLL_REBATE_PERMISSION],
                organization=self.get_organization()
            )
            send_email_as_per_settings(
                recipients=hrs,
                subject="Rebate Status",
                email_text=f"{request.user} has sent {instance.title} rebate request.",
                email_type=REBATE_IS_REQUESTED_BY_USER
            )
        elif kwargs.get('action') == CREATED:
            add_notification(
                text=f"Your new rebate entry was added.",
                recipient=instance.user,
                action=instance,
                actor=request.user,
                url=self.frontend_user_rebate_list_url
            )
            send_email_as_per_settings(
                recipients=instance.user,
                subject="Rebate Status",
                email_text=f"Dear {instance.user} Your {instance.title} rebate entry has been Created.",
                email_type=REBATE_IS_REQUESTED_ON_BEHALF_USER_BY_HR

            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        methods=['POST'],
        detail=False,
        url_path='new-create-request',
        parser_classes=(MultiPartParser,),
        serializer_class=RequestUserVoluntaryRebateCreateSerializer
    )
    def new_create_request(self, request, **kwargs):
        kwargs['remarks'] = 'Entry requested by user.'
        kwargs['action'] = CREATE_REQUEST
        raise_validation_error_if_payroll_in_generated_or_processing_state(
            organization=self.get_organization()
        )
        return self.create_rebate(request, **kwargs)

    def create(self, request, **kwargs):
        creator_remarks = request.data.get(
            'remarks'
        )
        kwargs['remarks'] = creator_remarks
        kwargs['invalidate_monthly_rebate_entry'] = True
        kwargs['action'] = CREATED
        return self.create_rebate(request, **kwargs)

    @action(methods=['POST'], detail=True, url_path='archive-rebate-entry')
    def archive_rebate_entry(self, request, pk=None, **kwargs):
        instance = self.get_object()

        remark_serializer = UserVoluntaryRebateActionRemarkSerializer(
            data={
                'remarks': request.data.get('remarks')
            }
        )
        remark_serializer.is_valid(raise_exception=True)

        UserVoluntaryRebateAction.objects.create(
            user_voluntary_rebate=instance,
            action=DELETED,
            remarks=self.request.data.get(
                'remarks'
            )
        )

        add_notification(
            text=f"Your {instance.title} rebate has been archived.",
            recipient=instance.user,
            action=instance,
            actor=request.user,
            url=self.frontend_user_rebate_list_url
        )
        send_email_as_per_settings(
            recipients=instance.user,
            subject="Rebate Status",
            email_text=f"Dear {instance.user} Your request{instance.title} rebate entry has been {action}.",
            email_type=REBATE_IS_APPROVED_DECLINED
        )
        if instance.rebate.duration_type == "Monthly":
            revert_fiscal_months_amount_to_zero_when_rebate_is_archived(
                instance)

        return Response(status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=True, url_path='accept-create-request')
    def accept_create_request(self, request, pk=None, **kwargs):
        raise_validation_error_if_payroll_in_generated_or_processing_state(
            organization=self.get_organization()
        )
        return self.add_voluntary_deduction_action(CREATED)

    @action(methods=['POST'], detail=True, url_path='reject-create-request')
    def reject_create_request(self, request, pk=None, **kwargs):
        return self.add_voluntary_deduction_action(CREATE_REJECTED)

    @action(methods=['POST'], detail=True, url_path='delete-request')
    def delete_request(self, request, pk=None, **kwargs):
        return self.add_voluntary_deduction_action(DELETE_REQUEST)

    @action(methods=['POST'], detail=True, url_path='accept-delete-request')
    def accept_delete_request(self, request, pk=None, **kwargs):
        return self.add_voluntary_deduction_action(DELETED)

    @action(methods=['POST'], detail=True, url_path='reject-delete-request')
    def reject_delete_request(self, request, pk=None, **kwargs):
        return self.add_voluntary_deduction_action(DELETE_REJECTED)

    def get_history_response(self, instance):
        serializer = self.get_serializer(instance.statuses.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=True, url_path='rebate-action-history', serializer_class=RebateActionHistorySerializer)
    def rebate_action_history(self, request, *args, **kwargs):
        instance = self.get_object()
        return self.get_history_response(instance)

    @action(methods=['GET'], detail=True, url_path='user-rebate-action-history', serializer_class=RebateActionHistorySerializer)
    def request_user_rebate_action_history(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            return Response(
                {'non_fields_errors': 'This rebate entry is not yours'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return self.get_history_response(instance)
