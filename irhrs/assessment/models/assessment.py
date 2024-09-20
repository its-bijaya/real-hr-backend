from django.contrib.auth import get_user_model
from django.db import models

from irhrs.assessment.models.helpers import ASSESSMENT_STATUS_CHOICES
from irhrs.common.models import BaseModel
from irhrs.core.validators import (validate_title, validate_description, validate_wysiwyg_field,
                                   MinMaxValueValidator)
from irhrs.organization.models import Organization
from irhrs.questionnaire.models.questionnaire import Question, Answer
from irhrs.training.models import Training

USER = get_user_model()


class AssessmentQuestions(BaseModel):
    is_mandatory = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField()
    question = models.ForeignKey(
        to=Question,
        related_name='+',
        on_delete=models.CASCADE
    )
    assessment_section = models.ForeignKey(
        to='assessment.AssessmentSection',
        on_delete=models.CASCADE,
        related_name='section_questions'
    )

    class Meta:
        ordering = 'order',
        unique_together = ('assessment_section', 'question')


class AssessmentSet(BaseModel):
    organization = models.ForeignKey(
        to=Organization,
        related_name='assessments',
        on_delete=models.CASCADE
    )
    title = models.CharField(
        max_length=255,
        validators=[validate_title],
    )
    description = models.TextField(
        blank=True,
        validators=[validate_description]
    )
    duration = models.DurationField()
    # as per new implementation total weightage has made 0 for default
    total_weightage = models.FloatField(default=0)
    marginal_weightage = models.FloatField(default=0)
    marginal_percentage = models.PositiveIntegerField(
        validators=[MinMaxValueValidator(1, 100)],
        default=50
    )
    total_questions = models.PositiveIntegerField(default=0)

    @property
    def assigned_users_count(self):
        # Care for unique users if multiple attempts are allowed.
        return self.assessments.count()

    def __str__(self):
        return self.title

    class Meta:
        unique_together = ('organization', 'title')


class AssessmentSection(BaseModel):
    title = models.CharField(
        max_length=255
    )
    description = models.TextField(
        blank=True,
        validators=[validate_description]
    )
    assessment_set = models.ForeignKey(
        to=AssessmentSet,
        related_name='sections',
        on_delete=models.CASCADE
    )
    questions = models.ManyToManyField(
        to=Question,
        through=AssessmentQuestions,
        through_fields=('assessment_section', 'question'),
        related_name='+'
    )
    total_weightage = models.FloatField()
    marginal_weightage = models.FloatField()

    def __str__(self):
        return self.title

    class Meta:
        ordering = ('created_at',)


class UserAssessment(BaseModel):
    """
    This model is filled when the HR/concerned authority generates Assessment for the user.
    """
    # TODO: @Shital (user, assessment_set) unique together
    user = models.ForeignKey(
        to=USER,
        related_name='assessments',
        on_delete=models.CASCADE,
        help_text="The user that gave this assessment."
    )
    assessment_set = models.ForeignKey(
        to=AssessmentSet,
        on_delete=models.CASCADE,
        related_name='assessments',
        help_text='The set of questions user appeared for.'
    )
    status = models.CharField(
        max_length=20,
        choices=ASSESSMENT_STATUS_CHOICES,
        help_text='Status of this assessment: Pending, In Progress, Completed, etc.',
        db_index=True
    )

    started_at = models.DateTimeField(
        null=True,
        help_text='When did the user started taking this assessment?'
    )
    ended_at = models.DateTimeField(
        null=True,
        help_text='When did this user completed this assessment?'
    )
    score = models.FloatField(
        null=True,
        help_text='How much did the user achieve in this assessment?'
    )
    remarks = models.TextField(
        blank=True,
        validators=[validate_description],
        help_text='Any remarks for this test from user?'
    )
    optional_remarks = models.TextField(
        blank=True,
        validators=[validate_description],
        help_text='Any extra remarks for this test? Other from User.'
    )
    associated_training = models.ForeignKey(
        to=Training,
        related_name='+',
        on_delete=models.SET_NULL,
        null=True
    )

    expiry_date = models.DateTimeField(
        help_text="Expiry Date for user assessment.",
        null=True
    )
    expired = models.BooleanField(default=False)

    def __str__(self):
        return (
            self.get_status_display()
            + ' -> '
            + str(self.assessment_set)
            + ' '
            + str(self.user)
        )


class QuestionResponse(BaseModel):
    # Preparation Phase.
    # Following fields will be pre-filled when assessment begins.
    user_assessment = models.ForeignKey(
        to=UserAssessment,
        related_name='question_responses',
        on_delete=models.CASCADE
    )
    section = models.ForeignKey(
        to=AssessmentSection,
        related_name='question_responses',
        on_delete=models.CASCADE
    )
    question = models.ForeignKey(
        to=Question,
        on_delete=models.CASCADE,
        related_name='+'
    )
    order = models.PositiveSmallIntegerField(
        help_text='Internal Field. Will use this to track next questions and so on.'
    )
    is_mandatory = models.BooleanField(default=True)

    # User Fields.
    answers = models.ManyToManyField(
        to=Answer,
        help_text='All the choices user can make.'
    )
    status = models.CharField(
        max_length=20,
        choices=ASSESSMENT_STATUS_CHOICES,
        db_index=True
    )
    score = models.FloatField(
        null=True,
        validators=[
            MinMaxValueValidator(
                min_value=0,
                max_value=100
            ),
        ],
        help_text="If Linear Scale, Keeps user's response."
                  'Else, score if correct answer. [for MCQs].'
                  'Else, Score from reviewer'
    )
    response = models.TextField(
        blank=True,
        validators=[validate_wysiwyg_field],
        help_text='This will be used for both short & Long text answers.'
    )

    remarks = models.TextField(
        blank=True,
        validators=[validate_wysiwyg_field],
        help_text='This will be used for any additional remarks from the reviewer.'
    )

    class Meta:
        ordering = 'order',
