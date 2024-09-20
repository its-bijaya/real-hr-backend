from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.conf import settings
from rest_framework import serializers

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.organization.api.v1.serializers.organization import OrganizationAppearanceSerializer
from irhrs.organization.models import Organization, OrganizationAppearance, UserOrganization
from irhrs.permission.api.v1.serializers.groups import UserGroupSerializer
from irhrs.permission.api.v1.serializers.hrs_permission import HRSPermissionSerializer
from irhrs.permission.models import HRSPermission
from irhrs.permission.models.hrs_permisssion import OrganizationGroup
from irhrs.users.api.v1.serializers.thin_serializers import UserThumbnailSerializer, \
    OrganizationThinSerializer

User = get_user_model()


def clear_permission_cache():
    for redis_key in cache.keys('permission_cache_*'):
        cache.delete(redis_key)


class OrganizationCreateSerializer(DynamicFieldsModelSerializer):
    appearance = OrganizationAppearanceSerializer(
        fields=('logo',)
    )
    admin_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Organization
        fields = ["id", "name", "abbreviation", "about", "slug",
                  "ownership", "appearance", "admin_count"]
        read_only_fields = ['slug']

    def validate(self, attrs):
        if Organization.objects.all().count() >= settings.MAX_ORGANIZATION_COUNT:
            raise serializers.ValidationError(
                f"You have reached assigned limit of {settings.MAX_ORGANIZATION_COUNT}."
            )
        return attrs

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == 'get':
            fields['appearance'] = OrganizationAppearanceSerializer(
                fields=['primary_color', 'secondary_color', 'header_logo',
                        'logo', 'background_image']
            )
        return fields

    def create(self, validated_data):
        appearance = validated_data.pop('appearance')
        validated_data['contacts'] = {}
        instance = super().create(validated_data)
        if appearance:
            OrganizationAppearance.objects.create(
                organization=instance, **appearance)
        return instance


class OrganizationUserSerializer(serializers.Serializer):
    users = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all().current(),
        many=True
    )
    organization = OrganizationThinSerializer(read_only=True)
    user_count = serializers.IntegerField(read_only=True)

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if request and request.method.lower() == 'get':
            fields['users'] = UserThumbnailSerializer(many=True)
        return fields

    def create(self, validated_data):
        organization = self.context['organization']
        users = validated_data.get('users')

        user_of_the_organization = UserOrganization.objects.filter(
            organization=organization
        )
        existing_from_list = user_of_the_organization.filter(user__in=users)

        existing_from_list.update(can_switch=True)
        user_of_the_organization.exclude(
            user__in=users).update(can_switch=False)

        user_ids_set = set(map(lambda x: x.id, users))
        new_users = user_ids_set - \
            set(existing_from_list.values_list('user', flat=True))

        new_user_organization = list()
        for user in new_users:
            new_user_organization.append(
                UserOrganization(
                    user_id=user,
                    organization=organization,
                    can_switch=True
                )
            )

        if new_user_organization:
            UserOrganization.objects.bulk_create(new_user_organization)
        clear_permission_cache()
        return organization


# class OrganizationPermissionSerializer(serializers.Serializer):
class OrganizationPermissionSerializer(DynamicFieldsModelSerializer):
    permissions = serializers.PrimaryKeyRelatedField(
        queryset=HRSPermission.objects.all(),
        many=True
    )
    permissions_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = OrganizationGroup
        fields = ['group', 'permissions', 'permissions_count']

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if request and request.method.lower() == 'get':
            fields['permissions'] = HRSPermissionSerializer(many=True)
            fields['group'] = UserGroupSerializer(fields=['id', 'name'])
        return fields

    def create(self, validated_data):
        organization = self.context.get('organization')
        group = validated_data.get('group')
        instance, created = OrganizationGroup.objects.get_or_create(
            organization=organization,
            group=group
        )
        permissions = validated_data.get('permissions')

        # following code is used to filter out organization specific permission
        # from non organization specific.

        if organization:
            fil = dict(organization_specific=False)
        else:
            fil = dict(organization_specific=True)
        permissions_to_be_filter = HRSPermission.objects.filter(**fil)

        if created:
            instance.permissions.set(permissions)
        else:
            old_permissions = instance.permissions.all()
            deleted_permissions = set(old_permissions) - set(permissions)
            new_permissions = set(permissions) - deleted_permissions
            new_permissions = new_permissions - set(permissions_to_be_filter)

            if deleted_permissions:
                instance.permissions.remove(*deleted_permissions)
            instance.permissions.set(new_permissions)
        clear_permission_cache()
        return instance
