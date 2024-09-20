from django.contrib.auth import get_user_model
from django.db.models import JSONField
from django.db import models

from irhrs.common.models.abstract import AbstractInterviewerModel
from irhrs.questionnaire.models.questionnaire import Question

User = get_user_model()


class ExitInterviewQuestionSet(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=1000, blank=True)
    questions = models.ManyToManyField(Question)
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class ExitInterview(AbstractInterviewerModel):
    separation = models.OneToOneField(
        to='hris.EmployeeSeparation',
        on_delete=models.CASCADE,
        related_name='exit_interview'
    )
    question_set = models.ForeignKey(
        ExitInterviewQuestionSet,
        on_delete=models.PROTECT,
        related_name='exit_interviews'
    )
    interviewer = models.ForeignKey(
        User,
        related_name='interview_response',
        on_delete=models.CASCADE
    )
    data = JSONField(blank=True, null=True)
    expires_at = models.DateTimeField(null=True, blank=True)
