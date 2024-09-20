from itertools import chain

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models

from irhrs.common.models import BaseModel, SlugModel
from irhrs.core.constants.common import UNPUBLISHED, PUBLISH_UNPUBLISH_CHOICES
from irhrs.core.validators import validate_natural_number, validate_title


class HRPolicyHeading(BaseModel, SlugModel):
    """
    This model covers the heading of the HR Policy.
    """
    organization = models.ForeignKey(
        'organization.Organization', related_name='policies',
        on_delete=models.CASCADE)
    title = models.CharField(max_length=255,
                             validators=[validate_title])
    description = models.TextField(blank=True)
    status = models.CharField(
        choices=PUBLISH_UNPUBLISH_CHOICES, default=UNPUBLISHED, max_length=50, db_index=True)
    order_field = models.PositiveSmallIntegerField(
        default=1, validators=[validate_natural_number])

    class Meta:
        ordering = ('order_field',)
        unique_together = ('order_field', 'title',)

    def __str__(self):
        return f"{self.title} - {self.organization.abbreviation}"


class HRPolicyBody(BaseModel, SlugModel):
    """
    This model covers the body of the certain heading of the HR Policy
    """
    heading = models.ForeignKey(
        HRPolicyHeading, on_delete=models.CASCADE, related_name="policy_bodies")
    title = models.CharField(max_length=255, help_text='Sub-title of the body.',
                             validators=[validate_title])
    body = models.TextField(blank=True)
    attachment = models.FileField(
        upload_to="policy-vision/attachments/",
        null=True, blank=True,
        validators=[FileExtensionValidator(
            allowed_extensions=list(chain.from_iterable(settings.ACCEPTED_FILE_FORMATS.values()))
        )]
    )
    parent = models.ForeignKey('self', related_name='child_bodies',
                               on_delete=models.SET_NULL, null=True, blank=True)
    order_field = models.FloatField(
        default=1, validators=[validate_natural_number])

    class Meta:
        ordering = ('order_field',)
        unique_together = ('title', 'order_field',)

    def __str__(self):
        return f"Policy Body of {self.heading}"
