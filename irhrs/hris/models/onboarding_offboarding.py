from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.db.models import Count
from django.db.models import Q
from django.utils.functional import cached_property

from irhrs.attendance.models import WorkShift
from irhrs.common.models import BaseModel, SlugModel
from irhrs.core.constants.user import GENDER_CHOICES, MARITAL_STATUS_CHOICES, SINGLE
from irhrs.core.utils.common import validate_full_name, humanize_interval
from irhrs.core.validators import validate_title, validate_future_date, \
    validate_future_datetime, MinMaxValueValidator
from irhrs.hris.constants import CHANGE_TYPE_CHOICES, EMAIL_STATUS_CHOICES, \
    NOT_SENT, LETTER_TEMPLATE_TYPE_CHOICES, BADGE_VISIBILITY_CHOICES, NEITHER, \
    SEPARATION_CATEGORY_CHOICES, ONBOARDING_STATUS, ACTIVE, OFFBOARDING_STATUS, \
    CHANGE_TYPE_STATUS
from irhrs.hris.models import CoreTask
from irhrs.leave.constants.model_constants import HOURLY_LEAVE_CATEGORIES
from irhrs.leave.models import LeaveType, LeaveAccount
from irhrs.organization.models import EmploymentLevel, EmploymentStatus, \
    EmploymentJobTitle, OrganizationDivision, \
    OrganizationBranch, Organization
from irhrs.payroll.models import Package
from irhrs.task.constants import COMPLETED, TASK_PRIORITIES, MINOR
from irhrs.task.models import Task
from irhrs.task.utils import get_task_attachment_path
from irhrs.users.models import UserExperience

CASCADE = models.CASCADE
USER = get_user_model()
fernet = Fernet(settings.FERNET_KEY)


class PrePostTaskMixin:
    _PENDING = 'In Progress'
    _COMPLETED = 'Completed'
    _UNASSIGNED = 'Pending'

    @cached_property
    def pre_task_status_stats(self):
        if self.pre_task:
            tracker_type = {
                PreEmployment: 'pre_employment',
                EmploymentReview: 'employment_review',
                EmployeeSeparation: 'separation'
            }
            pre_task = self.pre_task
            tracker = TaskTracking.objects.filter(
                task_template=pre_task
            ).filter(
                **{
                    tracker_type.get(type(self)): self
                }
            ).first()
            if tracker:
                res = tracker.tasks.aggregate(
                    assigned=Count('task'),
                    completed=Count(
                        'task',
                        filter=Q(task__status=COMPLETED)
                    )
                )
                assigned = res.get('assigned') or 0
                completed = res.get('completed') or 0
                return completed, assigned
        return None, None

    @cached_property
    def pre_task_status(self):
        completed, assigned = self.pre_task_status_stats
        if assigned:
            if assigned > 0:
                if assigned == completed:
                    return self._COMPLETED
                return self._PENDING
        return self._UNASSIGNED

    @cached_property
    def post_task_status_stats(self):
        if self.post_task:
            tracker_type = {
                PreEmployment: 'pre_employment',
                EmploymentReview: 'employment_review',
                EmployeeSeparation: 'separation'
            }
            post_task = self.post_task
            tracker = TaskTracking.objects.filter(
                task_template=post_task
            ).filter(
                **{
                    tracker_type.get(type(self)): self
                }
            ).first()
            if tracker:
                res = tracker.tasks.aggregate(
                    assigned=Count('task'),
                    completed=Count(
                        'task',
                        filter=Q(task__status=COMPLETED)
                    )
                )
                assigned = res.get('assigned') or 0
                completed = res.get('completed') or 0
                return completed, assigned
        return None, None

    @cached_property
    def post_task_status(self):
        completed, assigned = self.post_task_status_stats
        if assigned:
            if assigned > 0:
                if assigned == completed:
                    return self._COMPLETED
                return self._PENDING
        return self._UNASSIGNED


class TaskTemplateTitle(BaseModel, SlugModel):
    name = models.CharField(max_length=255, validators=[validate_title])
    template_type = models.CharField(
        max_length=6, choices=CHANGE_TYPE_CHOICES,
        db_index=True
    )
    organization = models.ForeignKey(
        to=Organization,
        on_delete=CASCADE
    )

    def __str__(self):
        return self.get_template_type_display() + ' for ' + self.name


