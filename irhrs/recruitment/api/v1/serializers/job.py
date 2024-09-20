import copy

from django.core.validators import MinValueValidator
from django.db.models import Q
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from irhrs.common.api.serializers.common import IndustrySerializer
from irhrs.core.constants.common import SKILL
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils.common import DummyObject, extract_documents
from irhrs.core.validators import MinMaxValueValidator
from irhrs.organization.api.v1.serializers.branch import OrganizationBranchSerializer
from irhrs.organization.api.v1.serializers.division import OrganizationDivisionSerializer
from irhrs.organization.api.v1.serializers.employment import (EmploymentJobTitleSerializer,
                                                              EmploymentStatusSerializer,
                                                              EmploymentLevelSerializer)
from irhrs.organization.api.v1.serializers.knowledge_skill_ability import \
    KnowledgeSkillAbilitySerializer
from irhrs.organization.api.v1.serializers.organization import OrganizationSerializer
from irhrs.organization.models.knowledge_skill_ability import KnowledgeSkillAbility
from irhrs.recruitment.api.v1.serializers.common import (
    SalarySerializer, JobBenefitSerializer, DocumentCategorySerializer)
from irhrs.recruitment.api.v1.serializers.question import QuestionSetSerializer
from irhrs.recruitment.constants import APPLIED, GENDER_CHOICES, PRE_SCREENING, POST_SCREENING, \
    PRE_SCREENING_INTERVIEW, ASSESSMENT, INTERVIEW_EVALUATION, REFERENCE_CHECK, CANDIDATE_LETTER, REJECTED, SALARY_DECLARATION, SALARY_DECLARED, SELECTED
from irhrs.recruitment.models import (Job, JobSetting, JobQuestion, Question,
                                      JobQuestionAnswer, Organization, OrganizationBranch,
                                      OrganizationDivision, EmploymentJobTitle,
                                      EDUCATION_DEGREE_CHOICES, QuestionSet, EmploymentLevel,
                                      EmploymentStatus, JobAttachment, get_user_model, Template)
from irhrs.recruitment.utils import get_or_create_salary
from irhrs.users.api.v1.serializers.thin_serializers import OrganizationThinSerializer
from irhrs.recruitment.utils.stages import letter_mapper, stage_mapper

USER = get_user_model()


class JobAttachmentSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = JobAttachment
        fields = '__all__'


class JobSettingSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = JobSetting
        exclude = ['job', 'id']


class JobBasicInformationSerializer(DynamicFieldsModelSerializer):
    title = serializers.SlugRelatedField(
        queryset=EmploymentJobTitle.objects.all(),
        slug_field='slug'
    )
    offered_salary = SalarySerializer(
        fields=['currency', 'operator', 'minimum', 'maximum', 'unit'],
        required=False
    )
    organization = serializers.SlugRelatedField(
        queryset=Organization.objects.all(),
        slug_field='slug'
    )
    branch = serializers.SlugRelatedField(
        queryset=OrganizationBranch.objects.all(),
        slug_field='slug',
        required=False,
        allow_null=True
    )
    division = serializers.SlugRelatedField(
        queryset=OrganizationDivision.objects.all(),
        slug_field='slug',
        required=False
    )
    employment_level = serializers.SlugRelatedField(
        queryset=EmploymentLevel.objects.all(),
        slug_field='slug'
    )
    employment_status = serializers.SlugRelatedField(
        queryset=EmploymentStatus.objects.all(),
        slug_field='slug'
    )

    requested_by = serializers.PrimaryKeyRelatedField(
        default=serializers.CurrentUserDefault(),
        queryset=USER.objects.all()
    )

    class Meta:
        model = Job
        fields = (
            'id', 'title', 'slug', 'organization', 'branch', 'division',
            'title', 'location', 'vacancies', 'deadline',
            'employment_status', 'offered_salary', 'salary_visible_to_candidate',
            'employment_level', 'preferred_shift', 'requested_by', 'expected_salary_required',
            'curriculum_vitae_required', 'references_required',
            'is_internal', 'show_vacancy_number'
        )
        read_only_fields = ['id', 'slug']
        extra_kwargs = {
            'deadline': {
                'required': True,
                'allow_null': False,
            },
            'title': {
                'required': True,
                'allow_null': False,
            },
            'salary_visible_to_candidate': {
                'required': False
            }
        }

    def update_or_create_offered_salary(self, offered_salary_data):
        if not self.instance and offered_salary_data is not None:
            return get_or_create_salary(offered_salary_data)

        elif offered_salary_data and offered_salary_data is not ...:
            return get_or_create_salary(
                offered_salary_data)

        elif offered_salary_data is None:
            return None

        return self.instance.offered_salary

    def after_create_or_update(self, instance, offered_salary):
        """All post save things to do"""

        offered_salary_instance = self.update_or_create_offered_salary(
            offered_salary)

        instance.offered_salary = offered_salary_instance
        instance.save()
        return instance

    def create(self, validated_data):
        vd_copy = copy.deepcopy(validated_data)
        offered_salary = validated_data.pop('offered_salary', None)
        instance = super().create(validated_data)
        self.after_create_or_update(instance, offered_salary)

        return DummyObject(id=instance.id, slug=instance.slug, **vd_copy)

    def update(self, instance, validated_data):
        offered_salary = validated_data.pop('offered_salary', ...)
        instance = super().update(instance, validated_data)
        return self.after_create_or_update(instance, offered_salary)


