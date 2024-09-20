from django.contrib.auth import get_user_model
from django.db.models import Max
from django.utils import timezone
from django.utils.functional import cached_property
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.core.constants.common import TASK_APPROVAL_NOTIFICATION
from irhrs.core.fields import RecursiveField
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils import nested_getattr
from irhrs.notification.utils import add_notification
from irhrs.task.api.v1.serializers.project import TaskProjectSerializer
from irhrs.task.constants import (
    COMPLETED, PENDING, OBSERVER,
    RESPONSIBLE_PERSON, CLOSED, TASK_STATUSES_CHOICES,
    ON_HOLD)
from irhrs.task.models import Task, TaskSettings, WorkLog, WorkLogAction
from irhrs.task.models.task import (
    TaskActivity, RecurringTaskDate,
    TaskAssociation, MAX_LIMIT_OF_TASK_SCORING_CYCLE, TaskCheckList)
from irhrs.task.utils.rrule import recurring_date_for_task
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from .association import TaskAssociationSerializer
from .checklist import TaskChecklistSerializer
from .recurring import RecurringTaskSerializer

USER = get_user_model()


class TaskThinSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Task
        fields = (
            'id', 'title', 'description', 'deadline',
            'status', 'priority', 'created_at'
        )


class RecurringTasksQueueSerializer(DynamicFieldsModelSerializer):
    created_task = TaskThinSerializer(read_only=True)

    class Meta:
        model = RecurringTaskDate
        fields = 'id', 'created_task', 'recurring_at', 'last_tried',


