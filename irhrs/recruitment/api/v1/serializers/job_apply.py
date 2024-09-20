import copy
import requests
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import transaction
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django_q.tasks import async_task
from rest_framework import serializers

from irhrs.attendance.tasks.send_notifications import generate_html_message
from irhrs.common.api.serializers.skill import SkillSerializer
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer, DummySerializer
from irhrs.core.utils import nested_get, nested_getattr, get_system_admin
from irhrs.core.utils.common import DummyObject
from irhrs.core.utils.custom_mail import custom_mail
from irhrs.recruitment.api.v1.mixins import Base64FileField
from irhrs.recruitment.api.v1.serializers.applicant import (
    ApplicantReferenceSerializer,
    ApplicantWorkExperienceSerializer,
    ApplicantEducationSerializer, ApplicantAttachmentSerializer)
from irhrs.recruitment.api.v1.serializers.common import SalarySerializer, LocationSerializer
from irhrs.recruitment.api.v1.serializers.external_profile import ExternalUserSerializer
from irhrs.recruitment.constants import (SCREENED, SHORTLISTED, REJECTED,
                                         SELECTED)
from irhrs.recruitment.models import (
    JobApply,
    JobApplyStage,
    ExternalUser,
    Applicant,
    ApplicantReference,
    ApplicantWorkExperience,
    JobQuestionAnswer, ApplicantEducation,
    ApplicantAttachment)
from irhrs.recruitment.utils import (
    get_or_create_salary,
    get_or_create_location,
    validate_attachment
)


class JobQuestionSerializer(DummySerializer):
    id = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    answer_choices = serializers.CharField()
    answer = serializers.CharField(allow_blank=False, allow_null=False, required=True)


