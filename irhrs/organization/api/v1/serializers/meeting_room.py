from django.db.models import Count
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.organization.api.v1.serializers.branch import OrganizationBranchSerializer
from irhrs.organization.api.v1.serializers.common_org_serializer import OrganizationSerializerMixin
from irhrs.organization.api.v1.serializers.organization import OrganizationSerializer
from irhrs.organization.models import (MeetingRoomAttachment, MeetingRoom,
                                       OrganizationBranch, MeetingRoomStatus, EquipmentAssignedTo)


class MeetingRoomAttachmentSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = MeetingRoomAttachment
        fields = ('id', 'image', 'caption',)


class MeetingRoomSerializer(DynamicFieldsModelSerializer):
    equipments = serializers.SerializerMethodField(read_only=True)
    attachments = MeetingRoomAttachmentSerializer(many=True, required=False)
    branch = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=OrganizationBranch.objects.all(),
        required=False,
        allow_null=True)
    available = serializers.SerializerMethodField(read_only=True)

    class Meta(OrganizationSerializerMixin.Meta):
        model = MeetingRoom
        fields = (
            'id', 'branch', 'name', 'description',
            'location', 'floor', 'area', 'capacity', 'attachments',
            'organization', 'slug', 'equipments', 'available'
        )
        read_only_fields = ('slug', 'organization',)

    def get_equipments(self, obj):
        return EquipmentAssignedTo.objects.filter(meeting_room=obj.id).order_by().values(
            'equipment__category').annotate(
            count=Count('id')).values('equipment__category__name', 'count')

    def validate_deleted_attachments(self, deleted_str):
        if not self.instance:
            return None

        attachment_pks = set(self.instance.attachments.all().values_list(
            'pk', flat=True))

        if not deleted_str:
            return []

        import re
        pattern = re.compile(r'((\d+,)+\d+)|\d+')

        if not pattern.match(deleted_str):
            raise serializers.ValidationError('Bad pk values')

        pks = set([int(pk) for pk in deleted_str.split(',')])

        if not pks.issubset(attachment_pks):
            raise serializers.ValidationError('Some of the ids does not exist')
        return pks

    def get_attachments(self, obj):
        return MeetingRoomAttachmentSerializer(
            many=True,
            instance=obj.attachments.order_by('created_at'),
            context=self.context
        ).data

    @staticmethod
    def extract_attachments(request_data):
        attachments = []
        data = dict(request_data)
        for key in data.copy():
            if key.startswith('attachment'):
                image = data.pop(key)
                attachments.append({'image': image[0], 'caption': ''})
        return attachments

    def validate_attachments(self, data):
        request_data = getattr(self.context['request'], 'data', None)
        if request_data:
            request_data = dict(request_data)
            attachments = self.extract_attachments(request_data)
            serialized_attachments = MeetingRoomAttachmentSerializer(data=attachments,
                                                                     many=True)
            attachment_size = 5 * 1024 * 1024
            for image in attachments:
                if image['image'].size > attachment_size:
                    raise serializers.ValidationError(
                        f'Image Size Should not Exceed {attachment_size / (1024 * 1024)} MB')

            if not serialized_attachments.is_valid():
                raise serializers.ValidationError('Invalid attachments.')
            return attachments
        return request_data

    def validate(self, attrs):
        attachments = self.validate_attachments(None)
        if attachments:
            attrs.update({
                'attachments': attachments
            })

        organization = self.context.get('organization')
        branch = attrs.get('branch')
        if branch and not branch.organization == organization:
            raise ValidationError(
                'This branch does not exists.'
            )

        attrs.update({'organization': organization})
        return super().validate(attrs)

    def get_available(self, obj):
        start_at = self.context['request'].GET.get('start_at')
        end_at = self.context['request'].GET.get('end_at')

        return obj.get_available(start_at, end_at)

    def get_fields(self):
        request = self.context.get('request')
        fields = super().get_fields()
        if request.method.lower() == 'get':
            fields.update({
                'branch': OrganizationBranchSerializer(fields=['name',
                                                               'slug'],
                                                       read_only=True),
                'organization': OrganizationSerializer(fields=["name",
                                                               "slug",
                                                               "abbreviation",
                                                               "appearance"],
                                                       read_only=True)

            })
        if request and self.instance and (request.method.upper() in ['PUT', 'PATCH']):
            fields["deleted_attachments"] = serializers.CharField(required=False)
        return fields

    def create(self, validated_data):
        attachments = validated_data.pop('attachments', None)
        meeting_room = super().create(validated_data)

        if attachments:
            for attachment in attachments:
                attachment.update({'meeting_room': meeting_room})
                MeetingRoomAttachment.objects.create(**attachment)
        return meeting_room

    def update(self, instance, validated_data):
        attachments = validated_data.pop('attachments', None)
        deleted_attachments = validated_data.pop('deleted_attachments', [])

        instance = super().update(instance, validated_data)

        if deleted_attachments:
            instance.attachments.filter(id__in=deleted_attachments).delete()

        if attachments:
            for attachment in attachments:
                attachment.update({'meeting_room': instance})
                MeetingRoomAttachment.objects.create(**attachment)

        instance.refresh_from_db()
        return instance


class MeetingRoomStatusSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = MeetingRoomStatus
        fields = ['id', 'booked_from', 'booked_to']

    def get_fields(self):
        fields = super().get_fields()
        if self.context.get('request').method.lower() == 'get':
            fields['room'] = MeetingRoomSerializer(
                source='meeting_room',
                fields=[
                    'id','slug', 'branch', 'name', 'description',
                    'location', 'floor', 'capacity', 'attachments',
                    'organization',
                ],
                context=self.context
            )
        return fields
