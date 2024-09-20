from django.contrib.auth.models import Group
from django.db import models
from django.utils.translation import gettext_lazy as _

from irhrs.common.models import BaseModel
from irhrs.core.constants.common import PERMISSION_CATEGORY_CHOICES


class HRSPermission(models.Model):
    """
    Model to store Permissions for this HR System
    """
    name = models.CharField(_('Name'), max_length=255, unique=True)
    code = models.CharField(_('Permission Code'), unique=True, max_length=5,
                            db_index=True)
    description = models.TextField(_('Description'), blank=True)
    organization_specific = models.BooleanField(default=True)
    category = models.CharField(_('Category'),
                                choices=PERMISSION_CATEGORY_CHOICES,
                                max_length=50,
                                db_index=True)

    def __str__(self):
        return f"{self.code}: {self.name}"


class OrganizationGroup(BaseModel):
    organization = models.ForeignKey(
        null=True,
        to='organization.Organization',
        on_delete=models.CASCADE,
        related_name='organization_permission_groups'
    )
    group = models.ForeignKey(
        to=Group,
        on_delete=models.CASCADE,
        related_name='organization_permission_groups'
    )
    permissions = models.ManyToManyField(
        to=HRSPermission,
    )

    def __str__(self):
        org = self.organization if self.organization else 'Commons'
        return f"{self.group} at {org}"
