from itertools import chain

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models as M
from django.utils import timezone
from django.utils.functional import cached_property

from irhrs.common.models import BaseModel
from irhrs.core.utils.common import modify_field_attributes
from .project import TaskProject
from .settings import Project
from .ra_and_core_tasks import CoreTask
from ..constants import (
    INVOLVEMENT_CHOICES, REMINDER_NOTIFICATION_METHODS, TASK_PRIORITIES,
    MINOR, TASK_STATUSES_CHOICES, PENDING, RESPONSIBLE_PERSON,
    OBSERVER, REMINDER_STATUS_CHOICES, REMINDER_PENDING, NOTIFICATION,
    CYCLE_STATUS, APPROVAL_PENDING)
from ..manager import TaskManager
from ..utils import (
    get_task_attachment_path, validate_efficiency, validate_score
)

User = get_user_model()
MAX_LIMIT_OF_TASK_SCORING_CYCLE = 2


@modify_field_attributes(
    created_by={
        'verbose_name': "Task Creator"
    }
)
class Task(BaseModel):
    ###########################################################################
    # project : A task must be lie inside a project , sometime a task may not
    #           be for a project , those tasks can be called personal task ,
    #           sometime personal tasks are required to manage my daily task
    # project = M.ForeignKey(TaskProject, on_delete=M.SET_NULL,
    #                        null=True, blank=True,
    #                        related_name='project_tasks')
    # From new implementation of worklog [hris-3181], Task model refers to new Project model
    project = M.ForeignKey(Project, on_delete=M.SET_NULL,
                           null=True, blank=True,
                           related_name='project_tasks')
    ##########################################################################

    ###########################################################################
    # title     :   Title is the required field to create a task , tasks can be
    #               created from the kanban board directly , where we only
    #               except title to  be given by the creator
    # created_by       :default authenticated user
    title = M.CharField(max_length=100)
    deleted_at = M.DateTimeField(null=True, blank=True)
    ###########################################################################

    description = M.TextField(null=True, blank=True,
                              help_text="Description about the Task",
                              max_length=10000)
    ###########################################################################
    # parent : parent relation is used to handle the sub-tasks
    # Figure 1 >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # ................ Task A :                           -> No parent
    # ........................Task B (A.1)                -> Parent is Task A
    # .................................... Task C (A.1.1) -> Parent is Task B
    # .................................... Task D (A.1.1) -> Parent is Task B
    # .......................Task E (A,2)                 -> Parent is Task A
    #
    # The parent relation will give me the flexibility to determine the tasks
    # and their sub-task but it would be hard to maintain the order of the
    # execution of the chained dependent task
    #               To solve this problem we introduce `:dependent` relation
    #               which will Have the order of the execution of dependent task
    # With the help of these two relations: (parent,dependent), dependent ,
    # chained task and the sub-task problem can be solved
    #  EG : TASK D IS DEPENDENT ON TASK C
    # Figure 2 >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # ................ Task A :                           -> No parent
    # ........................Task B (A.1)                -> Parent is Task A
    #                                                     -> No dependency
    # .................................... Task C (A.1.1) -> Parent is Task B
    #                                                     -> No dependency
    # .................................... Task D (A.1.1) -> Parent is Task B
    #                                                     -> Dependent on Task C
    # .......................Task E (A,2)                 -> Parent is Task A
    #                                                     -> No dependency
    # CONCLUSION : In figure 1 we know that the task C and D can be done
    # concurrently because they don't have any dependency , but in figure 2 ,
    # task C and D cannot be done parallel because Task D is dependent on
    # Task C , ie: when C is
    # completed then only D can be done
    parent = M.ForeignKey('self',
                          on_delete=M.CASCADE, related_name='+',
                          null=True, blank=True)
    # dependent = M.ForeignKey('self', on_delete=M.SET_NULL, related_name='+',
    #                          null=True, blank=True)
    ###########################################################################

    priority = M.CharField(max_length=9, choices=TASK_PRIORITIES,
                           default=MINOR)
    status = M.PositiveSmallIntegerField(choices=TASK_STATUSES_CHOICES,
                                         default=PENDING)

    ###########################################################################
    # TASK SETTINGS
    ###########################################################################

    # deadline : is required fields

    starts_at = M.DateTimeField(default=timezone.now,
                                help_text='Start Task from ')
    deadline = M.DateTimeField(help_text="Deadline for the task")

    # Start and finish is tracked when the task status changed to InProgress
    # and then Completed
    start = M.DateTimeField(null=True, blank=True,
                            help_text="Work on task started from")
    finish = M.DateTimeField(null=True, blank=True,
                             help_text="Work on task finished on")

    changeable_deadline = M.BooleanField(
        default=True,
        help_text="Responsible Can Change Deadline"
    )

    # Currently every tasks should have approval mechanism, this flag
    # has been kept which can be helpful in future
    approve_required = M.BooleanField(default=True,
                                      help_text="Approve Task When Completed")

    # task status reached to completed

    approved = M.BooleanField(default=False)
    approved_at = M.DateTimeField(null=True, blank=True)

    ###########################################################################
    # Recurring Task :
    #                If a task is recurring then it should have a recurring rule
    ###########################################################################
    recurring_rule = M.TextField(null=True, blank=True)
    recurring_first_run = M.DateField(null=True, blank=True)

    # freeze is a boolean kept to check if a task can be updated .
    # This field can be useful when the task is being cloned
    # used at : irhrs.task.utils.clone.task_disassociate
    freeze = M.BooleanField(default=False)
    objects = TaskManager()

    @property
    def recurring(self):
        return self if self.recurring_rule else None

    @property
    def responsible_persons(self):
        return self.task_associations.filter(association=RESPONSIBLE_PERSON)

    @responsible_persons.setter
    def responsible_persons(self, val):
        # refactor this one to have lazy loading of models
        from irhrs.task.utils.task import get_all_descendants

        past_states = set(
            self.task_associations.filter(
                association=RESPONSIBLE_PERSON
            ).values_list('user_id', flat=True)
        )
        present_state = set(item['user'].id for item in val)
        _delete_list = list(past_states - present_state)
        if _delete_list:
            for _d in _delete_list:
                # TEMP HACK
                # IF THE RESPONSIBLE PERSON OF THE SUB-TASKs ARE FROM THE
                # PARENT TASK THEN
                # `read_only` flag is set to True for such associated members
                # SOMETIME, THAT KIND OF RESPONSIBLE PERSONS ARE REMOVED
                # AND ADDED A NEW RESPONSIBLE PERSON
                # SO THOSE RESPONSIBLE PERSON SHOULD BE REMOVED TO
                # OBSERVERS INSTEAD OF REMOVING THEM
                associated_user = self.task_associations.get(user_id=_d)
                if associated_user.association == RESPONSIBLE_PERSON:
                    if associated_user.read_only:
                        associated_user.association = OBSERVER
                        associated_user.save()  # update_fields=['association']
                    else:
                        associated_user.delete()

                        desc_task = get_all_descendants(self.id)
                        count, _ = TaskAssociation.objects.filter(
                            user_id=_d, task_id__in=desc_task
                        ).exclude(association=RESPONSIBLE_PERSON).delete()
                        # since we are excluding association=RESPONSIBLE_PERSON
                        # in future we may need to set read_only to false to
                        # those excluded associations

        for item in val:
            try:
                i = self.task_associations.get(user=item['user'])
                i.association = RESPONSIBLE_PERSON
                i.save()  # update_fields=['association']
            except ObjectDoesNotExist:
                i = self.task_associations.create(
                    user=item['user'], association=RESPONSIBLE_PERSON
                )

                desc_task = get_all_descendants(self.id)
                for _task_id in desc_task:
                    _ = TaskAssociation.objects.get_or_create(
                        task_id=_task_id,
                        user=item['user'],
                        defaults={
                            'association': OBSERVER,
                            'read_only': True
                        })
            if 'core_tasks' in item.keys():
                if item['core_tasks']:
                    i.core_tasks.clear()
                    i.core_tasks.add(*item['core_tasks'])
                else:
                    i.core_tasks.clear()

    @property
    def observers(self):
        return self.task_associations.filter(association=OBSERVER)

    @observers.setter
    def observers(self, val):

        # refactor this one to have lazy loading of models
        from irhrs.task.utils.task import get_all_descendants

        past_states = set(
            self.task_associations.filter(
                association=OBSERVER).values_list('user_id', flat=True)
        )
        present_state = set(item['user'].id for item in val)
        _delete_list = list(past_states - present_state)
        if _delete_list:
            for _d in _delete_list:
                associated_user = self.task_associations.get(
                    user_id=_d
                )
                if associated_user.association == OBSERVER:
                    if not associated_user.read_only:
                        associated_user.delete()
                        desc_task = get_all_descendants(self.id)
                        count, _ = TaskAssociation.objects.filter(
                            user_id=_d, task_id__in=desc_task
                        ).exclude(association=RESPONSIBLE_PERSON).delete()

        for item in val:
            try:
                i = self.task_associations.get(user=item['user'])
                i.association = OBSERVER
                i.save(update_fields=['association'])
            except ObjectDoesNotExist:
                i = self.task_associations.create(user=item['user'],
                                                  association=OBSERVER)

                desc_task = get_all_descendants(self.id)
                for _task_id in desc_task:
                    _ = TaskAssociation.objects.get_or_create(
                        task_id=_task_id,
                        user=item['user'],
                        defaults={
                            'association': OBSERVER,
                            'read_only': True
                        })

            if 'core_tasks' in item.keys():
                if item['core_tasks']:
                    i.core_tasks.clear()
                    i.core_tasks.add(*item['core_tasks'])
                else:
                    i.core_tasks.clear()

    @property
    def check_lists(self):
        return self.task_checklists.all()

    @check_lists.setter
    def check_lists(self, val):
        pass

    @property
    def sub_tasks(self):
        return Task.objects.filter(parent=self).all()

    @property
    def recurring_task_queue(self):
        return self.recurring_task_queue.all()

    @property
    def is_delayed(self):
        # In future , send some description about
        # the condition executed for calculating delayed

        # [UPDATED] :
        # Check delayed only when Task status is in
        # [PENDING, IN_PROGRESS, COMPLETED]
        # Backend should not send T/F for other status
        # [CLOSED,ON_HOLD] because this
        # status have no connection with delayed
        # So , Backend will send T/F for [PENDING, IN_PROGRESS, COMPLETED]
        #                   'N/A' for [CLOSED,ON_HOLD]
        return (
            self.finish > self.deadline if self.finish else
            timezone.now() > self.deadline
        )

    # Flag to determine if the Task is Recurring
    @property
    def is_recurring(self):
        # Just checking if recurring_rule is empty or not
        return bool(self.recurring_rule)

    @property
    def assigned_to(self):
        return ', '.join(
            [u.user.full_name for u in self.task_associations.filter(
                association=RESPONSIBLE_PERSON
            )]
        )

    @property
    def assigned_user(self):
        return [u.user for u in self.task_associations.filter(association=RESPONSIBLE_PERSON)]

    def __str__(self):
        return f"{self.title}"


