from django.db import models

from irhrs.common.models import BaseModel, SlugModel
from irhrs.core.validators import validate_natural_number, validate_title


class OrganizationVision(BaseModel, SlugModel):
    """
    Vision can only exist once for the organization
    that's why using OneToOneField for the organization.
    """
    title = models.TextField(validators=[validate_title])
    organization = models.OneToOneField(
        to='organization.Organization', related_name='vision',
        on_delete=models.CASCADE, editable=False
    )

    class Meta:
        ordering = ('title',)
        unique_together = ('organization', 'title',)

    def __str__(self):
        return "{}'s Vision - {}".format(
            self.organization.abbreviation, self.title)


class OrganizationMission(BaseModel, SlugModel):
    """
    Organization may contain multiple missions to achieve the vision.

    Using models.FloatField on ordering field because of parent child relation
    on the existence of the mission. For eg: 1.1, 1.2, 1.3 could be the ordering
    fields.
    """
    organization = models.ForeignKey(
        to='organization.Organization', related_name='missions',
        on_delete=models.CASCADE, editable=False
    )
    title = models.CharField(
        max_length=255, validators=[validate_title],
        help_text="Short title on the mission of the organization/company.",
    )
    description = models.TextField(
        blank=True,
        help_text="Description on the mission."
    )
    parent = models.ForeignKey('self',
                               related_name='child_missions',
                               blank=True, null=True,
                               on_delete=models.CASCADE)
    order_field = models.FloatField(
        default=1, validators=[validate_natural_number])

    class Meta:
        ordering = ('order_field',)

    def __str__(self):
        return "{}'s Mission - {}".format(
            self.organization.abbreviation, self.title)
