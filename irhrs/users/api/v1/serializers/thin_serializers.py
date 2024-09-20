from rest_framework.fields import SerializerMethodField, ReadOnlyField, empty
from django.db.models import Q

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer, \
    DummySerializer
from irhrs.core.utils.common import get_today
from irhrs.organization.api.v1.serializers.branch import \
    OrganizationBranchSerializer
from irhrs.organization.api.v1.serializers.division import \
    OrganizationDivisionSerializer
from irhrs.organization.models import Organization
from ....models import User


class OrganizationThinSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Organization
        fields = (
            'name', 'abbreviation', 'slug'
        )


class UserThinSerializer(DynamicFieldsModelSerializer):
    """
    A thin Serializer for User that displays username, and their display picture
    """
    profile_picture = ReadOnlyField(
        source='profile_picture_thumb', allow_null=True
    )
    cover_picture = ReadOnlyField(
        source='cover_picture_thumb', allow_null=True
    )

    division = OrganizationDivisionSerializer(source='detail.division',
                                              fields=['name',
                                                      'slug'])
    job_title = SerializerMethodField()
    employee_level = SerializerMethodField()
    organization = OrganizationThinSerializer(source='detail.organization')
    is_current = SerializerMethodField()
    class Meta:
        model = User
        fields = [
            'id',
            'full_name',
            'profile_picture',
            'cover_picture',
            'division',
            'job_title',
            'email',
            'employee_level',
            'organization',
            'is_online',
            'last_online',
            'is_audit_user',
            'is_current',
        ]
        read_only_fields = ('is_online', 'last_online',)

    @staticmethod
    def get_job_title(instance):
        detail = instance.detail if hasattr(instance, 'detail') else None
        return detail.job_title.title \
            if detail and detail.job_title else 'Job Title N/A'

    @staticmethod
    def get_employee_level(instance):
        detail = instance.detail if hasattr(instance, 'detail') else None
        return (
            detail.employment_level.title
            if detail and detail.employment_level
            else 'Employee Level N/A'
        )

    @staticmethod
    def get_org(instance):
        detail = instance.detail if hasattr(instance, 'detail') else None
        return (
            detail.organization.abbreviation
            if detail and detail.organization
            else 'Employee Level N/A'
        )
    @staticmethod
    def get_is_current(instance):
        return instance.user_experiences.filter(
            Q(end_date__gte=get_today())|
            Q(end_date__isnull=True),
            is_current=True
        ).exists()


class UserSignatureSerializer(UserThinSerializer):
    signature = ReadOnlyField(
        source='signature_url', allow_null=True
    )

    class Meta(UserThinSerializer.Meta):
        fields = (
            'id', 'full_name', 'profile_picture', 'cover_picture', 'organization', 'is_current',
            'is_current', 'job_title', 'is_online', 'last_online', 'signature'
        )


class UserBranchThinSerializer(UserThinSerializer):
    branch = OrganizationBranchSerializer(source='detail.branch', fields=['name', 'slug'])

    class Meta(UserThinSerializer.Meta):
        fields = UserThinSerializer.Meta.fields + ['branch']


class UserThumbnailSerializer(UserThinSerializer):

    class Meta(UserThinSerializer.Meta):
        fields = (
            'id', 'full_name', 'profile_picture', 'cover_picture',
            'job_title', 'is_online', 'last_online', 'organization', 'is_current',
        )


class UserSupervisorDivisionSerializer(UserThinSerializer):
    supervisor = UserThinSerializer(
        read_only=True, source='first_level_supervisor'
    )
    division = OrganizationDivisionSerializer(
        fields=['name', 'slug'],
        source='detail.division',
        read_only=True
    )
    branch = OrganizationBranchSerializer(
        fields=['name', 'slug'],
        source='detail.branch',
        read_only=True
    )

    class Meta(UserThinSerializer.Meta):
        fields = UserThinSerializer.Meta.fields + [
            'username',
            'supervisor',
            'division',
            'branch'
        ]


class AuthUserThinSerializer(DynamicFieldsModelSerializer):
    profile_picture = ReadOnlyField(source='profile_picture_thumb')
    division = ReadOnlyField(source='detail.division.name', allow_null=True)
    organization = ReadOnlyField(source='detail.organization.name',
                                 allow_null=True)
    employee_code = ReadOnlyField(source='detail.code', allow_null=True)
    employee_level = ReadOnlyField(source='detail.employment_level.title', allow_null=True)
    organization_slug = ReadOnlyField(source='detail.organization.slug', allow_null=True)

    job_title = SerializerMethodField()
    is_current = SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'full_name', 'profile_picture', 'division', 'employee_code',
                  'employee_level', 'organization', 'is_online', 'last_online',
                  'organization_slug', 'job_title', 'is_current', 'username']
        read_only_fields = ('is_online', 'last_online',)

    def get_job_title(self, instance):
        detail = instance.detail if hasattr(instance, 'detail') else None
        return detail.job_title.title \
            if detail and detail.job_title else 'Job Title N/A'

    def get_is_current(self, instance):
        return instance.user_experiences.filter(Q(is_current=True) & Q(
            Q(end_date__isnull=True) | Q(end_date__gte=get_today()))).exists()


class ExtendedAuthUserThinSerializer(AuthUserThinSerializer):
    class Meta(AuthUserThinSerializer.Meta):
        fields = AuthUserThinSerializer.Meta.fields + ['username']


class UserThickSerializer(UserThinSerializer):
    class Meta(UserThinSerializer.Meta):
        fields = UserThinSerializer.Meta.fields + ['username']


class UserFieldThinSerializer(DummySerializer):
    """
    Similar to UserThinSerializer,
    Serializes User inside a user field.
    """
    user = SerializerMethodField()

    def __init__(self, instance=None, data=empty, **kwargs):
        self.user_fields = kwargs.pop(
            'user_fields',
            UserThickSerializer.Meta.fields
        )
        super().__init__(instance, data, **kwargs)

    def get_user(self, instance):
        return UserThickSerializer(
            instance=instance,
            fields=self.user_fields
        ).data

class UserBranchThickSerializer(UserThickSerializer):
    branch = OrganizationBranchSerializer(source='detail.branch', fields=['name', 'slug'])

    class Meta(UserThickSerializer.Meta):
        fields = UserThickSerializer.Meta.fields + ['branch']
