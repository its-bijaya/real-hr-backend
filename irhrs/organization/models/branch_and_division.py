from django.contrib.auth import get_user_model
from django.db import models

from irhrs.core.fields import JSONTextField
from irhrs.core.validators import validate_json_contact_in_branch
from irhrs.core.validators import validate_natural_number, validate_title

from irhrs.common.models import AbstractLocation, BaseModel
from irhrs.common.models import SlugModel

from .organization import Organization
from .mission_and_vision import OrganizationMission

USER = get_user_model()


class OrganizationDivision(BaseModel, SlugModel):
    """
    Organization Division holds all the information regarding
    Department, Unit, Project as per the organization's division structure.
    """
    organization = models.ForeignKey(
        to=Organization, on_delete=models.CASCADE, related_name="divisions",
        editable=False
    )
    parent = models.ForeignKey(
        to='self', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='division_child'
    )
    head = models.ForeignKey(
        to=USER, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='division_head'
    )
    name = models.CharField(
        max_length=150, validators=[validate_title]
    )
    description = models.TextField(blank=True)
    extension_number = models.PositiveSmallIntegerField(
        null=True, unique=True, validators=[validate_natural_number]
    )
    mission = models.ManyToManyField(to=OrganizationMission)
    strategies = models.TextField(blank=True)
    action_plans = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ('-name',)
        unique_together = ('organization', 'name',)

    def __str__(self):
        return self.name


class OrganizationBranch(BaseModel, SlugModel, AbstractLocation):
    organization = models.ForeignKey(
        Organization, related_name='branches',
        on_delete=models.CASCADE, editable=False
    )
    branch_manager = models.ForeignKey(
        USER, related_name='branch_manager_of', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    name = models.CharField(
        max_length=200, help_text='Name of the branch of the organization',
        validators=[validate_title]
    )
    region = models.CharField(max_length=255, null=True, blank=True)    # geographical_region
    description = models.TextField(blank=True)
    contacts = JSONTextField(validators=[validate_json_contact_in_branch])
    email = models.EmailField(blank=True)
    code = models.CharField(max_length=15, unique=True, null=True, blank=False)

    # max length set to 255 as our location field in Abstract address is also
    # the same
    mailing_address = models.TextField(blank=True, max_length=255)
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ('name',)
        unique_together = ('organization', 'name')

    def __str__(self):
        return self.name