class TaskFromTemplate(BaseModel):
    template = models.ForeignKey(
        to=TaskTemplateTitle, on_delete=models.CASCADE,
        related_name='templates'
    )
    # TODO @Ravi: Reduce the title char_field to 100, as limit for task is 100 chars only.
    #  Currently, limited through Serializer
    title = models.CharField(max_length=255, validators=[validate_title])
    description = models.TextField(
        max_length=10000,
        blank=True
    )
    observers = models.ManyToManyField(USER)
    priority = models.CharField(
        max_length=9, choices=TASK_PRIORITIES,
        default=MINOR, db_index=True
    )
    deadline = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    changeable_deadline = models.BooleanField(
        default=False, null=True,
        help_text="Responsible Can Change Deadline"
    )
    include_employee = models.BooleanField(default=False)

    def __str__(self):
        return self.template.name + ' ' + self.title


class TaskFromTemplateAttachment(BaseModel):
    attachment = models.FileField(
        upload_to=get_task_attachment_path,
        validators=[FileExtensionValidator(
            allowed_extensions=settings.ACCEPTED_FILE_FORMATS_LIST
        )]
    )
    caption = models.CharField(max_length=200, blank=True, null=True)
    template = models.ForeignKey(
        TaskFromTemplate, on_delete=models.CASCADE,
        related_name='attachments'
    )

    def __str__(self):
        return f"{self.attachment} | {self.caption}"


class TaskFromTemplateResponsiblePerson(BaseModel):
    task = models.ForeignKey(
        TaskFromTemplate, on_delete=models.CASCADE,
        related_name='responsible_persons'
    )
    user = models.ForeignKey(USER, on_delete=models.CASCADE)
    core_tasks = models.ManyToManyField(CoreTask)

    def __str__(self):
        return str(self.task) + ' for ' + self.user.full_name


class TaskFromTemplateChecklist(BaseModel):
    task = models.ForeignKey(
        to=TaskFromTemplate, on_delete=models.CASCADE,
        related_name='checklists'
    )
    title = models.CharField(
        max_length=100  # limited as per task's checklist.
    )
    order = models.IntegerField(null=True)

    def __str__(self):
        return self.title + ' for ' + self.task.title

    class Meta:
        unique_together = (
            'task', 'title'
        )
        ordering = 'order',


class LetterTemplate(BaseModel, SlugModel):
    """
    Base Letter Template for Offer Letters, Promotion Letters, etc.
    """
    title = models.CharField(
        max_length=255, validators=[validate_title]
    )
    message = models.TextField()
    type = models.CharField(
        max_length=10, choices=LETTER_TEMPLATE_TYPE_CHOICES,
        db_index=True
    )
    organization = models.ForeignKey(
        to=Organization,
        on_delete=CASCADE
    )

    def __str__(self):
        return self.get_type_display() + ' ' + self.title


class PreEmployment(PrePostTaskMixin, BaseModel):
    full_name = models.CharField(
        max_length=255, validators=[validate_full_name]
    )
    address = models.CharField(
        max_length=255,
        blank=True
    )
    gender = models.CharField(
        max_length=10, choices=GENDER_CHOICES,
        blank=True
    )
    deadline = models.DateTimeField(validators=[validate_future_datetime])
    date_of_join = models.DateField(validators=[validate_future_date])
    email = models.EmailField(blank=True, null=True)

    # FoKey's
    employment_level = models.ForeignKey(
        to=EmploymentLevel, on_delete=CASCADE
    )
    employment_status = models.ForeignKey(
        to=EmploymentStatus, on_delete=models.SET_NULL,
        null=True
    )
    job_title = models.ForeignKey(
        to=EmploymentJobTitle, on_delete=CASCADE
    )
    division = models.ForeignKey(
        to=OrganizationDivision, on_delete=models.SET_NULL,
        null=True
    )
    branch = models.ForeignKey(
        to=OrganizationBranch, on_delete=models.SET_NULL,
        null=True
    )
    payroll = models.ForeignKey(
        to=Package, on_delete=models.SET_NULL, null=True
    )
    organization = models.ForeignKey(
        to=Organization, on_delete=CASCADE
    )
    marital_status = models.CharField(
        max_length=20, choices=MARITAL_STATUS_CHOICES, default=SINGLE,
        db_index=True
    )
    job_description = models.TextField(blank=True, max_length=100000)
    job_specification = models.TextField(blank=True, max_length=100000)
    contract_period = models.DateField(null=True)
    template_letter = models.ForeignKey(
        to=LetterTemplate, on_delete=models.SET_NULL,
        null=True, related_name='pre_employments'
    )
    generated_letter = models.OneToOneField(
        to='hris.GeneratedLetter', on_delete=models.SET_NULL, null=True
    )
    pre_task = models.ForeignKey(
        to=TaskTemplateTitle,
        related_name='pre_task_employments',
        on_delete=CASCADE,
        null=True
    )
    post_task = models.ForeignKey(
        to=TaskTemplateTitle,
        related_name='post_tasks_employments',
        on_delete=CASCADE,
        null=True
    )
    employee = models.ForeignKey(
        to=USER,
        related_name='reviews',
        on_delete=CASCADE,
        null=True
    )
    status = models.CharField(
        max_length=20,
        choices=ONBOARDING_STATUS,
        default=ACTIVE,
        db_index=True
    )
    step = models.PositiveSmallIntegerField(
        validators=[MinMaxValueValidator(
            min_value=0, max_value=100
        )],
        null=True,
        help_text='Step/Grade of the employee to join.'
    )
    # HRIS-673 Implement Soft-Delete.
    is_deleted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('email', 'full_name')

    def __str__(self):
        return self.full_name + ' ' + self.job_title.title


