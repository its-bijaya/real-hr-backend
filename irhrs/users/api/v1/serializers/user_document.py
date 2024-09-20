import itertools

from django.conf import settings
from django.core.validators import FileExtensionValidator
from rest_framework.fields import FileField
from rest_framework.relations import SlugRelatedField

from irhrs.common.api.serializers.common import DocumentCategorySerializer
from irhrs.common.models import DocumentCategory
from irhrs.core.constants.common import EMPLOYEE
from irhrs.core.validators import DocumentTypeValidator
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from irhrs.users.api.v1.serializers.user_serializer_common import UserSerializerMixin
from irhrs.users.models.other import UserDocument

chain_iterable = itertools.chain.from_iterable


class UserDocumentSerializer(UserSerializerMixin):
    document_type = SlugRelatedField(queryset=DocumentCategory.objects.all(), slug_field='slug',
                                     validators=[DocumentTypeValidator(association_type=EMPLOYEE)])
    uploaded_by = UserThinSerializer(
        fields=["id", "full_name", "organization", "job_title", "profile_picture", "cover_picture", "organization", "is_current",],
        read_only=True
    )
    file = FileField(
        validators=[
            FileExtensionValidator(
                allowed_extensions=chain_iterable(settings.ACCEPTED_FILE_FORMATS.values())
            )
        ]
    )

    class Meta:
        model = UserDocument
        fields = ('slug', 'user', 'title', 'document_type', 'file', 'uploaded_by', 'created_at', 'modified_at')
        read_only_fields = ('user', 'slug')

    def before_create(self, validated_data, change_request=False):
        if self.request:
            validated_data.update({'uploaded_by': self.request.user})
        return validated_data

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method == 'GET':
            if 'document_type' in fields:
                fields['document_type'] = DocumentCategorySerializer(context=self.context,
                                                                     exclude_fields=['created_at', 'modified_at'])
        return fields

    def create(self, validated_data):
        validated_data = self.before_create(validated_data)
        return super(UserDocumentSerializer, self).create(validated_data)