class JobSpecificationSerializer(DynamicFieldsModelSerializer):
    is_experience_required = serializers.BooleanField(default=False,
                                                      write_only=True)
    min_experience_months = serializers.IntegerField(
        allow_null=True,
        write_only=True,
        validators=[
            MinMaxValueValidator(
                min_value=0, max_value=720,
                message="Ensure this value is between 0 and 60."
            )
        ],
        # year of experience can't exceed 60 years (assumption)
    )
    max_experience_months = serializers.IntegerField(
        allow_null=True,
        write_only=True,
        validators=[
            MinMaxValueValidator(
                min_value=0, max_value=720,
                message="Ensure this value is between 0 and 60."
            )
        ],
        # year of experience can't exceed 60 years (assumption)
    )

    is_gender_specific = serializers.BooleanField(
        default=False,
        write_only=True
    )
    gender = serializers.ChoiceField(
        choices=GENDER_CHOICES,
        allow_null=True,
        write_only=True
    )

    education_degree = serializers.ChoiceField(
        choices=EDUCATION_DEGREE_CHOICES,
        write_only=True,
        required=False,
        allow_blank=True
    )
    is_age_specific = serializers.BooleanField(
        default=False,
        write_only=True
    )
    min_age = serializers.IntegerField(
        allow_null=True,
        write_only=True,
        validators=[MinValueValidator(limit_value=0)]
    )
    max_age = serializers.IntegerField(
        allow_null=True,
        write_only=True,
        validators=[MinValueValidator(limit_value=0)]
    )

    question = serializers.PrimaryKeyRelatedField(
        queryset=QuestionSet.objects.all(),
        required=False,
        allow_null=True
    )
    required_two_wheeler = serializers.BooleanField(
        default=False,
        write_only=True
    )

    attachments = JobAttachmentSerializer(
        many=True, required=False, read_only=True
    )

    applicant_attachments = serializers.ListField(
        child=serializers.CharField(max_length=30, required=False),
        required=False,
        allow_empty=True
    )

    class Meta:
        model = Job
        fields = (
            "specification",
            "description",

            "is_education_specific",
            "education_degree",
            "education_program",

            "is_skill_specific",

            "is_experience_required",
            "min_experience_months",
            "max_experience_months",

            "is_gender_specific",
            "gender",

            "is_age_specific",
            "min_age",
            "max_age",

            "question",

            "required_two_wheeler",
            "attachments",
            "applicant_attachments",
        )

    @staticmethod
    def validate_skills(skills):
        if skills and len(skills) > 10:
            raise serializers.ValidationError(
                _("Can not add more than 10 skills"))
        return skills

    def get_existing_setting(self, jobseeker_field):
        assert self.instance is not None
        return self.instance.settings.filter(
            jobseeker_field=jobseeker_field).first()

    @staticmethod
    def validate_experience_constrains(attrs):
        is_experience_required = attrs.get("is_experience_required", None)
        min_experience_months = attrs.get("min_experience_months", None)
        max_experience_months = attrs.get("max_experience_months", None)

        if is_experience_required and not any(
            [min_experience_months, max_experience_months]):
            raise serializers.ValidationError(
                _("Either `min_experience_months` or"
                  " `max_experience_months` is required."))

        if min_experience_months and max_experience_months and (
            min_experience_months > max_experience_months):
            raise serializers.ValidationError(
                _("`max_experience_months` must be greater than "
                  "`min_experience_months`."))

        return attrs

    @staticmethod
    def validate_gender_constrains(attrs):
        is_gender_specific = attrs.get("is_gender_specific", None)
        gender = attrs.get("gender", None)

        if is_gender_specific and not gender:
            raise serializers.ValidationError(
                {"gender": _("This field is required")}
            )

        return attrs

    @staticmethod
    def validate_age_constrains(attrs):
        is_age_specific = attrs.get("is_age_specific", None)
        min_age = attrs.get("min_age", None)
        max_age = attrs.get("max_age", None)

        if is_age_specific and not any([min_age, max_age]):
            raise serializers.ValidationError(
                _("Either `min_age` or"
                  " `max_age` is required."))

        if min_age and max_age and (min_age > max_age):
            raise serializers.ValidationError(
                _("`max_age` must be greater than "
                  "`min_age`."))

        return attrs

    def validate(self, attrs):
        attrs = self.validate_experience_constrains(attrs)
        attrs = self.validate_gender_constrains(attrs)
        attrs = self.validate_age_constrains(attrs)

        if (attrs.get('is_education_specific') and
            not attrs.get('education_degree') and attrs.get('education_program')):
            raise serializers.ValidationError(
                _("Education Degree and Education Program is required.")
            )

        if attrs.get('is_skill_specific') and not attrs.get('skills'):
            raise serializers.ValidationError(
                {'skills': _("This field is required")})

        attachments = extract_documents(
            self.initial_data,
            file_field='attachment',
            filename_field='name'
        )
        serializer = JobAttachmentSerializer(data=attachments, many=True,
                                             fields=['attachment', 'name'])
        serializer.is_valid(raise_exception=True)
        attrs['attachments'] = attachments
        return attrs

    def update(self, instance, validated_data):
        skills = validated_data.pop('skills', [])
        instance.skills.clear()
        instance.skills.set(skills)
        instance.save()

        required_two_wheeler = validated_data.pop(
            'required_two_wheeler', False
        )
        self.update_required_two_wheeler(required_two_wheeler)
        question = validated_data.pop('question', None)
        if question:
            JobQuestion.objects.update_or_create(
                job=self.instance, defaults={'question': question})
        else:
            JobQuestion.objects.filter(job=self.instance).delete()
            
        job_setting_fields = [
            'is_experience_required',
            'min_experience_months',
            'max_experience_months',
            'is_gender_specific',
            'gender',
            'is_age_specific',
            'min_age',
            'max_age',
        ]

        for field in job_setting_fields:
            setting = instance.setting

            field_value = validated_data.pop(field, ...)
            if field_value is not ...:
                setattr(setting, field, field_value)
            setting.save()

        attachments = validated_data.pop('attachments', [])
        if attachments:
            JobAttachment.objects.bulk_create([
                JobAttachment(
                    job=instance,
                    **attachment
                ) for attachment in attachments
            ])

        applicant_attachments = validated_data.pop('applicant_attachments', [])
        attachment_list = []
        if applicant_attachments:
            attachment_list = [
                {'name': attachment_name, 'key': slugify(attachment_name).replace('-', '_')}
                for attachment_name in applicant_attachments
            ]

        instance = super().update(instance, validated_data)

        if attachment_list:
            instance.data = {
                'applicant_attachments': attachment_list
            }
            instance.save()

        return instance

    def update_required_two_wheeler(self, required_two_wheeler):
        setting = self.instance.setting
        setting.required_two_wheeler = required_two_wheeler
        setting.save()