class JobApplyCreateSerializer(DynamicFieldsModelSerializer):
    # skills = serializers.SlugRelatedField(
    #     queryset=KnowledgeSkillAbility.objects.filter(ksa_type=SKILL),
    #     slug_field='slug',
    #     many=True,
    #     required=False
    # )
    location = LocationSerializer(
        fields=['country', 'address', 'city_name']
    )
    user = ExternalUserSerializer(fields=[
        'uuid',
        'full_name',
        'email',
        'gender',
        'phone_number',
        'marital_status',
        'dob'
    ])
    profile_picture = Base64FileField(validators=[
        FileExtensionValidator(
            allowed_extensions=['jpg', 'jpeg', 'png', 'bmp', ]), validate_attachment])

    cv = Base64FileField(
        validators=[
            FileExtensionValidator(
                allowed_extensions=settings.ACCEPTED_FILE_FORMATS_LIST
            ),
            validate_attachment
        ],
        required=False
    )

    references = ApplicantReferenceSerializer(
        exclude_fields=['applicant', ],
        many=True,
        required=False
    )
    work_experiences = ApplicantWorkExperienceSerializer(
        exclude_fields=['applicant', ],
        many=True,
        required=False
    )
    expected_salary = SalarySerializer(allow_null=True, required=False)
    educations = ApplicantEducationSerializer(
        exclude_fields=['applicant', ],
        many=True,
        required=False
    )
    question = serializers.JSONField(required=False)

    attachments = ApplicantAttachmentSerializer(
        many=True,
        exclude_fields=['applicant', 'is_archived'],
        required=False
    )

    class Meta:
        model = JobApply
        fields = (
            'user',
            'location',
            # 'skills',
            'profile_picture',
            'cv',
            'references',
            'work_experiences',
            'expected_salary',
            'educations',
            'question',
            'attachments'
        )

    def create(self, validated_data):
        data = copy.deepcopy(validated_data)
        secret_key = getattr(settings, 'GOOGLE_RECAPTCHA_PRIVATE_KEY', None)
        recaptcha_token = self.context.get('recaptcha_token')
        recaptcha_data = {
            'response': recaptcha_token,
            'secret': secret_key
        }
        if not self.request.user.is_authenticated:
            response = requests.post('https://www.google.com/recaptcha/api/siteverify',
                                        data=recaptcha_data)
            json_result = response.json()

            if not json_result.get('success') or not json_result.get('score') > 0.5:
                raise serializers.ValidationError({
                    'non_field_errors': _("Could not verify the request.")
                })
        with transaction.atomic():
            try:
                user_data = validated_data.pop('user')
                profile_picture = validated_data.pop('profile_picture')
                user_data['profile_picture'] = profile_picture
                user = ExternalUser.objects.create(**user_data)

                salary = validated_data.get('expected_salary')

                if salary:
                    salary = get_or_create_salary(salary)

                location = validated_data.pop('location')
                if location:
                    location = get_or_create_location(location)

                cv = validated_data.pop('cv',None)

                applicant = Applicant.objects.create(
                    user=user,
                    expected_salary=salary,
                    address=location,
                    cv=cv,
                    education_degree=self.latest_education.get("degree", ''),
                    education_program=self.latest_education.get("program", '')
                )

                skills = validated_data.pop('skills', [])
                applicant.skills.set(skills)
                applicant.save()

                references = validated_data.pop('references', [])
                if references:
                    reference_list = [
                        ApplicantReference(
                            applicant=applicant,
                            name=data.get('name', ''),
                            email=data.get('email', ''),
                            designation=data.get('designation', ''),
                            org_name=data.get('org_name', ''),
                            phone_number=data.get('phone_number', ''),
                        ) for data in references
                    ]

                    ApplicantReference.objects.bulk_create(reference_list)

                educations = validated_data.pop('educations', None)
                if educations:
                    education_list = [
                        ApplicantEducation(
                            applicant=applicant,
                            degree=data.get('degree'),
                            program=data.get('program'),
                        ) for data in educations
                    ]

                    ApplicantEducation.objects.bulk_create(education_list)

                work_experiences = validated_data.pop('work_experiences', [])
                if work_experiences:
                    work_experiences_list = [
                        ApplicantWorkExperience(
                            applicant=applicant,
                            org_name=data.get('org_name', ''),
                            designation=data.get('designation', ''),
                            years_of_service=data.get('years_of_service', 0),
                        ) for data in work_experiences
                    ]

                    ApplicantWorkExperience.objects.bulk_create(work_experiences_list)
                applicant.experience_years = self.calculate_experience(work_experiences)
                applicant.save()

                attachments = validated_data.pop('attachments', [])
                if attachments:
                    ApplicantAttachment.objects.bulk_create([
                        ApplicantAttachment(
                            applicant=applicant,
                            **attachment
                        ) for attachment in attachments
                    ])

                job_apply_extra_info = dict()
                job_apply_extra_info['job_title'] = self.job.title.title
                job_apply_extra_info['candidate_name'] = applicant.user.full_name
                job_apply_instance = JobApply.objects.create(
                    applicant=applicant,
                    job=self.job,
                    data=job_apply_extra_info
                )
                JobApplyStage.objects.create(job_apply=job_apply_instance)

                question = validated_data.pop('question', None)
                if question:
                    JobQuestionAnswer.objects.create(
                        job_apply=job_apply_instance, data=question)

                data['user']['uuid'] = user.uuid

                return DummyObject(**data)
            except Exception as e:
                raise serializers.ValidationError(str(e))
            finally:
                # https://stackoverflow.com/questions/26942604/celery-and-transaction-atomic
                transaction.on_commit(lambda: self.send_success_email(
                    instance=job_apply_instance
                ))

    @staticmethod
    def send_success_email(instance):
        subject = 'Job Applied Successfully'
        content = """
    Thank you for your application for {0}. {1} will get back to you if you are shortlisted.

    HRMIS,
    {1}
    """.format(
            str(instance.job.title),
            str(instance.job.organization.name),
        )
        async_task(
            custom_mail,
            subject,
            content,
            get_system_admin().email,
            [instance.applicant.user.email],
            html_message=generate_html_message({
                'title': subject,
                'subtitle': subject,
                'message': content
            })
        )
        async_task(
            custom_mail,
            subject,
            content,
            get_system_admin().email,
            [get_system_admin().email],
            html_message=generate_html_message({
                'title': subject,
                'subtitle': subject,
                'message': content
            })
        )

    @property
    def applicant_attachments(self):
        if self.job and self.job.data:
            return [
                attachment.get('key') for attachment in self.job.data.get(
                    'applicant_attachments', []
                )
            ]
        return list()

    def validate(self, attrs):
        education = attrs.get('educations')
        if self.job.is_education_specific and not education:
            raise serializers.ValidationError(
                _('Education Information field is required')
            )
        cv = attrs.get('cv')
        if self.job.curriculum_vitae_required:
            if not cv:
                raise serializers.ValidationError(
                    _('Curriculum Vitae field is required')
                )

        reference = attrs.get('references')
        if self.job.references_required:
            if not reference:
                raise serializers.ValidationError(
                    _('Reference field is required')
                )

        phone_number = nested_get(attrs, 'user.phone_number')
        email = nested_get(attrs, 'user.email')
        if email and phone_number:
            has_already_applied = JobApply.objects.filter(
                job=self.job,
                applicant__user__phone_number=phone_number,
                applicant__user__email=email
            ).exists()
            if has_already_applied:
                raise serializers.ValidationError(
                    _('You Have already applied for this Job')
                )

        self.validate_age(attrs)
        self.validate_gender(attrs)
        self.validate_attachment(attrs)

        self.latest_education = self.get_latest_education_info(
            attrs.get('educations')
        )
        self.validate_education(self.latest_education)

        self.validate_experience(attrs)
        return attrs

    def validate_attachment(self, attrs):
        attachments = attrs.get('attachments', [])
        if len(self.applicant_attachments) != len(attachments):
            raise serializers.ValidationError(_(
                'Required attachments has not been submitted'
            ))

    @cached_property
    def job(self):
        return self.context.get('job')

    def validate_education(self, attrs):
        if not self.job.is_education_specific:
            return True

        education_degree = self.job.education_degree
        education_list = ['Below SLC', 'SLC', 'Intermediate', 'Diploma', 'Bachelor', 'Master',
                          'PHD']
        user_education = attrs.get('degree')

        if education_list.index(user_education) < education_list.index(education_degree):
            raise serializers.ValidationError(
                _('Applicant should have Education Degree of {}'.format(
                    education_degree)))
        return True

    def validate_experience(self, attrs):
        if not nested_getattr(self.job, 'setting.is_experience_required'):
            return True
        required_experience = nested_getattr(self.job, 'setting.min_experience_months') // 12
        applicant_experience = self.calculate_experience(attrs.get('work_experiences'))
        if applicant_experience < required_experience:
            raise serializers.ValidationError(
                _('Applicants should have minimum experience of {} Years'.format(
                    required_experience)))
        return True

    def validate_gender(self, attrs):
        if not nested_getattr(self.job, 'setting.is_gender_specific'):
            return True
        gender = attrs.get('user').get('gender')
        if gender:
            if gender.lower() != nested_getattr(self.job, 'setting.gender').lower():
                raise serializers.ValidationError(
                    _('Only {} Applicants are applicable'.format(
                        nested_getattr(self.job, 'setting.gender')
                    ))
                )
        return True

    def validate_age(self, attrs):
        if not nested_getattr(self.job, 'setting.is_age_specific'):
            return True
        dob = attrs.get('user').get('dob')
        if dob:
            age = ExternalUser.calculate_age(dob)
            job_min_age_required = nested_getattr(self.job, 'setting.min_age')
            job_max_age_required = nested_getattr(self.job, 'setting.max_age')
            if job_max_age_required and age >= job_max_age_required:
                raise serializers.ValidationError(
                    _('Applicant should have age below {} years'.format(job_max_age_required))
                )
            if job_min_age_required and age <= job_min_age_required:
                raise serializers.ValidationError(
                    _('Applicant should have age above {} years'.format(job_min_age_required))
                )
        return True

    @staticmethod
    def validate_question(question):
        question = question.get('question')
        if question and question.get('questions'):
            ser = JobQuestionSerializer(
                data=question.get('questions'),
                many=True
            )
            ser.is_valid(raise_exception=True)
        return question

    @staticmethod
    def calculate_experience(experiences):
        if not experiences:
            return 0
        years_of_service = [
            data.get('years_of_service', 0) for data in experiences
        ]
        return sum(years_of_service)

    @staticmethod
    def get_latest_education_info(educations):
        if not educations:
            return {}
        degrees = ['PHD', 'Master', 'Bachelor', 'Diploma', 'Intermediate', 'SLC', 'Below SLC']
        for degree in degrees:
            latest_education = next(
                (item for item in educations if item["degree"] == degree),
                None
            )
            if latest_education:
                return latest_education