class TaskSerializer(DynamicFieldsModelSerializer):
    check_lists = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False, write_only=True)
    responsible_persons = serializers.ListField(
        child=TaskAssociationSerializer(fields=('user', 'core_tasks',)),
        required=True, allow_null=False, allow_empty=False)
    observers = serializers.ListField(
        child=TaskAssociationSerializer(fields=('user', 'core_tasks',)),
        required=False, allow_null=True, allow_empty=True)
    recurring = RecurringTaskSerializer(required=False, allow_null=True)

    is_recurring = serializers.BooleanField(read_only=True)
    is_delayed = serializers.BooleanField(read_only=True)

    task_completion_percentage = serializers.SerializerMethodField()
    recurring_task_queue = RecurringTasksQueueSerializer(read_only=True,
                                                         many=True)
    can_view_task_history = serializers.SerializerMethodField()
    can_view_parent_task = serializers.SerializerMethodField()
    can_view_project = serializers.SerializerMethodField()
    attachments_count = serializers.IntegerField(
        source='task_attachments.count', read_only=True)
    comments_count = serializers.IntegerField(source='task_comments.count',
                                              read_only=True)
    sub_tasks_count = serializers.IntegerField(source='sub_tasks.count',
                                               read_only=True)
    starts_at = serializers.DateTimeField(allow_null=True, required=False)
    max_limit_of_scoring_cycle = serializers.SerializerMethodField()

    class Meta:
        # configuration starts
        _MODEL_FIELDS = ['id', 'project', 'title', 'description', 'parent',
                         'priority', 'status', 'deadline', 'starts_at',
                         'start', 'finish', 'changeable_deadline',
                         'approved_at',
                         'approved',
                         'approve_required', 'created_by', 'recurring',
                         'created_at', 'modified_at', 'freeze']
        _RELATED_MODEL_FIELDS = ['responsible_persons', 'observers',
                                 'check_lists',
                                 'recurring_task_queue']
        _EXTRA_FIELDS = ['is_recurring', 'task_completion_percentage',
                         'is_delayed', 'can_view_task_history',
                         'attachments_count', 'comments_count',
                         'sub_tasks_count',
                         'can_view_parent_task', 'can_view_project',
                         'max_limit_of_scoring_cycle']
        _READ_ONLY_FIELDS = ['approve_required', 'start', 'finish',
                             'created_at', 'modified_at', 'approved_at',
                             'approved', 'freeze']
        # configuration ends

        model = Task
        fields = _MODEL_FIELDS + _RELATED_MODEL_FIELDS + _EXTRA_FIELDS
        read_only_fields = _READ_ONLY_FIELDS

    @cached_property
    def task_settings(self):
        if self.request and self.request.user.is_authenticated:
            return TaskSettings.get_for_organization(self.request.user.detail.organization)
        return None

    def can_user_assign_task(self, responsible_person):
        if (
            self.task_settings and
            not self.task_settings.can_assign_to_higher_employment_level and
            (
                nested_getattr(self.request.user, 'detail.organization') ==
                nested_getattr(responsible_person, 'detail.organization')
            )
        ):
            return nested_getattr(
                responsible_person, 'detail.employment_level.order_field', default=0
            ) <= nested_getattr(
                self.request.user,
                'detail.employment_level.order_field',
                default=0
            )
        return True

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == 'get':
            fields['project'] = TaskProjectSerializer(
                fields=('id', 'name', 'created_by',))
            fields['parent'] = RecursiveField(
                fields=('id', 'title', 'status', 'priority'))
            fields['responsible_persons'] = TaskAssociationSerializer(
                fields=TaskAssociationSerializer.get_fields_(
                    thin_view=self.context.get('force_thin_view'),
                    exclude_fields=('verification_score',)
                ),
                many=True, context=self.context)
            fields['observers'] = TaskAssociationSerializer(
                fields=TaskAssociationSerializer.get_fields_(
                    thin_view=True,
                    exclude_fields=('verification_score',)
                ),
                many=True,
                context=self.context)
            fields['check_lists'] = TaskChecklistSerializer(many=True)
            fields['created_by'] = UserThinSerializer()

        if self.request and self.request.method.lower() in ['patch', 'put']:
            if 'from_template' not in self.context:
                fields['check_lists'] = serializers.PrimaryKeyRelatedField(
                    queryset=TaskCheckList.objects.filter(task=self.context.get('task')),
                    many=True
                )
        return fields

    # Extra Fields for Task Models for GET
    def get_can_view_task_history(self, obj):
        if obj.created_by == self.request.user or \
            obj.task_associations.filter(user=self.request.user).exists():
            return True
        return False

    def get_can_view_parent_task(self, obj):
        # THis is incomplete implementation since A supervisor and HR should be
        # able to see but has not been covered for now
        if obj.parent:
            if obj.parent.created_by == self.request.user or \
                obj.parent.task_associations.filter(
                    user=self.request.user).exists():
                return True
        return False

    def get_can_view_project(self, obj):
        # This is incomplete implementation since A supervisor and HR should be
        # able to see but has not been covered for now
        if obj.project:
            if obj.project.created_by == self.request.user or \
                self.request.user.user_activity_projects.filter(
                    pk=obj.project.id).exists():
                return True
        return False

    @staticmethod
    def get_max_limit_of_scoring_cycle(obj):
        return MAX_LIMIT_OF_TASK_SCORING_CYCLE

    # Total Task completion percentage
    # Currently generated using checklists completion only
    @staticmethod
    def get_task_completion_percentage(obj):
        check_list_count = obj.task_checklists.count()
        completed_checklists = obj.task_checklists.filter(
            completed_on__isnull=False).count()
        return (
                   completed_checklists / check_list_count) * 100 if completed_checklists else 0

    # This field can be updated by the Responsible Person
    def validate_status(self, status):
        if status != PENDING:
            if not self.instance:
                raise serializers.ValidationError(
                    "Initial Task Should have Pending Status")
        if status in [CLOSED, ON_HOLD]:
            if self.instance.created_by != self.request.user:
                raise serializers.ValidationError("Cannot set status")
        if status == COMPLETED:
            if self.instance.task_checklists.filter(
                completed_on__isnull=True).count() != 0:
                raise serializers.ValidationError(
                    "Cannot set to Completed having pending checklists")
            if Task.objects.filter(parent=self.instance,
                                   approved=False
                                   ).exclude(status=CLOSED).count() != 0:
                raise serializers.ValidationError(
                    "Cannot set to Completed having pending Sub Tasks")

        return status

    def validate_parent(self, parent_task):
        if not parent_task:
            return parent_task
        if parent_task.is_recurring:
            raise serializers.ValidationError("Cannot Create sub task "
                                              "for recurring Task")
        if parent_task.status in [ON_HOLD, CLOSED]:
            raise serializers.ValidationError("Task is on Hold or Closed")
        if self.instance and self.instance.parent == parent_task:
            return parent_task
        if not (
            parent_task.created_by == self.request.user or parent_task.task_associations.filter(
            user=self.request.user,
            association=RESPONSIBLE_PERSON).exists()):
            raise serializers.ValidationError(
                "You are not authorized to create sub task for this task")
        if parent_task.approved:
            raise serializers.ValidationError(
                "Cannot create sub task for completed and approved task")
        if self.instance and self.instance == parent_task:
            raise serializers.ValidationError(
                "A task cannot be parent to itself")
        return parent_task

    def validate_project(self, project):
        if not project:
            return project
        if not (project.created_by == self.request.user or
                self.request.user.user_activity_projects.filter(
                    project=project).exists()):
            raise serializers.ValidationError('You must be creator or '
                                              'member of this project')
        return project

    # This field can be updated by the Responsible Person
    def validate_deadline(self, deadline):
        if deadline < timezone.now():
            raise serializers.ValidationError('Cannot Set Deadline To Past')
        # check validation while updating if the
        # deadline is less than sub task deadline or not
        if self.instance:
            max_deadline_of_sub_task = Task.objects.filter(
                parent=self.instance).aggregate(Max('deadline'))
            if max_deadline_of_sub_task.get('deadline__max'):
                if deadline < max_deadline_of_sub_task['deadline__max']:
                    raise serializers.ValidationError(
                        'Should Be Greater Than Sub Task\'s Deadline')
        return deadline

    def validate_starts_at(self, starts_at):
        if self.instance:
            if not starts_at:
                return self.instance.starts_at
            if starts_at.replace(microsecond=0,
                                 second=0) != self.instance.starts_at.replace(
                microsecond=0,
                second=0):
                if starts_at < timezone.now():
                    raise serializers.ValidationError(
                        "Start Time should be in Future")
            if self.instance.status != PENDING:
                # lets check this small condition
                # If its the same data from api and instance then mark it valid
                raise serializers.ValidationError(
                    "Can ony update when Task is in Pending")
        else:
            if not starts_at:
                return timezone.now()
            if starts_at < timezone.now():
                raise serializers.ValidationError(
                    "Start Time should be in Future")
        return starts_at

    def validate(self, attrs):
        if self.instance and \
            self.instance.approved and \
            not self.instance.is_recurring:
            raise serializers.ValidationError(
                "Completed/Approved Task cannot be Updated")
        if self.instance and self.instance.parent and \
            self.instance.parent.status == COMPLETED:
            raise serializers.ValidationError(
                "Cannot Update Since the Parent Task is Completed")
        r_list = []
        o_list = []
        if 'responsible_persons' in attrs.keys():
            for i in attrs['responsible_persons']:
                if not self.can_user_assign_task(i['user']):
                    raise serializers.ValidationError({
                        'responsible_persons': 'Task assignment to higher employment level'
                                               ' not allowed.'
                    })

                r_list.append(i['user'].id)
                if i.get('core_tasks', None):
                    if not i['user'].current_experience:
                        raise serializers.ValidationError(
                            {
                                'responsible_persons': '{} has no current experience '.format(
                                    i['user'].full_name)})
                    else:
                        user_user_task_count = i[
                            'user'].current_experience.user_result_areas.filter(
                            core_tasks__in=i['core_tasks']).count()
                        if user_user_task_count != len(i['core_tasks']):
                            raise serializers.ValidationError(
                                {
                                    'responsible_persons': 'Invalid core tasks for {}'.format(
                                        i['user'].full_name)})
                    if len(i.get('core_tasks')) == 0:
                        raise serializers.ValidationError(
                            {
                                'responsible_persons': 'Core tasks are required for responsible person'})

                else:
                    raise serializers.ValidationError(
                        {
                            'responsible_persons': 'Core tasks are required for responsible person'})

        if 'observers' in attrs.keys():
            for i in attrs['observers']:
                o_list.append(i['user'].id)
                if i.get('core_tasks', None):
                    if not i['user'].current_experience:
                        raise serializers.ValidationError(
                            {
                                'observers': '{} has no current experience '.format(
                                    i['user'].full_name)})
                    else:
                        user_user_task_count = i[
                            'user'].current_experience.user_result_areas.filter(
                            core_tasks__in=i['core_tasks']).count()
                        if user_user_task_count != len(i['core_tasks']):
                            raise serializers.ValidationError(
                                {
                                    'observers': 'Invalid core tasks for {}'.format(
                                        i['user'].full_name)})
        _task_creator_id = self.request.user.id
        if self.instance:
            _task_creator_id = self.instance.created_by_id
        if _task_creator_id in r_list:
            raise serializers.ValidationError(
                'Task Creator cannot be assigned as Responsible Person')

        if _task_creator_id in o_list:
            raise serializers.ValidationError(
                'Task Creator cannot be assigned as Observer')

        if not len(r_list) == len(set(r_list)):
            raise serializers.ValidationError(
                'Responsible Persons should not be duplicate')
        if not len(o_list) == len(set(o_list)):
            raise serializers.ValidationError(
                'Observers should not be duplicate')
        if not len(r_list + o_list) == len(set(r_list + o_list)):
            raise serializers.ValidationError(
                'A person cannot be added as Responsible and Observer at the same time ')

        parent = attrs.get('parent', ...)
        if parent is not ...:
            _parent_deadline = attrs.get('parent').deadline if attrs.get(
                'parent') else self.instance.parent.deadline if self.instance and self.instance.parent else None
            _deadline = attrs.get('deadline') if attrs.get(
                'deadline') else self.instance.deadline if self.instance else None
            if _parent_deadline and _deadline:
                if _deadline >= _parent_deadline:
                    raise serializers.ValidationError(
                        {
                            'deadline': 'Deadline of Subtask cannot be greater than parent'})

        starts_at = attrs.get('starts_at', ...)
        if starts_at is not ...:
            _starts_at = attrs.get('starts_at') if attrs.get(
                'starts_at') else self.instance.starts_at if self.instance else None
            _deadline = attrs.get('deadline') if attrs.get(
                'deadline') else self.instance.deadline if self.instance else None
            if _starts_at and _deadline:
                if _starts_at >= _deadline:
                    raise serializers.ValidationError(
                        {
                            'deadline': 'Deadline should be greater than start time '})

        return attrs

    def validate_check_lists(self, checklist):
        if self.instance:
            task = self.context.get('task')
            if task and task.task_checklists.count() != len(checklist):
                raise ValidationError('Incomplete checklist for task.')
        return checklist

    def create(self, validated_data):
        post_save_data = dict()
        check_lists = validated_data.pop('check_lists', None)
        if 'recurring' in validated_data.keys():
            recurring = validated_data.pop('recurring', None)
            if recurring:
                validated_data.update(recurring)

        # since responsible persons and observers are from related model
        if 'responsible_persons' in validated_data.keys():
            post_save_data.update({'responsible_persons': validated_data.pop(
                'responsible_persons')})

        if 'observers' in validated_data.keys():
            post_save_data.update(
                {'observers': validated_data.pop('observers')})

        # Create the task with validated data
        task = super().create(validated_data)

        # create checklists
        self.create_checklists(check_lists, task)
        self.fields['check_lists'] = TaskChecklistSerializer(many=True)

        for k, v in post_save_data.items():
            if k == 'responsible_persons':
                # Call the responsible_person setter method
                task.responsible_persons = v
                # Update the serializer Data Type
                self.fields['responsible_persons'] = TaskAssociationSerializer(
                    many=True,
                    fields=(
                        'user',
                        'created_at',
                        'core_tasks',
                        'read_only'))

            elif k == 'observers':
                # call the observers setter method
                task.observers = v
                # Update the serializer Data Type
                self.fields['observers'] = TaskAssociationSerializer(many=True,
                                                                     fields=(
                                                                         'user',
                                                                         'created_at',
                                                                         'core_tasks',
                                                                         'read_only'))
        # If the created Task is recurring_task ,
        # then create every possible dates for this task when recurring Task are generated
        if task.recurring_rule:
            recurring_date_for_task(task)

        # if the created Task is sub task then
        #               copy assigner , assignee from Parent to Sub Task
        if task.parent:
            users = list(
                TaskAssociation.objects.filter(
                    task_id=task.parent_id
                ).exclude(user_id=task.created_by_id).values_list('user_id',
                                                                  flat=True))
            if task.parent.created_by_id != task.created_by_id:
                users.append(task.parent.created_by_id)

            for user in users:
                if task.task_associations.filter(user_id=user).exists():
                    _ = task.task_associations.filter(user_id=user).update(
                        read_only=True
                    )
                else:
                    _ = task.task_associations.create(user_id=user,
                                                      association=OBSERVER,
                                                      read_only=True,
                                                      )

        return task

    def update(self, instance: Task, validated_data):
        from irhrs.core.utils.change_request import get_changes

        # Evaluate recurring rule status and condition
        _current_recurring_status = False
        _past_recurring_status = True if instance.recurring_rule else False
        if 'recurring' in validated_data.keys():
            recurring = validated_data.pop('recurring')
            if recurring:
                _current_recurring_status = True
                validated_data.update(recurring)
            else:
                # delete previous generated dates if recurring is null
                _ = RecurringTaskDate.objects.filter(template=instance,
                                                     created_task__isnull=True).delete()
                validated_data.update({
                    'recurring_first_run': None,
                    'recurring_rule': None
                })
        _task_changes = get_changes(validated_data, instance)

        # Status check
        if 'status' in validated_data.keys():
            if instance.status != validated_data['status']:
                # TEMP HACK
                # if its the first time updating status then track the start time
                if not instance.start:
                    validated_data.update({'start': timezone.now()})

            if validated_data['status'] == COMPLETED:
                # update the finish tracker
                validated_data.update({'finish': timezone.now()})
                if instance.approve_required:
                    interactive_kwargs = self._get_interactive_notification_kwargs(
                        instance)
                    add_notification(
                        f'{instance.title} has been completed and '
                        f'awaits verification',
                        instance.created_by,
                        instance,
                        url=f'/user/task/approvals?as=assigner',
                        actor=self.request.user,
                        **interactive_kwargs
                    )
                else:
                    add_notification(
                        f'{instance.title} has been completed',
                        instance.created_by,
                        instance,
                        url=f'/user/task/my/{instance.id}/detail',
                        actor=self.request.user
                    )
                    # automatically set the approved Flag
                    validated_data.update({'approved': True,
                                           'finish': timezone.now()
                                           })
            else:
                # if status is changed to anything except COMPLETED
                # just change update the approved Flag
                validated_data.update({
                    'approved': False,
                    'finish': None,
                    'approved_at': None
                })

        # update the task with validated data
        task = super().update(instance, validated_data)
        if 'project' in validated_data.keys():
            # change project serializer DataType
            self.fields['project'] = TaskProjectSerializer(
                fields=('id', 'name', 'created_by',),
                read_only=True)

        if _past_recurring_status and _current_recurring_status:
            # updated the recurring rule , so update the recurring dates accordingly.
            recurring_date_for_task(instance, update=True)
        elif _current_recurring_status:
            # Created recurring rule so add recurring dates
            recurring_date_for_task(instance)

        # Create Task Change History/ Activity / Log
        if _task_changes:
            self.create_histories_for_task(_task_changes)

        checklists = validated_data.get('check_lists')
        if checklists:
            self.maintain_checklist_order(checklists)
        return task

    def maintain_checklist_order(self, checklists):
        task = self.context.get('task')
        old_checklists = task.task_checklists.all()
        old_checklists.update(order=None)
        for index, checklist in enumerate(checklists):
            checklist.order = index + 1
            checklist.save()

    def create_checklists(self, check_lists, task):
        if check_lists:
            from ....models.task import TaskCheckList
            TaskCheckList.objects.bulk_create(
                [
                    TaskCheckList(
                        task=task,
                        title=title,
                        created_by=self.request.user,
                        order=index + 1
                    ) for index, title in enumerate(check_lists)
                ]
            )

    def create_histories_for_task(self, changes):
        if not self.instance:
            return
        _histories = []
        for k, v in changes.items():
            if k == 'status':
                _choices = dict(TASK_STATUSES_CHOICES)
                description = 'Updated Status from {} to {}'.format(
                    _choices.get(int(v.get('old_value_display'))),
                    _choices.get(int(v.get('new_value_display')))
                )
            elif k == 'deadline':
                description = 'Updated Deadline from {} to {}'.format(
                    v.get('old_value_display').astimezone().strftime(
                        "%Y-%m-%d %H:%M:%S"),
                    v.get('new_value_display').astimezone().strftime(
                        "%Y-%m-%d %H:%M:%S")
                )
            elif k == 'description':
                description = 'Updated Description'
            elif k == 'starts_at':
                description = 'Updated Task Start Time from {} to {}'.format(
                    v.get('old_value_display').astimezone().strftime(
                        "%Y-%m-%d %H:%M:%S"),
                    v.get('new_value_display').astimezone().strftime(
                        "%Y-%m-%d %H:%M:%S")
                )
            elif k == 'changeable_deadline':
                if v.get('new_value'):
                    description = 'Turned on Changeable Deadline'
                else:
                    description = 'Turned off Changeable Deadline'
            else:
                if not v.get('old_value'):
                    if k == 'recurring_rule':
                        description = 'Created Recurring Rule'
                    elif k == 'recurring_first_run':
                        description = 'Added recurring first run at {}'.format(
                            v.get('new_value_display')
                        )
                    else:
                        description = 'Created {}  as {}'.format(
                            k.title(),
                            v.get('new_value_display')
                        )
                else:
                    if k == 'recurring_rule':
                        description = 'Updated Recurring Rule' if v.get(
                            'new_value') else "Removed Recurring Rule"
                    elif k == 'recurring_first_run':
                        description = 'Updated recurring first run from {} to {}'.format(
                            v.get('old_value_display'),
                            v.get('new_value_display')
                        ) if v.get(
                            'new_value') else "Removed Recurring first run date"
                    else:
                        description = 'Updated {} from {} to {}'.format(
                            k.title(),
                            v.get('old_value_display'),
                            v.get('new_value_display')
                        )
            _temp = TaskActivity(
                task=self.instance,
                previous_value=v.get('old_value'),
                previous_value_display=v.get('old_value_display'),
                present_value=v.get('new_value'),
                present_value_display=v.get('new_value_display'),
                key=k,
                description=description,
            )
            _histories.append(_temp)
        TaskActivity.objects.bulk_create(_histories)

    @staticmethod
    def _get_interactive_notification_kwargs(instance: Task) -> dict:
        # if only one responsible person then only send interactive notification
        if instance.responsible_persons.count() == 1:
            return dict(
                is_interactive=True,
                interactive_type=TASK_APPROVAL_NOTIFICATION,
                interactive_data={
                    'task_approval_id': instance.id,
                    'user_id': nested_getattr(
                        instance.responsible_persons.first(), 'user.id'
                    )
                }
            )

        return dict()


