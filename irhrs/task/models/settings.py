from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from irhrs.common.models import BaseModel
from irhrs.organization.models import Organization
from irhrs.hris.models import User


(HOUR, PIECE, DAY) = ("hour", "piece", "day")

UNIT_CHOICES = (
    (HOUR, HOUR),
    (PIECE, PIECE),
    (DAY, DAY)
)


class TaskSettings(BaseModel):
    """
    Organization Specific task configuration
    """
    organization = models.ForeignKey(to=Organization, on_delete=models.CASCADE,
                                     related_name='task_settings')
    can_assign_to_higher_employment_level = models.BooleanField(default=True)

    @classmethod
    def get_for_organization(cls, organization):
        instance = cls.objects.filter(organization=organization).first()
        if not instance:
            instance = cls(organization=organization, can_assign_to_higher_employment_level=True)
        return instance


class Activity(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(max_length=600, null=True, blank=True)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)
    employee_rate = models.FloatField(
        validators=[MinValueValidator(0)]
    )
    client_rate = models.FloatField(
        validators=[MinValueValidator(0)]
    )

    def __str__(self):
        return f"Activity: {self.name}"


class Project(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(max_length=600)
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    is_billable = models.BooleanField()

    def __str__(self):
        return f"Project: {self.name}"


class UserActivityProject(BaseModel):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="user_activity_projects"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="user_activity_projects"
    )
    activity = models.ForeignKey(
        Activity, on_delete=models.CASCADE, related_name="user_activity_projects"
    )

    is_billable = models.BooleanField()
    employee_rate = models.FloatField(default=0)
    client_rate = models.FloatField(default=0)

    class Meta:
        unique_together = ('user', 'activity', 'project')

    def __str__(self):
        return f"{self.project} - {self.user} - {self.activity}"

