from django.db import models

from irhrs.common.models import BaseModel
from irhrs.core.fields import JSONTextField
from irhrs.core.validators import (
    validate_json_contact, validate_title, validate_has_digit,
    validate_invalid_chars, validate_contact_person
)
from irhrs.common.models.commons import Bank
from .organization import Organization


class OrganizationBank(BaseModel):
    """
    One Organization can have many banks associated with it. This model holds
    the information on the bank detail of the organization along with its
    bank account number and location details.
    """
    organization = models.ForeignKey(
        to=Organization, related_name='banks',
        on_delete=models.CASCADE, editable=False
    )
    bank = models.ForeignKey(
        to=Bank, related_name='organization_banks', on_delete=models.CASCADE
    )
    account_number = models.CharField(
        max_length=150, blank=True, unique=True, validators=[
            validate_has_digit, validate_invalid_chars
        ]
    )
    contacts = JSONTextField(
        validators=[validate_json_contact]
    )
    branch = models.CharField(
        max_length=150, null=True, validators=[validate_title]
    )
    email = models.EmailField(
        blank=True, unique=True
    )
    contact_person = JSONTextField(
        blank=True, default={}, validators=[validate_contact_person]
    )

    class Meta:
        ordering = ('-id',)

    def __str__(self):
        return f"{self.bank} - {self.account_number}"