class TaskApprovalSerializer(TaskSerializer):
    class Meta(TaskSerializer.Meta):
        pass

    def get_responsible_persons(self, obj):
        cycle_status = self.context['request'].query_params.get(
            'cycle_status')
        fil = dict(
            association=RESPONSIBLE_PERSON
        )
        if cycle_status:
            task_association = obj.task_associations.filter(
                cycle_status=cycle_status
            )
        else:
            task_association = obj.task_associations.all()

        if self.context['request'].query_params.get('as') == 'responsible':
            fil.update({
                'user': self.context['request'].user
            })
        task_association = task_association.filter(**fil)

        return TaskAssociationSerializer(task_association,
                                         fields=TaskAssociationSerializer.get_fields_(
                                             thin_view=self.context.get(
                                                 'force_thin_view'),
                                             exclude_fields=(
                                                 'verification_score',)
                                         ),
                                         many=True, context=self.context).data

    def get_fields(self):
        fields = super().get_fields()
        fields["responsible_persons"] = serializers.SerializerMethodField()
        return fields


class StopRecurringTaskSerializer(serializers.Serializer):
    # queued_task = serializers.ListField(child=serializers.IntegerField())

    def get_fields(self):
        fields = super().get_fields()
        task = self.context.get('task')
        fields['queued_task'] = serializers.PrimaryKeyRelatedField(
            queryset=RecurringTaskDate.objects.filter(
                template=task,
                created_task__isnull=True
            ),
            many=True
        )
        return fields


