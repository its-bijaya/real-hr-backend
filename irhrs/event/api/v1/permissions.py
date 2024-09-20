from django.db.models import Q

from irhrs.event.models import EventDetail
from irhrs.permission.constants.permissions import (HAS_PERMISSION_FROM_METHOD, EVENT_PERMISSION)
from irhrs.permission.permission_classes import permission_factory

MeetingPermission = permission_factory.build_permission(
    'MeetingPermission',
    allowed_to=[HAS_PERMISSION_FROM_METHOD]
)

EventPermission = permission_factory.build_permission(
    'EventPermission',
    allowed_to=[EVENT_PERMISSION]
)


class BasicMeetingPermissionMixin:
    permission_classes = permission_factory.build_permission(
        'BasicMeetingPermission',
        allowed_to=[HAS_PERMISSION_FROM_METHOD]
    )

    def requested_meeting(self, member='user'):
        user = self.request.user

        if self.request.method.lower() == 'get':
            member = 'user'

        filter = {
            'time_keeper': Q(time_keeper__user=user),
            'minuter': Q(minuter__user=user),
            'user': Q(meeting_attendances__member=user)

        }
        return EventDetail.objects.filter(
            Q(event=self.kwargs.get('event_id')),
            Q(Q(created_by=user) | filter.get(member))
        ).first()


class MeetingPermissionForTimeKeeperMixin(BasicMeetingPermissionMixin):
    def has_user_permission(self):
        event_detail = self.meeting
        if event_detail:
            return event_detail == self.requested_meeting(member='time_keeper')
        return False


class MeetingPermissionForMinuterMixin(BasicMeetingPermissionMixin):
    def has_user_permission(self):
        event_detail = self.meeting
        if event_detail:
            return event_detail == self.requested_meeting(member='minuter')
        return False
