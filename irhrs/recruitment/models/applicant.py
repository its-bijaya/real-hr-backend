import os
import uuid

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models

from irhrs.common.models import (
    TimeStampedModel
)
from irhrs.core.constants.user import (
    EDUCATION_DEGREE_CHOICES
)
from irhrs.core.utils.common import get_complete_url, get_upload_path
from irhrs.core.validators import MinMaxValueValidator
from irhrs.organization.models.knowledge_skill_ability import KnowledgeSkillAbility
from irhrs.recruitment.constants import ATTACHMENT_TYPE_CHOICES, JOB_APPLY
from irhrs.recruitment.models.common import Location
from irhrs.recruitment.models.common import (
    Salary,
    AbstractReferenceContact
)
from irhrs.users.models.user import ExternalUser


def get_applicant_file_upload_path(instance, filename):
    """
    Instance must have applicant attribute which is ForeignKey to Jobseeker
    """
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join('applicant/documents/', filename)


class Applicant(TimeStampedModel):
    user = models.OneToOneField(
        ExternalUser,
        related_name='applicant',
        on_delete=models.CASCADE
    )

    address = models.ForeignKey(
        Location,
        null=True, blank=True,
        related_name='current_address_applicants',
        on_delete=models.SET_NULL
    )

    education_degree = models.CharField(
        max_length=20,
        choices=EDUCATION_DEGREE_CHOICES,
        blank=True
    )
    education_program = models.CharField(max_length=100, blank=True)
    skills = models.ManyToManyField(KnowledgeSkillAbility)
    expected_salary = models.ForeignKey(
        Salary,
        related_name='expected_salary_users',
        null=True, blank=True,
        on_delete=models.SET_NULL
    )
    cv = models.FileField(
        upload_to=get_applicant_file_upload_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=settings.ACCEPTED_FILE_FORMATS.get('documents')
            )
        ],
        null=True,
        blank=True
    )
    experience_years = models.FloatField(
        default=0,
        validators=[MinMaxValueValidator(min_value=0, max_value=60)]
    )

    def __str__(self):
        return self.user.full_name

    @property
    def cv_path(self):
        if self.cv:
            return get_complete_url(url=self.cv.url)
        else:
            return ''


class ApplicantReference(AbstractReferenceContact, TimeStampedModel):
    applicant = models.ForeignKey(
        Applicant,
        related_name='references',
        on_delete=models.CASCADE
    )


class ApplicantWorkExperience(TimeStampedModel):
    applicant = models.ForeignKey(
        Applicant,
        related_name='work_experiences',
        on_delete=models.CASCADE
    )
    org_name = models.CharField(max_length=255, db_index=True)
    designation = models.CharField(max_length=100, blank=True)
    years_of_service = models.FloatField(
        default=0,
        validators=[MinMaxValueValidator(min_value=0, max_value=60)]
    )

    is_archived = models.BooleanField(
        default=False, help_text='When deleted, is_archived returns True')

    def __str__(self):
        return '{}'.format(self.designation)


class ApplicantEducation(TimeStampedModel):
    applicant = models.ForeignKey(
        Applicant,
        related_name='educations',
        on_delete=models.CASCADE
    )
    degree = models.CharField(
        max_length=20,
        choices=EDUCATION_DEGREE_CHOICES
    )
    program = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f'{self.degree} in {self.program}'


class ApplicantAttachment(TimeStampedModel):
    applicant = models.ForeignKey(
        Applicant,
        related_name='attachments',
        on_delete=models.CASCADE
    )
    attachment = models.FileField(
        upload_to=get_upload_path,
        validators=[FileExtensionValidator(
            allowed_extensions=settings.ACCEPTED_FILE_FORMATS_LIST
        )]
    )
    name = models.CharField(max_length=255)

    # When does applicant upload these attachments for now in job apply
    # and salary negotiation play slip
    type = models.CharField(
        max_length=30,
        choices=ATTACHMENT_TYPE_CHOICES,
        default=JOB_APPLY
    )
    is_archived = models.BooleanField(default=False)
