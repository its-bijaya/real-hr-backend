from django.conf import settings
from django.db import transaction
from django.utils.functional import cached_property
from rest_framework import serializers

from irhrs.common.api.serializers.skill import SkillSerializer
from irhrs.core.constants.common import SKILL
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.validators import validate_phone_number
from irhrs.organization.api.v1.serializers.branch import OrganizationBranchSerializer
from irhrs.organization.api.v1.serializers.division import OrganizationDivisionSerializer
from irhrs.organization.api.v1.serializers.employment import EmploymentJobTitleSerializer, \
    EmploymentStatusSerializer, EmploymentLevelSerializer
from irhrs.recruitment.api.v1.mixins import Base64FileField
from irhrs.recruitment.api.v1.serializers.external_profile import ExternalUserSerializer
from irhrs.recruitment.models import (
    Applicant,
    ApplicantReference,
    ApplicantWorkExperience, GENDER_CHOICES, JobApply, KnowledgeSkillAbility,
    ApplicantEducation,
    ApplicantAttachment, FileExtensionValidator, nested_getattr)
from irhrs.recruitment.utils import validate_attachment


class ApplicantSerializerMixin:

    def create(self, validated_data):
        if self.applicant:
            validated_data['applicant'] = self.applicant
        return super().create(validated_data)

    @cached_property
    def applicant(self):
        return self.context.get('applicant')


class ApplicantAttachmentSerializer(DynamicFieldsModelSerializer):
    attachment = Base64FileField(
        validators=[
            FileExtensionValidator(
                allowed_extensions=settings.ACCEPTED_FILE_FORMATS_LIST
            ),
            validate_attachment
        ]
    )

    class Meta:
        model = ApplicantAttachment
        fields = '__all__'


class ApplicantReferenceSerializer(
    ApplicantSerializerMixin,
    DynamicFieldsModelSerializer
):

    class Meta:
        model = ApplicantReference
        fields = '__all__'


class ApplicantWorkExperienceSerializer(
    ApplicantSerializerMixin,
    DynamicFieldsModelSerializer
):

    class Meta:
        model = ApplicantWorkExperience
        fields = '__all__'


class ApplicantDetailSerializer(DynamicFieldsModelSerializer):
    user = ExternalUserSerializer(
        exclude_fields=['is_archived', 'profile_picture']
    )
    skills = serializers.SlugRelatedField(
        queryset=KnowledgeSkillAbility.objects.filter(ksa_type=SKILL),
        slug_field='slug',
        many=True
    )
    full_name = serializers.ReadOnlyField(source='user.full_name')
    address = serializers.ReadOnlyField(source='address.address')
    email = serializers.ReadOnlyField(source='user.email')

    class Meta:
        model = Applicant
        fields = '__all__'


class ApplicantCreateSerializer(DynamicFieldsModelSerializer):
    full_name = serializers.CharField(source='user.full_name')
    phone_number = serializers.CharField(max_length=15, source='user.phone_number', validators=[
        validate_phone_number
    ])
    gender = serializers.ChoiceField(
        source='user.gender',
        choices=GENDER_CHOICES
    )

    class Meta:
        model = Applicant
        fields = '__all__'


class ApplicantEducationSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = ApplicantEducation
        fields = '__all__'
        extra_kwargs = {
            'program': {
                'allow_blank': False
            }
        }


class ApplicantCVSerializer(DynamicFieldsModelSerializer):
    user = ExternalUserSerializer(
        fields=[
            'profile_picture', 'full_name',
            'phone_number', 'email',
            'gender', 'marital_status', 'dob',
            'age'
        ]
    )
    address = serializers.ReadOnlyField(source='address.address')
    skills = SkillSerializer(many=True, fields=['name', ])
    expected_salary_required = serializers.SerializerMethodField()
    expected_salary = serializers.ReadOnlyField(source='expected_salary.salary_repr')
    references = ApplicantReferenceSerializer(
        many=True,
        fields=[
            'name', 'email',
            'designation', 'org_name',
            'phone_number'
        ]
    )
    work_experiences = ApplicantWorkExperienceSerializer(
        many=True,
        fields=['org_name', 'designation', 'years_of_service']
    )
    educations = ApplicantEducationSerializer(
        many=True,
        fields=['degree', 'program']
    )
    attachments = ApplicantAttachmentSerializer(many=True, fields=['attachment', 'name'])
    answer = serializers.SerializerMethodField()

    class Meta:
        model = Applicant
        fields = '__all__'

    @staticmethod
    def get_answer(applicant):
        return nested_getattr(applicant, 'applied_job.answer.data') or dict()

    @staticmethod
    def get_expected_salary_required(applicant):
        return nested_getattr(applicant, 'applied_job.job.expected_salary_required') or False


class ApplicantOnBoardSerializer(DynamicFieldsModelSerializer):
    full_name_with_job = serializers.SerializerMethodField()
    full_name = serializers.ReadOnlyField(source='candidate_name')
    email = serializers.ReadOnlyField(source='candidate_email')

    job_title = EmploymentJobTitleSerializer(source='job.title', fields=['title', 'slug'])
    division = OrganizationDivisionSerializer(source='job.division', fields=['name', 'slug'])
    branch = OrganizationBranchSerializer(source='job.branch', fields=['name', 'slug'])
    employment_level = EmploymentLevelSerializer(
        source='job.employment_level', fields=['slug', 'title'])
    employment_status = EmploymentStatusSerializer(
        source='job.employment_status', fields=['title', 'slug'])

    description = serializers.ReadOnlyField(source='job.description')
    specification = serializers.ReadOnlyField(source='job.specification')
    address = serializers.ReadOnlyField(source='applicant.address.address')
    gender = serializers.ReadOnlyField(source='applicant.user.gender')

    class Meta:
        model = JobApply
        fields = '__all__'

    @staticmethod
    def get_full_name_with_job(apply):
        return f'{apply.candidate_name} [{apply.job_title}]'