class JobApplyInternalCreateSerializer(DynamicFieldsModelSerializer):
    internal_applicant = serializers.CurrentUserDefault()

    class Meta:
        model = JobApply
        fields = ('internal_applicant',)


class JobApplyStageSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = JobApplyStage
        fields = '__all__'


class ApplicationShortlistDetailSerializer(DynamicFieldsModelSerializer):
    apply_id = serializers.ReadOnlyField(source='id')
    job_title = serializers.ReadOnlyField()
    full_name = serializers.ReadOnlyField(source='applicant.user.full_name')
    profile_picture = serializers.SerializerMethodField()
    phone_number = serializers.ReadOnlyField(source='applicant.user.phone_number')
    address = serializers.ReadOnlyField(source='applicant.address.address')
    email = serializers.ReadOnlyField(source='applicant.user.email')
    experience = serializers.ReadOnlyField(source='applicant.experience_months')
    expected_salary = serializers.SerializerMethodField()
    skills = SkillSerializer(
        fields=['name'],
        source='applicant.skills',
        many=True
    )
    age = serializers.ReadOnlyField(source='applicant.user.age')
    gender = serializers.ReadOnlyField(source='applicant.user.gender')
    education_degree = serializers.ReadOnlyField(source='applicant.education_degree')
    cv = serializers.ReadOnlyField(source='applicant.cv_path', allow_null=True)
    experience_years = serializers.ReadOnlyField(source='applicant.experience_years')
    applicant_id = serializers.ReadOnlyField(source='applicant.id')
    applied_at = serializers.ReadOnlyField(source='created_at')
    answer = serializers.SerializerMethodField(read_only=True)

    candidate = serializers.SerializerMethodField()
    process_initialized = serializers.SerializerMethodField()
    remarks = serializers.ReadOnlyField()

    class Meta:
        model = JobApply
        fields = (
            'apply_id', 'job_title', 'status', 'profile_picture', 'full_name', 'phone_number',
            'email', 'experience', 'address', 'expected_salary', 'skills', 'age', 'gender',
            'education_degree', 'applied_at', 'cv', 'experience_years', 'applicant_id', 'answer',
            'candidate', 'process_initialized', 'remarks'
        )

    @staticmethod
    def get_candidate(instance):
        return ExternalUserSerializer(
            fields=['full_name', 'profile_picture', 'phone_number', 'email', 'gender'],
            instance=instance.applicant.user
        ).data

    @staticmethod
    def get_process_initialized(instance):
        return hasattr(instance, 'pre_screening')

    def get_profile_picture(self, instance):
        logo_path = instance.applicant.user.profile_picture.url \
            if instance.applicant.user.profile_picture else \
            '/static/defaults/applicant.jpg'
        return self.request.build_absolute_uri(logo_path)

    @staticmethod
    def get_expected_salary(instance):
        expected_salary = nested_getattr(
            instance,
            'applicant.expected_salary'
        )
        return str(expected_salary) if expected_salary else None

    @staticmethod
    def get_answer(instance):
        if hasattr(instance, 'answer'):
            return instance.answer.data
        return dict()


