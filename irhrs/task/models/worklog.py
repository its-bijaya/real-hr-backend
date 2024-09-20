from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from rest_framework.exceptions import ValidationError

from irhrs.common.models import BaseModel
from irhrs.task.models import Task, CoreTask
from irhrs.task.models.settings import Project, Activity


USER = get_user_model()

def validate_score(score):
    if not (1 <= score <= 10):
        raise ValidationError("Score must range from 1-10")
    return score


class WorkLog(BaseModel):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="daily_tasks", null=True
    )
    activity = models.ForeignKey(
        Activity, on_delete=models.CASCADE, related_name="daily_tasks", null=True
    )
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="daily_tasks", null=True
    )
    core_task = models.ManyToManyField(
        CoreTask, related_name="daily_tasks", blank=True
    )
    sender = models.ForeignKey(
        to=USER,
        related_name='daily_tasks_sender',
        on_delete=models.SET_NULL,
        null=True
    )
    receiver = models.ForeignKey(
        to=USER,
        related_name='daily_tasks_receiver',
        on_delete=models.SET_NULL,
        null=True
    )
    unit = models.FloatField(null=True)
    total_amount = models.FloatField(default=0, validators=[MinValueValidator(0)], null=True)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    activity_description = models.CharField(max_length=600)
    attachment = models.FileField(blank=True, null=True)

    def __str__(self):
        return f"{self.project} - {self.activity}"


(
    TODO,
    DRAFT,
    REQUESTED,
    APPROVED,
    DENIED,
    FORWARDED,
    CONFIRMED,
    CANCELED,
    ACKNOWLEDGED,
    SENT
) = (
    "todo",
    "draft",
    "requested",
    "approved",
    "denied",
    "forwarded",
    "confirmed",
    "canceled",
    "acknowledged",
    "sent"
)
WORKLOG_ACTION = (
    (TODO, TODO),
    (DRAFT, DRAFT),
    (REQUESTED, REQUESTED),
    (APPROVED, APPROVED),
    (DENIED, DENIED),
    (FORWARDED, FORWARDED),
    (CONFIRMED, CONFIRMED),
    (CANCELED, CANCELED),
    (ACKNOWLEDGED, ACKNOWLEDGED),
    (SENT, SENT)
)


class WorkLogAction(BaseModel):
    worklog = models.ForeignKey(
        WorkLog, on_delete=models.CASCADE, related_name="worklog_actions"
    )
    action = models.CharField(
        max_length=20,
        choices=WORKLOG_ACTION
    )
    action_performed_by = models.ForeignKey(
        to=USER, related_name='sent_worklogs', on_delete=models.CASCADE
    )
    remarks = models.TextField()
    score = models.PositiveSmallIntegerField(null=True, validators=[validate_score])
    action_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.action_performed_by} " \
               f"{self.action} for " \
               f"{self.worklog} with remarks {self.remarks}"
