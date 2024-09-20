from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.file_import_mixin import BackgroundFileImportMixin
from irhrs.core.mixins.viewset_mixins import OrganizationCommonsMixin, OrganizationMixin
from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.organization.api.v1.permissions import MeetingRoomPermission
from irhrs.organization.api.v1.serializers.meeting_room import MeetingRoomSerializer
from irhrs.organization.models import MeetingRoom, OrganizationBranch
from irhrs.permission.constants.permissions import (ORGANIZATION_PERMISSION,
                                                    ORGANIZATION_SETTINGS_PERMISSION,
                                                    MEETING_ROOM_PERMISSION)


class MeetingRoomViewSet(BackgroundFileImportMixin, OrganizationMixin,
                         OrganizationCommonsMixin, ModelViewSet):
    queryset = MeetingRoom.objects.all()
    serializer_class = MeetingRoomSerializer
    lookup_field = 'slug'
    filter_backends = (SearchFilter, FilterMapBackend, OrderingFilterMap)
    filter_map = {
        'branch': 'branch__slug',
        'location': ('location', 'icontains'),
        'floor': ('floor', 'icontains')
    }
    search_fields = ['name']
    parser_classes = (MultiPartParser, FormParser,)
    permission_classes = [MeetingRoomPermission]
    ordering_fields_map = {
        'name': 'name',
        'branch': 'branch__slug',
        'location': 'location',
        'floor': 'floor',
        'organization': 'organization__slug'
    }
    import_fields = [
        'NAME',
        'BRANCH',
        'LOCATION',
        'FLOOR',
        'AREA',
        'CAPACITY',
        'DESCRIPTION',
    ]
    values = [
        'Meeting Hall 1',
        '',
        'MinBhawan, Kathmandu',
        '1st floor',
        '120 sq. ft.',
        '123',
        'Description about meeting room.'
    ]
    sample_file_name = 'meeting_room'
    background_task_name = 'meeting_room'
    non_mandatory_field_value = {
        'area': '',
        'description': ''
    }

    def get_queryset(self):
        if self.action == 'available_rooms':
            return self.queryset.filter(organization=self.organization)
        return super().get_queryset()

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            kwargs.update({
                'exclude_fields': [
                    'description', 'area', 'capacity',
                    'attachments', 'organization', 'equipments'
                ]
            })
        if self.action != 'available_rooms':
            kwargs.update({
                'exclude_fields': kwargs.get('exclude_fields', []) + [
                    'available'
                ]
            })
        return super().get_serializer(*args, **kwargs)

    @action(methods=['get'], detail=False)
    def available_rooms(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def has_user_permission(self):
        if self.action == 'available_rooms':
            return True
        return validate_permissions(
            self.request.user.get_hrs_permissions(self.get_organization()),
            ORGANIZATION_SETTINGS_PERMISSION,
            MEETING_ROOM_PERMISSION
        )

    def get_queryset_fields_map(self):
        return {
            'branch': OrganizationBranch.objects.filter(
                organization__slug=self.kwargs.get('organization_slug')
            )
        }

    def get_failed_url(self):
        return f'/admin/{self.organization.slug}/organization/settings/meeting-room/?status=failed'

    def get_success_url(self):
        return f'/admin/{self.organization.slug}/organization/settings/meeting-room/?status=success'
