from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from irhrs.common.models import BaseModel
from irhrs.organization.models import Organization

USER = get_user_model()


class PayrollApprovalSetting(BaseModel):
    """
    Approval Level Settings of payroll
    """
    user = models.ForeignKey(USER, related_name='payroll_approval_settings',
                             on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, related_name='payroll_approval_settings',
                                     on_delete=models.CASCADE)
    approval_level = models.SmallIntegerField(validators=[MinValueValidator(limit_value=0)])

    class Meta:
        unique_together = (('organization', 'user'), ('organization', 'approval_level'))
        ordering = ('approval_level',)
