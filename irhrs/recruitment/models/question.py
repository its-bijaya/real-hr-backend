from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import JSONField
from django.db import models

from irhrs.common.models import BaseModel, TimeStampedModel
from irhrs.core.validators import validate_description
from irhrs.questionnaire.models.questionnaire import Question
from irhrs.recruitment.constants import QUESTION_SET_CHOICES

USER = get_user_model()


class QuestionSet(BaseModel):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=1000, blank=True)
    form_type = models.CharField(
        choices=QUESTION_SET_CHOICES,
        max_length=30
    )
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class RecruitmentQuestions(BaseModel):
    is_mandatory = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField()
    question = models.ForeignKey(
        to=Question,
        related_name='+',
        on_delete=models.CASCADE
    )
    question_section = models.ForeignKey(
        to='RecruitmentQuestionSection',
        on_delete=models.CASCADE,
        related_name='recruitment_questions'
    )

    class Meta:
        ordering = 'order',
        unique_together = ('question_section', 'question')


class RecruitmentQuestionSection(BaseModel):
    title = models.CharField(
        max_length=255
    )
    description = models.TextField(
        blank=True,
        validators=[validate_description],
        max_length=settings.TEXT_FIELD_MAX_LENGTH
    )
    question_set = models.ForeignKey(
        to=QuestionSet,
        related_name='sections',
        on_delete=models.CASCADE
    )
    questions = models.ManyToManyField(
        to=Question,
        through=RecruitmentQuestions,
        through_fields=('question_section', 'question'),
        related_name='+'
    )

    class Meta:
        ordering = 'created_at',


class AbstractQuestionSetAnswers(TimeStampedModel):
    user = models.ForeignKey(
        USER,
        on_delete=models.SET_NULL,
        null=True
    )

    # data stores all the answers to questions and other unexpected fields
    data = JSONField(blank=True)

    class Meta:
        abstract = True
