from django.db import models
from django.db.models.fields import related
from irhrs.common.models import BaseModel
from irhrs.organization.models import FiscalYear
from django.contrib.auth import get_user_model

from irhrs.payroll.constants import VOLUNTARY_REBATE_DURATION_UNIT_CHOICES, \
    VOLUNTARY_REBATE_TYPE_CHOICES
from irhrs.payroll.models import RebateSetting

User = get_user_model()


class UserVoluntaryRebate(BaseModel):
    title = models.CharField(
        max_length=255
    )

    rebate = models.ForeignKey(
        RebateSetting, on_delete=models.CASCADE, related_name='voluntary_rebates', null=True)

    description = models.CharField(
        max_length=600
    )

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='voluntary_rebates'
    )

    fiscal_year = models.ForeignKey(
        FiscalYear,
        on_delete=models.CASCADE,
        related_name='voluntary_rebates'
    )

    duration_unit = models.CharField(
        max_length=20,
        choices=VOLUNTARY_REBATE_DURATION_UNIT_CHOICES
    )

    amount = models.FloatField()

    fiscal_months_amount = models.JSONField(null=True)



class UserVoluntaryRebateDocument(BaseModel):
    user_voluntary_rebate = models.ForeignKey(
        UserVoluntaryRebate,
        related_name='documents',
        on_delete=models.CASCADE
    )
    file_name = models.CharField(max_length=150)
    file = models.FileField()


# Voluntary rebate actions constants

(
    CREATE_REQUEST,
    CREATED,
    CREATE_REJECTED,
    DELETE_REQUEST,
    DELETED,
    DELETE_REJECTED
) = (
    'Requested',
    'Approved',
    'Denied',
    'Archive Requested',
    'Archived',
    'Archive Denied'
)

VOLUNTARY_REBATE_ACTION_CHOICES = (
    (CREATE_REQUEST, CREATE_REQUEST),
    (CREATED, CREATED),
    (CREATE_REJECTED, CREATE_REJECTED),
    (DELETE_REQUEST, DELETE_REQUEST),
    (DELETED, DELETED),
    (DELETE_REJECTED, DELETE_REJECTED),
)

class UserVoluntaryRebateAction(BaseModel):
    user_voluntary_rebate = models.ForeignKey(
        UserVoluntaryRebate,
        related_name='statuses',
        on_delete=models.CASCADE
    )

    action = models.CharField(
        max_length=20,
        choices=VOLUNTARY_REBATE_ACTION_CHOICES
    )
    remarks = models.CharField(
        max_length=255
    )
