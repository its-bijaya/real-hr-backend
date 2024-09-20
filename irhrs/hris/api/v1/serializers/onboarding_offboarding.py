import re
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q, Count
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.relations import SlugRelatedField

from irhrs.attendance.api.v1.serializers.workshift import WorkShiftSerializer
from irhrs.attendance.constants import WORKDAY
from irhrs.attendance.utils.attendance import humanize_interval
from irhrs.core.constants import EMAIL_TEMPLATE_MAX_LENGTH
from irhrs.core.constants.user import FEMALE, OTHER, MALE, TERMINATED
from irhrs.core.mixins.serializers import (
    DynamicFieldsModelSerializer,
    add_fields_to_serializer_class)
from irhrs.core.utils import (
    nested_getattr,
    get_patch_attr)
from irhrs.core.utils.common import DummyObject, get_complete_url, get_today
from irhrs.core.utils.dependency import get_dependency
from irhrs.core.validators import validate_future_date, validate_title
from irhrs.hris.api.v1.serializers.core_task import UserResultAreaSerializer, CoreTaskSerializer
from irhrs.hris.constants import (
    OFFER_LETTER, ACCEPTED, DECLINED,
    LETTER_NOT_GENERATED, OFFER_LETTER_LETTER_PARAMS, CHANGE_TYPE,
    CHANGE_TYPE_LETTER_PARAMS, ONBOARDING, ONBOARDING_LETTER_PARAMS,
    OFFBOARDING, OFFBOARDING_LETTER_PARAMS, OFFBOARDING_SEQUENCE,
    PAYROLL_REVIEWED, ACTIVE, STOPPED, HOLD, SENT, DOWNLOADED, SAVED,
    COMPLETED as HRIS_COMPLETED, PENDING, ONBOARDING_SEQUENCE, IN_PROGRESS, LEAVE_REVIEWED,
    ATTENDANCE_REVIEWED, PENDING_TASKS_REVIEWED, CUSTOM, CUSTOM_LETTER_PARAMS,
    CHANGE_TYPE_SEQUENCE, EXPERIENCE_ADDED, PAYROLL_CHANGED, WORKSHIFT_CHANGED, CORE_TASKS_UPDATED,
    LEAVE_UPDATED
)
from irhrs.hris.models.onboarding_offboarding import (
    GeneratedLetter,
    TaskTracking, TaskTemplateMapping,
    StatusHistory, TaskFromTemplateResponsiblePerson, TaskFromTemplateAttachment,
    LeaveEncashmentOnSeparationChangeHistory, LeaveEncashmentOnSeparation)
from irhrs.hris.utils import (
    choice_field_display, create_task_from_templates,
    create_letter_from_template, validate_no_off_boarding_in_progress,
    validate_no_employment_review_in_progress)
from irhrs.leave.api.v1.serializers.settings import LeaveTypeSerializer
from irhrs.leave.constants.model_constants import HOURLY_LEAVE_CATEGORIES
from irhrs.leave.tasks import get_active_master_setting, get_proportionate_leave_balance
from irhrs.notification.utils import notify_organization
from irhrs.organization.api.v1.serializers.branch import \
    OrganizationBranchSerializer
from irhrs.organization.api.v1.serializers.division import \
    OrganizationDivisionSerializer
from irhrs.organization.api.v1.serializers.employment import \
    (
    EmploymentLevelSerializer, EmploymentStatusSerializer,
    EmploymentJobTitleSerializer)
from irhrs.organization.models import (
    EmploymentLevel, EmploymentStatus,
    EmploymentJobTitle, OrganizationDivision, OrganizationBranch)
from irhrs.payroll.api.v1.serializers import MinimalPackageDetailSerializer
from irhrs.payroll.utils.virtual_user_payroll import calculate_payroll
from irhrs.permission.constants.permissions import HRIS_PERMISSION, HRIS_ON_BOARDING_PERMISSION
from irhrs.task.api.v1.serializers.task import TaskSerializer
from irhrs.task.constants import COMPLETED, TASK_ATTACHMENT_MAX_UPLOAD_SIZE
from irhrs.task.models.task import TaskAttachment
from irhrs.users.api.v1.serializers.experience import (
    UserExperienceSerializer,
    UserUpcomingExperienceSerializer)
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer, \
    UserThumbnailSerializer, UserThickSerializer
from ....models import (
    TaskTemplateTitle, TaskFromTemplate, TaskFromTemplateChecklist,
    PreEmployment, ChangeType, LeaveChangeType, EmployeeChangeTypeDetail,
    EmployeeSeparationType, EmployeeSeparation, LetterTemplate,
    EmploymentReview,
)

USER = get_user_model()


class AutoAddSlugMixin:
    """
    Auto add created_at, modified_at, slug or id everywhere.
    """

    def get_created_at(self, instance):
        return instance.created_at.astimezone()

    def get_modified_at(self, instance):
        return instance.modified_at.astimezone()

    def get_fields(self):
        fields = super().get_fields()
        fields['created_at'] = SerializerMethodField(read_only=True)
        fields['modified_at'] = SerializerMethodField(read_only=True)

        # add id or slug what is available.
        fields['slug'] = serializers.ReadOnlyField()
        fields['id'] = serializers.ReadOnlyField()
        return fields


class PrePostTaskMixin:
    """
    decide when to allow pre and post tasks.
    Update: Added `status` field.
    `status` will be completed if all pre and post tasks are completed.
    """

    pre_task_status_stats = SerializerMethodField()
    post_task_status_stats = SerializerMethodField()

    def get_fields(self):
        fields = super().get_fields()
        fields['pre_task'] = serializers.SlugRelatedField(
            slug_field='slug',
            queryset=TaskTemplateTitle.objects.filter(
                organization=self.context.get('organization'),
                template_type=self.context.get('letter_type')
            ),
            allow_null=True,
            required=False
        )
        fields['post_task'] = serializers.SlugRelatedField(
            slug_field='slug',
            queryset=TaskTemplateTitle.objects.filter(
                organization=self.context.get('organization'),
                template_type=self.context.get('letter_type')
            ),
            allow_null=True,
            required=False
        )
        if self.request and self.request.method == 'POST':
            fields.pop('pre_task', None)
            fields.pop('post_task', None)
        elif self.request and self.request.method == 'GET':
            fields['status_remark'] = serializers.SerializerMethodField()
        else:
            fields['status_remark'] = serializers.CharField(
                write_only=True,
                max_length=600,
                allow_blank=True,
                required=False
            )
        fields['task_status'] = SerializerMethodField(read_only=True)
        fields['pre_task_status'] = serializers.ReadOnlyField()
        fields['post_task_status'] = serializers.ReadOnlyField()
        return fields

    def get_status_remark(self, instance):
        return getattr(instance.history.first(), 'remarks', None)

    def get_task_status(self, instance):
        pre_status = instance.pre_task_status
        if pre_status == 'Completed':
            post_status = instance.post_task_status
            if post_status == 'Completed':
                return 'Completed'
            return 'In Progress'
        return pre_status

    def validate_pre_task(self, pre_task):
        if self.instance:
            if self.instance.pre_task:
                if not pre_task and self.instance.pre_task_status == 'Pending':
                    return pre_task
                elif self.instance.pre_task != pre_task:
                    raise ValidationError(
                        "Cannot update pre-task"
                    )
            if pre_task and pre_task == self.instance.post_task:
                raise ValidationError(
                    "Pre and Post Task cannot be same."
                )
        return pre_task

    def validate_post_task(self, post_task):
        if not self.instance:
            raise ValidationError(
                "Cannot assign post task when instance is not created."
            )
        else:
            if not self.instance.post_task and not post_task:
                return None
        if self.instance.pre_task and self.instance.pre_task == post_task:
            raise ValidationError(
                "Pre and Post task cannot be the same."
            )
        if self.instance.post_task:
            if not post_task and self.instance.post_task_status == 'Pending':
                return None
            if self.instance.post_task != post_task:
                raise ValidationError(
                    "Cannot update post task"
                )
        return post_task

    @transaction.atomic()
    def update(self, instance, validated_data):
        tracker_type = {
            PreEmployment: 'pre_employment',
            EmploymentReview: 'employment_review',
            EmployeeSeparation: 'separation'
        }
        if 'pre_task' in validated_data:
            pre_task = validated_data.get(
                'pre_task'
            )
            if not pre_task:
                TaskTracking.objects.filter(
                    task_template=instance.pre_task
                ).filter(
                    **{
                        tracker_type.get(type(instance)): instance
                    }
                ).delete()
        if 'post_task' in validated_data:
            post_task = validated_data.get(
                'post_task'
            )
            if not post_task:
                TaskTracking.objects.filter(
                    task_template=instance.post_task
                ).filter(
                    **{
                        tracker_type.get(type(instance)): instance
                    }
                ).delete()
        status_remark = validated_data.pop('status_remark', None)
        old_status = instance.status
        new_status = get_patch_attr(
            'status',
            validated_data,
            self
        )
        if new_status and old_status != new_status:
            StatusHistory.objects.create(
                **{
                    tracker_type.get(type(instance)): instance
                },
                status=new_status,
                remarks=status_remark
            )
        return super().update(instance, validated_data)

    def get_pre_task_status_stats(self, instance):
        return dict(
            zip(
                ('completed', 'assigned'), instance.pre_task_status_stats)
        )

    def get_post_task_status_stats(self, instance):
        return dict(
            zip(
                ('completed', 'assigned'), instance.post_task_status_stats)
        )

    def validate(self, attrs):
        status = attrs.get('status')
        status_remark = attrs.get('status_remark')

        # do not allow further change in status once completed
        instance = getattr(self, 'instance', None)
        if instance and status and instance.status == HRIS_COMPLETED and \
            status \
            != instance.status:
            raise ValidationError({
                'status': ['Can not update status once completed']
            })

        if status in [HOLD, STOPPED] and not status_remark:
            raise ValidationError({
                'status_remark': f'Remark is essential for {status} status.'
            })
        return attrs


