from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db.models import JSONField
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.contrib.postgres.fields import ArrayField

from irhrs.common.models import (
    BaseModel, SlugModel,
    Skill, DocumentCategory
)
from irhrs.core.constants.user import GENDER_CHOICES, EDUCATION_DEGREE_CHOICES
from irhrs.core.utils.common import get_upload_path
from irhrs.core.validators import validate_future_datetime
from irhrs.organization.models import (
    EmploymentJobTitle, Organization,
    OrganizationBranch, OrganizationDivision,
    Industry,
    EmploymentLevel,
    EmploymentStatus, get_user_model)
from irhrs.organization.models.knowledge_skill_ability import KnowledgeSkillAbility
from irhrs.recruitment.constants import (
    JOB_APPLY_STATUS_CHOICES, PREFERRED_SHIFT_CHOICES, ANYTIME,
    JOB_STATUS_CHOICES,
    DRAFT,
    PUBLISHED
)
from irhrs.recruitment.models.common import (
    JobBenefit,
    Salary
)
from irhrs.recruitment.models.question import QuestionSet


USER = get_user_model()


def job_stages_default():
    return [value for value, _ in JOB_APPLY_STATUS_CHOICES]

class Job(SlugModel, BaseModel):
    title = models.ForeignKey(
        EmploymentJobTitle,
        related_name='jobs',
        on_delete=models.DO_NOTHING
    )
    organization = models.ForeignKey(
        to=Organization,
        on_delete=models.CASCADE,
        related_name='jobs'
    )
    branch = models.ForeignKey(
        to=OrganizationBranch,
        on_delete=models.SET_NULL,
        null=True,
        related_name='jobs'
    )
    division = models.ForeignKey(
        to=OrganizationDivision,
        on_delete=models.SET_NULL,
        null=True,
        related_name='jobs'
    )
    industry = models.ForeignKey(
        Industry,
        on_delete=models.SET_NULL,
        null=True
    )

    vacancies = models.PositiveSmallIntegerField(default=1)
    deadline = models.DateTimeField(
        null=True,
        db_index=True,
        validators=[validate_future_datetime]
    )

    # Permanent, Probation, Contract and so on
    employment_status = models.ForeignKey(
        EmploymentStatus,
        on_delete=models.DO_NOTHING,
        related_name='jobs'
    )

    preferred_shift = models.CharField(
        choices=PREFERRED_SHIFT_CHOICES,
        max_length=30,
        default=ANYTIME
    )

    # Junior Assistant, Assistant, Senior Assistant, Junior Executive
    employment_level = models.ForeignKey(
        EmploymentLevel,
        on_delete=models.DO_NOTHING,
        related_name='jobs'
    )
    location = models.CharField(
        max_length=255,
        blank=True
    )
    offered_salary = models.ForeignKey(
        Salary, null=True,
        related_name='jobs',
        on_delete=models.SET_NULL
    )
    salary_visible_to_candidate = models.BooleanField(default=True)
    expected_salary_required = models.BooleanField(default=False)
    references_required = models.BooleanField(default=False)
    curriculum_vitae_required = models.BooleanField(default=False)
    logo = models.ImageField(upload_to=get_upload_path, null=True, blank=True)
    show_vacancy_number = models.BooleanField(default=False)

    # --------------- / basic information ------------------------------------#

    # ------------ job specifications ----------------------------------------#
    # alternate description is customized job detail for a job post
    # when this field is set contents of job detail page will be replaced by
    # this description
    alternate_description = models.TextField(
        verbose_name='Alternative Description', blank=True)

    description = models.TextField(blank=True)
    specification = models.TextField(verbose_name='job specification',
                                     blank=True)

    is_skill_specific = models.BooleanField(default=False)
    skills = models.ManyToManyField(KnowledgeSkillAbility)

    # applicants who met following education requirements can only apply
    education_degree = models.CharField(
        max_length=20,
        choices=EDUCATION_DEGREE_CHOICES,
        blank=True
    )
    education_program = ArrayField(
        models.CharField(max_length=50, blank=True),
        null=True
    )
    is_education_specific = models.BooleanField(default=False)

    is_document_required = models.BooleanField(default=False)
    document_categories = models.ManyToManyField(
        DocumentCategory,
        blank=True
    )

    benefits = models.ManyToManyField(JobBenefit, blank=True)

    apply_online = models.BooleanField(default=True)
    apply_online_alternative = models.TextField(
        verbose_name='Apply Instruction', blank=True,
        help_text="Provide alternative way to apply for this job")

    status = models.CharField(
        choices=JOB_STATUS_CHOICES,
        default=DRAFT,
        max_length=50,
        db_index=True
    )

    hit_count = models.IntegerField(default=0)

    # posted at represents job published date . we inherit created_at field
    # from BaseModel to represent the job created date by employer themselves.
    posted_at = models.DateTimeField(
        auto_now_add=False, db_index=True,
        null=True, blank=True,
        help_text='Job approved date time')

    # add banner and logo to job itself rather that fkey
    banner = models.ImageField(upload_to='uploads/job/banner/',
                               null=True, blank=True)

    # Data to be pre-filled for job.
    data = JSONField(default=dict)
    remarks = models.TextField(blank=True)
    # For internal Vacancy
    is_internal = models.BooleanField(default=False)

    # Score for Selecting candidate for rostered list
    requested_by = models.ForeignKey(
        USER,
        on_delete=models.SET_NULL,
        null=True
    )

    # Information regarding hiring a candidate like questions for Screening, Interview and category
    # and other information are saved in hiring_info could be a flow too.
    hiring_info = JSONField(null=True, blank=True)

    stages = ArrayField(
        models.CharField(choices=JOB_APPLY_STATUS_CHOICES, max_length=50),
        size=len(JOB_APPLY_STATUS_CHOICES),
        default=job_stages_default
    )

    def __str__(self):
        return self.title.title

    def _get_slug_text(self):
        return self.title.title

    @property
    def frontend_link(self):
        frontend_base_url = getattr(settings, 'FRONTEND_URL')
        return frontend_base_url

    @classmethod
    def get_qs(cls, status=PUBLISHED, check_deadline=True, joins=False, is_internal=False):
        queryset = Job.objects.filter(status=status)

        if check_deadline:
            queryset = queryset.filter(deadline__gt=timezone.now())

        if joins:
            queryset = queryset.select_related(
                'title', 'organization',
                'branch', 'division',
                'offered_salary', 'setting',
            ).prefetch_related(
                'skills', 'benefits', 'document_categories'
            )

        if is_internal:
            queryset = queryset.filter(is_internal=True)
        return queryset

    def save(self, *args, **kwargs):
        if self.id:
            original = Job.objects.filter(id=self.id).first()
            if original and original.status != PUBLISHED and self.status == PUBLISHED:
                self.posted_at = timezone.now()
        super().save(*args, **kwargs)


