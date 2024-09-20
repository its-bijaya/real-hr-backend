from django.contrib.auth.models import Group
from django.db.models import Count
from rest_framework.viewsets import ModelViewSet

from irhrs.core.utils.common import validate_permissions
from irhrs.permission.api.v1.serializers.groups import UserGroupSerializer
from irhrs.permission.api.v1.serializers.organization import clear_permission_cache
from irhrs.permission.constants.groups import ADMIN
from irhrs.permission.constants.permissions import HRIS_ON_BOARDING_PERMISSION, AUTH_PERMISSION
from irhrs.permission.permission_classes import GroupPermission


class UserGroupViewSet(ModelViewSet):
    """
    list:

    List of user groups and their respective permissions


    create:

    Create user groups

        data = {
            "name": "group name",
            "hrs_permissions": [permission1_id, permission2_id, ...],
            "user_set": [user1_id, user2_id, ...]
        }

    update:

    Update group details

    See create docs for fields ....

    partial_update:

    Partial update for group details

    See create docs for fields
    """

    # do not allow to change admin permissions, admin should always get all the
    # permissions
    queryset = Group.objects.all().exclude(name=ADMIN)
    serializer_class = UserGroupSerializer
    permission_classes = [GroupPermission]

    def has_user_permission(self):
        user = self.request.user
        # guess which organization granted user to access this page.
        if validate_permissions(
            user.get_hrs_permissions(user.switchable_organizations_pks),
            HRIS_ON_BOARDING_PERMISSION
        ):
            return True
        return False

    def get_serializer(self, *args, **kwargs):
        if not validate_permissions(
            self.request.user.get_hrs_permissions(),
            AUTH_PERMISSION
        ) or self.action in ['list', 'create']:
            kwargs.update({
                'exclude_fields': ['user_set']
            })
        return super().get_serializer(*args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.annotate(user_count=Count('user'))

    def update(self, request, *args, **kwargs):
        resp = super().update(request, *args, **kwargs)
        clear_permission_cache()
        return resp