class TaskTemplateTitleSerializer(AutoAddSlugMixin,
                                  DynamicFieldsModelSerializer):
    class Meta:
        model = TaskTemplateTitle
        fields = (
            'name', 'template_type', 'modified_at', 'slug'
        )
        read_only_fields = ('slug',)

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method == 'GET':
            fields['template_type'] = SerializerMethodField()
        return fields

    def get_template_type(self, instance):
        return choice_field_display(instance, 'template_type')

    def create(self, validated_data):
        validated_data.update({
            'organization': self.context.get('organization')
        })
        return super().create(validated_data)

    def validate(self, attrs):
        params = dict(
            template_type=attrs.get('template_type'),
            name__iexact=attrs.get('name'),
            organization=self.context.get('organization'),
        )
        qs = self.Meta.model.objects.filter(**params)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(
                'The task for this template for this '
                'organization already exists.'
            )
        return super().validate(attrs)


class TaskFromTemplateChecklistSerializer(AutoAddSlugMixin,
                                          DynamicFieldsModelSerializer):
    class Meta:
        model = TaskFromTemplateChecklist
        fields = 'title',


class TaskFromTemplateAttachmentSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = TaskFromTemplateAttachment
        fields = '__all__'

    def create(self, validated_data):
        validated_data.update({'template': self.context.get('template')})
        return super().create(validated_data)

    @staticmethod
    def validate_attachment(attachment):
        if attachment.size > TASK_ATTACHMENT_MAX_UPLOAD_SIZE:
            raise serializers.ValidationError(
                f'File Size Should not Exceed {TASK_ATTACHMENT_MAX_UPLOAD_SIZE / (1024 * 1024)} MB')
        return attachment


class TaskMultiAssignSerializer(serializers.Serializer):
    template_mapping = serializers.PrimaryKeyRelatedField(
        queryset=TaskTemplateMapping.objects.all(),
        many=True
    )

    @staticmethod
    def validate_template_mapping(template):
        if len(template) == 0:
            raise ValidationError(
                {
                    'detail': 'Must select at-least one template while assigning task.'
                }
            )
        return template

    def build_observer(self, instance, observer, include_employee):
        # user = self.context.get('request').user.id
        # if user in observer:
        #     observer.remove(user)

        if include_employee and instance.employee:
            observer.append(instance.employee.id)

        return list(
            map(
                lambda observer: {'user': observer, 'core_tasks': []},
                observer
            )
        )

    # def build_responsible_person(self, responsible_person):
    #     return list(
    #         filter(
    #             lambda x: x.get('user') != self.context.get('request').user.id,
    #             responsible_person
    #         )
    #     )

    def generate_task_data(self, validated_data):
        for instance in validated_data.get('template_mapping'):
            if instance.task:
                continue
            template_detail = TaskFromTemplateSerializer(
                instance.template_detail,
                fields=[
                    'id', 'title', 'description', 'observers', 'priority', 'deadline',
                    'changeable_deadline', 'checklists', 'responsible_persons'
                ],
            ).data
            checklists = template_detail.pop('checklists')
            deadline = template_detail.pop('deadline')
            template_detail.update(
                {
                    'check_lists': list(
                        map(
                            lambda x: x.get('title'),
                            checklists
                        )
                    ),
                    'observers': self.build_observer(
                        self.context.get('actual_object'),
                        template_detail.get('observers'),
                        instance.template_detail.include_employee
                    ),
                    # 'responsible_persons': self.build_responsible_person(
                    #     template_detail.get('responsible_persons')
                    # ),
                    'deadline': get_today(with_time=True) + timedelta(days=deadline),
                    'starts_at': get_today(with_time=True) + timedelta(minutes=15)
                }
            )
            yield instance, template_detail

    def create_attachment_for_task(self, instance, created_task):
        attachments = instance.template_detail.attachments.all()
        if attachments:
            task_attachments = []
            for temp_attachment in attachments:
                task_attachments.append(
                    TaskAttachment(
                        attachment=temp_attachment.attachment,
                        caption=temp_attachment.caption,
                        task=created_task
                    )
                )

            if task_attachments:
                TaskAttachment.objects.bulk_create(task_attachments)

    # @transaction.atomic()
    def create(self, validated_data):
        templates = self.generate_task_data(validated_data)
        task_context = self.context.copy()
        for instance, data in templates:
            task_serializer = TaskSerializer(
                exclude_fields=[
                    'recurring', 'project', 'parent'
                ],
                context=task_context,
                data=data,
            )
            task_serializer.is_valid(raise_exception=True)
            created_task = task_serializer.save()
            instance.task = created_task
            instance.save()
            self.create_attachment_for_task(instance, created_task)
        return DummyObject(**validated_data)


class TaskForTemplateResponsibleSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = TaskFromTemplateResponsiblePerson
        fields = ['user', 'core_tasks']

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method == 'GET':
            fields['user'] = UserThinSerializer(
                fields=['id', 'full_name', 'profile_picture', 'cover_picture','organization','is_current',]
            )
            fields['core_tasks'] = CoreTaskSerializer(
                many=True, read_only=True,
                fields=(
                    'id', 'title', 'description',
                    'order', 'result_area'
                )
            )
        return fields


