from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.db import models

from irhrs.common.models import AbstractLocation, AbstractPhoneNumber
from irhrs.core.constants.user import ADDRESS_TYPES, DEPENDENT_DOCUMENT_TYPES, PERMANENT, CONTACT_OF, SELF
from irhrs.core.utils.common import get_upload_path
from irhrs.core.validators import validate_has_digit, validate_invalid_chars, validate_title, validate_address, validate_past_date
from irhrs.common.models import SlugModel, BaseModel

USER = get_user_model()


class UserAddress(BaseModel, AbstractLocation):
    """
    Model to hold the information RealHRsoft user's address.
    """
    user = models.ForeignKey(
        USER,
        related_name='addresses',
        on_delete=models.CASCADE,
        editable=False
    )
    address_type = models.CharField(
        max_length=10, choices=ADDRESS_TYPES,
        default=PERMANENT
    )

    class Meta:
        ordering = ('address',)
        unique_together = ('user', 'address_type',)

    def __str__(self):
        return f"Address of {self.user} - {self.address}"


class UserContactDetail(BaseModel, SlugModel, AbstractPhoneNumber):
    user = models.ForeignKey(USER,
                             related_name='contacts',
                             on_delete=models.CASCADE,
                             editable=False)
    contact_of = models.CharField(choices=CONTACT_OF, max_length=15,
                                  default=SELF)
    name = models.CharField(max_length=255,
                            validators=[validate_title],
                            blank=True)
    address = models.CharField(max_length=255,
                               validators=[validate_address], )
    emergency = models.BooleanField(default=False)
    email = models.EmailField(blank=True)
    is_dependent = models.BooleanField(default=False)
    date_of_birth = models.DateField(
        validators=[validate_past_date],
        blank=True, null=True
    )
    occupation = models.CharField(max_length=255, blank=True, default='')
    attachment = models.FileField(
        upload_to=get_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=settings.ACCEPTED_FILE_FORMATS_LIST)],
        blank=True, null=True
    )
    dependent_id_type = models.IntegerField(choices=DEPENDENT_DOCUMENT_TYPES, null=True)
    dependent_id_number = models.CharField(
        max_length=50,
        default='',
        validators=[validate_invalid_chars, validate_has_digit]
    )

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return f"Contact of {self.user} - {self.contact_of} -" \
               f"{self.number}"


