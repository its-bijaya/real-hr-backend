from django.db.models import Count, Q
from django.http import Http404
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response

from irhrs.core.mixins.serializers import DummySerializer
from irhrs.core.mixins.viewset_mixins import ListViewSetMixin, OrganizationMixin
from irhrs.notification.api.v1.serializers.notification import \
    (NotificationSerializer, NotificationReminderSerializer,
     OrganizationNotificationSerializer)
from irhrs.notification.models import Notification
from irhrs.notification.models.notification import OrganizationNotification
from irhrs.notification.utils import (read_notifications, read_notification,
                                      remind_notification_at)
from irhrs.permission.constants.permissions import HAS_PERMISSION_FROM_METHOD
from irhrs.permission.permission_classes import permission_factory


class NotificationViewSet(ListViewSetMixin):
    """
    Notification ViewSet

    list:
    List of all notifications

    params =

        {
            "read": true/false
        }

    read_all:
    Read all notifications

    remind:
    Set reminder to notification

    data = {
        "remind_at": "yyyy-mm-ddThh:dd"
    }
    """
    serializer_class = NotificationSerializer
    filter_fields = ['read']

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        response.data.update(self.get_stats())
        return response

    def get_serializer_class(self):
        if self.action == 'remind':
            return NotificationReminderSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user,
            notify_on__lte=timezone.now()
        ).select_related(
            'actor',
            'actor__detail',
            'actor__detail__organization',
            'actor__detail__job_title',
            'actor__detail__division',
            'actor__detail__employment_level'
        )

    @action(methods=['POST'], detail=False, url_name='read-all',
            url_path='read-all')
    def read_all(self, request):
        notifications = Notification.objects.filter(
            recipient=request.user)
        read_notifications(notifications)
        return Response(self.get_stats())

    @action(methods=['POST'], detail=True, url_name='read', url_path='read')
    def read(self, request, *args, **kwargs):
        notification = self.get_object()
        read_notification(notification)
        return Response(self.get_stats())

    @action(methods=['POST'], detail=True, url_name='remind',
            url_path='remind')
    def remind(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notification = self.get_object()

        if remind_notification_at(notification,
                                  serializer.data.get('remind_at')):
            return Response({
                'message': 'Successfully set reminder.',
                'remind_at': notification.notify_on
            })
        else:
            return Response({
                'message': 'Could not set reminder'
            }, status=400)

    def get_stats(self):
        stats = self.get_queryset().aggregate(
            total_count=Count('id'),
            read_count=Count('id', filter=Q(read=True))
        )
        stats.update({'unread_count': stats.get('total_count') - stats.get(
            'read_count')})
        return stats


class OrganizationNotificationViewSet(OrganizationMixin, ListViewSetMixin):
    """
    Notification ViewSet

    list:
    List of all notifications

    params =

        {
            "read": true/false
        }

    read_all:
    Read all notifications

    remind:
    Set reminder to notification

    data = {
        "remind_at": "yyyy-mm-ddThh:dd"
    }
    """
    serializer_class = OrganizationNotificationSerializer
    permission_classes = [permission_factory.build_permission(
        "OrganizationNotificationPermission",
        allowed_to=[HAS_PERMISSION_FROM_METHOD]
    )]
    filter_fields = ('is_resolved',)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data.update(self.get_stats())
        return response

    def has_user_permission(self):
        user = self.request.user
        if user and user.is_authenticated and user.switchable_organizations_pks:
            return True
        return False

    def get_queryset(self):
        notification_permissions = self.request.user.get_hrs_permissions(
            self.get_organization()
        ).union(
            self.request.user.get_hrs_permissions(None)
        )
        return OrganizationNotification.objects.filter(
            recipient=self.get_organization(),
            associated_permissions__overlap=list(notification_permissions)
        ).distinct().select_related(
            'actor',
            'actor__detail',
            'actor__detail__organization',
            'actor__detail__job_title',
            'actor__detail__division',
            'actor__detail__employment_level',
        )

    @action(
        methods=['POST'],
        detail=True,
        url_name='perform-action',
        url_path=f"(?P<action>(unresolve|resolve))",
        serializer_class=DummySerializer
    )
    def perform_action(self, *args, **kwargs):
        action_requested = kwargs.get('action')
        if action_requested not in [
            'unresolve', 'resolve'
        ]:
            raise Http404
        notification = self.get_object()
        notification.is_resolved = action_requested == 'resolve'
        notification.save()
        return Response(self.get_stats())

    def get_stats(self):
        stats = self.get_queryset().aggregate(
            total_count=Count('id'),
            unresolved=Count('id', filter=Q(is_resolved=False)),
            resolved=Count('id', filter=Q(is_resolved=True)),
        )
        return stats
