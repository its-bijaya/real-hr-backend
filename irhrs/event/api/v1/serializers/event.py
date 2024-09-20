from datetime import timedelta

from dateutil.parser import parse
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from rest_framework import serializers

from irhrs.core.constants.organization import INVITED_TO_EVENT_EMAIL, EVENT_CANCELED_DELETED_EMAIL, \
    EVENT_UPDATED_EMAIL
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils import email
from irhrs.core.utils.common import validate_permissions
from irhrs.core.validators import validate_recurring_rule
from irhrs.event.constants import (PUBLIC, PENDING, MEETING, OUTSIDE, INSIDE, MEETING_ORGANIZER,
                                   TIME_KEEPER_AND_MINUTER, TIME_KEEPER, MINUTER, MEMBER)
from irhrs.event.models import (Event, EventMembers, EventDetail, MeetingAgenda,
                                MeetingAttendance, MeetingNotification)
from irhrs.event.utils import get_event_frontend_url
from irhrs.event.utils.recurring import create_recurring_events
from irhrs.noticeboard.models import User
from irhrs.notification.models import Notification
from irhrs.notification.utils import add_notification
from irhrs.organization.api.v1.serializers.meeting_room import \
    MeetingRoomStatusSerializer
from irhrs.organization.models import MeetingRoomStatus, MeetingRoom
from irhrs.permission.constants.permissions import EVENT_PERMISSION
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer

USER = get_user_model()


class EventMembersSerializer(DynamicFieldsModelSerializer):

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() in ['get', 'patch']:
            fields['user'] = UserThinSerializer(read_only=True,
                                                fields=(
                                                    'id', 'full_name',
                                                    'profile_picture',
                                                    'cover_picture',
                                                    'job_title',
                                                    'is_online',
                                                    'last_online',
                                                    'is_current',
                                                    'organization'))
            fields['event'] = EventSerializer(
                fields=(
                    'id', 'title', 'description', 'featured_image', 'start_at',
                    'end_at', 'location', 'event_type'),
                read_only=True, context=self.context)
        return fields

    class Meta:
        model = EventMembers
        fields = 'id', 'user', 'event', 'invitation_status',

    @staticmethod
    def validate_invitation_status(status):
        if status == PENDING:
            raise serializers.ValidationError(
                'Cannot set Invitation Status to Pending')
        return status


