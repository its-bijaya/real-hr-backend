from django.db.models import Exists, OuterRef
from rest_framework import serializers
from rest_framework.serializers import ValidationError

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils.common import get_complete_url, validate_permissions
from irhrs.event.api.v1.serializers.event import EventSerializer
from irhrs.event.constants import MEETING_DOCUMENT_MAX_UPLOAD_SIZE, PUBLIC
from irhrs.event.models import MeetingDocument, EventDetail, MeetingAgenda, \
    MeetingAttendance, AgendaComment, MeetingNotification, AgendaTask, \
    MeetingAcknowledgeRecord
from irhrs.organization.api.v1.serializers.meeting_room import \
    MeetingRoomStatusSerializer
from irhrs.permission.constants.permissions import EVENT_PERMISSION
from irhrs.task.api.v1.serializers.task import TaskSerializer
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer


class MeetingDocumentSerializer(DynamicFieldsModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = MeetingDocument
        fields = ['id', 'document', 'caption', 'url']

    def create(self, validated_data):
        validated_data.update({'meeting': self.context.get('meeting')})
        return super().create(validated_data)

    def validate(self, attrs):
        meeting_obj = self.context['meeting']
        user = self.context['request'].user

        if not (meeting_obj.created_by == user or
                meeting_obj.minuter == user):
            raise ValidationError({
                'detail': 'You are not authorized to perform this action'
            })
        return attrs

    @staticmethod
    def validate_document(document):
        if document.size > MEETING_DOCUMENT_MAX_UPLOAD_SIZE:
            raise serializers.ValidationError(
                f'File Size Should not Exceed {MEETING_DOCUMENT_MAX_UPLOAD_SIZE / (1024 * 1024)} MB')
        return document

    @staticmethod
    def get_url(obj):
        return get_complete_url(obj.document.url)


class AgendaCommentSerializer(DynamicFieldsModelSerializer):
    user = UserThinSerializer(
        source='commented_by',
        read_only=True,
        fields=(
            'id', 'full_name',
            'profile_picture',
            'is_online',
            'is_current', 'organization',
        )
    )

    class Meta:
        model = AgendaComment
        fields = ['id', 'content', 'user', 'created_at']
        read_only_field = ['created_at']

    def validate(self, attrs):
        user = self.context['request'].user
        agenda = self.context.get('agenda')
        member = agenda.meeting.event.event_members.filter(
            user=user)
        if not (member.exists() or user == agenda.meeting.created_by):
            raise ValidationError({'commented_by': 'Must be member of meeting'
                                                   ' to comment on agenda'})
        attrs.update({
            'agenda': agenda,
            'commented_by': user
        })
        return attrs


class AgendaSerializer(DynamicFieldsModelSerializer):
    comment = serializers.SerializerMethodField()
    agenda_task = serializers.SerializerMethodField()

    class Meta:
        model = MeetingAgenda
        fields = ['id', 'title', 'discussion', 'decision', 'discussed',
                  'comment', 'agenda_task']
        read_only_fields = ['comment']

    def get_comment(self, obj):
        return AgendaCommentSerializer(obj.comments,
                                       many=True,
                                       fields=['id',
                                               'content',
                                               'user',
                                               'created_at'],
                                       context=self.context
                                       ).data

    def get_agenda_task(self, obj):
        return MeetingAgendaTaskSerializer(
            obj.agenda_tasks,
            many=True,
            fields=['id', 'task'],
            context=self.context
        ).data


class MeetingSerializer(DynamicFieldsModelSerializer):
    agenda = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    notification_time = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()
    acknowledged = serializers.SerializerMethodField()

    class Meta:
        model = EventDetail
        _MODEL_FIELD = ['id', 'time_keeper', 'minuter',
                        'other_information', 'prepared', ]
        _OTHER_FIELD = ['notification_time', 'event', 'agenda',
                        'role', 'members', 'documents','acknowledged']
        fields = _MODEL_FIELD + _OTHER_FIELD

        read_only_field = ['time_keeper',
                           'minuter']

    def get_agenda(self, obj):
        fields = ['id', 'title']
        if obj.prepared or obj.minuter == self.request.user or obj.created_by == self.request.user:
            fields += ['discussion', 'decision', 'discussed', 'comment',
                       'agenda_task']
        return AgendaSerializer(obj.meeting_agendas.all(), fields=fields,
                                many=True,
                                context=self.context).data

    def get_fields(self):
        fields = super().get_fields()
        if self.context['request'].method.lower() == 'get':
            fields['time_keeper'] = serializers.SerializerMethodField()
            fields['minuter'] = serializers.SerializerMethodField()
            fields['event'] = EventSerializer(
                fields=[
                    'id', 'title', 'description', 'event_type', 'start_at',
                    'end_at', 'event_category', 'repeat_rule',
                    'my_event_status', 'members', 'meeting_room',
                    'event_location', 'location'
                ],
                context=self.context
            )
        return fields

    def get_documents(self, obj):
        return MeetingDocumentSerializer(
            obj.documents,
            many=True,
            fields=['id', 'document', 'caption', 'url'],
            context=self.context
        ).data

    @staticmethod
    def get_time_keeper(obj):
        return obj.time_keeper.user.id if obj.time_keeper else None

    @staticmethod
    def get_minuter(obj):
        return obj.minuter.user.id if obj.minuter else None

    def get_notification_time(self, obj):
        return MeetingNotificationSerializer(
            obj.notifications.all(),
            fields=['id', 'time'],
            many=True,
            context=self.context
        ).data

    def get_role(self, obj):
        member = obj.meeting_attendances.filter(
            member=self.context['request'].user
        ).first()
        if member:
            return member.position
        return None

    def get_members(self, obj):
        if self.instance and self.request:
            def _check_permission():
                if obj.event.created_by == self.request.user or (
                    obj.event.event_type == PUBLIC and obj.event.members_can_see_guest
                ):
                    return True

                def _is_member():
                    return obj.event.event_members.filter(
                            user=self.request.user
                        ).exists()

                def _is_hr():
                    organization = self.context.get('org')
                    return self.request.query_params.get('as', None) == 'hr' \
                           and validate_permissions(
                        self.request.user.get_hrs_permissions(organization),
                        EVENT_PERMISSION
                    )

                if (_is_member() and obj.event.members_can_see_guest) or _is_hr():
                    return True
                return False

        if not _check_permission():
            return []

        return MeetingAttendanceSerializer(
            obj.meeting_attendances.annotate(
                acknowledged=Exists(
                    MeetingAcknowledgeRecord.objects.filter(
                        member_id=OuterRef('member_id'),
                        meeting_id=OuterRef('meeting_id')
                    )
                )
            ).select_related(
                'member', 'member__detail', 'member__detail__job_title',
                'member__detail__division', 'meeting',
                'meeting__time_keeper__user', 'meeting__minuter__user'
            ).order_by(
                'member__first_name',
                'member__middle_name',
                'member__last_name'
            ),
            many=True,
            fields=['id', 'user', 'arrival_time', 'remarks',
                    'position', 'acknowledged'],
            context=self.context
        ).data

    def get_acknowledged(self, obj):
        return obj.acknowledge_records.filter(
            member=self.context['request'].user
        ).exists()


class MeetingAttendanceSerializer(DynamicFieldsModelSerializer):
    acknowledged = serializers.ReadOnlyField()

    class Meta:
        model = MeetingAttendance
        fields = ['id', 'member', 'arrival_time', 'position', 'remarks',
                  'acknowledged']
        read_only_fields = ['status', 'acknowledged']
        extra_kwargs = {
            'members': {'write_only': True}
        }

    def get_fields(self):
        fields = super().get_fields()
        if self.context['request'].method.lower() == 'get':
            fields['user'] = UserThinSerializer(
                source='member',
                fields=[
                    'id', 'full_name',
                    'profile_picture', 'cover_picture',
                    'job_title', 'is_online',
                    'last_online', 'is_current', 'organization',
                ]
            )
        return fields


class MeetingNotificationSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = MeetingNotification
        fields = ['id', 'time']


class MeetingAgendaTaskSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = AgendaTask
        fields = ['id', 'agenda', 'task']
        read_only_fields = 'agenda',

    def get_fields(self):
        fields = super().get_fields()
        if self.context.get('request').method.lower() == 'get':
            fields['agenda'] = AgendaSerializer(
                fields=['id', 'title'],
                context=self.context
            )
            fields['task'] = TaskSerializer(
                fields=[
                    'title', 'priority', 'deadline', 'status',
                    'id'
                ],
                context=self.context
            )
        return fields

    def create(self, validated_data):
        validated_data['agenda'] = self.context.get('agenda')
        return super().create(validated_data)

