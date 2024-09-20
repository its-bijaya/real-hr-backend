from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import ReadOnlyField

from irhrs.common.api.serializers.common import EquipmentCategorySerializer
from irhrs.common.models.commons import EquipmentCategory
from irhrs.core.utils.common import get_upload_path, get_complete_url, get_today
from irhrs.core.constants.organization import DAMAGED, USED, DIVISION_BRANCH, \
    MEETING_ROOM, USER, IDLE
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils.common import _validate_uniqueness
from irhrs.core.validators import validate_image_size
from irhrs.organization.api.v1.serializers.branch import \
    OrganizationBranchSerializer
from irhrs.organization.api.v1.serializers.division import \
    OrganizationDivisionSerializer
from irhrs.organization.api.v1.serializers.meeting_room import MeetingRoomSerializer
from irhrs.organization.models import (EquipmentAssignedTo,
                                       OrganizationDivision, OrganizationBranch)
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from .common_org_serializer import OrganizationSerializerMixin
from ....models import OrganizationEquipment


class OrganizationEquipmentSerializer(OrganizationSerializerMixin):
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=EquipmentCategory.objects.all()
    )
    equipment_picture_thumbnail = ReadOnlyField(
        source='equipment_picture_thumb',
        allow_null=True)
    assigned_detail = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta(OrganizationSerializerMixin.Meta):
        model = OrganizationEquipment
        fields = (
            'id', 'category', 'name', 'brand_name', 'code', 'amount',
            'purchased_date', 'service_order', 'bill_number',
            'reference_number', 'assigned_to', 'status',
            'specifications', 'equipment_picture',
            'equipment_picture_thumbnail', 'remark', 'slug',
            'assigned_detail',
        )
        read_only_fields = ('slug', 'organization')
        extra_kwargs = {
            'code': {
                'allow_blank': False
            },
            'equipment_picture': {
                'required': False
            }
        }

    def get_status(self, obj):
        if obj.is_damaged:
            return DAMAGED
        if obj.is_currently_assigned:
            return USED
        return IDLE

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if request and request.method.lower() == "get":
            fields['category'] = EquipmentCategorySerializer(
                fields=['name', 'type', 'slug'],
                read_only=True
            )
        return fields

    def get_assigned_detail(self, obj):
        if obj.is_currently_assigned:
            fields = ['assigned_date']
            if obj.assigned_to == USER:
                fields.append('user')
            elif obj.assigned_to == MEETING_ROOM:
                fields.append('meeting_room')
            else:
                fields = fields + ['branch', 'division']
            return EquipmentAssignedToSerializer(
                obj.assignments.first() if obj.assignments.first() else None,
                fields=fields,
                context=self.context
            ).data

        return None

    def validate_code(self, code):
        organization = self.context.get('organization')
        if _validate_uniqueness(
                self=self,
                queryset=organization.equipments.all(),
                fil={'code__iexact': code}
        ):
            raise ValidationError(
                "Equipment with this code already exists."
            )
        return code

    def update(self, instance, validated_data):
        if self.request.method == 'PATCH':
            # negate the value on each call to this endpoint
            instance.is_damaged = not(instance.is_damaged)
            instance.save()
            return instance
        return super().update(instance, validated_data)

    @staticmethod
    def validate_equipment_picture(picture):
        if picture:
            return validate_image_size(picture)
        return picture

    def validate_assigned_to(self, value):
        _obj = self.instance
        if _obj and not value == _obj.assigned_to:
            if _obj.assignments.filter(released_date__isnull=True).exists():
                raise ValidationError({
                    'assigned_to': 'This equipment has been assigned.'
                })
        return value


