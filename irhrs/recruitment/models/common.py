from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.db import models

from irhrs.common.models import AbstractLocation, BaseModel, SlugModel
from irhrs.core.validators import validate_title
from irhrs.document.utils import get_document_file_path
from irhrs.leave.constants.model_constants import MONTHLY
from irhrs.organization.models import Organization
from irhrs.recruitment.constants import (
    VERIFICATION_STATUS_CHOICES, PENDING,
    CURRENCY, NRS,
    SALARY_OPERATOR, SALARY_UNITS,
    EQUALS,
    QUESTION_TYPE_CHOICES,
    TEMPLATE_TYPE_CHOICES)
from irhrs.recruitment.models.location import City, Country


class Location(BaseModel, AbstractLocation):
    """Location table"""
    address = models.CharField(max_length=255)
    city_name = models.CharField(max_length=200, blank=True)
    city = models.ForeignKey(
        City,
        null=True,
        on_delete=models.SET_NULL,
        related_name='locations'
    )
    country = models.ForeignKey(
        Country,
        null=True,
        on_delete=models.SET_NULL,
        related_name='locations'
    )

    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)

    status = models.CharField(
        choices=VERIFICATION_STATUS_CHOICES,
        default=PENDING, max_length=30, db_index=True
    )

    def __str__(self):
        return self.address

    @property
    def district(self):
        return getattr(self.city, 'district', None)

    @property
    def province(self):
        return getattr(self.district, 'province', None)


class JobBenefit(BaseModel):
    """
    Service provided to employee by organization.
    """
    name = models.CharField(
        max_length=255,
        db_index=True,
        unique=True
    )
    status = models.CharField(
        choices=VERIFICATION_STATUS_CHOICES,
        default=PENDING,
        max_length=30,
        db_index=True
    )

    def __str__(self):
        return self.name


class JobCategory(SlugModel, BaseModel):
    """
    Category of job. Eg. IT and Telecommunications
    """
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True)
    name = models.CharField(max_length=250, db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = (('parent', 'name'), )


class Salary(BaseModel):
    """
    Model to store salary.

    Can store salary range or single salary value with or without operator

    *takes minimum salary if no operator available
    """
    currency = models.CharField(choices=CURRENCY, default=NRS, max_length=25,
                                db_index=True)
    operator = models.CharField(choices=SALARY_OPERATOR, null=True,
                                max_length=25, db_index=True)

    minimum = models.FloatField(null=True, blank=True, default=0,
                                validators=[MinValueValidator(limit_value=0)])
    maximum = models.FloatField(null=True, blank=True,
                                validators=[MinValueValidator(limit_value=0)])
    unit = models.CharField(choices=SALARY_UNITS, default=MONTHLY,
                            max_length=25, db_index=True)

    def __str__(self):
        return self.salary_repr

    @property
    def salary_repr(self):
        if self.maximum:
            return '{}. {:,.2f} - {:,.2f} {}'.format(
                self.currency, self.minimum, self.maximum, self.unit)
        elif self.minimum in [0.0, 0, None]:
            return 'Negotiable'
        return '{} {}. {:,.2f} {}'.format(
            self.operator if self.operator != EQUALS else '',
            self.currency,
            self.minimum,
            self.unit
        )


class Language(BaseModel):
    """Store available languages"""
    name = models.CharField(max_length=100, db_index=True, unique=True)
    status = models.CharField(choices=VERIFICATION_STATUS_CHOICES,
                              default=PENDING, max_length=25, db_index=True)
    alternative_names = ArrayField(
        models.CharField(max_length=255, blank=True),
        blank=True
    )
    relevance = models.IntegerField(null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('relevance',)


class AbstractSocialAccount(models.Model):
    """
    These days even pets have social media accounts we need to accommodate for
    such situations.
    """
    account_name = models.CharField(max_length=100, db_index=True)
    url = models.URLField(max_length=255, db_index=True)

    def __str__(self):
        return self.account_name

    class Meta:
        abstract = True


class AbstractDocument(models.Model):
    """
    Abstract model for documents
    """
    attachment = models.FileField(
        upload_to=get_document_file_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'bmp', 'pdf',
                                    'doc', 'docx', 'xls', 'xlsx', 'odt',
                                    'ods', 'ppt', 'pptx', 'txt'])]
    )

    def __str__(self):
        return str(self.attachment)

    def get_attachment(self):
        return self.attachment.url.split('/')[-1] if self.attachment else ''

    class Meta:
        abstract = True


class AbstractReferenceContact(models.Model):
    """
    This is a generic model to store contact information related to any other
    model. Used currently to store Applicant references' and client's contact
    person.
    """
    name = models.CharField(max_length=50, db_index=True)
    email = models.EmailField(blank=True)
    designation = models.CharField(max_length=100, blank=True)
    org_name = models.CharField(max_length=255, db_index=True, blank=True)
    phone_number = models.CharField(max_length=30)

    is_archived = models.BooleanField(
        default=False, help_text='When deleted, is_archived returns True')

    def archive(self):
        self.is_archived = True
        self.save()

    def __str__(self):
        return "{} - {}".format(self.name, self.is_archived)

    class Meta:
        abstract = True


class Question(BaseModel):
    name = models.CharField(max_length=200, blank=True)
    question = models.TextField()
    description = models.TextField(blank=True)

    question_type = models.CharField(
        max_length=50,
        choices=QUESTION_TYPE_CHOICES
    )

    order = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(limit_value=1)]
    )
    is_required = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)


# Common class for letter and report template [mimic letter template from irhrs]
class Template(BaseModel, SlugModel):
    title = models.CharField(
        max_length=255, validators=[validate_title]
    )
    message = models.TextField()
    type = models.CharField(
        max_length=30, choices=TEMPLATE_TYPE_CHOICES
    )
    organization = models.ForeignKey(
        to=Organization,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.get_type_display() + ' ' + self.title