class TaskFromTemplateSerializer(AutoAddSlugMixin,
                                 DynamicFieldsModelSerializer):
    checklists = TaskFromTemplateChecklistSerializer(many=True)
    checklists_count = serializers.ReadOnlyField()
    title = serializers.CharField(
        max_length=100,
        validators=[validate_title]
    )
    observers = serializers.PrimaryKeyRelatedField(
        queryset=USER.objects.all().current(),
        many=True,
        required=False
    )
    deadline_date = serializers.SerializerMethodField()

    class Meta:
        model = TaskFromTemplate
        fields = (
            'template', 'title', 'description', 'modified_at', 'checklists_count',
            'id', 'observers', 'priority', 'deadline', 'include_employee',
            'changeable_deadline', 'checklists', 'responsible_persons', 'deadline_date'
        )

    @transaction.atomic()
    def create(self, validated_data):
        check_list = validated_data.pop('checklists', [])
        responsible_persons = validated_data.pop('responsible_persons', [])
        instance = super().create(validated_data)

        TaskFromTemplateChecklist.objects.bulk_create([
            TaskFromTemplateChecklist(
                title=data.get('title'),
                task=instance,
                order=index + 1
            ) for index, data in enumerate(check_list)
        ])

        for responsible_person in responsible_persons:
            responsible = TaskFromTemplateResponsiblePerson.objects.create(
                task=instance,
                user=responsible_person.get('user')
            )
            responsible.core_tasks.set(responsible_person.get('core_tasks'))
            responsible.save()
        return instance

    @transaction.atomic()
    def update(self, instance, validated_data):
        old_check_list = set(
            instance.checklists.values_list('title', flat=True)
        )
        validated_checklist = validated_data.pop('checklists', [])
        responsible_persons = validated_data.pop('responsible_persons', [])
        check_list = list(map(lambda x: x.get('title'), validated_checklist))

        new = set(check_list) - old_check_list
        remove = old_check_list - set(check_list)
        TaskFromTemplateChecklist.objects.bulk_create([
            TaskFromTemplateChecklist(
                title=data,
                task=instance
            ) for data in new
        ])
        instance.checklists.filter(
            title__in=remove
        ).delete()

        updated_checklists = instance.checklists.all()
        for checklist in updated_checklists:
            checklist.order = check_list.index(checklist.title) + 1
            checklist.save()

        instance.checklists_count = instance.checklists.count()

        instance.responsible_persons.all().delete()
        for responsible_person in responsible_persons:
            responsible = TaskFromTemplateResponsiblePerson.objects.create(
                task=instance,
                user=responsible_person.get('user')
            )
            responsible.core_tasks.set(responsible_person.get('core_tasks'))
            responsible.save()
        return super().update(instance, validated_data)

    def get_fields(self):
        fields = super().get_fields()
        fields['responsible_persons'] = TaskForTemplateResponsibleSerializer(
            many=True,
            required=False,
            context=self.context
        )
        if self.request and self.request.method == 'GET':
            fields['template'] = TaskTemplateTitleSerializer()
            fields['observers'] = UserThinSerializer(
                fields=['id', 'full_name', 'profile_picture', 'cover_picture','organization','is_current',],
                many=True
            )
        else:
            fields['template'] = SlugRelatedField(
                slug_field='slug',
                queryset=TaskTemplateTitle.objects.filter(
                    organization=self.context.get('organization')
                )
            )
        return fields

    def validate_checklists(self, checklists):
        clist = [d.get('title').lower() for d in checklists]
        duplicated = any([
            clist.count(elem) > 1 for elem in clist
        ])
        if duplicated:
            raise ValidationError(
                'The checklist items cannot be duplicated.'
            )
        return checklists

    def validate(self, attrs):
        queryset = self.Meta.model.objects.filter(
            template=attrs.get('template'),
            title__iexact=attrs.get('title')
        )
        observers = set(attrs.get('observers'))
        responsible_persons = set(
            map(
                lambda x: x.get('user'),
                attrs.get('responsible_persons')
            )
        )
        if observers.intersection(responsible_persons):
            raise ValidationError(
                "Same person can't be observer as well as responsible person "
                "at once."
            )

        if self.instance:
            if self.instance.tasktemplatemapping_set.filter(
                task__isnull=False
            ).exists():
                raise ValidationError(
                    "Cannot edit template once assigned."
                )
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise ValidationError(
                'The task for this template already exists.'
            )
        return super().validate(attrs)

    @staticmethod
    def get_deadline_date(instance):
        return get_today(with_time=True) + timedelta(days=instance.deadline)


class EmploymentReviewSerializer(PrePostTaskMixin,
                                 AutoAddSlugMixin,
                                 DynamicFieldsModelSerializer):
    effective_date = SerializerMethodField(read_only=True)
    change_type = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=ChangeType.objects.all()
    )
    pre_task_status_stats = SerializerMethodField()
    post_task_status_stats = SerializerMethodField()
    steps = SerializerMethodField()

    class Meta:
        model = EmploymentReview
        fields = (
            'employee', 'change_type', 'effective_date', 'id', 'remarks',
            'pre_task_status_stats', 'post_task_status_stats', 'status',
            'steps',
        )

    @staticmethod
    def get_employment_review_sequence(instance) -> list:
        change_type = instance.change_type
        setting_to_step_map = {
            'affects_experience': EXPERIENCE_ADDED,
            'affects_payroll': PAYROLL_CHANGED,
            'affects_work_shift': WORKSHIFT_CHANGED,
            'affects_core_tasks': CORE_TASKS_UPDATED,
            'affects_leave_balance': LEAVE_UPDATED,
        }
        sequence = list(CHANGE_TYPE_SEQUENCE)
        for setting_flag, step in setting_to_step_map.items():
            if not getattr(change_type, setting_flag):
                sequence.remove(step)
        return sequence

    def get_steps(self, instance):
        selected_change_type_sequence = self.get_employment_review_sequence(instance)
        return EmployeeSeparationSerializer.get_steps_from_current_status(
            currently_at=instance.status,
            sequence=selected_change_type_sequence
        )

    @staticmethod
    def get_effective_date(instance):
        effective_date = nested_getattr(
            instance, 'detail.new_experience.start_date'
        )
        return effective_date

    def validate(self, attrs):
        employee = attrs.get('employee')
        change_type = attrs.get('change_type')
        if self.request and self.request.method == 'POST':
            validate_no_off_boarding_in_progress(employee)
        queryset = EmploymentReview.objects.filter(
            employee=employee
        ).exclude(
            status__in=[STOPPED, HRIS_COMPLETED]
        )
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.filter(change_type=change_type).exists():
            raise ValidationError(
                "The change type for this employee already exists."
            )
        # if queryset exists and is currently active, please raise.
        in_progress = queryset.exclude(
            detail__new_experience__upcoming=False
        ).first()
        if in_progress:
            raise ValidationError({
                'change_type':
                    f'Cannot create a change type, {in_progress.change_type} is '
                    f'pending.'
            })
        # do not allow editing once pre-task is set, or experience is set.
        is_set = getattr(self.instance, 'pre_task', None) or nested_getattr(
            self.instance, 'detail.experience'
        )
        if is_set:
            employee = get_patch_attr('employee', attrs, self) == self.instance.employee
            change_type = get_patch_attr('change_type', attrs, self) == self.instance.change_type
            errors = dict()
            if not employee:
                errors.update({
                    'employee': 'Cannot update once the tasks are set.'
                })
            if not change_type:
                errors.update({
                    'change_type': 'Cannot update once the tasks are set.'
                })
            if errors:
                raise ValidationError(errors)
        return super().validate(attrs)

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method in ['POST', 'PUT', 'PATCH']:
            fields['employee'] = serializers.PrimaryKeyRelatedField(
                queryset=USER.objects.filter(
                    detail__organization=self.context.get('organization')
                ),
            )
        else:
            fields['employee'] = UserThinSerializer(
                context=self.context,
                read_only=True
            )
            fields['change_type'] = ChangeTypeSerializer(
                context=self.context,
                read_only=True
            )
        return fields

    def create(self, validated_data):
        user = validated_data.get('employee')
        change_type = validated_data.get('change_type')
        detail_data = {}
        experience = user.user_experiences.order_by(
            '-start_date'
        ).first()
        if change_type.affects_experience:
            detail_data.update({
                'old_experience': experience
            })
        if change_type.affects_payroll:
            last_payroll_slot = experience.user_experience_packages.order_by(
                '-active_from_date'
            ).first()
            detail_data.update({
                'old_payroll': nested_getattr(
                    last_payroll_slot, 'package'
                )
            })
        if change_type.affects_work_shift:
            detail_data.update({
                'old_work_shift': nested_getattr(
                    user,
                    'attendance_setting.work_shift'
                ),
            })

        detail = EmployeeChangeTypeDetail.objects.create(
            change_type=change_type,
            **detail_data
        )
        validated_data.update({
            'detail': detail
        })
        return super().create(validated_data)

    def get_task_status(self, instance):
        return 'Change Type ' + super().get_task_status(instance)

    @staticmethod
    def calculate_proportionate_leave_balance(employment_review):
        user = employment_review.employee
        upcoming_experience = employment_review.detail.new_experience
        if employment_review.change_type.affects_leave_balance:
            LeaveChangeType.objects.filter(change_type=employment_review.detail).delete()
            last_experience = user.user_experiences.exclude(
                upcoming=True
            ).order_by(
                '-start_date'
            ).first()
            user_leave_accounts = user.leave_accounts.filter(
                is_archived=False,
                rule__leave_type__master_setting=get_active_master_setting(
                    organization=user.detail.organization
                )
            )
            leave_change_type = []
            for account in user_leave_accounts:
                balance_to_add = get_proportionate_leave_balance(
                    account, upcoming_experience.start_date, upcoming_experience.end_date,
                )
                if last_experience.end_date and last_experience.end_date > upcoming_experience.start_date:
                    # this value to be interpreted as penalty.
                    penalty = get_proportionate_leave_balance(
                        leave_account=account,
                        start_date=upcoming_experience.start_date,
                        end_date=last_experience.end_date
                    )
                    balance_to_add = max(balance_to_add - penalty, 0)
                change_type = LeaveChangeType(
                    balance=account.usable_balance,
                    update_balance=(
                        account.usable_balance + balance_to_add
                    ),
                    leave_type=account.rule.leave_type,
                    leave_account=account,
                    change_type=employment_review.detail
                )
                leave_change_type.append(change_type)
            LeaveChangeType.objects.bulk_create(leave_change_type)

    def update(self, instance, validated_data):
        ret = super().update(instance, validated_data)
        new_experience = nested_getattr(ret, 'detail.new_experience')
        if new_experience:
            if ret.status == STOPPED:
                # remove the new_experience
                package_slots = getattr(
                    new_experience, 'user_experience_packages', None
                )
                if package_slots:
                    # can cause Protected Error.
                    package_slots.all().delete()
                new_experience.delete()
        return ret


