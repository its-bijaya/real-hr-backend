import uuid

from django.conf import settings
from django.db.models import JSONField
from django.contrib.auth import get_user_model
from django.db import models

from irhrs.common.models import BaseModel, DutyStation
from irhrs.core.constants.user import GENDER_CHOICES
from irhrs.core.validators import validate_description, validate_future_datetime, validate_title
from irhrs.core.constants.payroll import (
    APPROVED_BY,
    SUPERVISOR,
    EMPLOYEE,
    SUPERVISOR_LEVEL_FOR_RECRUITMENT,
)
from irhrs.forms.constants import FORM_STATUS, ANSWER_SHEET_APPROVAL_STATUS
from irhrs.organization.models import Organization, OrganizationBranch, EmploymentStatus, \
    EmploymentLevel, OrganizationDivision, EmploymentJobTitle
from irhrs.questionnaire.models.questionnaire import Question, Answer

User = get_user_model()


class Form(BaseModel):
    """
    This is an individual form object.
    """
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False
    )
    organization = models.ForeignKey(
        Organization,
        related_name='organization_forms',
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=255, validators=[validate_title])
    deadline = models.DateTimeField(
        validators=[validate_future_datetime],
        null=True
    )
    description = models.CharField(max_length=1000, blank=True, null=True)

    disclaimer_text = models.TextField(
        max_length=settings.TEXT_FIELD_MAX_LENGTH,
        blank=True,
        null=True
    )

    is_multiple_submittable = models.BooleanField(default=False)
    is_anonymously_fillable = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    is_draft = models.BooleanField(default=True)
    question_set = models.ForeignKey(
        'FormQuestionSet',
        related_name="forms",
        on_delete=models.CASCADE,
        null=True
    )

    def __str__(self):
        return self.name

    @property
    def show_user_filters(self):
        setting = getattr(self, 'setting', None)
        if not setting:
            return False
        return any((
            setting.branch, setting.division, setting.job_title, setting.employment_type,
            setting.employment_level, setting.duty_station, setting.gender
        ))


