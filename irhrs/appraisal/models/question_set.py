from django.db import models
from django.conf import settings

from irhrs.common.models import BaseModel
from irhrs.core.validators import validate_description, validate_future_datetime, validate_title
from irhrs.organization.models import OrganizationBranch, OrganizationDivision, EmploymentJobTitle, \
    EmploymentLevel, Organization
from irhrs.questionnaire.models.questionnaire import Question


class PerformanceAppraisalQuestionSet(BaseModel):
    organization = models.ForeignKey(
        Organization,
        related_name='performance_appraisal_question_sets',
        on_delete=models.CASCADE,
        null=True
    )
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=1000, blank=True)
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class PerformanceAppraisalQuestionSection(BaseModel):
    title = models.CharField(
        max_length=255
    )
    description = models.TextField(
        blank=True,
        validators=[validate_description],
        max_length=settings.TEXT_FIELD_MAX_LENGTH
    )
    question_set = models.ForeignKey(
        to=PerformanceAppraisalQuestionSet,
        related_name='sections',
        on_delete=models.CASCADE
    )
    questions = models.ManyToManyField(
        to=Question,
        through='PerformanceAppraisalQuestion',
        through_fields=('question_section', 'question'),
        related_name='+'
    )

    class Meta:
        ordering = 'created_at',

    def __str__(self):
        return self.title


class PerformanceAppraisalQuestion(BaseModel):
    is_mandatory = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField()
    question_section = models.ForeignKey(
        to=PerformanceAppraisalQuestionSection,
        on_delete=models.CASCADE,
        related_name='pa_questions'
    )
    question = models.ForeignKey(
        to=Question,
        related_name='pa_questions',
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = 'order',
        unique_together = ('question_section', 'question')

# TODO @shital @wrufesh change QuestionSetUserType to QuestionSetQuestionPresenceCriteria


class QuestionSetUserType(BaseModel):
    question = models.ForeignKey(
        PerformanceAppraisalQuestion,
        on_delete=models.CASCADE,
        related_name='appraisal_user_type'
    )
    question_set = models.ForeignKey(
        PerformanceAppraisalQuestionSet,
        on_delete=models.CASCADE,
        related_name='appraisal_user_type'
    )
    branches = models.ManyToManyField(
        OrganizationBranch,
        related_name='+',
    )
    divisions = models.ManyToManyField(
        OrganizationDivision,
        related_name='+'
    )
    job_titles = models.ManyToManyField(
        EmploymentJobTitle,
        related_name='+'
    )
    employment_levels = models.ManyToManyField(
        EmploymentLevel,
        related_name='+'
    )
