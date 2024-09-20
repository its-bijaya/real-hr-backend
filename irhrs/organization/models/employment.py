from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from irhrs.common.models import SlugModel, BaseModel
from irhrs.core.constants.common import DURATION_CHOICES, ASSISTANT, EMPLOYMENT_LEVEL_CHOICE
from irhrs.core.validators import validate_natural_number, validate_title, \
    MinMaxValueValidator
from .organization import Organization


class EmploymentLevel(BaseModel, SlugModel):
    """
    User's employment level which will be assigned as per the organization
    structure. Employment Level and *Designation* goes by the same terminology.

    Employment Level includes data such as:
        Junior Assistant, Assistant, Senior Assistant, Junior Executive
        and so on.
    """
    organization = models.ForeignKey(
        to=Organization, related_name='employment_levels',
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=150, validators=[validate_title])
    description = models.TextField(
        blank=True,
        max_length=600
    )
    code = models.CharField(
        max_length=50, blank=True, validators=[validate_title]
    )
    order_field = models.FloatField(
        validators=[validate_natural_number, MaxValueValidator(200)]
    )
    is_archived = models.BooleanField(default=False)
    scale_max = models.PositiveSmallIntegerField(
        validators=[MinMaxValueValidator(
            min_value=1, max_value=100
        )],
    )
    auto_increment = models.BooleanField(
        default=False,
        help_text="Enabling this flag will add a change type automatically."
    )
    auto_add_step = models.PositiveSmallIntegerField(
        validators=[MinMaxValueValidator(
            min_value=1, max_value=100
        )],
        null=True,
        help_text='Add this value automatically after certain period. 1-100'
    )
    changes_on_fiscal = models.BooleanField(null=True, )
    frequency = models.PositiveSmallIntegerField(
        null=True,
        validators=[MinMaxValueValidator(
            min_value=1, max_value=3000
        )],
        help_text='Period range 1-3000'
    )
    duration = models.CharField(
        max_length=1,
        blank=True,
        choices=DURATION_CHOICES,
        help_text="Day, Month or Year",
        db_index=True
    )
    level = models.CharField(max_length=15, choices=EMPLOYMENT_LEVEL_CHOICE, default='',
                             blank=True, db_index=True)

    def __str__(self):
        return "{} - {}".format(self.organization.abbreviation, self.title)

    class Meta:
        ordering = ('order_field',)
        unique_together = ('organization', 'title')


class EmploymentStatus(BaseModel, SlugModel):
    """
    User's employment level which will be according to the organization
    and can have multiple employment status per organization.

    Employment Status includes data such as:
        Permanent, Probation, Contract and so on.
    """
    organization = models.ForeignKey(
        to=Organization, related_name='employment_status',
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=150, validators=[validate_title])
    description = models.TextField(blank=True)
    is_contract = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return "{} - {}".format(self.organization.abbreviation, self.title)

    class Meta:
        ordering = ('title', 'organization',)
        unique_together = ('title', 'organization',)
        verbose_name_plural = 'Employment Status'


class EmploymentJobTitle(BaseModel, SlugModel):
    """
    Employment Job Title also referred to the specific job title of the user.
    It basically involves the job title of the employment such as:
        QC, JS Programmer, Python Programmer, Junior Developer and so on.
    """
    organization = models.ForeignKey(
        to='organization.Organization', related_name='job_titles',
        on_delete=models.CASCADE, editable=False)
    title = models.CharField(max_length=150, validators=[validate_title])
    description = models.TextField(blank=True)

    class Meta:
        ordering = ('title', 'organization',)
        unique_together = ('title', 'organization',)

    def __str__(self):
        return self.title


class EmploymentStep(BaseModel, SlugModel):
    """
    Employment Step holds the data on steps to achieve the promotion according
    to the organizational structure.
    """
    organization = models.ForeignKey(Organization,
                                     related_name='steps',
                                     on_delete=models.CASCADE,
                                     editable=False)
    title = models.CharField(max_length=150, validators=[validate_title])
    description = models.TextField(blank=True)

    class Meta:
        ordering = ('title', 'organization',)

    def __str__(self):
        return self.title
