import itertools

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models

from irhrs.common.models import BaseModel, SlugModel
from irhrs.core.fields import JSONTextField
from irhrs.core.utils.common import get_upload_path
from irhrs.core.utils.training import find_training_members
from irhrs.core.validators import (
    validate_title, validate_description, validate_json_contact, validate_wysiwyg_field,
    MinMaxValueValidator)
from irhrs.organization.models import Organization, MeetingRoomStatus, OrganizationBranch, \
    OrganizationDivision, EmploymentJobTitle, EmploymentLevel, EmploymentStatus
from irhrs.organization.models.knowledge_skill_ability import KnowledgeSkillAbility
from .helpers import (
    TRAINING_NATURE, TRAINING_NEED_CHOICES,
    TRAINING_STATUS_CHOICES, PENDING, STATUS_CHOICES,
    TRAINING_VISIBILITY_CHOICES, PUBLIC,
    TRAINING_MEMBER_POSITION, MEMBER)
from ..constants import NRS, AMOUNT_TYPE

USER = get_user_model()


class TrainingType(SlugModel, BaseModel):
    organization = models.ForeignKey(
        to=Organization,
        on_delete=models.CASCADE,
        null=True
    )
    title = models.CharField(
        max_length=255,
        validators=[validate_title],
        help_text='Self Explanatory'
    )
    description = models.TextField(
        validators=[validate_description],
        blank=True,
        help_text='Self Explanatory'
    )
    budget_limit = models.FloatField(
        null=True,
        validators=[MinValueValidator(0.0)],
        help_text='The total budget company wishes to spend on trainings of this type.'
    )
    amount_type = models.CharField(
        max_length=3,
        choices=AMOUNT_TYPE,
        default=NRS
    )

    # budget_hours = models.FloatField(
    #     validators=[validate_natural_number],
    #     help_text='The total time company wishes to spend on trainings of this type.'
    # )

    def __str__(self):
        return self.title


