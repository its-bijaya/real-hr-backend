from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.validators import FileExtensionValidator
from django.db.models import JSONField
from django.db import models

# ALL UTILS TO BE MOVED TO HELPERS FOR PORTABILITY
from irhrs.common.models import BaseModel, SlugModel
from irhrs.core.utils.common import get_upload_path
from irhrs.core.validators import validate_wysiwyg_field, MinMaxValueValidator, validate_title, \
    validate_description
from irhrs.organization.models import Organization
from irhrs.questionnaire.models.helpers import QUESTION_TYPES, ANSWER_TYPES


class QuestionCategory(SlugModel, BaseModel):
    title = models.CharField(
        max_length=255,
        validators=[validate_title]
    )
    description = models.TextField(
        blank=True,
        validators=[validate_wysiwyg_field]
    )
    category = models.CharField(
        max_length=25,
        choices=QUESTION_TYPES,
        db_index=True
    )
    organization = models.ForeignKey(
        to=Organization,
        on_delete=models.CASCADE,
        related_name='+'
    )

    class Meta:
        ordering = ('title',)
        unique_together = ('title', 'organization', 'category',)

    def __str__(self):
        return self.title


class Question(BaseModel):
    title = models.TextField(
        max_length=1000,
        help_text='Question Text.'
    )
    organization = models.ForeignKey(
        to=Organization,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    description = models.TextField(
        max_length=1000,
        blank=True
    )
    answer_choices = models.CharField(
        max_length=60,
        choices=ANSWER_TYPES,
        help_text='The types of answer choices. Eg: MCQ, Linear Scale, etc.',
        db_index=True
    )
    question_type = models.CharField(
        max_length=25,
        choices=QUESTION_TYPES,
        help_text='Question Type. Eg: Assessment, PA, Feedback, Interview, etc.',
        db_index=True
    )
    category = models.ForeignKey(
        to=QuestionCategory,
        related_name='questions',
        on_delete=models.PROTECT,
        help_text='Question Category. Eg: Easy, Medium, Hard, etc.'
    )
    order = models.PositiveIntegerField(
        help_text='Default Ordering of the question in repository. It shall vary in Question Sets.'
    )
    weightage = models.PositiveIntegerField(
        help_text='The weightage of the question. Or, can be called `marks`',
        null=True, blank=True
    )
    image = models.ImageField(upload_to=get_upload_path, blank=True)
    is_open_ended = models.BooleanField(default=False)
    difficulty_level = models.PositiveSmallIntegerField(
        validators=[
            MinMaxValueValidator(
                min_value=1,
                max_value=10
            )
        ],
        default=1
    )
    rating_scale = models.PositiveIntegerField(null=True)
    display_type = models.CharField(max_length=20, null=True, blank=True)
    extra_data = JSONField(null=True)

    def __str__(self):
        return self.title

    # ToDo: @shital make organization and order field unique together
    # class Meta:
    #     unique_together = ('organization', 'order')

    class Meta:
        ordering = 'order',

    @property
    def answers(self):
        return self.all_answer_choices.all()


class Answer(BaseModel):
    question = models.ForeignKey(
        to=Question,
        on_delete=models.CASCADE,
        related_name='all_answer_choices'
    )
    title = models.CharField(
        max_length=255
    )
    description = models.TextField(
        blank=True,
        validators=[validate_description]
    )
    is_correct = models.BooleanField(default=False)
    image = models.ImageField(blank=True, upload_to=get_upload_path)
    attachment = models.FileField(
        upload_to=get_upload_path,
        null=True,
        blank=True,
        validators=[FileExtensionValidator(
            allowed_extensions=settings.ACCEPTED_FILE_FORMATS_LIST
        )]
    )
    remarks = models.TextField(
        blank=True,
        validators=[validate_description]
    )
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = 'order',
        unique_together = ('question', 'title', 'attachment')

    def __str__(self):
        return 'Ans: ' + self.title
