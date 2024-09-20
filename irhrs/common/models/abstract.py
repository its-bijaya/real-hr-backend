from cuser.fields import CurrentUserField
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db.models import JSONField
from django.db import models

from irhrs.core.constants.interviewer import PROCESS_STATUS_CHOICES, PENDING
from irhrs.core.constants.user import CONTACT_CHOICES, MOBILE
from irhrs.core.slugify import unique_slugify
from irhrs.core.utils.common import get_upload_path
from irhrs.core.validators import validate_future_datetime


class IRHRSModel(models.Model):
    class Meta:
        abstract = True


class CuserModel(models.Model):
    created_by = CurrentUserField(
        add_only=True,
        related_name="%(app_label)s_%(class)s_created",
        on_delete=models.SET_NULL,
        null=True
    )

    modified_by = CurrentUserField(
        related_name="%(app_label)s_%(class)s_modified",
        on_delete=models.SET_NULL,
        null=True
    )

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at', '-modified_at')
        abstract = True


class BaseModel(CuserModel, TimeStampedModel, IRHRSModel):
    class Meta:
        ordering = ('-created_at', '-modified_at')
        abstract = True


class SlugModel(models.Model):
    slug = models.SlugField(unique=True, max_length=255, blank=True)

    class Meta:
        abstract = True

    def _get_slug_text(self):
        assert any([hasattr(self, 'name'), hasattr(self, 'title')])
        slug_text = ''
        if hasattr(self, 'name'):
            slug_text = self.name.lower()
        elif hasattr(self, 'title'):
            slug_text = self.title.lower()
        return slug_text

    def _get_previous_slug_text(self):
        if self.id:
            _pre_data = self.__class__.objects.get(id=self.id)
            return _pre_data._get_slug_text()
        return None

    def save(self, *args, **kwargs):
        slug_text = self._get_slug_text()
        pre_slug_text = self._get_previous_slug_text()
        if not self.slug or slug_text != pre_slug_text:
            unique_slugify(self, slug_text)
        return super().save(*args, **kwargs)


class AbstractLocation(models.Model):
    street = models.CharField(max_length=255, db_index=True, blank=True)
    city = models.CharField(max_length=100, db_index=True, blank=True)
    country_ref = models.ForeignKey(
        to='recruitment.Country', related_name="+", on_delete=models.CASCADE,
        default=603, blank=True, db_index=True
    )
    province = models.ForeignKey(
        to='recruitment.Province', related_name="+", on_delete=models.CASCADE,
        null=True, blank=True
    )
    district = models.ForeignKey(
        to='recruitment.District', related_name="+", on_delete=models.CASCADE,
        null=True, blank=True
    )

    address = models.CharField(max_length=255, db_index=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    postal_code = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def country(self):
        return self.country_ref.name


class AbstractPhoneNumber(models.Model):
    """
    Abstract phone number fields to maintain "only" phone numbers
    """
    number = models.CharField(max_length=25, db_index=True, blank=True)
    number_type = models.CharField(
        choices=CONTACT_CHOICES, max_length=10, blank=True,
        db_index=True)

    def __str__(self):
        return str(self.number)

    class Meta:
        abstract = True


class AbstractInterviewerModel(BaseModel):
    status = models.CharField(
        choices=PROCESS_STATUS_CHOICES,
        default=PENDING,
        max_length=20,
        db_index=True
    )
    location = models.CharField(max_length=255, blank=True)
    scheduled_at = models.DateTimeField(null=True, validators=[validate_future_datetime])

    class Meta:
        abstract = True


class AbstractInterviewerAnswerModel(BaseModel):
    data = JSONField(blank=True, null=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=PROCESS_STATUS_CHOICES, default=PENDING,
                              db_index=True)

    class Meta:
        abstract = True


class AbstractDocumentModel(BaseModel):
    attachment = models.FileField(
        upload_to=get_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=settings.ACCEPTED_FILE_FORMATS_LIST)]
    )
    name = models.CharField(max_length=255, default='Unnamed')

    class Meta:
        abstract = True

    def __str__(self):
        return self.name