class ChangeType(BaseModel, SlugModel):
    organization = models.ForeignKey(
        to=Organization,
        on_delete=CASCADE,
        related_name='review_change_types'
    )
    title = models.CharField(max_length=255, validators=[validate_title])
    affects_experience = models.BooleanField()
    affects_payroll = models.BooleanField()
    affects_work_shift = models.BooleanField()
    affects_core_tasks = models.BooleanField()
    affects_leave_balance = models.BooleanField()
    badge_visibility = models.CharField(
        max_length=1,
        choices=BADGE_VISIBILITY_CHOICES,
        default=NEITHER,
        db_index=True
    )

    def __str__(self):
        return self.title

    @property
    def is_assigned(self):
        return self.details.exists()


class LeaveChangeType(BaseModel):
    leave_type = models.ForeignKey(
        to=LeaveType, on_delete=CASCADE
    )
    leave_account = models.ForeignKey(
        to=LeaveAccount, on_delete=CASCADE,
    )
    balance = models.FloatField()
    update_balance = models.FloatField(null=True)
    change_type = models.ForeignKey(
        to='hris.EmployeeChangeTypeDetail',
        related_name='leave_changes',
        on_delete=CASCADE
    )

    def __str__(self):
        return self.leave_type.name + str(self.balance) + ' -> ' \
               + str(self.update_balance)


class EmployeeChangeTypeDetail(BaseModel):
    change_type = models.ForeignKey(
        to=ChangeType, on_delete=models.SET_NULL,
        related_name='details', null=True
    )
    old_experience = models.ForeignKey(
        to=UserExperience, on_delete=models.SET_NULL,
        related_name='old_change_types', null=True
    )
    new_experience = models.ForeignKey(
        to=UserExperience, on_delete=models.SET_NULL,
        related_name='new_change_types', null=True
    )
    old_work_shift = models.ForeignKey(
        to=WorkShift, on_delete=models.SET_NULL,
        related_name='old_change_types', null=True
    )
    new_work_shift = models.ForeignKey(
        to=WorkShift, on_delete=models.SET_NULL,
        related_name='new_change_types', null=True
    )
    old_payroll = models.ForeignKey(
        to=Package, on_delete=models.SET_NULL,
        related_name='old_change_types', null=True
    )
    new_payroll = models.ForeignKey(
        to=Package, on_delete=models.SET_NULL,
        related_name='new_change_types', null=True
    )


class EmployeeSeparationType(BaseModel, SlugModel):
    title = models.CharField(max_length=100, validators=[validate_title])
    category = models.CharField(
        choices=SEPARATION_CATEGORY_CHOICES,
        max_length=20,
        db_index=True
    )
    organization = models.ForeignKey(
        to=Organization,
        related_name='separation_types',
        on_delete=CASCADE
    )
    display_leave = models.BooleanField(
        default=True
    )
    display_payroll = models.BooleanField(
        default=True
    )
    display_attendance_details = models.BooleanField(
        default=True
    )
    display_pending_tasks = models.BooleanField(
        default=True
    )
    badge_visibility = models.CharField(
        max_length=1,
        choices=BADGE_VISIBILITY_CHOICES,
        default=NEITHER,
        db_index=True
    )

    def __str__(self):
        return self.title

    @property
    def is_assigned(self):
        return self.employeeseparation_set.exists()