class LetterTemplateSerializer(AutoAddSlugMixin,
                               DynamicFieldsModelSerializer):
    message = serializers.CharField(
        max_length=EMAIL_TEMPLATE_MAX_LENGTH
    )
    status = serializers.ReadOnlyField(source='get_status_display')

    allowed_templates = {
        OFFER_LETTER: OFFER_LETTER_LETTER_PARAMS.keys(),
        CHANGE_TYPE: CHANGE_TYPE_LETTER_PARAMS.keys(),
        ONBOARDING: ONBOARDING_LETTER_PARAMS.keys(),
        OFFBOARDING: OFFBOARDING_LETTER_PARAMS.keys(),
        CUSTOM: CUSTOM_LETTER_PARAMS.keys()
    }

    class Meta:
        model = LetterTemplate
        fields = (
            'title', 'message', 'type', 'status'
        )

    def validate(self, attrs):
        template_type = attrs.get('type')
        message_content = attrs.get('message')
        allowed = self.allowed_templates.get(
            template_type
        )
        contents = set(re.compile(r'\{\{[_\w ]+\}\}').findall(message_content))
        extra = contents - set(allowed)
        if extra:
            raise ValidationError({
                'message': ','.join(extra) + (' is ' if len(
                    extra
                ) == 1 else ' are ') + 'not allowed.'
            })
        return attrs

    def validate_title(self, title):
        qs = self.Meta.model.objects.filter(
            organization=self.context.get('organization'),
            title__iexact=title
        )
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(
                f"The letter template with title `{title}` already exists for "
                f"this organization"
            )
        return title

    def create(self, validated_data):
        validated_data.update({
            'organization': self.context.get('organization')
        })
        return super().create(validated_data)

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method == 'GET':
            fields['type'] = SerializerMethodField()
        return fields

    def get_type(self, instance):
        return choice_field_display(instance, 'type')


class EmployeeSeparationTHinSerializer(serializers.ModelSerializer):
    employee = UserThumbnailSerializer()

    class Meta:
        model = EmployeeSeparation
        fields = ['id', 'employee']


class EmployeeSeparationSerializer(PrePostTaskMixin,
                                   AutoAddSlugMixin,
                                   DynamicFieldsModelSerializer):
    separation_type = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=EmployeeSeparationType.objects.all()
    )
    pre_task_status_stats = SerializerMethodField()
    post_task_status_stats = SerializerMethodField()
    exit_interview = SerializerMethodField()
    steps = SerializerMethodField()

    class Meta:
        model = EmployeeSeparation
        fields = (
            'employee', 'separation_type', 'parted_date', 'release_date',
            'remarks', 'pre_task', 'post_task', 'id', 'status', 'exit_interview',
            'effective_date', 'pre_task_status_stats', 'post_task_status_stats',
            'steps'
        )

    def get_steps(self, instance):
        selected_separation_sequence = self.get_separation_sequence(instance)
        return self.get_steps_from_current_status(
            currently_at=instance.status,
            sequence=selected_separation_sequence
        )

    @staticmethod
    def get_separation_sequence(instance) -> list:
        """
        Filters and returns applicable steps from the pool of separation_type checklists.
        :param instance: off boarding instance
        :return: applicable sequences.
        """
        separation_type = instance.separation_type
        setting_to_step_map = {
            'display_leave': LEAVE_REVIEWED,
            'display_payroll': PAYROLL_REVIEWED,
            'display_attendance_details': ATTENDANCE_REVIEWED,
            'display_pending_tasks': PENDING_TASKS_REVIEWED,
        }
        selected_separation_sequence = list(OFFBOARDING_SEQUENCE)
        for setting_flag, step in setting_to_step_map.items():
            if not getattr(separation_type, setting_flag):
                selected_separation_sequence.remove(step)
        return selected_separation_sequence

    @staticmethod
    def get_steps_from_current_status(currently_at, sequence):
        default_pending = currently_at if currently_at in (HOLD, STOPPED,) else PENDING
        blocked = default_pending != PENDING

        if currently_at == ACTIVE:
            current_status = -1
        elif currently_at in sequence:
            current_status = sequence.index(currently_at)
        else:
            current_status = len(sequence)

        done_text = default_pending if blocked else HRIS_COMPLETED
        todo_text = default_pending if blocked else IN_PROGRESS

        def get_status(index, current_index):
            if current_index == -1:
                return PENDING
            if index <= current_index:
                return done_text
            if index > (current_index + 1):
                return default_pending
            return todo_text
        return [
            {
                'slug': step,
                'status': get_status(ind, current_status)
            } for ind, step in enumerate(sequence)
        ]

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method == 'GET':
            fields['employee'] = add_fields_to_serializer_class(
                UserThickSerializer,
                {
                    'is_active': serializers.ReadOnlyField(),
                    'username': serializers.ReadOnlyField(),
                }
            )(context=self.context)
            fields['separation_type'] = EmployeeSeparationTypeSerializer()
            view = self.context.get('view')
            if getattr(view, 'action') == 'retrieve':
                # reporting fields: Leave consumption, Pending Tasks, Attendance
                # Payroll details
                disp = list()
                if self.instance:
                    separation_type = self.instance.separation_type
                    if separation_type.display_leave:
                        disp.append('leave_details')
                    if separation_type.display_attendance_details:
                        disp.append('attendance_details')
                    if separation_type.display_payroll:
                        disp.append('payroll_details')
                fields.update(
                    **{
                        f: SerializerMethodField() for f in disp
                    }
                )
        else:
            fields['employee'] = serializers.PrimaryKeyRelatedField(
                queryset=USER.objects.filter(
                    detail__organization=self.context.get('organization'),
                )
            )
        return fields

    @staticmethod
    def get_leave_details(instance):
        return list()

    @staticmethod
    def get_attendance_details(instance):
        user = instance.employee
        this_year = timezone.now().year
        last_month_year = (timezone.now() - relativedelta(months=1)).year
        this_month = timezone.now().month
        past_month = (timezone.now() - relativedelta(months=1)).month
        qs = user.timesheets.filter(
            timesheet_for__lte=get_today()
        ).aggregate(
            wd_this_month=Count(
                'timesheet_for',
                filter=Q(
                    coefficient=WORKDAY,
                    timesheet_for__month=this_month,
                    timesheet_for__year=this_year
                ),
                distinct=True
            ),
            present_this_month=Count(
                'timesheet_for',
                filter=Q(is_present=True,
                         timesheet_for__month=this_month,
                         timesheet_for__year=this_year),
                distinct=True
            ),
            absent_this_month=Count(
                'timesheet_for',
                filter=Q(is_present=False,
                         coefficient=WORKDAY,
                         timesheet_for__month=this_month,
                         timesheet_for__year=this_year),
                distinct=True
            ),
            wd_past_month=Count(
                'timesheet_for',
                filter=Q(
                    coefficient=WORKDAY,
                    timesheet_for__month=past_month,
                    timesheet_for__year=last_month_year
                ),
                distinct=True
            ),
            present_past_month=Count(
                'timesheet_for',
                filter=Q(is_present=True,
                         timesheet_for__month=past_month,
                         timesheet_for__year=last_month_year),
                distinct=True
            ),
            absent_past_month=Count(
                'timesheet_for',
                filter=Q(is_present=False,
                         coefficient=WORKDAY,
                         timesheet_for__month=past_month,
                         timesheet_for__year=last_month_year),
                distinct=True
            ),
        )
        this_month_name = timezone.now().strftime('%b')
        last_month_name = (
            timezone.now()
            - relativedelta(months=1)
        ).strftime('%b')
        return [
            {
                'month': this_month_name,
                'working_days': qs.get('wd_this_month'),
                'present': qs.get('present_this_month'),
                'absent': qs.get('absent_this_month'),
            },
            {
                'month': last_month_name,
                'working_days': qs.get('wd_past_month'),
                'present': qs.get('present_past_month'),
                'absent': qs.get('absent_past_month'),
            }
        ]

    @staticmethod
    def get_payroll_details(instance):
        """
        {
            'Basic Salary': 30000.0,
            'Overtime Rate': 1000.0,
            'Basic Remuneration': 9677.42,
            'Overtime': 0.0,
            'Total Salary': 9677.42,
            'TDS': 2783.3
        }
        """
        from irhrs.payroll.models import ReportRowRecord
        return ReportRowRecord.get_current_fiscal_year_payroll_stat(
            instance.employee, get_today()
        )

    @staticmethod
    def get_exit_interview(instance):
        return hasattr(instance, 'exit_interview')

    def validate(self, attrs):
        employee = attrs.get('employee')
        status = attrs.get('status')
        if self.request and self.request.method == 'POST':
            validate_no_employment_review_in_progress(employee)
        qs = EmployeeSeparation.objects.exclude(
            status=STOPPED
        ).filter(
            employee=employee
        )
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(
                "Off Boarding for this user is in progress."
            )
        parted_date = get_patch_attr(
            'parted_date',
            attrs,
            self
        )
        release_date = get_patch_attr(
            'release_date',
            attrs,
            self
        )

        effective_date = get_patch_attr(
            'effective_date',
            attrs,
            self
        )

        separation_type = get_patch_attr(
            'separation_type',
            attrs,
            self
        )

        if status == HRIS_COMPLETED and not release_date:
            raise ValidationError({
                'non_field_error': ['Last working date need to be added.']
            })

        if employee and release_date:
            get_last_payroll_generated_date, payroll_installed = get_dependency(
                'irhrs.payroll.utils.helpers.get_last_payroll_generated_date'
            )
            paid_upto = get_last_payroll_generated_date(employee)
            if paid_upto and release_date < paid_upto:
                raise ValidationError({
                    'release_date': [f"Last working date {release_date} must be greater than last paid date {paid_upto}."]
                })

        is_terminated = separation_type and separation_type.category == TERMINATED
        if is_terminated:
            if effective_date:
                raise ValidationError({
                    'effective_date': ['Effective date is not required for separation type of'
                                       ' category \'terminated\'']
                })
            if parted_date:
                raise ValidationError({
                    'parted_date': ['Resigned date is not required for separation type of'
                                    ' category \'terminated\'']
                })

        if effective_date and parted_date:
            if effective_date < parted_date:
                raise ValidationError({
                    'effective_date': ['Approved date must be greater than Resigned Date']
                })

        is_not_terminated = separation_type and separation_type.category != TERMINATED
        errors = dict()
        if is_not_terminated:
            if not effective_date:
                errors.update({
                    'effective_date': ['This field may not be null.'],
                })
            if not parted_date:
                errors.update({
                    'parted_date': ['This field may not be null.']
                })

        if errors:
            raise ValidationError(errors)

        if release_date and effective_date and (release_date < effective_date):
            raise ValidationError({
                'release_date': ["Last working date must be greater than Approved date."]
            })

        return super().validate(attrs)

    def validate_post_task(self, post_task):
        super().validate_post_task(post_task)
        post_task_step = OFFBOARDING_SEQUENCE.index(PAYROLL_REVIEWED)
        if self.instance.status not in OFFBOARDING_SEQUENCE:
            return self.instance.post_task
        current_step = OFFBOARDING_SEQUENCE.index(self.instance.status)
        if post_task and current_step < post_task_step:
            raise ValidationError(
                "Setting Post Task is disallowed before payroll is reviewed."
            )
        return post_task

    def update(self, instance, validated_data):
        current_experience = instance.employee.current_experience
        if not current_experience:
            current_experience = instance.employee.user_experiences.first()

        if validated_data.get('status') == HRIS_COMPLETED and current_experience:
            current_experience.end_date = get_patch_attr(
                'release_date',
                validated_data,
                self
            )
            current_experience.save()
        return super().update(instance, validated_data)

    def validate_status(self, status):
        if not self.instance:
            return status
        if status not in self.get_separation_sequence(self.instance) + [
            ACTIVE, HRIS_COMPLETED, HOLD, STOPPED
        ]:
            raise ValidationError(
                _("The step %s is not allowed." % status)
            )
        return status