class JobSetting(models.Model):
    job = models.OneToOneField(
        Job,
        on_delete=models.CASCADE,
        related_name='setting'
    )

    is_experience_required = models.BooleanField(default=False)
    min_experience_months = models.IntegerField(
        validators=[MinValueValidator(limit_value=0)], null=True)
    max_experience_months = models.IntegerField(
        validators=[MinValueValidator(limit_value=0)],
        null=True
    )

    is_gender_specific = models.BooleanField(default=False)
    gender = models.CharField(
        choices=GENDER_CHOICES,
        max_length=20,
        null=True
    )

    is_age_specific = models.BooleanField(default=False)
    min_age = models.IntegerField(
        validators=[MinValueValidator(limit_value=0)],
        null=True
    )
    max_age = models.IntegerField(
        validators=[MinValueValidator(limit_value=0)],
        null=True
    )

    required_two_wheeler = models.BooleanField(default=False)

    def __str__(self):
        return f"Job setting - {str(self.job)}"


class JobQuestion(BaseModel):
    job = models.OneToOneField(
        Job, related_name='question',
        on_delete=models.CASCADE
    )
    question = models.ForeignKey(
        QuestionSet,
        on_delete=models.CASCADE,
        related_name='job_questions'
    )


class JobAttachment(BaseModel):
    job = models.ForeignKey(
        Job,
        related_name='attachments',
        on_delete=models.CASCADE
    )
    attachment = models.FileField(
        upload_to=get_upload_path,
        validators=[FileExtensionValidator(
            allowed_extensions=settings.ACCEPTED_FILE_FORMATS_LIST
        )]
    )
    name = models.CharField(max_length=255)
    is_archived = models.BooleanField(default=False)