class Training(SlugModel, BaseModel):
    training_type = models.ForeignKey(
        to=TrainingType,
        related_name='trainings',
        on_delete=models.CASCADE,
        help_text='The Type of this training. The budget and budget hours are subset to this FK.'
    )
    name = models.CharField(
        max_length=255,
        validators=[validate_title],
        help_text='Self Explanatory'
    )
    description = models.TextField(
        validators=[validate_description],
        blank=True,
        help_text='Self Explanatory'
    )
    image = models.ImageField(
        upload_to=get_upload_path,
        blank=True,
        help_text='Background/Banner for this training.'
    )
    start = models.DateTimeField(
        # validators=[validate_future_datetime],
        help_text='Start Date for this training.'
    )
    end = models.DateTimeField(
        # validators=[validate_future_datetime],
        help_text='Expected End Date for this training.'
    )

    start_time = models.TimeField(
        null=True,
        help_text='Start time for training'
    )

    end_time = models.TimeField(
        null=True,
        help_text='End time for training'
    )

    nature = models.CharField(
        max_length=10,
        choices=TRAINING_NATURE,
        help_text='Where will this training be held?'
    )
    location = models.TextField(
        help_text='Where will the training be held?',
        null=True
    )
    budget_allocated = models.FloatField(
        null=True,
        validators=[MinValueValidator(0.0)],
        help_text='The financial weightage of this training.'
    )
    # budget_hours = models.FloatField(
    #     validators=[validate_natural_number],
    #     help_text='The weightage of this training in terms of hours.'
    # )
    status = models.CharField(
        max_length=20,
        choices=TRAINING_STATUS_CHOICES,
        default=PENDING,
        help_text='Training Status: Pending, Completed, In Progress, etc.',
        db_index=True
    )
    visibility = models.CharField(
        max_length=10,
        choices=TRAINING_VISIBILITY_CHOICES,
        default=PUBLIC,
        help_text='Is this training visible to all users?'
    )
    users_can_apply = models.BooleanField(
        default=False,
        help_text='Allow users to send a join request for this training?'
    )
    acceptance_deadline = models.DateTimeField(
        null=True,
        help_text='If users can apply to this training, when should they apply before?'
    )

    coordinator = models.ForeignKey(
        USER,
        related_name='training_coordinator',
        on_delete=models.CASCADE,
        null=True
    )

    internal_trainers = models.ManyToManyField(
        USER,
        related_name='internal_trainers'
    )

    external_trainers = models.ManyToManyField(
        to='training.Trainer',
        related_name='external_trainers'
    )

    # For recurring Training
    recurring_rule = models.TextField(null=True, blank=True)
    recurring_first_run = models.DateField(null=True, blank=True)
    average_score = models.FloatField(null=True)

    # For assigning according to hris_aspects
    job_title = models.ManyToManyField(
        EmploymentJobTitle,
        related_name='training_job_title',
        blank=True
    )
    division = models.ManyToManyField(
        OrganizationDivision,
        related_name='training_division',
        blank=True
    )
    employment_level = models.ManyToManyField(
        EmploymentLevel,
        related_name='training_employment_level',
        blank=True
    )
    branch = models.ManyToManyField(
        OrganizationBranch,
        related_name='training_branch',
        blank=True
    )
    employment_type = models.ManyToManyField(
        EmploymentStatus,
        related_name='training_employment_type',
        blank=True
    )

    meeting_room = models.OneToOneField(MeetingRoomStatus, related_name='training',
                                        on_delete=models.SET_NULL, blank=True, null=True)
    program_cost = models.FloatField(
        default=0,
        validators=[MinValueValidator(0.0)]
    )
    tada = models.FloatField(
        default=0,
        validators=[MinValueValidator(0.0)],
        help_text='Traveling Allowance and Dearness Allowance'
    )
    accommodation = models.FloatField(
        default=0,
        validators=[MinValueValidator(0.0)]
    )
    trainers_fee = models.FloatField(
        default=0,
        validators=[MinValueValidator(0.0)]
    )
    others = models.FloatField(
        default=0,
        validators=[MinValueValidator(0.0)]
    )

    @property
    def members(self):
        # Prefetch this.
        return self.members_qs()

    @property
    def recurring(self):
        return self if self.recurring_rule else None

    @property
    def is_recurring(self):
        return bool(self.recurring_rule)

    def members_qs(self):
        training_members = find_training_members(self.id)
        qs = USER.objects.filter(
            id__in=training_members,
        ).select_related(
            'detail', 'detail__organization', 'detail__division',
            'detail__job_title', 'detail__employment_level'
        )
        return qs
    @property
    def members_count(self):
        return self.members_qs().count()

    def __str__(self):
        return self.name


class RecurringTrainingDate(BaseModel):
    recurring_at = models.DateField()
    template = models.ForeignKey(
        Training, on_delete=models.CASCADE,
        related_name='recurring_training_queue'
    )
    created_training = models.OneToOneField(Training, on_delete=models.CASCADE, null=True)
    remarks = models.TextField(null=True, blank=True)
    last_tried = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.recurring_at} for {self.template}'


class UserTraining(BaseModel):
    # TODO@anyone: Remove UserTraining model in `users` app.
    user = models.ForeignKey(
        to=USER,
        on_delete=models.CASCADE,
        related_name='user_trainings'
    )
    training = models.ForeignKey(
        to=Training,
        related_name='user_trainings',
        on_delete=models.CASCADE,
        help_text='The training user wishes to join'
    )

    start = models.DateTimeField(help_text='When did the user join this training?')
    end = models.DateTimeField(
        null=True,
        help_text='Not Required.\nWhen will the training end?'
    )

    # Reference means how user was eligible for training.
    # Example:
    #   1. User Could have asked for training
    #   2. An assessment report concluded this necessity.
    #   3. Through Performance Appraisal.
    #   4. Through Task Efficiency.

    training_need = models.CharField(
        max_length=21,
        choices=TRAINING_NEED_CHOICES,
        help_text="""
            Why the user needs this training?
            1. User Could have asked for training
            2. An assessment report concluded this necessity.
            3. Through Performance Appraisal.
        """
    )


