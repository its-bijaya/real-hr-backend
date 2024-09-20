from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from irhrs.core.constants.common import HRIS
from irhrs.core.constants.user import PENDING, APPROVED, REJECTED
from irhrs.core.mixins.viewset_mixins import OrganizationMixin, \
    ListRetrieveViewSetMixin, GetStatisticsMixin
from irhrs.core.utils.filters import OrderingFilterMap, FilterMapBackend
from irhrs.core.utils.user_activity import create_user_activity
from irhrs.hris.api.v1.permissions import ChangeRequestPermission
from irhrs.hris.api.v1.serializers.change_request import \
    ChangeRequestSerializer, ChangeRequestUpdateSerializer
from irhrs.hris.utils import get_my_change_request_frontend_url
from irhrs.notification.utils import add_notification
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from irhrs.users.models.change_request import ChangeRequest
from irhrs.users.utils import send_logged_out_signal, send_user_update_signal
from irhrs.websocket.helpers import send_for_group as websocket_group


class ChangeRequestViewSet(
    OrganizationMixin,
    GetStatisticsMixin,
    ListRetrieveViewSetMixin,
):
    serializer_class = ChangeRequestSerializer
    permission_classes = (ChangeRequestPermission,)
    filter_backends = [FilterMapBackend, SearchFilter, OrderingFilterMap]
    filter_map = {
        "user": "user",
        "status": "status",
        "category": "category",
        "division": "user__detail__division__slug",
        'start_date': 'created_at__date__gte',
        'end_date': 'created_at__date__lte',
    }
    search_fields = [
        "user__first_name",
        "user__middle_name",
        "user__last_name",
    ]
    ordering_fields_map = {
        "status": "status",
        "category": "category",
        "created_at": "created_at",
        "full_name": (
            "user__first_name",
            "user__middle_name",
            "user__last_name"
        )
    }
    ordering = "-created_at"
    statistics_field = 'status'

    def get_serializer_class(self):
        if self.action in ['approve', 'reject']:
            return ChangeRequestUpdateSerializer
        return super().get_serializer_class()

    def has_user_permission(self):
        if self.request.method.lower() == 'get' and self.request.query_params.get(
            'as') == 'supervisor':
            try:
                user = int(self.request.query_params.get('user'))
            except ValueError:
                return False
            if user in self.request.user.subordinates_pks:
                return True

        if self.request.query_params.get('supervisor'):
            return self.request.query_params.get('supervisor') == str(
                self.request.user.id)

        if self.request.query_params.get('user'):
            return str(self.request.user.id) == self.request.query_params.get(
                'user')
        return False

    def get_queryset(self):
        supervisor_id = self.request.query_params.get('supervisor')
        user_id = self.request.query_params.get('user')
        fil = dict(
            user__user_experiences__is_current=True,
            user__detail__organization=self.get_organization()
        )

        if supervisor_id:
            if supervisor_id == str(self.request.user.id):
                fil.update({
                    'user_id__in':
                        self.request.user.subordinates_pks
                })
            else:
                # if supervisor does not match return none
                return ChangeRequest.objects.get_queryset().none()
        elif user_id and user_id == str(self.request.user.id):
            # To fix count issues in normal user views add user filter in
            # get queryset for self user
            fil.update({'user_id': self.request.user.id})
        return ChangeRequest.objects.filter(**fil)

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        return queryset.select_related(
            'content_type',
            'user__detail',
            'user__detail__employment_level',
            'user__detail__job_title',
            'user__detail__organization',
            'user__detail__division',
        )

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        stats = {
            'total': self.statistics.get('All'),
            'pending': self.statistics.get(PENDING),
            'approved': self.statistics.get(APPROVED),
            'rejected': self.statistics.get(REJECTED)
        }
        response.data.update({'stats': stats})
        return response

    @action(methods=['POST'], detail=True)
    def approve(self, request, *args, **kwargs):
        # The change requests were accepted before the validation of Change
        # Request. Hence, even when change request failed its validation,
        # the change request had already been applied.
        change_request = self.get_object()
        serializer = self.get_serializer(
            instance=change_request,
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        if change_request.apply_change_request():
            # approved change requests
            serializer.save()

            change_request.status = APPROVED
            change_request.updated_by = request.user

            change_request.save()

            create_user_activity(
                actor=request.user,
                message_string="approved Change Request.",
                category=HRIS
            )
            add_notification(
                actor=request.user,
                text=f"{request.user.full_name} accepted your change request.",
                action=change_request,
                recipient=change_request.user,
                url=get_my_change_request_frontend_url()
            )

            change_request.user.refresh_from_db()
            self.send_change_data(change_request=change_request)

            return Response({
                'message': 'Successfully Applied Change Request'
            }, 200)
        else:
            return Response({
                'non_field_errors': 'Could not apply change request.'
                                    ' There might be conflict with previous change request. Please review.'
            }, 400)

    @action(methods=['POST'], detail=True)
    def reject(self, request, *args, **kwargs):
        change_request = self.get_object()
        serializer = self.get_serializer(
            instance=change_request,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        change_request.status = REJECTED
        change_request.updated_by = request.user
        change_request.save()

        create_user_activity(
            actor=request.user,
            message_string=f"declined Change Request.",
            category=HRIS
        )

        add_notification(
            actor=request.user,
            text=f"{request.user.full_name} declined your change request with remarks '{change_request.remarks}'.",
            action=change_request,
            recipient=change_request.user,
            url=get_my_change_request_frontend_url()
        )

        return Response({'message': 'Rejected change request.'})

    @staticmethod
    def send_change_data(change_request):
        valid_categories = ['General Information']
        if change_request.category in valid_categories:
            send_user_update_signal(change_request.user)
