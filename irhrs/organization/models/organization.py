from itertools import chain

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.functional import cached_property

from irhrs.common.models import (BaseModel, SlugModel, AbstractLocation,
                                 Industry)
from irhrs.core.constants.common import ORGANIZATION
from irhrs.core.constants.organization import (ORGANIZATION_OWNERSHIP,
                                               ORGANIZATION_SIZE)
from irhrs.core.fields import JSONTextField
from irhrs.core.utils.common import get_upload_path, get_complete_url
from irhrs.core.validators import (validate_title, validate_json_contact,
                                   validate_has_digit, validate_invalid_chars, validate_past_date,
                                   DocumentTypeValidator, validate_image_file_extension)
from irhrs.organization.utils.cache import build_application_settings_cache

USER = get_user_model()


class Organization(BaseModel, SlugModel):
    name = models.CharField(
        max_length=255, validators=[validate_title],
        help_text="Name of the Organization/Company.",
    )
    abbreviation = models.CharField(
        max_length=15, help_text='Short form of the Organization/Company.'
    )
    about = models.TextField(max_length=6000)

    parent = models.ForeignKey(
        to='self', related_name='child_organizations', null=True, blank=True,
        on_delete=models.SET_NULL
    )
    industry = models.ForeignKey(
        to=Industry, related_name='organizations', null=True, blank=True,
        on_delete=models.SET_NULL
    )
    organization_head = models.ForeignKey(
        to=USER, related_name='org_head_of', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    administrators = models.ManyToManyField(
        to=USER, blank=True, related_name="admin_of"
    )

    ownership = models.CharField(choices=ORGANIZATION_OWNERSHIP, max_length=15)
    size = models.CharField(
        choices=ORGANIZATION_SIZE, max_length=25,
        help_text='Size of the Organization/Company'
    )
    website = models.URLField(blank=True)
    established_on = models.DateField(
        null=True, validators=[validate_past_date]
    )
    email = models.EmailField(blank=True)
    contacts = JSONTextField(validators=[validate_json_contact])
    registration_number = models.CharField(
        max_length=50, blank=True,
        validators=[validate_has_digit, validate_invalid_chars]
    )
    vat_pan_number = models.CharField(
        max_length=50, blank=True,
        validators=[validate_has_digit, validate_invalid_chars])

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('created_at', 'name',)

    @cached_property
    def disabled_applications(self):
        disabled_apps = cache.get(f'disabled_applications_{self.id}')
        if disabled_apps is not None:
            return disabled_apps
        build_application_settings_cache(self)
        return cache.get(f'disabled_applications_{self.id}')

    @property
    def abstract_address(self):
        return self.address.address


class OrganizationAddress(BaseModel, AbstractLocation):
    """
    An organization contains only one particular address at the given time.

    Note:
    Organization address is maintained here in different model, as it adds the
    unnecessary fields on the main organization model. We are also doing this
    because organization address is not accessed every time when
    we query for the organization.
    """
    organization = models.OneToOneField(
        Organization, related_name='address', on_delete=models.CASCADE)
    mailing_address = models.TextField(blank=True)

    def __str__(self):
        return "{} - {}".format(self.address, self.organization)

    class Meta:
        verbose_name_plural = 'Organization Address'


class OrganizationAppearance(BaseModel):
    organization = models.OneToOneField(
        Organization, related_name='appearance', on_delete=models.CASCADE)
    primary_color = models.CharField(max_length=7, default="#42a5f5")
    secondary_color = models.CharField(max_length=7, default="#FFFFFF")
    header_logo = models.ImageField(
        upload_to='organization/header-logo/',
        blank=True,
        validators=[validate_image_file_extension]
    )
    logo = models.ImageField(
        upload_to='organization/logo/',
        blank=True,
        validators=[validate_image_file_extension]
    )
    background_image = models.ImageField(
        upload_to='organization/bg-image/',
        blank=True,
        validators=[validate_image_file_extension]
    )

    def __str__(self):
        return "Appearance Settings of {}".format(
            self.organization.abbreviation)

    @property
    def get_header_logo(self):
        return get_complete_url(
            self.header_logo.url
        ) if self.header_logo else get_complete_url(
            'images/default/cover.png',
            att_type='static'
        )

    @property
    def get_logo(self):
        return get_complete_url(
            self.logo.url
        ) if self.header_logo else get_complete_url(
            'images/default/cover.png',
            att_type='static'
        )

    @property
    def get_background_image(self):
        return get_complete_url(
            self.background_image.url
        ) if self.header_logo else get_complete_url(
            'images/default/cover.png',
            att_type='static'
        )


class OrganizationDocument(BaseModel, SlugModel):
    organization = models.ForeignKey(to=Organization,
                                     related_name='org_documents',
                                     on_delete=models.CASCADE,
                                     editable=False)
    category = models.ForeignKey('common.DocumentCategory',
                                 on_delete=models.SET_NULL,
                                 related_name='associated_documents',
                                 help_text='Document Category', null=True,
                                 validators=[DocumentTypeValidator(
                                     association_type=ORGANIZATION)]
                                 )
    title = models.CharField(max_length=255,
                             validators=[validate_title],
                             help_text="Title of the organization document.")
    description = models.TextField(blank=True)
    attachment = models.FileField(
        null=True,
        upload_to=get_upload_path,
        validators=[FileExtensionValidator(
            allowed_extensions=list(chain.from_iterable(settings.ACCEPTED_FILE_FORMATS.values()))
        )]
    )

    is_archived = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    is_downloadable = models.BooleanField(default=True)
    require_acknowledgement = models.BooleanField(default=False)
    acknowledgements = models.ManyToManyField(
        USER,
        help_text="Users who acknowledge this document will be kept here."
    )
    for_resignation = models.BooleanField(default=False)
    document_text = models.TextField(blank=True)

    class Meta:
        ordering = ('title',)
        unique_together = ('organization', 'title', 'category')

    def __str__(self):
        return "Organization Document - {}".format(self.title)


class UserOrganization(BaseModel):
    user = models.ForeignKey(
        to=USER, on_delete=models.CASCADE,
        related_name='organization'
    )
    organization = models.ForeignKey(
        to=Organization, on_delete=models.CASCADE,
        related_name='users'
    )
    can_switch = models.BooleanField(default=False)

    def __str__(self):
        return "{} belongs to {}".format(self.user,
                                         self.organization.abbreviation)
