from django.db import models

from irhrs.common.models import BaseModel
from irhrs.hris.models import User
from irhrs.organization.models import Organization


class Operation(BaseModel):
    """
    Model to record Operations in unit of work
    """
    title = models.CharField(max_length=255)
    description = models.TextField(max_length=600, blank=True)
    organization = models.ForeignKey(
        to=Organization,
        related_name='operations',
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('title', 'organization')
        ordering = ('-modified_at',)

    def __str__(self):
        return f"Operation: {self.title} - {self.organization}"


class OperationCode(BaseModel):
    """
    Model to record Operation Codes
    """
    title = models.CharField(max_length=255)
    description = models.TextField(max_length=600, blank=True)
    organization = models.ForeignKey(
        to=Organization,
        related_name='operation_codes',
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('title', 'organization')
        ordering = ('-modified_at',)

    def __str__(self):
        return f"Operation: {self.title} - {self.organization}"


(HOUR, PIECE) = ("hour", "piece")

UNIT_CHOICES = (
    (HOUR, HOUR),
    (PIECE, PIECE)
)


class OperationRate(BaseModel):
    """Relate operation with operation_code with a rate"""
    operation = models.ForeignKey(
        to=Operation,
        on_delete=models.CASCADE,
        related_name='rates'
    )
    operation_code = models.ForeignKey(
        to=OperationCode,
        on_delete=models.CASCADE,
        related_name='rates'
    )
    rate = models.FloatField()
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)

    class Meta:
        unique_together = ('operation', 'operation_code')
        ordering = ('-modified_at',)

    def __str__(self):
        return f"Rate: {self.operation.title} - {self.operation_code.title} - {self.rate} " \
               f"- {self.operation.organization}"


class UserOperationRate(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_operation_rate")
    rate = models.ForeignKey(
        OperationRate,
        on_delete=models.CASCADE,
        related_name="user_operation_rate"
    )

    class Meta:
        unique_together = ('user', 'rate')

    def __str__(self):
        return f"{self.user} - {self.rate}"