class EmployeeSeparation(PrePostTaskMixin, BaseModel):
    employee = models.ForeignKey(
        to=USER, on_delete=CASCADE
    )
    separation_type = models.ForeignKey(
        to=EmployeeSeparationType, on_delete=CASCADE
    )
    parted_date = models.DateField(
        help_text='The date employee asked to leave the company.',
        null=True
    )
    effective_date = models.DateField(
        help_text='The date, HR accepted the resignation.',
        null=True
    )
    release_date = models.DateField(
        null=True,
        help_text='The date, employee disappears from the system.'
    )
    status = models.CharField(
        max_length=23,
        choices=OFFBOARDING_STATUS,
        default=ACTIVE,
        db_index=True
    )
    remarks = models.CharField(max_length=settings.TEXT_FIELD_MAX_LENGTH)
    pre_task = models.ForeignKey(
        to=TaskTemplateTitle,
        related_name='separation_pre_tasks',
        on_delete=CASCADE,
        null=True
    )
    post_task = models.ForeignKey(
        to=TaskTemplateTitle,
        related_name='separation_post_tasks',
        on_delete=CASCADE,
        null=True
    )

    def __str__(self):
        prefix = ""
        if self.parted_date:
            prefix = 'on' + self.parted_date.strftime('%Y-%m-%d')

        return self.separation_type.title + self.employee.full_name + prefix


class EmploymentReview(PrePostTaskMixin, BaseModel):
    employee = models.ForeignKey(
        to=USER, on_delete=CASCADE, related_name='employment_reviews'
    )
    change_type = models.ForeignKey(
        to=ChangeType,
        related_name='employment_reviews',
        on_delete=CASCADE
    )
    pre_task = models.ForeignKey(
        to=TaskTemplateTitle,
        related_name='pre_task_reviews',
        on_delete=CASCADE,
        null=True
    )
    post_task = models.ForeignKey(
        to=TaskTemplateTitle,
        related_name='post_task_reviews',
        on_delete=CASCADE,
        null=True
    )
    detail = models.OneToOneField(
        to=EmployeeChangeTypeDetail,
        related_name='review',
        on_delete=CASCADE
    )
    status = models.CharField(
        default=ACTIVE,
        choices=CHANGE_TYPE_STATUS,
        max_length=20,
        db_index=True
    )
    remarks = models.TextField(
        blank=True,
        max_length=5000
    )

    def __str__(self):
        return str(self.change_type) + self.employee.full_name + \
               self.created_at.strftime('%Y-%m-%d')


class TaskTemplateMapping(BaseModel):
    template_detail = models.ForeignKey(
        to=TaskFromTemplate,
        on_delete=CASCADE
    )
    task = models.ForeignKey(
        to=Task,
        on_delete=CASCADE,
        null=True
    )


class TaskTracking(BaseModel):
    pre_employment = models.ForeignKey(
        to=PreEmployment,
        related_name='task',
        on_delete=CASCADE,
        null=True
    )
    employment_review = models.ForeignKey(
        to=EmploymentReview,
        related_name='task',
        on_delete=CASCADE,
        null=True
    )
    separation = models.ForeignKey(
        to=EmployeeSeparation,
        related_name='task',
        on_delete=CASCADE,
        null=True
    )
    task_template = models.ForeignKey(
        to=TaskTemplateTitle,
        related_name='generated_tasks',
        on_delete=CASCADE
    )
    tasks = models.ManyToManyField(
        to=TaskTemplateMapping
    )


