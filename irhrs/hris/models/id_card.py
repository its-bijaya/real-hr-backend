from django.contrib.auth import get_user_model
from django.db import models

from irhrs.common.models import BaseModel
from irhrs.core.utils.common import get_upload_path
from irhrs.core.validators import validate_image_file_extension

USER = get_user_model()


class IdCardTemplate(BaseModel):
    """
    Template for ID cards.

    :cvar name: Name of Template
    :cvar sample: Template Sample from common

    :cvar logo: Organization logo
    :cvar background_image: Background Image
    :cvar auth_signature: Authorized signature

    :cvar org_address: Company address
    :cvar org_phone_no: Company phone numbers
    :cvar org_email: Company address

    :cvar slogan: Slogan of organization to display in id card

    :cvar profile_image_height: Height of profile image used with this template
    :cvar profile_image_width: Width of profile image used with this template
    """
    name = models.CharField(
        help_text="Name of template",
        max_length=50
    )
    sample = models.ForeignKey(
        'common.IdCardSample',
        on_delete=models.CASCADE,
        related_name='templates',
        help_text='Template sample from commons'
    )
    organization = models.ForeignKey(
        'organization.Organization',
        related_name='id_card_templates',
        on_delete=models.CASCADE,
        help_text="Organization associated with template"
    )

    logo = models.ImageField(
        help_text="Organization logo", upload_to=get_upload_path,
        validators=[validate_image_file_extension],
        null=True
    )
    background_image = models.ImageField(
        help_text="Background Image of card.", upload_to=get_upload_path,
        null=True, blank=True, validators=[validate_image_file_extension]
    )

    auth_signature = models.ImageField(
        help_text="Authorized signature",
        upload_to=get_upload_path, blank=True, null=True, validators=[validate_image_file_extension]
    )
    slogan = models.TextField(
        help_text="Slogan of organization",
        max_length=1000,
        blank=True
    )

    org_address = models.CharField(help_text="Address of organization.", max_length=200, blank=True, null=True)
    org_phone_no = models.CharField(help_text="Phone Number Section text.", max_length=100, blank=True, null=True)
    org_email = models.EmailField(help_text="Email of organization", blank=True, null=True)

    profile_image_height = models.IntegerField(
        help_text="Height of profile image used with this template",
        blank=True, null=True
    )
    profile_image_width = models.IntegerField(
        help_text="Width of profile image used with this template",
        blank=True, null=True
    )

    def __str__(self):
        return self.name


class IdCard(BaseModel):
    """
    Individual ID card generated from template.

    :cvar template: Template instance
    :cvar user: User associated with the organization
    :cvar profile_picture: Profile Image used in ID card


    *These parts are to be filled automatically by the system*
    :cvar full_name: User's full name
    :cvar job_title: User's job title
    :cvar employment_level: User's employment level
    :cvar contact_no: Contact Number of user

    """
    template = models.ForeignKey(
        IdCardTemplate,
        help_text="Id Card Template",
        on_delete=models.CASCADE, related_name='id_cards')
    user = models.ForeignKey(
        USER,
        on_delete=models.CASCADE,
        related_name='id_cards',
    )

    profile_picture = models.ImageField(
        upload_to=get_upload_path, help_text="Profile Image",
        validators=[validate_image_file_extension],
        null=True
    )
    issued_on = models.DateField(help_text="Issued Date", null=True)
    expire_on = models.DateField(help_text="Expiry Date", null=True)

    # Filled automatically from user details
    full_name = models.CharField(max_length=255, help_text="Full name")
    user_email = models.CharField(max_length=255, help_text="User Email", blank=True)
    employee_code = models.CharField(max_length=150, help_text="Employee Code", blank=True)
    division = models.CharField(max_length=150, help_text="Division", blank=True)
    employment_level = models.CharField(max_length=150, help_text="Employment Level", blank=True)
    phone_no = models.CharField(max_length=50, blank=True, null=True,
                                help_text="Contact Number of Employee")
    address = models.CharField(max_length=255, blank=True, null=True,
                                       help_text="Address of the employee")
    citizenship_number = models.CharField(max_length=255, blank=True, null=True,
                                          help_text="Citizenship Number")
    signature = models.ImageField(null=True, help_text="Signature of the employee")

    def __str__(self):
        return self.full_name
