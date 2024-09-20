from itertools import chain

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator

from irhrs.common.models.notification_template import NotificationTemplate
from irhrs.common.models.commons import SlugModel, BaseModel
from irhrs.core.constants.common import NOTIFICATION_TYPE_CHOICES
from irhrs.core.constants.organization import MORAL_CHOICES, DO
from irhrs.core.validators import validate_title
from irhrs.organization.managers import NotificationTemplateMapManager
from irhrs.core.utils.common import get_upload_path
from .organization import Organization


class OrganizationEthics(BaseModel, SlugModel):
    """
    This model usually holds the data on do's and don'ts of the organization,
    also should cover the scenario of rules or regulation of the organization
    as well.
    """
    organization = models.ForeignKey(Organization,
                                     on_delete=models.CASCADE,
                                     related_name='ethics',
                                     editable=False)
    title = models.CharField(max_length=255, validators=[validate_title])
    description = models.TextField(blank=True, max_length=settings.TEXT_FIELD_MAX_LENGTH)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL,
                               null=True, blank=True,
                               related_name='child_ethics')
    moral = models.CharField(max_length=15, choices=MORAL_CHOICES, default=DO)
    published = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    attachment = models.FileField(
        null=True,
        upload_to=get_upload_path,
        validators=[FileExtensionValidator(
            allowed_extensions=list(chain.from_iterable(settings.ACCEPTED_FILE_FORMATS.values()))
        )]
    )
    is_downloadable = models.BooleanField(default=True)
    document_text = models.TextField(blank=True, max_length=10000)

    class Meta:
        ordering = ('title', 'moral',)
        unique_together = ('organization', 'title')
        verbose_name_plural = 'Organization Ethics'

    def __str__(self):
        return self.title


def default_active_status(*args):
    return ["Default"]


class NotificationTemplateMap(BaseModel):
    organization = models.ForeignKey(
        to=Organization,
        on_delete=models.CASCADE,
        related_name='templates'
    )
    template = models.ForeignKey(
        to=NotificationTemplate,
        on_delete=models.CASCADE
    )
    is_active = models.BooleanField(
        default=False
    )
    active_status = ArrayField(
        base_field=models.CharField(max_length=32),
        default=default_active_status
    )
    objects = NotificationTemplateMapManager()

    def __str__(self):
        return f"{self.template.get_type_display()} for {self.organization}"