class EquipmentAssignedToSerializer(DynamicFieldsModelSerializer):
    division = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=OrganizationDivision.objects.all(),
        required=False,
        allow_null=True)
    branch = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=OrganizationBranch.objects.all(),
        required=False,
        allow_null=True)

    class Meta:
        model = EquipmentAssignedTo
        fields = [
            'id',
            'equipment',
            'user',
            'division',
            'branch',
            'meeting_room',
            'assigned_date',
        ]

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == 'get':
            fields.update({
                'equipment': OrganizationEquipmentSerializer(fields=('id',
                                                                     'name',
                                                                     'category',
                                                                     'code',
                                                                     'status',
                                                                     'slug',
                                                                     'equipment_picture_thumbnail'),
                                                             read_only=True),
                'user': UserThinSerializer(fields=('id',
                                                   'full_name',
                                                   'profile_picture',
                                                   'cover_picture',
                                                   'job_title',
                                                   'is_online',
                                                   'organization',
                                                   'is_current',
                                                   ),
                                           read_only=True),
                'division': OrganizationDivisionSerializer(fields=['name',
                                                                   'slug'],
                                                           read_only=True),
                'branch': OrganizationBranchSerializer(fields=['name',
                                                               'slug'],
                                                       read_only=True),
                'meeting_room': MeetingRoomSerializer(fields=[
                    'name',
                    'slug',
                    'location'],
                    read_only=True, context=self.context),
            })
        return fields

    def validate(self, attrs):
        equipment = attrs.get('equipment')
        user = attrs.get('user')
        division = attrs.get('division')
        branch = attrs.get('branch')
        meeting_room = attrs.get('meeting_room')
        if equipment:
            if user:
                self.validate_assigned_to_user(attrs)
            elif division or branch:
                self.validate_assigned_to_division_branch(attrs)
            elif meeting_room:
                self.validate_assigned_to_meeting_room(attrs)
            else:
                raise ValidationError(
                    {
                        'detail': ["Equipment must be assigned."]
                    }
                )
        return attrs

    def validate_assigned_to_user(self, attrs, ):
        equipment = attrs.get('equipment')
        user = attrs.get('user')
        if not equipment.assigned_to == USER:
            raise ValidationError({
                'user': ['This equipment can '
                         'be assigned to ' + equipment.assigned_to.lower() + ' only']
            })
        if attrs.get('branch') or attrs.get('division') or attrs.get('meeting_room'):
            raise ValidationError(
                {
                    'meeting_room': ["Equipment can assigned to either"
                                     " user or division and branch or meeting room, at once."]
                }
            )
        if not user.detail.organization == self.context.get(
                'organization') \
                and not user.detail.organization == equipment.organization:
            raise ValidationError(
                {
                    'user': ["Equipment from another "
                             "organization cannot be assigned."]
                }
            )

    def validate_assigned_to_meeting_room(self, attrs):
        equipment = attrs.get('equipment')
        meeting_room = attrs.get('meeting_room')
        if not equipment.assigned_to == MEETING_ROOM:
            raise ValidationError({
                'meeting_room': ['This equipment can '
                                 'be assigned to ' + equipment.assigned_to.replace("_", " ").lower() + ' only']
            })
        if attrs.get('branch') or attrs.get('division') or attrs.get('user'):
            raise ValidationError(
                {
                    'meeting_room': ["Equipment can assigned to either "
                                     "user or division and branch or meeting room, at once."]
                }
            )
        if not meeting_room.organization == self.context.get(
                'organization') \
                and not meeting_room.organization == equipment.organization:
            raise ValidationError(
                {
                    'meeting_room': ["Equipment from another "
                                     "organization cannot be assigned."]
                }
            )

    def validate_assigned_to_division_branch(self, attrs):
        equipment = attrs.get('equipment')
        branch = attrs.get('branch')
        division = attrs.get('division')

        if not equipment.assigned_to == DIVISION_BRANCH:
            raise ValidationError({
                'detail': ['This equipment can '
                           'be assigned to ' + equipment.assigned_to.replace("_", " ").lower() + ' only']
            })
        if attrs.get('meeting_room') or attrs.get('user'):
            raise ValidationError(
                {
                    'meeting_room': ["Equipment can assigned to either"
                                     "user or division and branch or meeting room, at once."]
                }
            )
        if division:
            if not division.organization == self.context.get('organization') \
                    and not division.organization == equipment.organization:
                raise ValidationError({
                    'division': ["Equipment from another "
                                 "organization cannot be assigned."]
                })
        if branch:
            if not branch.organization == self.context.get('organization') \
                    and not branch.organization == equipment.organization:
                raise ValidationError({
                    'branch': ["Equipment from another "
                               "organization cannot be assigned."]
                })

    def validate_equipment(self, equipment):
        if not equipment.organization == self.context.get('organization'):
            raise ValidationError(
                {
                    'equipment': ["Equipment from another "
                                  "organization cannot be assigned."]
                }
            )
        if equipment.is_currently_assigned:
            raise ValidationError(
                {
                    'equipment': ["Used equipment cannot be assigned."]
                }
            )

        if equipment.is_damaged:
            raise ValidationError(
                {
                    'equipment': ["Damaged equipment cannot be assigned."]
                }
            )

        return equipment


class EquipmentAssignedToBulkSerializer(serializers.ModelSerializer):
    assignments = EquipmentAssignedToSerializer(many=True)

    class Meta:
        model = EquipmentAssignedTo
        fields = '__all__'

    def create(self, validated_data):
        assignments = validated_data["assignments"]
        assignment_objs = [
            self.Meta.model(**assignment) for assignment in assignments
        ]
        created = self.Meta.model.objects.bulk_create(assignment_objs)
        result = {
            "assignments": created
        }
        return result

    def validate(self, attrs):
        assignments = attrs.get('assignments')
        # validation to prevent duplicate equipments in request data
        seen_equipments = set()
        for assignment in assignments:
            if assignment["equipment"] not in seen_equipments:
                seen_equipments.add(assignment["equipment"])
        if len(seen_equipments) != len(assignments):
            raise ValidationError({
                'equipment': 'Multiple equipments cannot be assigned at '
                f'the same time.'
            })
        return attrs


class EquipmentAssignedToHistorySerializer(DynamicFieldsModelSerializer):
    user = UserThinSerializer(fields=('id',
                                      'full_name',
                                      'profile_picture',
                                      'cover_picture',
                                      'job_title',
                                      'is_online',
                                      'organization',
                                      'is_current',
                                      ),
                              read_only=True)

    class Meta:
        model = EquipmentAssignedTo
        fields = ('id', 'equipment', 'user', 'released_date', 'assigned_date')


class UserEquipmentSerializer(OrganizationEquipmentSerializer):
    def get_assigned_detail(self, obj):
        if obj.is_currently_assigned and obj.assigned_to == USER:
            fields = ['assigned_date']
            return EquipmentAssignedToSerializer(
                obj.assignments.first() if obj.assignments.first() else None,
                fields=fields,
                context=self.context
            ).data
        return None