class LeaveBalanceField(serializers.ReadOnlyField):

    def __init__(self, **kwargs):
        self.source_field_name = kwargs.get('source')
        kwargs['source'] = '*'
        super().__init__(**kwargs)

    def to_representation(self, instance):
        source = self.source_field_name or self.field_name
        value = nested_getattr(instance, source)
        if value is not None:
            if instance.rule.leave_type.category in HOURLY_LEAVE_CATEGORIES:
                return humanize_interval(value * 60)
            return round(value) if settings.ROUND_LEAVE_BALANCE else round(value, 2)
        return None


class LeaveReportSerializer(serializers.Serializer):
    id = serializers.ReadOnlyField()
    leave_type = LeaveTypeSerializer(
        source='rule.leave_type',
        fields=['id', 'name', 'category']
    )
    balance = LeaveBalanceField(source='usable_balance')
    renew_balance = LeaveBalanceField()
    proportionate = LeaveBalanceField()
    carry_forward = LeaveBalanceField()
    used_balance = LeaveBalanceField()
    encashed_balance = serializers.SerializerMethodField()
    edited = serializers.SerializerMethodField()

    @staticmethod
    def get_encashed_balance(instance, pretty=True):
        if instance.edited_encashment is not None:
            value = instance.edited_encashment
        elif hasattr(instance.rule, 'renewal_rule') and not hasattr(instance.rule, 'accumulation_rule'):
            value = instance.carry_forward + instance.proportionate - instance.used_balance
        else:
            value = instance.usable_balance

        if pretty and instance.rule.leave_type.category in HOURLY_LEAVE_CATEGORIES:
            return humanize_interval(value * 60)
        return round(value) if settings.ROUND_LEAVE_BALANCE else round(value, 2)

    @staticmethod
    def get_edited(instance):
        return bool(instance.edited_encashment)


class EmployeeSeparationLeaveEncashmentEditSerializer(serializers.Serializer):
    encashed_balance = serializers.FloatField(write_only=True)
    remarks = serializers.CharField(max_length=255, write_only=True)
    message = serializers.ReadOnlyField()

    def create(self, validated_data):
        # shound not be called create with this serializer
        raise NotImplementedError

    def update(self, instance, validated_data):
        separation = self.context.get('view').get_separation()
        user = self.context.get('request').user
        encashment = instance.encashment_edits_on_separation.filter(separation=separation).first()
        if encashment:
            old_balance = encashment.encashment_balance
        else:
            encashment = LeaveEncashmentOnSeparation(
                separation=separation,
                leave_account=instance
            )
            old_balance = LeaveReportSerializer.get_encashed_balance(instance, pretty=False)

        encashment.encashment_balance = validated_data.get('encashed_balance')

        history = LeaveEncashmentOnSeparationChangeHistory(
            actor=user,
            previous_balance=old_balance,
            new_balance=validated_data.get('encashed_balance'),
            remarks=validated_data.get('remarks')
        )

        with transaction.atomic():
            encashment.save()

            # set relation after save
            history.encashment = encashment
            history.save()

        instance.message = "Successfully updated encashed balance."
        return instance


class EmployeeSeparationLeaveEncashmentEditHistorySerializer(DynamicFieldsModelSerializer):
    actor = UserThumbnailSerializer()
    message = serializers.ReadOnlyField(source="__str__")
    previous_balance = serializers.ReadOnlyField(source='previous_balance_display')
    new_balance = serializers.ReadOnlyField(source='new_balance_display')

    class Meta:
        model = LeaveEncashmentOnSeparationChangeHistory
        fields = (
            "id",
            "actor",
            "previous_balance",
            "new_balance",
            "remarks",
            "message"
        )


class EmployeeSeparationTypeSerializer(AutoAddSlugMixin,
                                       DynamicFieldsModelSerializer):
    is_assigned = serializers.ReadOnlyField()

    class Meta:
        model = EmployeeSeparationType
        fields = (
            'title', 'slug', 'display_leave', 'display_payroll',
            'display_attendance_details', 'display_pending_tasks',
            'is_assigned', 'badge_visibility', 'category'
        )
        read_only_fields = (
            'slug',
        )

    def validate(self, attrs):
        attrs.update({
            'organization': self.context.get('organization')
        })
        return super().validate(attrs)

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method == 'GET':
            fields['badge_visibility'] = SerializerMethodField()
            fields['category'] = SerializerMethodField()
        return fields

    @staticmethod
    def get_badge_visibility(instance):
        return choice_field_display(instance, 'badge_visibility')

    @staticmethod
    def get_category(instance):
        return choice_field_display(instance, 'category')