class GeneratedLetter(BaseModel):
    employee = models.ForeignKey(
        to=USER,
        on_delete=CASCADE,
        null=True
    )
    pre_employment = models.ForeignKey(
        to=PreEmployment,
        related_name='generated_letters',
        on_delete=CASCADE,
        null=True
    )
    employment_review = models.ForeignKey(
        to=EmploymentReview,
        related_name='generated_letters',
        on_delete=CASCADE,
        null=True
    )
    separation = models.ForeignKey(
        to=EmployeeSeparation,
        related_name='generated_letters',
        on_delete=CASCADE,
        null=True
    )
    letter_template = models.ForeignKey(
        to=LetterTemplate,
        on_delete=CASCADE,
        related_name='generated_letters'
    )
    email = models.EmailField(blank=True, null=True)
    uri = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(
        max_length=10, choices=EMAIL_STATUS_CHOICES, default=NOT_SENT,
        db_index=True
    )
    remarks = models.TextField(max_length=600)

    def __str__(self):
        return self.email + ' ' + self.status

    def regenerate(self):
        from irhrs.hris.utils import generate_offer_letter

        instance = next(
            filter(
                None,
                [self.pre_employment, self.employment_review, self.separation]
            ),
            None
        )
        if instance:
            message = generate_offer_letter(
                instance,
                self.letter_template,
                uri=self.uri,
                generated_instance=self
            )
        else:
            message = ''
        self.message = message
        if isinstance(instance, PreEmployment):
            self.email = instance.employee.email if instance.employee else instance.email
        elif isinstance(instance, EmploymentReview):
            self.email = instance.employee.email
        elif isinstance(instance, EmployeeSeparation):
            self.email = instance.employee.email
        self.save(update_fields=['message', 'email'])


class GeneratedLetterHistory(BaseModel):
    letter = models.ForeignKey(
        to=GeneratedLetter,
        related_name='history',
        on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=10, choices=EMAIL_STATUS_CHOICES, db_index=True
    )
    remarks = models.TextField(max_length=600, blank=True, null=True)

    def __str__(self):
        return f"{self.letter} was {self.status}"


class StatusHistory(BaseModel):
    pre_employment = models.ForeignKey(
        to=PreEmployment,
        related_name='history',
        on_delete=CASCADE,
        null=True
    )
    employment_review = models.ForeignKey(
        to=EmploymentReview,
        related_name='history',
        on_delete=CASCADE,
        null=True
    )
    separation = models.ForeignKey(
        to=EmployeeSeparation,
        related_name='history',
        on_delete=CASCADE,
        null=True
    )
    status = models.CharField(
        max_length=50,  # choices have been removed, because the choices can
        # be from 3 models combined. We could either merge all 3, or leave its
        # choices blank (as it is never exposed to the user).
        db_index=True
    )
    remarks = models.TextField(max_length=600, blank=True, null=True)

    def __str__(self):
        instance = next(filter(
            None,
            [self.pre_employment, self.employment_review, self.separation],
        ), None)
        return f"{instance} was {self.status}"


class LeaveEncashmentOnSeparation(BaseModel):
    separation = models.ForeignKey(EmployeeSeparation, on_delete=models.CASCADE,
                                   related_name='encashment_edits')

    leave_account = models.ForeignKey(LeaveAccount, on_delete=models.CASCADE,
                                      related_name='encashment_edits_on_separation')
    encashment_balance = models.FloatField()

    class Meta:
        unique_together = ('separation', 'leave_account')

    def __str__(self):
        return f"{self.separation} -" \
               f" {self.leave_account.rule.leave_type.name}:" \
               f" {self.encashment_balance}"


class LeaveEncashmentOnSeparationChangeHistory(BaseModel):
    encashment = models.ForeignKey(LeaveEncashmentOnSeparation,
                                   on_delete=models.CASCADE,
                                   related_name='history')
    actor = models.ForeignKey(USER, on_delete=models.SET_NULL, null=True)
    previous_balance = models.FloatField()
    new_balance = models.FloatField()
    remarks = models.CharField(max_length=255)

    @property
    def previous_balance_display(self):
        if self.encashment.leave_account.rule.leave_type.category in HOURLY_LEAVE_CATEGORIES:
            return humanize_interval(self.previous_balance * 60)
        return round(self.previous_balance, 2)

    @property
    def new_balance_display(self):
        if self.encashment.leave_account.rule.leave_type.category in HOURLY_LEAVE_CATEGORIES:
            return humanize_interval(self.new_balance * 60)
        return round(self.new_balance, 2)

    def __str__(self):
        return f"{self.actor.full_name} updated balance" \
               f" from {self.previous_balance_display} to {self.new_balance_display} with remarks"\
               f" '{self.remarks}'."