class TaskAssociatedUsersSerializer(DynamicFieldsModelSerializer):
    division = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    employment_level = serializers.SerializerMethodField()

    class Meta:
        model = USER
        fields = [
            'full_name',
            'employment_level',
            'division',
            'organization',
        ]

    @staticmethod
    def get_division(obj):
        return nested_getattr(obj, 'detail.division') or '' if hasattr(obj, 'detail') else ''

    @staticmethod
    def get_organization(obj):
        return nested_getattr(obj, 'detail.organization') or '' if hasattr(obj, 'detail') else ''

    @staticmethod
    def get_employment_level(obj):
        return nested_getattr(obj, 'detail.employment_level')


class TaskExportSerializer(DynamicFieldsModelSerializer):
    created_by = TaskAssociatedUsersSerializer()
    assigned_to = serializers.SerializerMethodField()
    changeable_deadline = serializers.SerializerMethodField()
    approve_required = serializers.SerializerMethodField()
    approved = serializers.SerializerMethodField()
    freeze = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'created_by', 'assigned_to', 'created_at', 'modified_at',
            'project', 'title', 'deleted_at', 'description', 'parent',
            'get_priority_display', 'get_status_display', 'starts_at',
            'deadline', 'start', 'finish', 'changeable_deadline',
            'approve_required', 'approved', 'approved_at', 'recurring_rule',
            'recurring_first_run', 'freeze'
        ]

    @staticmethod
    def get_assigned_to(task):
        return TaskAssociatedUsersSerializer(
            task.assigned_user,
            many=True,
        ).data

    @staticmethod
    def get_changeable_deadline(obj):
        return str(obj.changeable_deadline)

    @staticmethod
    def get_approve_required(obj):
        return str(obj.approve_required)

    @staticmethod
    def get_approved(obj):
        return str(obj.approved)

    @staticmethod
    def get_freeze(obj):
        return str(obj.freeze)