class FormSetting(BaseModel):
    form = models.OneToOneField(
        Form,
        related_name="setting",
        on_delete=models.CASCADE
    )
    branch = models.ForeignKey(
        OrganizationBranch,
        related_name='form_settings',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES, blank=True, null=True)
    employment_type = models.ForeignKey(
        EmploymentStatus,
        related_name='form_settings',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    employment_level = models.ForeignKey(
        EmploymentLevel,
        related_name='form_settings',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    division = models.ForeignKey(
        OrganizationDivision,
        related_name='form_settings',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    job_title = models.ForeignKey(
        EmploymentJobTitle,
        related_name='form_settings',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    duty_station = models.ForeignKey(
        DutyStation,
        related_name='form_settings',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )


class UserForm(BaseModel):
    """
    This model holds form assignments.
    """
    user = models.ForeignKey(
        User,
        related_name='form_assignments',
        on_delete=models.CASCADE
    )
    form = models.ForeignKey(
        Form,
        related_name='form_assignments',
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('user', 'form')


class AnonymousFormAnswerSheet(BaseModel):
    form = models.ForeignKey(
        Form,
        related_name='anon_form_instances',
        on_delete=models.CASCADE
    )
    question_answers = models.ManyToManyField(
        'AnonymousFormIndividualQuestionAnswer'
    )



class UserFormAnswerSheet(BaseModel):
    '''
    This is an answer sheet.
    '''
    user = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name="answer_sheets",
        null=True
    )
    form = models.ForeignKey(
        Form,
        related_name='answer_sheets',
        on_delete=models.CASCADE
    )

    question_answers = models.ManyToManyField(
        'UserFormIndividualQuestionAnswer'
    )
    is_approved = models.BooleanField(default=False)
    is_draft = models.BooleanField(default=True)
    next_approval_level = models.FloatField(null=True)


class FormQuestionSet(BaseModel):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=1000, blank=True)
    is_archived = models.BooleanField(default=False)
    organization = models.ForeignKey(
        Organization,
        related_name='form_question_sets',
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name


class FormQuestionSection(BaseModel):
    title = models.CharField(
        max_length=255
    )
    description = models.TextField(
        blank=True,
        validators=[validate_description],
        max_length=settings.TEXT_FIELD_MAX_LENGTH
    )
    question_set = models.ForeignKey(
        to=FormQuestionSet,
        related_name='sections',
        on_delete=models.CASCADE
    )
    questions = models.ManyToManyField(
        to=Question,
        through='FormQuestion',
        through_fields=('question_section', 'question'),
        related_name='+'
    )

    class Meta:
        ordering = 'created_at',


class FormQuestion(BaseModel):
    is_mandatory = models.BooleanField(default=True)
    answer_visible_to_all_users = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField()
    question_section = models.ForeignKey(
        to=FormQuestionSection,
        on_delete=models.CASCADE,
        related_name='form_questions'
    )
    question = models.ForeignKey(
        to=Question,
        related_name='+',
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = 'order',
        unique_together = ('question_section', 'question')


class AnonymousFormIndividualQuestionAnswer(BaseModel):
    '''
    This is an individual question answer related to sheet.
    Mostly used for calculating stats because aggregating JSON field
    for stats was too complex.
    '''
    question = models.ForeignKey(
        FormQuestion,
        related_name="anonymous_individual_question_answers",
        on_delete=models.CASCADE
    )
    answers = JSONField(blank=True, null=True)
    answer_sheet = models.ForeignKey(
        AnonymousFormAnswerSheet,
        related_name="anonymous_individual_question_answers",
        on_delete=models.CASCADE
    )

class UserFormIndividualQuestionAnswer(BaseModel):
    '''
    This is an individual question answer related to sheet.
    Mostly used for calculating stats because aggregating JSON field
    for stats was too complex.
    '''
    question = models.ForeignKey(
        FormQuestion,
        related_name="individual_question_answers",
        on_delete=models.CASCADE
    )
    answers = JSONField(blank=True, null=True)
    answer_sheet = models.ForeignKey(
        UserFormAnswerSheet,
        related_name="individual_question_answers",
        on_delete=models.CASCADE
    )


class FormApprovalSettingLevel(BaseModel):
    approve_by = models.CharField(
        max_length=10,
        choices=APPROVED_BY,
        default=SUPERVISOR
    )
    supervisor_level = models.CharField(
        max_length=10,
        choices=SUPERVISOR_LEVEL_FOR_RECRUITMENT,
        null=True,
        blank=True
    )
    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='form_approval_setting',
        null=True,
        blank=True
    )
    approval_level = models.FloatField()
    form = models.ForeignKey(
        Form,
        related_name='form_approval_setting',
        on_delete=models.CASCADE
    )

    def __str__(self):
        if self.approve_by == EMPLOYEE:
            return f"Approval setting - {self.employee.first_name}"
        else:
            return f"Approval setting - {self.supervisor_level} supervisor."


class FormAnswerSheetApproval(BaseModel):
    approval_level = models.FloatField()
    approve_by = models.CharField(
        max_length=10,
        choices=APPROVED_BY,
        default=SUPERVISOR
    )
    supervisor_level = models.CharField(
        max_length=10,
        choices=SUPERVISOR_LEVEL_FOR_RECRUITMENT,
        null=True,
        blank=True
    )
    employees = models.ManyToManyField(
        User,
        related_name='form_answer_sheet_approvals',
    )
    answer_sheet = models.ForeignKey(
        UserFormAnswerSheet,
        related_name='form_answer_sheet_approvals',
        on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=10,
        choices=ANSWER_SHEET_APPROVAL_STATUS
    )


class AnswerSheetStatus(BaseModel):
    answer_sheet = models.ForeignKey(
        UserFormAnswerSheet,
        related_name='status',
        on_delete=models.CASCADE
    )
    approver = models.ForeignKey(
        User,
        related_name='status',
        on_delete=models.PROTECT,
    )
    approval_level = models.ForeignKey(
        to=FormAnswerSheetApproval,
        on_delete=models.CASCADE,
        null=True
    )
    action = models.CharField(
        max_length=10,
        choices=FORM_STATUS
    )
    remarks = models.CharField(
        max_length=255
    )
