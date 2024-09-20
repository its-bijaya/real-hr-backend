from django.db import models

from irhrs.core.constants.common import (
    RELIGION_AND_ETHNICITY_CATEGORY,
    DOCUMENT_TYPE_ASSOCIATION_CHOICES, BOTH,
    ORGANIZATION_ASSET_CHOICES)
from irhrs.core.utils.common import get_upload_path
from irhrs.core.validators import validate_title, validate_image_file_extension
from ..models.abstract import BaseModel, SlugModel, AbstractLocation


class Industry(BaseModel, SlugModel):
    """
    Model that holds the information on the industry types of the organization.
    """
    name = models.CharField(max_length=255, unique=True, db_index=True)

    def __str__(self):
        return f"{self.name}"


class DocumentCategory(BaseModel, SlugModel):
    """
    Model that holds the information on the document categories
    for the overall system.

    Overall system as in:
    Document Categories will apply on user's document/organization's document
    or can be associated anywhere wherever document attachment is provided.
    """
    name = models.CharField(max_length=255, unique=True, db_index=True)
    associated_with = models.CharField(
        max_length=15,
        choices=DOCUMENT_TYPE_ASSOCIATION_CHOICES,
        default=BOTH,
        db_index=True
    )

    @property
    def has_associated_documents(self):
        #          user documents                   organization documents
        related_names = {
            'user_documents',
            'associated_documents'
            # 'trainer_attachments'
        }

        def exists(_related_names):
            for related_name in _related_names:
                yield getattr(self, related_name).exists()

        return any(exists(related_names))

    def __str__(self):
        return f"{self.name}"


class Disability(BaseModel, SlugModel):
    title = models.CharField(max_length=255, unique=True,
                             validators=[validate_title])
    description = models.TextField(blank=True)

    def __str__(self):
        return f"Disability of {self.title}"


class ReligionAndEthnicity(BaseModel, SlugModel):
    """
    Model to hold the static information on religion and ethnicity.

    The information on this table could be in constants as well, but to handle
    the purpose of user manipulating the data themselves, this model has been
    maintained.
    """
    name = models.CharField(max_length=50, unique=True, db_index=True,
                            validators=[validate_title])
    category = models.CharField(max_length=10,
                                choices=RELIGION_AND_ETHNICITY_CATEGORY,
                                db_index=True)

    class Meta:
        ordering = ('name', 'category')

    def __str__(self):
        return f"{self.name} - {self.category}"


class HolidayCategory(BaseModel, SlugModel):
    """
    Model that stores the Holiday category. The holiday category encapsulates
    public, and organizational holidays.

    Examples: Public Holiday, Festival Holiday, etc.
    """
    name = models.CharField(max_length=150,
                            unique=True,
                            validators=[validate_title])
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name}"


class Bank(BaseModel, AbstractLocation, SlugModel):
    name = models.CharField(max_length=255,
                            validators=[validate_title])
    logo = models.ImageField(upload_to=get_upload_path, null=True,
                             validators=[validate_image_file_extension])
    acronym = models.CharField(max_length=15)

    def __str__(self):
        return self.name


class EquipmentCategory(BaseModel, SlugModel):
    """
       Model that stores the Equipment category. The equipment category encapsulates
       equipment category name and type.

       Examples: name: Chair,Monitor and type: Intangible Tangible, etc.
       """
    name = models.CharField(max_length=50, validators=[validate_title], unique=True)
    type = models.CharField(max_length=10,
                            choices=ORGANIZATION_ASSET_CHOICES,
                            db_index=True)

    def __str__(self):
        return f"{self.name}"