class LeaveChangeTypeSerializer(AutoAddSlugMixin,
                                DynamicFieldsModelSerializer):
    leave_type = serializers.ReadOnlyField(source='leave_type.name')

    class Meta:
        model = LeaveChangeType
        fields = (
            'leave_type', 'balance', 'update_balance', 'id', 'leave_account'
        )
        read_only_fields = (
            'balance', 'leave_type', 'id'
        )


class LeaveChangeTypeBulkSerializer(LeaveChangeTypeSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=LeaveChangeType.objects.all()
    )

    class Meta(LeaveChangeTypeSerializer.Meta):
        fields = LeaveChangeTypeSerializer.Meta.fields + ('id',)

    def create(self, data):
        instance = data.get('id')  # the leave change type object
        instance.update_balance = data.get('update_balance')  # set directly
        instance.save(update_fields=['update_balance'])
        return instance


class GeneratedLetterSerializer(AutoAddSlugMixin,
                                DynamicFieldsModelSerializer):
    title = serializers.ReadOnlyField(source='letter_template.title')
    is_sent = serializers.SerializerMethodField()
    is_downloaded = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    employee_detail = serializers.SerializerMethodField()

    class Meta:
        model = GeneratedLetter
        fields = (
            'employee_detail', 'email', 'uri', 'message', 'status', 'id', 'remarks', 'title',
            'is_sent', 'is_downloaded', 'is_saved',
        )

    @staticmethod
    def get_employee_detail(letter):
        employee = None
        if letter.employee:
            employee = letter.employee
        if letter.pre_employment:
            employee = letter.pre_employment.employee
        if letter.employment_review:
            employee = letter.employment_review.employee
        if letter.separation:
            employee = letter.separation.employee
        if employee:
            return UserThinSerializer(instance=employee).data
        else:
            return None

    @staticmethod
    def get_is_sent(instance):
        if hasattr(instance, 'is_sent'):
            return instance.is_sent
        return instance.history.filter(
            status=SENT
        ).exists()

    @staticmethod
    def get_is_downloaded(instance):
        if hasattr(instance, 'is_downloaded'):
            return instance.is_downloaded
        return instance.history.filter(
            status=DOWNLOADED
        ).exists()

    @staticmethod
    def get_is_saved(instance):
        if hasattr(instance, 'is_saved'):
            return instance.is_saved
        return instance.history.filter(
            status=SAVED
        ).exists()


class PreEmploymentSerializer(PrePostTaskMixin, AutoAddSlugMixin,
                              DynamicFieldsModelSerializer):
    employment_level = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=EmploymentLevel.objects.all()
    )
    employment_status = serializers.SlugRelatedField(
        slug_field='slug',
        required=False,
        allow_null=True,
        queryset=EmploymentStatus.objects.all()
    )
    job_title = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=EmploymentJobTitle.objects.all()
    )
    division = serializers.SlugRelatedField(
        slug_field='slug',
        required=False,
        allow_null=True,
        queryset=OrganizationDivision.objects.all()
    )
    branch = serializers.SlugRelatedField(
        slug_field='slug',
        required=False,
        allow_null=True,
        queryset=OrganizationBranch.objects.all()
    )
    generated_letter = GeneratedLetterSerializer(
        fields=['status', 'remarks', 'id', 'is_downloaded', 'is_saved',
                'is_sent'],
        read_only=True
    )
    template_letter = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=LetterTemplate.objects.filter(
            type=OFFER_LETTER
        ),
        required=False
    )
    task_status = serializers.SerializerMethodField(read_only=True)
    profile_pic = serializers.SerializerMethodField(read_only=True)
    pre_task_status_stats = SerializerMethodField()
    post_task_status_stats = SerializerMethodField()
    steps = SerializerMethodField()

    class Meta:
        model = PreEmployment
        fields = (
            'full_name', 'address', 'gender', 'deadline', 'date_of_join',
            'email', 'employment_level', 'contract_period', 'template_letter',
            'employment_status', 'job_title', 'division', 'branch',
            'payroll', 'generated_letter', 'id', 'status', 'pre_task',
            'post_task', 'employee', 'step', 'profile_pic', 'task_status',
            'job_description', 'job_specification', 'marital_status',
            'post_task_status_stats', 'pre_task_status_stats', 'steps'
        )

    @staticmethod
    def get_steps(instance):
        return EmployeeSeparationSerializer.get_steps_from_current_status(
            currently_at=instance.status,
            sequence=ONBOARDING_SEQUENCE
        )

    def get_profile_pic(self, instance):
        url = {
            MALE: 'images/default/male.png',
            FEMALE: 'images/default/female.png',
            OTHER: 'images/default/other.png'
        }.get(instance.gender)
        return get_complete_url(
            url=url,
            att_type='static'
        )

    def get_fields(self):
        fields = super().get_fields()
        if self.request:
            if self.request.method == 'GET':
                fields['employee'] = UserThinSerializer(context=self.context)
                fields['employment_level'] = EmploymentLevelSerializer(
                    fields=['title', 'slug']
                )
                fields['employment_status'] = EmploymentStatusSerializer()
                fields['job_title'] = EmploymentJobTitleSerializer()
                fields['division'] = OrganizationDivisionSerializer()
                fields['branch'] = OrganizationBranchSerializer()
                fields['status'] = SerializerMethodField()
            elif self.request.method == 'POST':
                fields.pop('pre_task', None)
                fields.pop('status', None)
                fields.pop('post_task', None)
                fields.pop('employee', None)
            else:
                fields['employee'] = serializers.PrimaryKeyRelatedField(
                    queryset=USER.objects.filter(
                        detail__organization=self.context.get('organization')
                    ),
                    required=False,
                    allow_null=True
                )
                fields['employment_level'] = serializers.SlugRelatedField(
                    slug_field='slug',
                    queryset=EmploymentLevel.objects.filter(
                        organization=self.context.get('organization')
                    )
                )
                fields['employment_status'] = serializers.SlugRelatedField(
                    slug_field='slug',
                    queryset=EmploymentStatus.objects.filter(
                        organization=self.context.get('organization')
                    )
                )
                fields['job_title'] = serializers.SlugRelatedField(
                    slug_field='slug',
                    queryset=EmploymentJobTitle.objects.filter(
                        organization=self.context.get('organization')
                    )
                )
                fields['division'] = serializers.SlugRelatedField(
                    slug_field='slug',
                    queryset=OrganizationDivision.objects.filter(
                        organization=self.context.get('organization')
                    )
                )
                fields['branch'] = serializers.SlugRelatedField(
                    slug_field='slug',
                    required=False,
                    allow_null=True,
                    queryset=OrganizationBranch.objects.filter(
                        organization=self.context.get('organization')
                    )
                )
                fields['template_letter'] = serializers.SlugRelatedField(
                    slug_field='slug',
                    queryset=LetterTemplate.objects.filter(
                        type=OFFER_LETTER
                    ),
                    required=False
                )
        return fields

    def create(self, validated_data):
        validated_data.update({
            'organization': self.context.get('organization')
        })
        return super().create(validated_data)

    def get_task_status(self, instance):
        _OB = 'On Boarding '
        letter = instance.generated_letter
        if not letter:
            return LETTER_NOT_GENERATED
        if letter.status == ACCEPTED:
            if instance:
                if instance.pre_task:
                    if instance.employee:
                        if instance.post_task and instance.post_task_status \
                            == 'Completed':
                            return _OB + 'Completed'
                    return _OB + ' Started'
        return letter.get_status_display()

    def validate(self, attrs):
        deadline = attrs.get('deadline')
        doj = attrs.get('date_of_join')
        contract_date = attrs.get('contract_period')
        pre_task = attrs.get('pre_task')
        post_task = attrs.get('post_task')
        employment_status = attrs.get('employment_status')
        if employment_status:
            if not attrs.get('employment_status').is_contract and contract_date:
                raise ValidationError(
                    "Can not set contract date if employment status is not "
                    "contract"
                )
            elif employment_status.is_contract and not contract_date:
                raise ValidationError(
                    "Contract Period required for employment with Contract "
                    "status."
                )
        if pre_task and post_task and pre_task == post_task:
            raise ValidationError(
                "The pre and post task must be different"
            )
        if doj and deadline and doj < deadline.date():
            raise ValidationError(
                'The date of join must be greater than deadline.'
            )
        if contract_date and doj and contract_date < doj:
            raise ValidationError(
                'The contract expiring must be greater than date of join.'
            )
        if self.instance:
            if attrs.get('post_task') and not self.instance.employee:
                raise ValidationError(
                    "Please add user before selecting post task."
                )
        return super().validate(attrs)

    def validate_address(self, address=''):
        if address:
            if not re.fullmatch(pattern='[\w \-\d,]+', string=address):
                raise ValidationError(
                    "The address can only contain words, hyphens and spaces."
                )
        return address

    def validate_contract_period(self, period):
        return validate_future_date(period)

    def validate_status(self, status):
        if not self.instance:
            return status
        if status == COMPLETED:
            if not self.instance.employee:
                raise ValidationError({
                    'status': 'Employee must be added before marking on '
                              'boarding complete.'
                })
        return status

    def get_status(self, instance):
        generated_letter = instance.generated_letter
        if instance.status == ACTIVE:
            if generated_letter:
                return generated_letter.status
        return instance.status

    def update(self, instance, validated_data):
        current_template_letter = validated_data.get('template_letter')
        if current_template_letter and current_template_letter != \
            instance.template_letter:
            validated_data.update({
                'generated_letter': None
            })
        return super().update(instance, validated_data)

    def validate_template_letter(self, template_letter):
        if not self.instance:
            return template_letter
        old_template = self.instance.template_letter
        if old_template and template_letter and old_template != template_letter:
            generated_letter = self.instance.generated_letter
            if generated_letter and generated_letter.status in [ACCEPTED, DECLINED]:
                raise ValidationError(
                    f'The {generated_letter.get_status_display()} letter '
                    f'cannot be updated.'
                )
        return template_letter


