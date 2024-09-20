from itertools import chain

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.db import models
from django.forms.utils import pretty_name

from irhrs.common.models.abstract import BaseModel
from irhrs.core.utils.common import get_upload_path
from irhrs.organization.models import Organization
from ..constants import EXPORT_STATUS_CHOICES, EXPORTED_AS_CHOICES, QUEUED
from ...permission.models import HRSPermission

USER = get_user_model()


class Export(BaseModel):
    """
    Keep record of exports
    """
    user = models.ForeignKey(USER, related_name="exports", on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, related_name="exports", on_delete=models.SET_NULL, null=True)

    # name of export given by user
    name = models.CharField(max_length=150, default="Unnamed")

    # Export type is maintained by views allowing export function
    # For each view this key should be different
    export_type = models.CharField(max_length=50)

    exported_as = models.CharField(choices=EXPORTED_AS_CHOICES, max_length=10,
                                   db_index=True)
    export_file = models.FileField(
        upload_to=get_upload_path,
        null=True, blank=True,
        validators=[FileExtensionValidator(
            allowed_extensions=list(chain.from_iterable(settings.ACCEPTED_FILE_FORMATS.values()))
        )]
    )

    status = models.CharField(choices=EXPORT_STATUS_CHOICES, max_length=10, default=QUEUED,
                              db_index=True)
    remarks = models.CharField(max_length=255, blank=True)
    traceback = models.TextField(blank=True)
    associated_permissions = models.ManyToManyField(to=HRSPermission)

    def __str__(self):
        return f"{self.title} - {self.created_at.date()} by {self.user.full_name}"

    @property
    def title(self):
        return f"{pretty_name(self.export_type)}- {self.name}"
