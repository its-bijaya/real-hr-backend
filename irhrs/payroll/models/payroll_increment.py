from django.contrib.auth import get_user_model
from django.db import models
from irhrs.common.models import BaseModel

Employee = get_user_model()


class PayrollIncrement(BaseModel):
    """
    This model is to record increments in payroll without change in package or
    experience
    """
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE,
        related_name='payroll_increments'
    )
    percentage_increment = models.FloatField()
    effective_from = models.DateField()
    remarks = models.TextField(max_length=600)



