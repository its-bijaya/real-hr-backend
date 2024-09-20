from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator

from irhrs.core.constants.user import MALE, FEMALE, OTHER
from irhrs.core.utils.common import get_complete_url
from irhrs.core.validators import validate_title
from .common_org_serializer import OrganizationSerializerMixin
from ....models import OrganizationDivision


class OrganizationDivisionSerializer(OrganizationSerializerMixin):
    extension_number = serializers.CharField(
        required=False,
        max_length=4,
        allow_blank=True,
        allow_null=True  # for patch requests.
    )
    parent = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=OrganizationDivision.objects.all(),
        allow_null=True,
        required=False
    )
    name = serializers.CharField(
        required=True,
        max_length=150,
        validators=[validate_title]
    )
    email = serializers.CharField(
        allow_blank=True,
        max_length=200,
        validators=[
            UniqueValidator(
                queryset=OrganizationDivision.objects.all(),
                lookup='iexact',
                message='This email already exists')
        ]
    )

    class Meta(OrganizationSerializerMixin.Meta):
        model = OrganizationDivision
        fields = ('id', 'organization', 'name', 'description', 'parent', 'head',
                  'extension_number', 'strategies', 'action_plans', 'slug',
                  'email', 'is_archived', 'created_at', 'modified_at')
        read_only_fields = ('slug',)
        extra_kwargs = {
            'name': {
                'allow_null': False,
                'max_length': 150,
            }
        }

    def validate_extension_number(self, ext_number):
        """
        Changing the field because the front end is sending string.
        :param ext_number:
        :return:
        """
        if not ext_number:
            return None
        if not ext_number.isdigit():
            raise ValidationError("A valid integer is required.")

        queryset = OrganizationDivision.objects.filter(extension_number=ext_number)
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)

        if queryset.exists():
            raise ValidationError(f'Extension Number {ext_number} already exists.')

        return int(ext_number)

    def validate_name(self, name):
        organization = self.context.get('organization')
        qs = organization.divisions.filter(name=name)
        if self.instance:
            qs = qs.exclude(name=self.instance.name)
        if qs.exists():
            raise ValidationError("This organization already has "
                                  "division of this name.")
        return name

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')

        if request:
            if request.method == 'GET':
                fields['child_divisions'] = \
                    serializers.SerializerMethodField(
                        read_only=True)
                fields['parent'] = serializers.SerializerMethodField(
                    read_only=True)
                fields['head'] = serializers.SerializerMethodField(
                    read_only=True)
            elif request.method in ['PUT', 'PATCH']:
                if self.instance:
                    fields['parent'] = serializers.SlugRelatedField(
                        slug_field='slug',
                        queryset=OrganizationDivision.objects.exclude(
                            slug=self.instance.slug
                        ),
                        allow_null=True
                    )
        return fields

    @staticmethod
    def get_head(instance):
        # Could not import ThinSerializer due to nested trouble.
        head = getattr(instance, 'head', None)
        if not head:
            return None
        return {
            'full_name': head.full_name,
            'profile_picture': head.profile_picture_thumb,
            'cover_picture': head.cover_picture_thumb,
            'job_title': head.detail.job_title.title if head.detail.job_title else 'N/A',
            'id': head.id
        }

    @staticmethod
    def get_parent(instance):
        return {
            "name": instance.parent.name,
            "slug": instance.parent.slug,
        } if instance.parent else None

    @staticmethod
    def get_child_divisions(instance):
        child_division = []
        # check prefetch
        children = instance.division_child if isinstance(
            instance.division_child, list) else instance.division_child.all()
        for child in children:
            child_data = {
                'name': child.name,
                'slug': child.slug
            }
            child_division.append(child_data)
        return child_division