class JobAdditionalInfoSerializer(DynamicFieldsModelSerializer):
    required_two_wheeler = serializers.BooleanField(
        default=False,
        write_only=True
    )

    class Meta:
        model = Job
        fields = (
            'benefits',
            'is_document_required',
            'document_categories',
            'required_two_wheeler'
        )

    def validate(self, attrs):
        is_document_required = attrs.get('is_document_required', None)
        document_categories = attrs.get('document_categories', None)

        if is_document_required and not document_categories:
            raise serializers.ValidationError({
                'document_categories': _("This field is required.")
            })
        return attrs

    def update_required_two_wheeler(self, required_two_wheeler):
        setting = self.instance.setting
        setting.required_two_wheeler = required_two_wheeler
        setting.save()

    def update(self, instance, validated_data):
        required_two_wheeler = validated_data.pop(
            'required_two_wheeler', False
        )
        self.update_required_two_wheeler(required_two_wheeler)

        return super().update(instance, validated_data)


class JobHiringInformationSerializer(DynamicFieldsModelSerializer):
    pre_screening = serializers.PrimaryKeyRelatedField(
        queryset=QuestionSet.objects.filter(is_archived=False, form_type=PRE_SCREENING),
        required=False,
        allow_null=True
    )
    post_screening = serializers.PrimaryKeyRelatedField(
        queryset=QuestionSet.objects.filter(is_archived=False).filter(
            Q(form_type=PRE_SCREENING) | Q(form_type=POST_SCREENING)
        ),
        required=False,
        allow_null=True
    )
    pre_screening_interview = serializers.PrimaryKeyRelatedField(
        queryset=QuestionSet.objects.filter(is_archived=False).filter(
            Q(form_type=PRE_SCREENING_INTERVIEW)
        ),
        required=False,
        allow_null=True

    )
    assessment = serializers.PrimaryKeyRelatedField(
        queryset=QuestionSet.objects.filter(is_archived=False).filter(
            Q(form_type=ASSESSMENT)
        ),
        required=False,
        allow_null=True

    )
    interview = serializers.PrimaryKeyRelatedField(
        queryset=QuestionSet.objects.filter(is_archived=False).filter(
            Q(form_type=INTERVIEW_EVALUATION)
        ),
        required=False,
        allow_null=True
    )
    reference_check = serializers.PrimaryKeyRelatedField(
        queryset=QuestionSet.objects.filter(is_archived=False).filter(
            Q(form_type=REFERENCE_CHECK)
        ),
        required=False,
        allow_null=True

    )

    pre_screening_letter = serializers.SlugRelatedField(
        queryset=Template.objects.filter(type=CANDIDATE_LETTER),
        slug_field='slug',
        required=False,
        allow_null=True
    )
    post_screening_letter = serializers.SlugRelatedField(
        queryset=Template.objects.filter(type=CANDIDATE_LETTER),
        slug_field='slug',
        required=False,
        allow_null=True
    )
    pre_screening_interview_letter = serializers.SlugRelatedField(
        queryset=Template.objects.filter(type=CANDIDATE_LETTER),
        slug_field='slug',
        required=False,
        allow_null=True
    )
    assessment_letter = serializers.SlugRelatedField(
        queryset=Template.objects.filter(type=CANDIDATE_LETTER),
        slug_field='slug',
        required=False,
        allow_null=True
    )
    interview_letter = serializers.SlugRelatedField(
        queryset=Template.objects.filter(type=CANDIDATE_LETTER),
        slug_field='slug',
        required=False,
        allow_null=True
    )
    reference_check_letter = serializers.SlugRelatedField(
        queryset=Template.objects.filter(type=CANDIDATE_LETTER),
        slug_field='slug',
        required=False,
        allow_null=True
    )
    selected_letter = serializers.SlugRelatedField(
        queryset=Template.objects.filter(type=CANDIDATE_LETTER),
        slug_field='slug',
        required=False,
        allow_null=True
    )
    rejected_letter = serializers.SlugRelatedField(
        queryset=Template.objects.filter(type=CANDIDATE_LETTER),
        slug_field='slug',
        required=False,
        allow_null=True
    )
    written_score = serializers.IntegerField(
        min_value=0,
        max_value=100,
        default=25
    )
    interview_score = serializers.IntegerField(
        min_value=0,
        max_value=100,
        default=75
    )

    categories = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False
    )

    score = serializers.FloatField(
        min_value=0,
        max_value=100,
        required=False
    )

    # Previous job from where we copy hiring information
    previous_job = serializers.PrimaryKeyRelatedField(
        queryset=Job.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Job
        fields = [
            'pre_screening', 'post_screening',
            'categories', 'previous_job',
            'pre_screening_interview',
            'assessment', 'interview',

            'score',
            'written_score',
            'interview_score',


            'reference_check',
            'pre_screening_letter',
            'post_screening_letter',
            'pre_screening_interview_letter',
            'assessment_letter',
            'interview_letter',
            'reference_check_letter',
            'selected_letter',
            'rejected_letter',
            'stages'
        ]

    def validate(self, attrs):
        if not attrs.get('score') and not attrs.get('categories'):
            raise serializers.ValidationError(_('Either score or categories is required'))

        stages = attrs.get('stages')
        required_stages = {APPLIED, SELECTED, REJECTED}
        optional_stages = set(stages) - required_stages

        if not optional_stages:
            raise serializers.ValidationError(
                "At least one stage needs to be selected"
            )

        optional_stages.discard(SALARY_DECLARED)
        for stage in optional_stages:
            question_set = stage_mapper.get(stage)
            if not attrs.get(question_set):
                raise serializers.ValidationError(
                    f"{question_set} question is required"
                )
        return attrs

    def update(self, instance, validated_data):
        copy_data = copy.deepcopy(validated_data)

        previous_job = validated_data.pop('previous_job', None)
        stages = validated_data.pop('stages', None)
        if stages:
            instance.stages = stages
            instance.save()

        if previous_job:
            data = previous_job.hiring_info
        else:
            data = dict()

            information = [

                # Question sets
                'pre_screening',
                'post_screening',
                'pre_screening_interview',
                'assessment',
                'interview',
                'reference_check',

                # Letters
                'pre_screening_letter',
                'post_screening_letter',
                'pre_screening_interview_letter',
                'assessment_letter',
                'interview_letter',
                'reference_check_letter',
                'selected_letter',
                'rejected_letter'
            ]
            for key in information:
                obj = validated_data.pop(key, None)
                if obj:
                    data[key] = {
                        'id': obj.id,
                        'name': getattr(obj, 'name', ''),
                        'title': getattr(obj, 'title', '')
                    }
                    if hasattr(obj, 'slug'):
                        data[key]['slug'] = obj.slug

            categories = validated_data.pop('categories', [])
            if categories:
                data['categories'] = categories

            scores = [
                'score',
                'written_score',
                'interview_score'
            ]
            for score in scores:
                value = validated_data.pop(score, None)
                if value:
                    data[score] = value

        if data:
            instance.hiring_info = data
            instance.save(update_fields=['hiring_info'])
        return DummyObject(**copy_data)


class JobPublicSerializer(DynamicFieldsModelSerializer):
    job_title = serializers.ReadOnlyField(source='title.title')
    industry = IndustrySerializer()
    organization = OrganizationThinSerializer()
    branch = OrganizationBranchSerializer(fields=['name', 'slug'])
    division = OrganizationDivisionSerializer(fields=['name'])
    offered_salary = serializers.SerializerMethodField()
    skills = serializers.SerializerMethodField()
    benefits = serializers.SerializerMethodField()
    document_categories = serializers.SerializerMethodField()
    setting = JobSettingSerializer(read_only=True)
    employment_status = serializers.ReadOnlyField(source='employment_status.title')
    employment_level = serializers.ReadOnlyField(source='employment_level.title')
    question_set = serializers.SerializerMethodField()
    attachments = JobAttachmentSerializer(
        read_only=True,
        fields=['attachment', 'name'], many=True
    )
    applicant_attachments = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'job_title', 'organization', 'industry', 'branch', 'division', 'slug',
            'location', 'organization',
            'vacancies', 'deadline', 'employment_status',
            'preferred_shift', 'employment_level', 'location',
            'offered_salary', 'salary_visible_to_candidate', 'logo',
            'alternate_description', 'description',
            'specification', 'is_skill_specific', 'skills',
            'education_degree', 'education_program', 'is_education_specific',
            'is_document_required', 'document_categories',
            'benefits', 'apply_online', 'apply_online_alternative',
            'status', 'hit_count', 'attachments',
            'posted_at', 'banner', 'setting', 'question_set',
            'applicant_attachments', 'expected_salary_required',
            'curriculum_vitae_required', 'references_required', 'is_internal', 'user_id',
            'show_vacancy_number', 'hiring_info'
        ]

    @staticmethod
    def get_applicant_attachments(job):
        if job.data:
            return job.data.get('applicant_attachments', [])
        return list()

    def get_offered_salary(self, job):
        if not (job.offered_salary and (
            job.salary_visible_to_candidate or self.context.get('is_hr_admin')
        )):
            return 'Not Mentioned'
        return job.offered_salary.salary_repr

    @staticmethod
    def get_skills(job):
        return list(job.skills.all().values_list('name', flat=True))

    @staticmethod
    def get_benefits(job):
        return list(job.benefits.all().values_list('name', flat=True))

    @staticmethod
    def get_document_categories(job):
        return list(
            job.document_categories.all().values_list('name', flat=True))

    def get_question_set(self, job):
        question_set = JobQuestion.objects.filter(job=job).first()
        return JobQuestionSerializer(
            question_set,
            fields=['id', 'question'],
            context=self.context
        ).data

    def get_user_id(self, obj):
        if obj.is_internal and self.request.user.is_authenticated:
            return self.request.user.id
        return None