class TaskAssociation(BaseModel):
    user = M.ForeignKey(User, on_delete=M.CASCADE)
    association = M.CharField(max_length=18, choices=INVOLVEMENT_CHOICES)
    is_active = M.BooleanField(default=True)
    task = M.ForeignKey(Task, on_delete=M.CASCADE,
                        related_name='task_associations')
    core_tasks = M.ManyToManyField(CoreTask)

    read_only = M.BooleanField(default=False,
                               help_text='Determines if the '
                                         'row is editable or not ')
    efficiency_from_priority = M.FloatField(null=True, blank=True,
                                            validators=[validate_efficiency])
    efficiency_from_timely = M.FloatField(null=True, blank=True,
                                          validators=[validate_efficiency])
    efficiency_from_score = M.FloatField(null=True, blank=True,
                                         validators=[validate_efficiency])
    efficiency = M.FloatField(null=True, blank=True,
                              validators=[validate_efficiency])
    cycle_status = M.CharField(max_length=32, blank=True,
                               default=APPROVAL_PENDING, choices=CYCLE_STATUS,
                               db_index=True)

    class Meta:
        unique_together = ('user', 'task'),
        verbose_name = 'Task User'
        verbose_name_plural = 'Task Users'

    def __str__(self):
        return f"{self.user} | {self.association} | {self.task} "

    @cached_property
    def get_latest_score_cycle(self):
        return self.taskverificationscore_set.first()

    @cached_property
    def current_score(self):
        return self.get_latest_score_cycle.score if \
            self.get_latest_score_cycle else None

    @cached_property
    def _ack(self):
        return self.get_latest_score_cycle.ack if \
            self.get_latest_score_cycle else None

    @cached_property
    def total_cycle(self):
        return self.taskverificationscore_set.count()

    @cached_property
    def scores(self):
        return self.taskverificationscore_set.order_by('created_at')