class EventSerializer(DynamicFieldsModelSerializer):
    my_event_status = serializers.SerializerMethodField(read_only=True)
    members = serializers.ListField(write_only=True)
    featured_image = serializers.ImageField(write_only=True, required=False)
    repeat_rule = serializers.CharField(validators=[validate_recurring_rule],
                                        allow_null=True, allow_blank=True,
                                        required=False)
    eventdetail = serializers.JSONField(required=False, write_only=True,
                                    allow_null=True)
    meeting_room = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Event
        fields = ('id', 'generated_from', 'title', 'description', 'location',
                  'event_type', 'start_at', 'end_at',
                  'featured_image', 'event_category',
                  'members_can_modify',
                  'members_can_invite', 'members_can_see_guest', 'repeat_rule',
                  'created_by', 'event_location',
                  'modified_by', 'members',
                  'my_event_status', 'meeting_room',
                  'interactive_event', 'enabled_event', 'eventdetail')
        read_only_fields = ('created_by',
                            'modified_by',
                            'generated_from')

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == 'get':
            fields['featured_image'] = serializers.CharField()
            if 'members' in fields.keys():
                fields['members'] = serializers.SerializerMethodField(
                    read_only=True)
            fields['created_by'] = UserThinSerializer(read_only=True,
                                                      fields=(
                                                          'id', 'full_name',
                                                          'profile_picture',
                                                          'cover_picture',
                                                          'job_title',
                                                          'is_online',
                                                          'last_online',
                                                          'is_current',
                                                          'organization',))
            fields['meeting_room'] = MeetingRoomStatusSerializer(
                source='room',
                fields=['id', 'room', 'booked_from', 'booked_to'],
                context=self.context
            )
        return fields

    def validate_members(self, user):
        clean_data = []
        if len(user) == 0 and user[1] in ['null', '']:
            return clean_data
        if len(user) != len(set(user)):
            raise serializers.ValidationError(
                "Duplicate members are not allowed")

        def _filter_func(u):
            try:
                int(u)
                return True
            except (ValueError, TypeError):
                return False

        filtered_list = list(
            map(lambda x: int(x), filter(_filter_func, set(user))))
        if filtered_list:
            clean_data = list(
                filter(lambda x: USER.objects.filter(id=x).exists(),
                       filtered_list))
            if len(filtered_list) != len(clean_data):
                raise serializers.ValidationError("Invalid User ID")
        if self.instance:
            if self.instance.created_by_id in clean_data:
                raise serializers.ValidationError(
                    "Event Creator cannot be assigned as event members")
        else:
            if self.request.user.id in clean_data:
                raise serializers.ValidationError(
                    "Event Creator cannot be assigned as event members")

        return clean_data

    def validate(self, attrs):
        user = self.context['request'].user
        start_at = attrs.get('start_at') or (self.instance.start_at if
                                             self.instance else None)
        end_at = attrs.get('end_at') or (self.instance.end_at if
                                         self.instance else None)
        meeting_room = attrs.get('meeting_room')
        if attrs.get('event_location') == INSIDE and not meeting_room:
            raise serializers.ValidationError({
                'meeting_room': [
                    'Meeting room is mandatory for inside location.']
            })

        _room = MeetingRoom.objects.filter(id=meeting_room).first()
        if meeting_room:
            if not _room:
                raise serializers.ValidationError({
                    'meeting_room': ['Invalid Meeting Room.']
                })
            elif self.instance:
                _prev_room = self.instance.room.meeting_room if self.instance.room \
                    else None

                if not _prev_room == _room and not _room.get_available(
                        start_at=start_at, end_at=end_at):
                    raise serializers.ValidationError({
                        'meeting_room': [
                            f'Meeting Room for {start_at} - {end_at}'
                            f' is not available.'
                        ]
                    })
            else:
                if not _room.get_available(start_at=start_at, end_at=end_at):
                    raise serializers.ValidationError({
                        'meeting_room': [
                            f'Meeting Room for {start_at} - {end_at}'
                            f' is not available.'
                        ]
                    })

        if (start_at and end_at) and start_at >= end_at:
            raise serializers.ValidationError(
                {'end_at': 'Should be in greater than Start Date'})
        rule = attrs.get('repeat_rule')
        if rule:
            rule_dict = {i.split('=')[0].lower(): i.split('=')[1] for i in
                         rule.split(';')}
            if rule_dict.get('until'):
                _until = parse(rule_dict.get('until'))
                if _until.date() < start_at.date():
                    raise serializers.ValidationError(
                        {
                            'repeat_rule': 'Rule end date should be greater '
                                           'than Event start date'
                        }
                    )

        if attrs.get('event_location') == OUTSIDE and not attrs.get('location'):
            raise serializers.ValidationError({
                'location': ['Outside location is mandatory.']
            })

        eventdetail = attrs.get('eventdetail')
        notification_times = getattr(eventdetail, 'notification_time', None)

        if attrs.get('event_category') == MEETING:
            _ = attrs.pop('members_can_modify', None)
            _ = attrs.pop('members_can_invite', None)
            attrs.update({
                'members_can_see_guest': True
            })
            if not eventdetail:
                raise serializers.ValidationError({
                    'eventdetail': ['Insufficient eventdetail detail. Time Keeper, '
                                    'Minuter, Meeting Room,and Agenda are some of'
                                    ' the fields to be added.']
                })
            if not isinstance(notification_times, list):
                notification_times = [notification_times]
            for time in notification_times:
                duration = attrs.get('start_at') - timezone.now()
                if time and timedelta(minutes=time) > duration:
                    raise serializers.ValidationError({
                        'notification_time': ['Notification time can not be set'
                                              ' after eventdetail start time.']
                    })
            agendas = eventdetail.get('agenda', None)
            if isinstance(agendas, list):
                for agenda in agendas:
                    if len(agenda) > 2000:
                        raise serializers.ValidationError({
                            'agenda': 'Agenda must be less then 2000 characters.'
                        })
        if eventdetail:
            event_members = attrs.get('members')
            time_keeper = eventdetail.get('time_keeper')
            if time_keeper and time_keeper == user.id:
                raise serializers.ValidationError({
                    'time_keeper': 'Meeting organizer cannot '
                                   'be assigned as time keeper.'
                })

            if time_keeper and not event_members:
                raise serializers.ValidationError({
                    'members': ['Time Keeper must be member of eventdetail']
                })

            if event_members and time_keeper and not time_keeper in event_members:
                raise serializers.ValidationError({
                    'time_keeper': 'Time Keeper must be member of the eventdetail.'
                })

            minuter = eventdetail.get('minuter')
            if minuter and minuter == user.id:
                raise serializers.ValidationError({
                    'minuter': 'Meeting organizer cannot '
                               'be assigned as minuter.'
                })
            if event_members and minuter and not minuter in event_members:
                raise serializers.ValidationError({
                    'minuter': 'Minuter must me member of the meeting.'
                })

        return attrs

    def get_members(self, obj):
        data = {'data': [], '_condition_status': 'No Permission',
                'members_count': 0}
        if self.instance and self.request:
            def _check_permission():
                if obj.created_by == self.request.user or (
                        obj.event_type == PUBLIC and obj.members_can_see_guest):
                    return True

                # if obj.event_members.filter(user=self.request.user).exists()
                # and obj.members_can_see_guest:
                def _is_member():
                    return self.request.user.id in \
                           [x.user.id for x in obj._prefetched_members] \
                        if hasattr(obj,
                                   '_prefetched_members') else \
                        obj.event_members.filter(
                            user=self.request.user
                        ).exists()

                def _is_hr():
                    organization = self.context.get('org')
                    return self.request.query_params.get('as', None) == 'hr' \
                           and validate_permissions(
                        self.request.user.get_hrs_permissions(organization),
                        EVENT_PERMISSION
                    )

                if (_is_member() and obj.members_can_see_guest) or _is_hr():
                    return True
                return False

            is_valid = _check_permission()

            if is_valid:
                members = obj._prefetched_members if \
                    hasattr(obj,
                            '_prefetched_members') else \
                    obj.event_members.select_related(
                        'user', 'user__detail', 'user__detail__job_title')
                ser = EventMembersSerializer(members, read_only=True,
                                             many=True, context=self.context,
                                             fields=(
                                                 'user', 'invitation_status'))
                data.update({'data': ser.data,
                             'members_count': len(obj._prefetched_members)
                             if hasattr(obj, '_prefetched_members')
                             else obj.event_members.count(),
                             '_condition_status': 'Success'})
        return data

    def get_my_event_status(self, obj):
        m_obj = list(filter(lambda x: x.user == self.request.user,
                            obj._prefetched_members)) if \
            hasattr(obj, '_prefetched_members') else \
            obj.event_members.filter(
                user=self.request.user).first()
        if m_obj:
            m_obj = m_obj[0] if isinstance(m_obj, list) else m_obj
            ser = EventMembersSerializer(m_obj, read_only=True,
                                         context=self.context,
                                         fields=('invitation_status',))
            return ser.data.get('invitation_status', None)
        return None

    def create(self, validated_data):
        members = validated_data.pop('members', None)
        eventdetail = validated_data.pop('eventdetail', None)
        room = validated_data.pop('meeting_room', None)
        if validated_data.get('event_location') == INSIDE:
            meeting_room = MeetingRoomStatus.objects.create(
                meeting_room_id=room,
                booked_from=validated_data.get('start_at'),
                booked_to=validated_data.get('end_at')
            )
            validated_data.update({
                'room': meeting_room
            })
        event = super().create(validated_data)
        self.fields['featured_image'] = serializers.CharField()
        self.fields['members'] = serializers.SerializerMethodField(
            read_only=True)
        self.create_members(event, members)
        self.create_meeting(event_instance=event, _meeting=eventdetail,
                                members=members)
        if event.repeat_rule:
            create_recurring_events(event)
        return event

    def update(self, instance, validated_data):
        members = validated_data.pop('members', None)

        # if validated data has other than members, than event details must have been changed
        updated_other_than_members = bool(validated_data)

        # placed here but not at last because we only want to send to old members,
        # new ones will get invitation email
        if updated_other_than_members:
            recipients = []
            for member in instance.event_members.all():
                if email.can_send_email(member.user, EVENT_UPDATED_EMAIL):
                    recipients.append(member.user.email)

            if recipients:
                subject = f"Event Update"
                message = f"Event {instance.title} has been updated."
                email.send_notification_email(
                    recipients=recipients,
                    subject=subject,
                    notification_text=message
                )

        eventdetail = validated_data.pop('eventdetail', None)
        room = validated_data.pop('meeting_room', None)

        self.create_members(instance, members)
        self.fields['members'] = serializers.SerializerMethodField(
            read_only=True)
        if (instance.event_location == INSIDE and validated_data.get(
                'event_location') == OUTSIDE):
            instance.room.delete()
            instance.room = None
            instance.save()

        created_instance = super().update(instance, validated_data)
        if room:
            meeting_room = self._update_meeting_room(
                instance=instance,
                created_instance=created_instance,
                room=room
            )

            created_instance.room = meeting_room
            created_instance.save()
        self.create_meeting(
            event_instance=instance,
            _meeting=eventdetail,
            members=members
        )
        return created_instance

    def _update_meeting_room(self, instance, created_instance, room):
        _pre_is_inside = (instance.event_location == INSIDE)
        _now_is_inside = (created_instance.event_location == INSIDE)
        _pre_room_id = instance.room_id
        _pre_room = instance.room
        if _now_is_inside:
            if not _pre_is_inside:
                booked_room = MeetingRoomStatus.objects.create(
                    meeting_room_id=room,
                    booked_from=created_instance.start_at,
                    booked_to=created_instance.end_at
                )
            else:
                is_valid_room = self._validate_room(
                    event=created_instance,
                    room=room,
                    prev_room=_pre_room
                )
                if not is_valid_room:
                    if _pre_room:
                        MeetingRoomStatus.objects.get(
                            id=_pre_room_id).delete()
                    booked_room = MeetingRoomStatus.objects.create(
                        meeting_room_id=room,
                        booked_from=created_instance.start_at,
                        booked_to=created_instance.end_at
                    )
                else:
                    booked_room = _pre_room
            return booked_room
        elif _pre_is_inside and not _now_is_inside:
            MeetingRoomStatus.objects.get(id=_pre_room_id).delete()
            return None

    @staticmethod
    def _validate_room(event, room, prev_room):
        if not prev_room or not (room == prev_room.meeting_room.id
                                 and event.start_at == prev_room.booked_from
                                 and event.end_at == prev_room.booked_to):
            return False
        return True

    def create_members(self, event_instance, members):
        if members is None:
            return
        if not members:
            if event_instance.created_by == self.request.user:
                past_states = set(
                    event_instance.event_members.all().values_list('user_id',
                                                                   flat=True)
                )
                event_instance.event_members.all().delete()
                self.delete_notifications(event_instance, past_states)
        else:
            past_states = set(
                event_instance.event_members.all().values_list('user_id',
                                                               flat=True))
            present_state = set(id for id in members)
            _delete_list = list(past_states - present_state)
            if past_states != present_state:
                if _delete_list:
                    if event_instance.created_by == self.request.user:
                        _ = event_instance.event_members.filter(
                            user_id__in=_delete_list).delete()
                        self.delete_notifications(event_instance, _delete_list)
                for user_id in members:
                    member, created = \
                        event_instance.event_members.get_or_create(
                            user_id=user_id)
                    if created:
                        self.send_invitation_notification(member)

    def create_meeting(self, event_instance, _meeting, members):
        if _meeting is None:
            meeting = getattr(event_instance, 'eventdetail', None)
            created = None
        else:
            agendas = _meeting.pop('agenda', None)
            _time_keeper = event_instance.event_members.filter(
                user_id=_meeting.get('time_keeper')).first() if _meeting.get('time_keeper') else None
            _minuter = event_instance.event_members.filter(
                user_id=_meeting.get('minuter')).first() if _meeting.get('minuter') else None
            times = _meeting.pop('notification_time', None)
            _data = {
                'time_keeper': _time_keeper,
                'minuter': _minuter
            }
            meeting, created = EventDetail.objects.update_or_create(
                event=event_instance,
                defaults=_data
            )
            if agendas:
                meeting_agenda = [MeetingAgenda(meeting=meeting, title=agenda)
                                  for agenda in agendas]
                MeetingAgenda.objects.bulk_create(meeting_agenda)

            if isinstance(times, list):
                notifications = [MeetingNotification(meeting=meeting, time=time)
                                 for time in times]
                MeetingNotification.objects.bulk_create(notifications)
            elif isinstance(times, int):
                MeetingNotification.objects.create(meeting=meeting, time=times)
        if meeting:
            self._generate_meeting_attendance(
                instance=meeting,
                members=members,
                _meeting=_meeting,
                created=created
            )
        return meeting

    @staticmethod
    def _calculate_position(creator, time_keeper, minuter, user):
        if user == creator:
            return MEETING_ORGANIZER
        elif user == time_keeper and user == minuter:
            return TIME_KEEPER_AND_MINUTER
        elif user == time_keeper:
            return TIME_KEEPER
        elif user == minuter:
            return MINUTER
        else:
            return MEMBER

    def _generate_meeting_attendance(self, instance, members, _meeting,
                                     created=False):

        time_keeper = _meeting.get('time_keeper') if _meeting else \
            instance.time_keeper.user_id if getattr(instance, 'time_keeper', None) else None
        minuter = _meeting.get('minuter') if _meeting else \
            instance.minuter.user_id if getattr(instance, 'minuter', None) else None
        creator = instance.created_by.id if getattr(instance, 'created_by', None) else None

        if created:
            if members:
                members.append(self.request.user.id)
                user_attendance = [
                    MeetingAttendance(
                        member_id=user_id,
                        meeting=instance,
                        position=self._calculate_position(
                            creator=creator,
                            time_keeper=time_keeper,
                            minuter=minuter,
                            user=user_id
                        )
                    ) for user_id in members]
                MeetingAttendance.objects.bulk_create(user_attendance)
            else:
                MeetingAttendance.objects.create(
                    member=self.request.user,
                    meeting=instance,
                    position=self._calculate_position(
                        creator=creator,
                        time_keeper=time_keeper,
                        minuter=minuter,
                        user=self.request.user.id
                    )
                )
        else:
            if not members:
                MeetingAttendance.objects.filter(
                    meeting=instance
                ).exclude(member=getattr(instance, 'created_by', None)).delete()
            else:
                past_states = set(instance.meeting_attendances.exclude(
                    member=getattr(instance, 'created_by', None)
                ).values_list('member_id', flat=True))
                present_state = set(id for id in members)
                _delete_list = list(past_states - present_state)
                if past_states != present_state:
                    if _delete_list:
                        _ = instance.meeting_attendances.filter(
                            member_id__in=_delete_list).delete()
                    for user_id in members:
                        member, created = instance.meeting_attendances.get_or_create(
                            member_id=user_id)
                        member.position = self._calculate_position(
                            creator=creator,
                            time_keeper=time_keeper,
                            minuter=minuter,
                            user=user_id
                        )
                        member.save()
                else:
                    attendances = instance.meeting_attendances.all()
                    for attendance in attendances:
                        attendance.position = self._calculate_position(
                            creator=creator,
                            time_keeper=time_keeper,
                            minuter=minuter,
                            user=attendance.member_id
                        )
                        attendance.save()

    def send_invitation_notification(self, member):
        actor = self.request.user
        notification_text = "has invited you to the event " \
                            f"{member.event.title} ."
        notification_url = get_event_frontend_url(member.event)
        add_notification(
            recipient=member.user,
            text=notification_text,
            actor=actor,
            action=member.event,
            url=notification_url,
        )
        if email.can_send_email(member.user, INVITED_TO_EVENT_EMAIL):
            subject = f"Invitation to {member.event.title}"
            message = f"{actor.full_name} {notification_text}"
            email.send_notification_email(
                recipients=[member.user.email],
                notification_text=message,
                subject=subject
            )

    @staticmethod
    def delete_notifications(event, deleted_member_ids):
        # Delete notification related to event if user is kicked out of that
        # event
        content_type = ContentType.objects.get_for_model(event)
        Notification.objects.filter(
            action_content_type=content_type,
            action_object_id=event.id,
            recipient_id__in=deleted_member_ids
        ).delete()

        recipients = []
        for user in USER.objects.filter(id__in=deleted_member_ids):
            if email.can_send_email(user, EVENT_CANCELED_DELETED_EMAIL):
                recipients.append(user.email)

        if recipients:
            email.send_notification_email(
                recipients=recipients,
                notification_text=f"You have been removed from the event {event.title}.",
                subject=f"Removed from the event {event.title}"
            )


class TopLikeSerializer(UserThinSerializer, DynamicFieldsModelSerializer):
    like_count = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = UserThinSerializer.Meta.fields + ['like_count']


class TopCommentSerializer(UserThinSerializer, DynamicFieldsModelSerializer):
    comment_count = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = UserThinSerializer.Meta.fields + ['comment_count']


class EventDetailExportSerializer(serializers.Serializer):
    def get_fields(self):
        fields = super().get_fields()
        fields['event_details'] = serializers.PrimaryKeyRelatedField(
            queryset=EventDetail.objects.all()
        )
        return fields

