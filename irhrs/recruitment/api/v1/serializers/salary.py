from django.utils.translation import gettext as _
from rest_framework import serializers

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils.common import extract_documents
from irhrs.recruitment.api.v1.serializers.external_profile import ExternalUserSerializer
from irhrs.recruitment.constants import SALARY_DECLARATION, PROGRESS, SELECTED, PENDING, \
    SALARY_DECLARED
from irhrs.recruitment.models import (
    SalaryDeclaration, Template,
    ApplicantAttachment
)
from irhrs.recruitment.utils.util import get_no_objection_info


class SalaryDeclarationAttachmentSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = ApplicantAttachment
        fields = '__all__'


class SalaryDeclarationSerializer(DynamicFieldsModelSerializer):
    frontend_link = serializers.ReadOnlyField()
    email_template = serializers.SlugRelatedField(
        queryset=Template.objects.all(),
        slug_field='slug'
    )
    candidate = serializers.SerializerMethodField()

    attachments = SalaryDeclarationAttachmentSerializer(
        many=True,
        exclude_fields=['applicant', 'is_archived'],
        required=False
    )

    no_objection_info = serializers.SerializerMethodField()

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.upper() == 'GET':
            fields['attachments'] = serializers.SerializerMethodField()
        return fields

    class Meta:
        model = SalaryDeclaration
        fields = '__all__'

    @staticmethod
    def get_no_objection_info(instance):
        return get_no_objection_info(SALARY_DECLARED, apply_id=instance.job_apply)

    @staticmethod
    def validate_status(status):
        if status not in [PENDING, PROGRESS]:
            raise serializers.ValidationError(_('Only Pending and Progress status is supported'))
        return status

    @staticmethod
    def get_candidate(instance):
        return ExternalUserSerializer(
            fields=['full_name', 'profile_picture', 'phone_number', 'email', 'gender'],
            instance=instance.job_apply.applicant.user
        ).data

    def get_attachments(self, instance):
        return SalaryDeclarationAttachmentSerializer(
            ApplicantAttachment.objects.filter(
                is_archived=False,
                applicant=instance.job_apply.applicant,
                type=SALARY_DECLARATION
            ),
            many=True,
            context=self.context
        ).data

    def update(self, instance, validated_data):
        email_template = validated_data.get('email_template')
        template_changed = email_template != instance.email_template

        attachments = validated_data.pop('attachments', [])
        instance = super().update(instance, validated_data)

        if attachments:
            ApplicantAttachment.objects.bulk_create([
                ApplicantAttachment(
                    applicant=instance.job_apply.applicant,
                    type=SALARY_DECLARATION,
                    **attachment
                ) for attachment in attachments
            ])

        if email_template and template_changed:
            instance.send_mail()
        return instance

    def extract_documents(self):
        return extract_documents(
            self.initial_data,
            file_field='attachment',
            filename_field='name'
        )

    def validate(self, attrs):
        attrs['attachments'] = self.extract_documents()
        return super().validate(attrs)