class TaskVerificationScore(BaseModel):
    association = M.ForeignKey(TaskAssociation, on_delete=M.CASCADE)
    score = M.PositiveSmallIntegerField(validators=[validate_score])
    remarks = M.TextField()
    ack = M.BooleanField(null=True, )
    ack_remarks = M.TextField(null=True, blank=True)
    ack_at = M.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.association} got {self.score}"


class TaskCheckList(BaseModel):
    task = M.ForeignKey(Task, on_delete=M.CASCADE,
                        related_name='task_checklists')
    title = M.CharField(max_length=100)
    completed_by = M.ForeignKey(User, on_delete=M.SET_NULL, null=True,
                                related_name='+')
    completed_on = M.DateTimeField(null=True)
    order = M.IntegerField(validators=[MinValueValidator(1)], null=True)

    def __str__(self):
        return f"{self.task} has-> {self.title}"

    class Meta:
        ordering = ('order', 'created_at')


class TaskReminder(BaseModel):
    remind_on = M.DateTimeField()
    user = M.ForeignKey(User, on_delete=M.CASCADE,
                        related_name='user_task_reminders')
    method = M.CharField(max_length=12, choices=REMINDER_NOTIFICATION_METHODS,
                         default=NOTIFICATION)
    task = M.ForeignKey(Task, on_delete=M.CASCADE,
                        related_name='task_task_reminder')
    sent_on = M.DateTimeField(null=True, blank=True)
    status = M.CharField(max_length=8, choices=REMINDER_STATUS_CHOICES,
                         default=REMINDER_PENDING)
    extra_data = M.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user} on {self.remind_on} for {self.task} by " \
               f"{self.method}"