class UserTrainingRequest(BaseModel):
    user = models.ForeignKey(
        to=USER,
        related_name='training_requests',
        on_delete=models.CASCADE
    )
    training = models.ForeignKey(
        to=Training,
        on_delete=models.CASCADE,
        related_name='training_requests'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        db_index=True
    )
    request_remarks = models.CharField(max_length=255)
    action_remarks = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.training.name


class Trainer(BaseModel):
    organization = models.ForeignKey(
        to=Organization,
        on_delete=models.CASCADE,
        related_name='+'
    )
    full_name = models.CharField(
        max_length=255,
        validators=[validate_title],
        help_text='Full name of the trainer.'
    )
    email = models.EmailField(
        help_text='Email of the trainer.'
    )
    description = models.TextField(
        validators=[validate_wysiwyg_field]
    )
    expertise = models.ManyToManyField(
        to=KnowledgeSkillAbility,
        # We can through this model for additional info like (exp years, etc.)
    )
    contact_info = JSONTextField(
        help_text='Contact Information of Trainer.\nFormat is {"Phone": "45454545",...}',
        validators=[validate_json_contact]
    )
    image = models.ImageField(upload_to=get_upload_path, blank=True)

    def __str__(self):
        return self.full_name


class TrainerAttachments(BaseModel):
    trainer = models.ForeignKey(
        to=Trainer,
        related_name='attachments',
        on_delete=models.CASCADE
    )
    # attachment_type = models.ForeignKey(
    #     to=DocumentCategory,
    #     on_delete=models.CASCADE,
    #     related_name='trainer_attachments'
    # )
    file = models.FileField(
        upload_to=get_upload_path
    )


class TrainingFeedback(BaseModel):
    """
    User shall give feedback about the trainings they've attended.
    """
    training = models.ForeignKey(
        to=Training,
        related_name='feedbacks',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        to=USER,
        related_name='training_feedbacks',
        on_delete=models.CASCADE
    )
    remarks = models.TextField(
        validators=[validate_wysiwyg_field]
    )
    rating = models.FloatField(
        validators=[MinMaxValueValidator(
            min_value=1,
            max_value=10
        )]
    )

    def __str__(self):
        return str(self.rating) + self.remarks


ALLOWED_FORMATS = list(
    itertools.chain.from_iterable(settings.ACCEPTED_FILE_FORMATS.values())
)


class TrainingAttachments(BaseModel):
    """
    Store Attachments from training.
    """
    training = models.ForeignKey(
        to=Training,
        related_name='attachments',
        on_delete=models.CASCADE
    )
    attachments_remarks = models.TextField(
        blank=True,
        validators=[validate_wysiwyg_field]
    )

    def __str__(self):
        return self.content


class TrainingAttachment(models.Model):
    training_attachment = models.ForeignKey(
        to=TrainingAttachments,
        related_name='files',
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=120, null=True)
    file = models.FileField(
        validators=[FileExtensionValidator(
            allowed_extensions=ALLOWED_FORMATS
        )],
        upload_to=get_upload_path
    )
    # TODO:@shital implement file type for separating image form files


class TrainingAttendance(BaseModel):
    member = models.ForeignKey(
        USER,
        related_name='training_attendance',
        on_delete=models.CASCADE,
        null=True
    )
    external_trainer = models.ForeignKey(
        Trainer,
        related_name='training_attendance',
        on_delete=models.CASCADE,
        null=True
    )
    training = models.ForeignKey(
        Training,
        related_name='training_attendance',
        on_delete=models.CASCADE,
    )
    position = models.CharField(
        max_length=20,
        choices=TRAINING_MEMBER_POSITION,
        default=MEMBER
    )
    arrival_time = models.DateTimeField(null=True)
    remarks = models.CharField(max_length=1000, null=True)
