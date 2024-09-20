from django.core.validators import MinValueValidator
from django.db import models

from irhrs.common.models import BaseModel
from irhrs.organization.models import OrganizationDivision
from irhrs.users.models import UserExperience


class ResultArea(BaseModel):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, max_length=600)
    division = models.ForeignKey(OrganizationDivision,
                                 on_delete=models.CASCADE,
                                 related_name='division_result_areas')

    class Meta(BaseModel.Meta):
        unique_together = ('title', 'division',)

    def __str__(self):
        return f"{self.title} created by {self.created_by}" \
            if self.created_by else f"{self.title}"


class CoreTask(BaseModel):
    result_area = models.ForeignKey(ResultArea, on_delete=models.CASCADE,
                                    related_name='core_tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, max_length=600)
    order = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(limit_value=1)]
    )

    class Meta:
        unique_together = ('result_area', 'order',)
        ordering = ('order',)

    def __str__(self):
        return f"Core Task of Result area: {self.result_area}"


class UserResultArea(BaseModel):
    user_experience = models.ForeignKey(UserExperience,
                                        related_name='user_result_areas',
                                        on_delete=models.CASCADE)
    result_area = models.ForeignKey(ResultArea,
                                    related_name='associated_users',
                                    on_delete=models.CASCADE)
    core_tasks = models.ManyToManyField(CoreTask)
    key_result_area = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user_experience', 'result_area',)

    def __str__(self):
        return f"User: {self.user_experience}, " \
               f"Result Area: {self.result_area}, key {self.key_result_area}"