class ChangeTypeSerializer(AutoAddSlugMixin, DynamicFieldsModelSerializer):
    is_assigned = serializers.ReadOnlyField()

    class Meta:
        model = ChangeType
        fields = (
            'title', 'affects_experience', 'affects_payroll',
            'affects_work_shift', 'affects_core_tasks',
            'affects_leave_balance', 'slug', 'is_assigned',
            'badge_visibility'
        )
        read_only_fields = (
            'slug',
        )

    def validate(self, attrs):
        attrs.update({
            'organization': self.context.get('organization')
        })
        return super().validate(attrs)

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method == 'GET':
            fields['badge_visibility'] = SerializerMethodField()
        return fields

    @staticmethod
    def get_badge_visibility(instance):
        return choice_field_display(instance, 'badge_visibility')


class OfferLetterSerializer(DynamicFieldsModelSerializer):
    deadline = serializers.ReadOnlyField(source='pre_employment.deadline')
    pre_employment = SerializerMethodField()
    org_name = serializers.ReadOnlyField(
        source='preemployment.organization.name'
    )
    org_logo = serializers.SerializerMethodField()
    message = SerializerMethodField()

    class Meta:
        model = GeneratedLetter
        fields = (
            'email', 'message', 'status', 'remarks', 'deadline',
            'pre_employment', 'org_name', 'org_logo'
        )
        read_only_fields = (
            'email', 'message'
        )
        extra_kwargs = {
            'remarks': {
                'required': False
            }
        }

    def get_org_logo(self, instance):
        url = nested_getattr(
            instance,
            'preemployment.organization.appearance.logo.url'
        )
        if url:
            return settings.BACKEND_URL + url
        else:
            return get_complete_url('images/default/cover.png',
                                    att_type='static')

    def validate(self, attrs):
        status = attrs.get('status')
        remarks = attrs.get('remarks')
        if status == DECLINED and not remarks:
            raise ValidationError({
                'remarks': 'Please add remarks stating your reasons.'
            })
        return attrs

    def validate_status(self, status):
        if status in [ACCEPTED, DECLINED]:
            return status
        raise ValidationError(
            "You should `Accept` or `Decline` the offer."
        )

    @staticmethod
    def get_pre_employment(instance):
        ret = PreEmploymentSerializer(
            instance.preemployment,
            fields=[
                'full_name', 'address', 'gender', 'deadline', 'date_of_join',
                'email', 'employment_level', 'contract_period',
                'template_letter', 'employment_status', 'job_title',
                'division', 'branch', 'payroll', 'employee', 'step',
                'profile_pic',
            ]).data
        ret['payroll'] = calculate_payroll(
            instance.preemployment
        )
        return ret

    def save(self, **kwargs):
        instance = super().save(**kwargs)
        pre_employment = instance.preemployment
        text = f"{pre_employment.full_name} has " \
               f"{instance.get_status_display().lower()} the job offer."
        url = f"/admin/{pre_employment.organization.slug}/hris/employees/" \
              f"pre-employment/employee-details?id={pre_employment.id}"
        notify_organization(
            text=text,
            action=instance.preemployment,
            organization=pre_employment.organization,
            url=url,
            permissions=[
                HRIS_PERMISSION,
                HRIS_ON_BOARDING_PERMISSION
            ]
        )
        return instance

    def get_message(self, instance):
        msg = instance.message
        remove_link = self.context.get('remove_link', False)
        if remove_link:
            msg = re.sub(
                '<div id="notification_url">(.|\n)*?</div>', '',
                msg
            )
        return msg


class TaskTemplateMappingSerializer(AutoAddSlugMixin,
                                    DynamicFieldsModelSerializer):
    template_files = serializers.PrimaryKeyRelatedField(
        queryset=TaskFromTemplateAttachment.objects.all(),
        many=True,
        write_only=True
    )

    class Meta:
        model = TaskTemplateMapping
        fields = (
            'template_detail', 'task', 'id', 'template_files'
        )

    def create(self, validated_data):
        return DummyObject(**validated_data)

    def update(self, instance, validated_data):
        attachments = validated_data.pop('template_files', [])
        if instance.task:
            return instance
        task_serializer = TaskSerializer(
            exclude_fields=[
                'recurring', 'project', 'parent'
            ],
            context=self.context,
            data=self.initial_data.get('task'),
        )
        task_serializer.is_valid(raise_exception=True)
        created_task = task_serializer.save()
        validated_data.update({
            'task': created_task
        })

        if attachments:
            task_attachment = []
            for temp_attachment in attachments:
                task_attachment.append(
                    TaskAttachment(
                        attachment=temp_attachment.attachment,
                        caption=temp_attachment.caption,
                        task=created_task
                    )
                )
            if task_attachment:
                TaskAttachment.objects.bulk_create(task_attachment)
        return super().update(instance, validated_data)

    def get_fields(self):
        fields = super().get_fields()
        context = self.context
        context['from_template'] = True

        fields['task'] = TaskSerializer(
            exclude_fields=[
                'recurring', 'project', 'parent'
            ],
            allow_null=True,
            context=context
        )
        fields['template_detail'] = TaskFromTemplateSerializer(
            fields=[
                'id', 'title', 'description', 'observers', 'priority', 'deadline',
                'include_employee',
                'deadline_date', 'changeable_deadline', 'checklists', 'responsible_persons'
            ],
            read_only=True,
            context=context
        )
        return fields


class TaskTrackingSerializer(AutoAddSlugMixin, DynamicFieldsModelSerializer):
    total_tasks = serializers.ReadOnlyField(allow_null=True)
    total_completed = serializers.ReadOnlyField(allow_null=True)
    task_template = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=TaskTemplateTitle.objects.all()
    )

    class Meta:
        model = TaskTracking
        fields = (
            'pre_employment', 'change_type', 'separation',
            'id', 'total_tasks', 'total_completed', 'task_template',
        )
        extra_kwargs = {
            'pre_employment': {
                'required': False,
                'allow_null': True
            },
            'change_type': {
                'required': False,
                'allow_null': True
            },
            'separation': {
                'required': False,
                'allow_null': True
            },
        }

    def validate(self, attrs):
        pre_employment = 1 if attrs.get('pre_employment', None) else 0
        change_type = 1 if attrs.get('change_type', None) else 0
        separation = 1 if attrs.get('separation', None) else 0

        if pre_employment + change_type + separation == 1:
            return attrs
        raise ValidationError(
            "Only one of 'pre_employment', 'change_type', 'separation' "
            "should be selected."
        )

    @transaction.atomic()
    def create(self, validated_data):
        instance = super().create(validated_data)
        create_task_from_templates(instance)
        return instance

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method == 'GET':
            fields['pre_employment'] = PreEmploymentSerializer(allow_null=True)
            fields['change_type'] = ChangeTypeSerializer(allow_null=True)
            fields['separation'] = EmployeeSeparationSerializer(allow_null=True)
            fields['task_template'] = TaskTemplateTitleSerializer()
        return fields