JOB_APPLY_STATUS_CHOICES = [
    (SCREENED, 'Screened'),
    (SHORTLISTED, 'Shortlisted'),
    (REJECTED, 'Rejected'),
    (SELECTED, 'Selected')
]


class JobApplyStatusChangeSerializer(DynamicFieldsModelSerializer):
    status = serializers.ChoiceField(choices=JOB_APPLY_STATUS_CHOICES)

    class Meta:
        model = JobApplyStage
        fields = ('status', 'remarks')


class EligibleCandidateSerializer(DynamicFieldsModelSerializer):
    apply_id = serializers.ReadOnlyField(source='id')
    job_title = serializers.ReadOnlyField()
    full_name = serializers.ReadOnlyField(source='applicant.user.full_name')
    profile_picture = serializers.ReadOnlyField(
        source='applicant.user.profile_picture_thumb')
    email_sent = serializers.SerializerMethodField()

    class Meta:
        model = JobApply
        fields = (
            'apply_id',
            'job_title',
            'full_name',
            'profile_picture',
            'applicant_id',
            'email_sent',
            'status'
        )

    @staticmethod
    def get_email_sent(apply):
        return bool(apply.data.get('confirmation_email_sent'))


class RejectedCandidateSerializer(EligibleCandidateSerializer):
    class Meta(EligibleCandidateSerializer.Meta):
        pass

    @staticmethod
    def get_email_sent(apply):
        return bool(apply.data.get('rejected_email_sent'))
