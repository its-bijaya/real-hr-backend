from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.db import models

from irhrs.common.models import BaseModel, SlugModel
from irhrs.core.utils.common import get_upload_path, get_today
from irhrs.core.validators import (validate_title, validate_image_size,
                                   validate_user_age,
                                   validate_image_file_extension)

User = get_user_model()


class Holiday(BaseModel, SlugModel):
    """
    Holiday Category stores information about Organization's holiday.
    # Note:
        * even if there are nullable fields, they will be required through
        serializer.
        * start_date and end_date has been converted to date only.
        Serializer will accept a range of date. For all dates, individual entry
        for holiday will be created.
    """
    organization = models.ForeignKey(
        to='organization.Organization', on_delete=models.SET_NULL, null=True
    )
    category = models.ForeignKey(
        to='common.HolidayCategory', on_delete=models.SET_NULL, null=True
    )
    name = models.CharField(max_length=150, validators=[validate_title])
    description = models.TextField(blank=True)
    date = models.DateField(null=False)
    image = models.ImageField(
        validators=[validate_image_size, validate_image_file_extension], upload_to=get_upload_path, blank=True
    )

    def __str__(self):
        return self.name

    @property
    def applicable_users(self):
        queryset = User.objects.filter(detail__organization=self.organization).current()
        rule = getattr(self, 'rule', None)
        if not rule:
            # applicable for all
            return queryset
        fil = dict()

        divisions = list(rule.division.all())
        ethnicities = list(rule.ethnicity.all())
        religions = list(rule.religion.all())
        branches = list(rule.branch.all())

        if divisions:
            fil["detail__division__in"] = divisions
        if ethnicities:
            fil["detail__ethnicity__in"] = ethnicities
        if religions:
            fil["detail__religion__in"] = religions
        if branches:
            fil["detail__branch__in"] = branches
        if rule.gender and rule.gender != 'All':
            fil["detail__gender"] = rule.gender
        if rule.lower_age:
            fil["detail__date_of_birth__lte"] = get_today() - relativedelta(years=rule.lower_age)
        if rule.upper_age:
            fil["detail__date_of_birth__gte"] = get_today() - relativedelta(years=rule.upper_age)

        return queryset.filter(**fil)


class HolidayRule(BaseModel):
    """
    Set the rules for which holiday is applicable(able to select Ethnicity,
    Religion, Branch, Gender, Age) while adding the holiday
    """
    holiday = models.OneToOneField(
        to='organization.Holiday', on_delete=models.SET_NULL, null=True,
        related_name='rule'
    )
    division = models.ManyToManyField(
        to='organization.OrganizationDivision',
        related_name='holiday_division'
    )
    ethnicity = models.ManyToManyField(
        to='common.ReligionAndEthnicity',
        related_name='holiday_ethnicity',
        limit_choices_to={'category': 'Ethnicity'}
    )
    religion = models.ManyToManyField(
        to='common.ReligionAndEthnicity',
        related_name='holiday_religion',
        limit_choices_to={'category': 'Religion'}
    )
    branch = models.ManyToManyField(
        to='organization.OrganizationBranch',
        related_name='holiday_branch',
    )
    gender = models.CharField(
        max_length=10,
        choices=[
            ('All', 'All'),
            ('Male', 'Male'),
            ('Female', 'Female'),
            ('Other', 'Other')
        ],
        null=False, blank=False, db_index=True
    )
    lower_age = models.PositiveSmallIntegerField(
        validators=[validate_user_age],
        null=True
    )
    upper_age = models.PositiveSmallIntegerField(
        validators=[validate_user_age],
        null=True
    )