class GenerateLetterSerializer(AutoAddSlugMixin,
                               DynamicFieldsModelSerializer):
    letter_template = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=LetterTemplate.objects.all(),
        write_only=True
    )
    status = serializers.ReadOnlyField(source='get_status_display')
    title = serializers.ReadOnlyField(source='letter_template.title')
    is_sent = serializers.ReadOnlyField()
    is_downloaded = serializers.ReadOnlyField()
    is_saved = serializers.ReadOnlyField()

    class Meta:
        model = GeneratedLetter
        fields = (
            'employee', 'letter_template', 'message', 'id', 'status', 'title',
            'is_sent', 'is_downloaded', 'is_saved',
        )
        extra_kwargs = {
            'message': {
                'read_only': True
            },
        }

    def validate(self, attrs):
        pre_employment = self.context.get('pre_employment', None)
        employment_review = self.context.get('employment_review', None)
        separation = self.context.get('separation', None)
        employee = attrs.get('employee', None)
        letter_template = attrs.get('letter_template', None)
        if bool(pre_employment) + bool(employment_review) + bool(separation) \
            != 1:
            raise ValidationError(
                "Only one of 'pre_employment', 'employment_review', "
                "'separation' should be selected."
            )
        qs = GeneratedLetter.objects.filter(
            pre_employment=pre_employment,
            employment_review=employment_review,
            separation=separation,
            employee=employee,
            letter_template=letter_template
        )
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(
                'The letter for current selection already exists.'
            )
        return attrs

    def get_fields(self):
        fields = super().get_fields()
        filter_type = self.context.get('letter_type')
        fields['letter_template'] = serializers.SlugRelatedField(
            slug_field='slug',
            queryset=LetterTemplate.objects.filter(
                type=filter_type,
                organization=self.context.get('organization')
            ),
            write_only=True
        )
        return fields

    @transaction.atomic()
    def create(self, validated_data):
        template = validated_data.get('letter_template')
        pre_employment = self.context.get('pre_employment')
        employment_review = self.context.get('employment_review')
        separation = self.context.get('separation')

        if pre_employment:
            email = pre_employment.employee.email if pre_employment.employee \
                else pre_employment.email
        elif employment_review:
            email = employment_review.employee.email
        elif separation:
            email = separation.employee.email
        else:
            email = ''
        message = create_letter_from_template(
            template,
            self.context
        )
        validated_data.update({
            'message': message,
            'email': email,
            'pre_employment': pre_employment,
            'employment_review': employment_review,
            'separation': separation,
        })
        return super().create(validated_data)

    def update(self, instance, attrs):
        return instance


class EmployeeChangeTypeDetailSerializer(AutoAddSlugMixin,
                                         DynamicFieldsModelSerializer):
    class Meta:
        model = EmployeeChangeTypeDetail
        fields = (
            'change_type',
            'old_experience',
            'new_experience',
            'old_work_shift',
            'new_work_shift',
            'old_payroll',
            'new_payroll',
        )
        read_only_fields = (
            'change_type',
            'old_experience',
            'old_work_shift',
            'old_payroll',
            'old_core_tasks',
        )

    def get_fields(self):
        ctx = self.context
        fields = super().get_fields()
        if self.request.method == 'GET':
            fields['change_type'] = ChangeTypeSerializer(context=self.context)
            fields['old_work_shift'] = WorkShiftSerializer(
                context=ctx
            )
            fields['old_experience'] = UserExperienceSerializer(
                exclude_fields=['skill', 'steps_history', 'user'],
                context=ctx
            )
            fields['new_experience'] = UserExperienceSerializer(
                exclude_fields=['skill', 'steps_history', 'user'],
                context=ctx
            )
            fields['old_core_tasks'] = UserResultAreaSerializer(
                # exclude_fields=['user'],
                read_only=True,
                context=self.context,
                source='old_experience.user_result_areas',
                many=True
            )
            fields['new_core_tasks'] = UserResultAreaSerializer(
                # exclude_fields=['user'],
                read_only=True,
                context=self.context,
                source='new_experience.user_result_areas',
                many=True,
            )
            fields['old_work_shift'] = WorkShiftSerializer(
                context=self.context
            )
            fields['new_work_shift'] = WorkShiftSerializer(
                context=self.context
            )
            fields['old_payroll'] = MinimalPackageDetailSerializer(
                context=self.context
            )
            fields['new_payroll'] = MinimalPackageDetailSerializer(
                context=self.context
            )
            fields['active_from_date'] = serializers.SerializerMethodField()
        else:
            fields['new_experience'] = UserUpcomingExperienceSerializer(
                exclude_fields=['skill'],
                allow_null=True,
                required=False,
                context=ctx
            )
        return fields

    def get_active_from_date(self, obj):
        if obj.new_experience:
            return obj.new_experience.start_date

    def update(self, instance, validated_data):
        ctx = self.context
        ctx.update({
            'check_current': False,
            'user': self.instance.old_experience.user
        })
        new_exp = None
        if 'new_experience' in validated_data:
            validated_data.pop('new_experience', {})
            new_experience = self.initial_data.get('new_experience', {})
            ser = UserUpcomingExperienceSerializer(
                instance=self.instance.new_experience,
                exclude_fields=['skill'],
                data=new_experience,
                context=ctx
            )
            ser.is_valid(raise_exception=True)
            new_exp = ser.save()
            validated_data.update({
                'new_experience': new_exp
            })
        ret = super().update(instance, validated_data)
        if new_exp:
            EmploymentReviewSerializer.calculate_proportionate_leave_balance(instance.review)
        return ret

    def validate(self, attrs):
        new_experience = get_patch_attr(
            'new_experience',
            attrs,
            self
        )
        if not new_experience:
            raise ValidationError(
                "Please assign new experience before updating other details."
            )
        return super().validate(attrs)


class TaskReportSerializer(serializers.Serializer):
    completed_tasks = serializers.ReadOnlyField(allow_null=True)
    total_tasks = serializers.ReadOnlyField(allow_null=True)
    pending_tasks = serializers.ReadOnlyField(allow_null=True)
    percentage = serializers.ReadOnlyField(allow_null=True)

    def get_fields(self):
        fields = super().get_fields()

        fields['pre_employment'] = SerializerMethodField()
        fields['employment_review'] = SerializerMethodField()
        fields['separation'] = SerializerMethodField()
        report_type = self.context.get('report_type')
        distinct = ['pre_employment', 'employment_review', 'separation']
        # this is the list of items to pop. Exclude the current report type.
        # Hence, provide highly dynamic fields architecture.
        try:
            distinct.remove(report_type)
        except ValueError:
            pass
        [fields.pop(f) for f in distinct]
        return fields

    def get_pre_employment(self, instance):
        return PreEmploymentSerializer(
            instance,
            context=self.context,
        ).data

    def get_employment_review(self, instance):
        return EmploymentReviewSerializer(
            instance,
            context=self.context
        ).data

    def get_separation(self, instance):
        return EmployeeSeparationSerializer(
            instance,
            context=self.context
        ).data


class TaskTemplateTitleDownloadSerializer(DynamicFieldsModelSerializer):
    templates = TaskFromTemplateSerializer(
        many=True,
    )

    class Meta:
        model = TaskTemplateTitle
        fields = (
            'name', 'templates'
        )


class EmployeeSeparationEditSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = EmployeeSeparation
        fields = 'release_date',

    def validate_release_date(self, release_date):
        get_last_payroll_generated_date, payroll_installed = get_dependency(
            'irhrs.payroll.utils.helpers.get_last_payroll_generated_date'
        )
        paid_upto = get_last_payroll_generated_date(self.instance.employee)
        if paid_upto and release_date and release_date < paid_upto:
            raise ValidationError(
                f"Last working date {release_date} must be greater than last paid date {paid_upto}."
            )

        if nested_getattr(self.instance, 'separation_type.category') != TERMINATED:
            effective_date = getattr(
                self.instance,
                'effective_date',
            )
            if effective_date and release_date and (release_date < effective_date):
                raise ValidationError(
                    f"Last working date must be greater than approved date."
                )
        return release_date


class StatusHistorySerializer(DynamicFieldsModelSerializer):
    created_by = UserThinSerializer(
        fields=['id', 'full_name', 'profile_picture', 'cover_picture','organization','is_current',]
    )

    class Meta:
        model = StatusHistory
        fields = 'status', 'remarks', 'created_at', 'created_by'