class JobSerializer(DynamicFieldsModelSerializer):
    organization = OrganizationThinSerializer()
    division = OrganizationDivisionSerializer(
        fields=['slug', 'name']
    )
    branch = OrganizationBranchSerializer(
        fields=['slug', 'name']
    )
    offered_salary = SalarySerializer(
        fields=['currency', 'operator', 'minimum', 'maximum', 'unit'])
    job_title = serializers.ReadOnlyField(source='title.title')

    setting = JobSettingSerializer(read_only=True)
    application_count = serializers.ReadOnlyField()

    employment_status = EmploymentStatusSerializer(fields=['title', 'slug'])
    employment_level = EmploymentLevelSerializer(fields=['title', 'slug'])
    question = serializers.SerializerMethodField()
    current_status = serializers.ReadOnlyField()
    skills = serializers.PrimaryKeyRelatedField(
        queryset=KnowledgeSkillAbility.objects.filter(
            ksa_type=SKILL,
        ),
        many=True
    )
    attachments = JobAttachmentSerializer(
        many=True, fields=['id', 'attachment', 'name']
    )

    class Meta:
        model = Job

        basic_fields = [
            'id', 'title', 'location', 'job_title', 'title', 'current_status',
            'slug', 'created_at', 'modified_at', 'organization',
            'vacancies', 'deadline', 'division', 'branch', 'employment_status',
            'preferred_shift', 'offered_salary', 'logo', 'alternate_description',
            'description', 'specification', 'is_skill_specific', 'skills',
            'education_degree', 'education_program', 'is_education_specific',
            'is_document_required', 'document_categories', 'employment_level',
            'benefits', 'apply_online', 'apply_online_alternative',
            'status', 'hit_count', 'question', 'hiring_info',
            'posted_at', 'modified_at', 'banner', 'setting',
            'salary_visible_to_candidate', 'attachments', 'data', 'expected_salary_required',
            'is_internal', 'stages', 'show_vacancy_number'

        ]
        extra_fields = [
            'application_count'
        ]
        fields = basic_fields + extra_fields

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.upper() == 'GET':
            if 'title' in fields:
                fields['title'] = EmploymentJobTitleSerializer(
                    fields=['id', 'title', 'slug'])
            if 'skills' in fields:
                fields['skills'] = KnowledgeSkillAbilitySerializer(
                    fields=['id', 'name', 'slug'],
                    many=True,
                    context=self.context
                )
            if 'benefits' in fields:
                fields['benefits'] = JobBenefitSerializer(
                    fields=['id', 'name'], many=True, context=self.context)
            if 'organization' in fields:
                fields['organization'] = OrganizationSerializer(
                    context=self.context, fields=['name'])
            if 'document_categories' in fields:
                fields['document_categories'] = DocumentCategorySerializer(
                    fields=['id', 'name'], many=True, context=self.context)
        return fields

    @staticmethod
    def get_question(instance):
        if hasattr(instance, 'question'):
            return QuestionSetSerializer(instance=instance.question.question).data
        return ''


class JobQuestionSerializer(DynamicFieldsModelSerializer):
    job = serializers.SlugRelatedField(
        queryset=Job.get_qs(),
        slug_field='slug'
    )

    class Meta:
        model = JobQuestion
        fields = '__all__'

    def get_fields(self):
        fields = super().get_fields()
        if 'question' in fields and self.request.method.upper() == 'GET':
            fields['question'] = QuestionSetSerializer()
        return fields

    def create(self, validated_data):
        question_data = validated_data.pop('question')
        question = Question.objects.create(**question_data)
        validated_data['question'] = question
        return super().create(validated_data)


class JobQuestionAnswerSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = JobQuestionAnswer
        fields = '__all__'
