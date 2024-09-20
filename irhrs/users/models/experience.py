from django.contrib.auth import get_user_model
from django.db import models

from irhrs.common.models import SlugModel, Skill, BaseModel
from irhrs.core.validators import validate_title, MinMaxValueValidator
from irhrs.organization.models import OrganizationDivision, EmploymentLevel, \
    EmploymentStatus, OrganizationBranch, Organization, \
    EmploymentJobTitle
from irhrs.users.managers import UserExperienceManager

USER = get_user_model()


class UserExperienceStepHistory(BaseModel):
    experience = models.ForeignKey(
        to='users.UserExperience',
        related_name='step_histories',
        on_delete=models.CASCADE
    )
    step = models.PositiveSmallIntegerField()
    start_date = models.DateField()
    end_date = models.DateField(null=True)

    def __str__(self):
        return f"{self.step} step for {self.experience} from {self.start_date}"


class UserExperience(BaseModel):
    job_title = models.ForeignKey(EmploymentJobTitle,
                                  related_name='user_experiences',
                                  on_delete=models.SET_NULL,
                                  null=True
                                  )
    user = models.ForeignKey(USER,
                             related_name='user_experiences',
                             on_delete=models.CASCADE,
                             editable=False)
    organization = models.ForeignKey(Organization,
                                     related_name='user_experiences',
                                     on_delete=models.SET_NULL,
                                     null=True)
    division = models.ForeignKey(OrganizationDivision,
                                 related_name='user_experiences',
                                 on_delete=models.SET_NULL,
                                 null=True)
    employee_level = models.ForeignKey(EmploymentLevel,
                                       related_name='user_experiences',
                                       on_delete=models.SET_NULL,
                                       null=True)
    employment_status = models.ForeignKey(EmploymentStatus,
                                          related_name='user_experiences',
                                          on_delete=models.SET_NULL,
                                          null=True)
    branch = models.ForeignKey(OrganizationBranch,
                               related_name='user_experiences',
                               on_delete=models.SET_NULL,
                               null=True)
    change_type = models.ForeignKey(
        'hris.ChangeType',
        related_name='user_experiences',
        on_delete=models.SET_NULL,
        null=True
    )
    replacing = models.ForeignKey(USER,
                                  related_name='replaced_by_user_experience',
                                  on_delete=models.SET_NULL,
                                  null=True)
    skill = models.ManyToManyField(Skill)
    is_current = models.BooleanField()
    start_date = models.DateField(null=False)
    end_date = models.DateField(null=True)
    job_description = models.TextField(blank=True, max_length=100000)
    job_specification = models.TextField(blank=True, max_length=100000)
    objective = models.TextField(blank=True, max_length=100000)
    in_probation = models.BooleanField(default=False)
    probation_end_date = models.DateField(null=True)

    # Scale and Grade fields
    current_step = models.PositiveSmallIntegerField(
        validators=[MinMaxValueValidator(
            min_value=0, max_value=100
        )],
    )

    upcoming = models.BooleanField(
        default=False,
        help_text="Field to decide if the experience is upcoming. Will be "
                  "hidden from normal user."
    )

    objects = UserExperienceManager()

    class Meta:
        ordering = ('-start_date',)

    def __str__(self):
        return f"{self.user} - {self.job_title}"


class UserPastExperience(BaseModel, SlugModel):
    user = models.ForeignKey(USER,
                             related_name="past_experiences",
                             on_delete=models.CASCADE,
                             editable=False)
    title = models.CharField(max_length=150, validators=[validate_title])
    organization = models.CharField(max_length=150, validators=[validate_title])
    responsibility = models.TextField(max_length=5000)
    department = models.CharField(max_length=150,
                                  validators=[validate_title])
    employment_level = models.CharField(max_length=150,
                                        validators=[validate_title])
    employment_status = models.CharField(max_length=150,
                                         validators=[validate_title])
    job_location = models.CharField(max_length=150,
                                    validators=[validate_title])
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.title} - {self.organization}"

    class Meta:
        ordering = ('start_date',)
        unique_together = ('title', 'organization', 'start_date',)


class UserVolunteerExperience(BaseModel, SlugModel):
    user = models.ForeignKey(to=USER,
                                   related_name="volunteer_experiences",
                                   on_delete=models.CASCADE,
                                   editable=False)
    organization = models.CharField(max_length=150,
                                    validators=[validate_title])
    cause = models.CharField(max_length=150,
                             validators=[validate_title],
                             blank=True)
    title = models.CharField(max_length=150, validators=[validate_title])
    role = models.CharField(max_length=150)
    description = models.TextField(max_length=600)
    currently_volunteering = models.BooleanField(default=False)

    start_date = models.DateField()
    end_date = models.DateField(null=True)

    def __str__(self):
        return "Volunteering by - {}".format(self.title, )

    class Meta:
        ordering = ['title']
        unique_together = ('user', 'title',)