class RecurringTaskDate(BaseModel):
    recurring_at = M.DateField()
    template = M.ForeignKey(Task, on_delete=M.CASCADE,
                            related_name='recurring_task_queue')
    created_task = M.OneToOneField(Task, on_delete=M.CASCADE, null=True)
    remarks = M.TextField(null=True, blank=True)
    last_tried = M.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.recurring_at} for {self.template}'


class TaskAttachment(BaseModel):
    attachment = M.FileField(
        upload_to=get_task_attachment_path,
        validators=[FileExtensionValidator(
            allowed_extensions=list(chain.from_iterable(settings.ACCEPTED_FILE_FORMATS.values()))
        )]
    )
    caption = M.CharField(max_length=200, blank=True, null=True)
    task = M.ForeignKey(Task, on_delete=M.CASCADE,
                        related_name='task_attachments')

    class Meta:
        ordering = 'created_at',

    def __str__(self):
        return f"{self.attachment} | {self.caption}"


class TaskComment(BaseModel):
    comment = M.TextField(max_length=1000)
    task = M.ForeignKey(Task, on_delete=M.CASCADE,
                        related_name='task_comments')

    class Meta:
        ordering = '-created_at',
        verbose_name = 'Task Comment'
        verbose_name_plural = 'Task Comments'

    def __str__(self):
        return f"{self.created_by}"


class TaskActivity(BaseModel):
    task = M.ForeignKey(Task, on_delete=M.CASCADE, related_name='histories')
    previous_value = M.TextField(blank=True, null=True)
    previous_value_display = M.TextField(blank=True, null=True)
    present_value = M.TextField(blank=True, null=True)
    present_value_display = M.TextField(blank=True, null=True)
    key = M.CharField(max_length=50)
    description = M.TextField()

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f"{self.task} || {self.previous_value} --> {self.present_value}"
