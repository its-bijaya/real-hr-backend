from datetime import datetime
from numbers import Number
from typing import Union

import pytz

from django.contrib.auth import get_user_model
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.attendance.utils.attendance import get_adjustment_request_receiver
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.hris.api.v1.serializers.core_task import CoreTaskSerializer
from irhrs.task.api.v1.serializers.settings import ProjectListSerializer, ActivitySerializer
from irhrs.task.api.v1.serializers.task import TaskSerializer
from irhrs.task.models import WorkLog, DRAFT, REQUESTED, APPROVED, \
    WorkLogAction, ACKNOWLEDGED, CONFIRMED, SENT
from irhrs.task.models.settings import HOUR, UserActivityProject
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer


ATTACHMENT_MAX_UPLOAD_SIZE = 5 * 1024 * 1024
KTM = pytz.timezone("Asia/Kathmandu")


class WorLogListSerializer(DynamicFieldsModelSerializer):
    status = serializers.ReadOnlyField()
    sender = UserThinSerializer(
        fields=('id', 'full_name', 'profile_picture', 'job_title', 'organization', 'is_current',),
        read_only=True
    )
    permissions = serializers.ReadOnlyField(allow_null=True)
    score = serializers.SerializerMethodField()
    project = ProjectListSerializer(fields=('id', 'name'))
    activity = ActivitySerializer(fields=('id', 'name', 'unit'))
    feedback = serializers.SerializerMethodField()
    task = TaskSerializer(fields=('id', 'title'))
    core_task = CoreTaskSerializer(fields=('id', 'title'), many=True)

    class Meta:
        model = WorkLog
        fields = (
            'id', 'project', 'activity', 'task', 'core_task', 'unit', 'start_time', 'end_time',
            'activity_description', 'attachment', 'status', 'sender', 'permissions', 'score',
            'feedback'
        )

    def get_score(self, obj: WorkLog) -> Union[Number, str, None]:
        """
        :return: Number if finds score attribute in WorkLogAction else returns str.
            Returns None when WorkLog status doesn't lie in [APPROVED, ACKNOWLEDGED, CONFIRMED]
        """
        if obj.status in [APPROVED, ACKNOWLEDGED, CONFIRMED]:
            worklog_action = obj.worklog_actions.filter(action=APPROVED).first()
            return getattr(worklog_action, 'score', "N/A")
        return None

    def get_feedback(self, obj: WorkLog) -> str:
        worklog_action = obj.worklog_actions.filter(action=obj.status).first()
        return getattr(worklog_action, 'remarks', "N/A")


class WorLogToDoCreateSerializer(ModelSerializer):
    status = serializers.ReadOnlyField()

    class Meta:
        model = WorkLog
        fields = ('activity_description', 'status')


class WorLogToDoBulkCreateSerializer(serializers.Serializer):
    requests = WorLogToDoCreateSerializer(many=True, write_only=True)

    def create(self, validated_data):
        sender = self.context.get('user')
        receiver = get_adjustment_request_receiver(sender)
        requests = validated_data.get("requests")
        instances = WorkLog.objects.bulk_create(
            [
                WorkLog(
                    sender=sender,
                    receiver=receiver,
                    **req
                ) for req in requests
            ]
        )
        for instance in instances:
            # update each status of work log to DRAFT when created directly without creating TO_DOs
            instance.status = DRAFT
        return instances


class WorLogToDoStartSerializer(ModelSerializer):
    class Meta:
        model = WorkLog
        fields = ('start_time', )


class WorLogCreateDailyTaskSerializer(DynamicFieldsModelSerializer):
    status = serializers.ReadOnlyField()

    class Meta:
        model = WorkLog
        fields = (
            'project', 'activity', 'unit', 'task', 'core_task', 'status', 'start_time',
            'end_time', 'activity_description', 'attachment'
        )

    def get_fields(self):
        fields = super().get_fields()
        if self.context.get('mode') in ['supervisor', 'hr']:
            fields['user'] = serializers.PrimaryKeyRelatedField(
                queryset=get_user_model().objects.all().current(),
                write_only=True
            )
        return fields

    def validate(self, attrs):
        start_time = attrs.get("start_time")
        end_time = attrs.get("end_time")
        attachment = attrs.get("attachment")
        user = attrs.get('user')
        mode = self.context.get('mode')

        if (start_time and end_time) and start_time > end_time:
            raise ValidationError({
                "end_time": "End time should be greater than start time."
            })
        if not attrs.get('activity_description'):
            raise ValidationError({
                "activity_description": "This field may not be null."
            })
        if attachment and attachment.size > ATTACHMENT_MAX_UPLOAD_SIZE:
            raise ValidationError(
                    'File Size Should not Exceed '
                    f'{ATTACHMENT_MAX_UPLOAD_SIZE / (1024 * 1024)} MB'
            )

        if user and (user.id not in self.request.user.subordinates_pks):
            raise ValidationError("You don't have permission to assign worklog to this user.")

        sender = self.request.user
        if mode in ['hr', 'supervisor']:
            sender = user
            if not user:
                raise ValidationError("User must be select inorder to create on behalf of user")

        receiver = get_adjustment_request_receiver(sender)
        if not receiver:
            raise ValidationError('Supervisor is not assigned. Please assign supervisor.')
        return attrs

    def create(self, validated_data):
        sender = self.request.user
        receiver = get_adjustment_request_receiver(sender)
        unit = validated_data.get('unit')
        activity = validated_data.get('activity')
        total_amount = None
        if unit and activity:
            if activity.unit == HOUR:
                unit = round(unit/60, 2)
            user_activity = UserActivityProject.objects.filter(
                project=validated_data.get('project'),
                activity=activity,
                user=sender
            )
            emp_rate = getattr(user_activity, 'employee_rate', 0)
            total_amount = round(unit * emp_rate, 2)
        if self.context.get('mode') in ['supervisor', 'hr']:
            sender = validated_data.pop('user')
            receiver = get_adjustment_request_receiver(sender)

        validated_data.update({
            "sender": sender,
            "receiver": receiver,
            "unit": unit,
            "total_amount": total_amount
        })
        worklog = super().create(validated_data)
        return worklog

    def update(self, instance, validated_data):
        sender = self.request.user
        activity = validated_data.get('activity')
        unit = validated_data.get('unit')
        total_amount = None
        if unit and activity:
            if activity.unit == HOUR:
                unit = round(unit/60, 2)
            user_activity = UserActivityProject.objects.filter(
                project=validated_data.get('project'),
                activity=activity,
                user=sender
            ).first()
            emp_rate = getattr(user_activity, 'employee_rate', 0)
            total_amount = round(unit * emp_rate, 2)
        validated_data.update({
            "sender": sender,
            "unit": unit,
            "total_amount": total_amount
        })
        return super().update(instance, validated_data)


class WorkLogApproveSerializer(ModelSerializer):
    class Meta:
        model = WorkLogAction
        fields = ('worklog', 'remarks', 'score')

    def validate(self, attrs):
        if not attrs.get('score'):
            raise ValidationError({
                "score": "This field may not be null"
            })
        return attrs


class WorkLogBulkApproveSerializer(serializers.Serializer):
    requests = WorkLogApproveSerializer(many=True, write_only=True)

    def create(self, validated_data):
        instance = WorkLogAction.objects.bulk_create(
            [
                WorkLogAction(
                    action_performed_by=self.context.get('user'),
                    worklog=req.get('worklog'),
                    score=req.get('score'),
                    remarks=req.get('remarks'),
                    action=APPROVED,
                    action_date=datetime.now(KTM)
                ) for req in validated_data.get('requests')
            ]
        )
        return instance


class WorkLogActionRemarksSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = WorkLogAction
        fields = ('worklog', 'remarks')


class WorkLogActionBulkRemarksSerializer(serializers.Serializer):
    requests = WorkLogActionRemarksSerializer(many=True, write_only=True)

    def create(self, validated_data):
        instance = WorkLogAction.objects.bulk_create(
            [
                WorkLogAction(
                    action_performed_by=self.context.get('user'),
                    worklog=req.get('worklog'),
                    remarks=req.get('remarks'),
                    action=self.context.get('action'),
                    action_date=datetime.now(KTM)
                ) for req in validated_data.get('requests')
            ]
        )
        return instance


class WorkLogHistorySerializer(DynamicFieldsModelSerializer):
    action = serializers.ReadOnlyField()
    action_performed_by = UserThinSerializer()
    action_performed_to = UserThinSerializer(allow_null=True)
    remarks = serializers.ReadOnlyField()

    class Meta:
        model = WorkLogAction
        fields = ('action', 'action_performed_by', 'action_performed_to', 'score',
                  'remarks', 'created_at',)
        read_only_fields = 'created_at',


class WorkLogReportSerializer(DynamicFieldsModelSerializer):
    requested_date = serializers.SerializerMethodField()
    confirmed_date = serializers.SerializerMethodField()
    sent_date = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    sender = UserThinSerializer(
        fields=('id', 'full_name', 'profile_picture', 'job_title', 'organization', 'is_current',),
        read_only=True
    )
    project = ProjectListSerializer()
    activity = ActivitySerializer(fields=('id', 'name', 'unit'))
    employee_rate = serializers.SerializerMethodField()
    task = TaskSerializer(fields=('id', 'title'))
    core_task = CoreTaskSerializer(fields=('id', 'title'), many=True)

    class Meta:
        model = WorkLog
        fields = (
            'id', 'project', 'activity', 'task', 'core_task', 'unit', 'sender', 'status',
            'activity_description', 'requested_date', 'confirmed_date', 'sent_date', 'total_amount',
            'employee_rate'
        )

    def get_fields(self):
        fields = super().get_fields()
        if self.context.get('mode') == "hr":
            fields['activity'] = ActivitySerializer()
            fields['client_rate'] = serializers.SerializerMethodField()
            fields['total_client_amount'] = serializers.SerializerMethodField()
        return fields

    def get_employee_rate(self, obj: WorkLog) -> Number:
        user_activity = UserActivityProject.objects.filter(
            project=obj.project,
            activity=obj.activity,
            user=obj.sender
        ).first()
        return getattr(user_activity, 'employee_rate', 0)

    def get_client_rate(self, obj: WorkLog) -> Number:
        user_activity = UserActivityProject.objects.filter(
            project=obj.project,
            activity=obj.activity,
            user=obj.sender
        ).first()
        return getattr(user_activity, 'client_rate', 0)

    def get_requested_date(self, obj: WorkLog) -> Union[datetime, None]:
        worklog_action = WorkLogAction.objects.filter(worklog=obj, action=REQUESTED).first()
        return getattr(worklog_action, 'action_date', None)

    def get_confirmed_date(self, obj: WorkLog) -> Union[datetime, None]:
        worklog_action = WorkLogAction.objects.filter(worklog=obj, action=CONFIRMED).first()
        return getattr(worklog_action, 'action_date', None)

    def get_sent_date(self, obj: WorkLog) -> Union[datetime, None]:
        worklog_action = WorkLogAction.objects.filter(worklog=obj, action=SENT).first()
        return getattr(worklog_action, 'action_date', None)

    def get_status(self, obj: WorkLog) -> Union[str, None]:
        worklog_action = obj.worklog_actions.all().order_by('-modified_at').first()
        return getattr(worklog_action, 'action', None)

    def get_total_client_amount(self, obj: WorkLog) -> Union[Number, None]:
        activity = obj.activity
        quantity = obj.unit
        user_activity = UserActivityProject.objects.filter(
                project=obj.project,
                activity=activity,
                user=obj.sender
            ).first()
        client_rate = getattr(user_activity, 'client_rate', 0)
        if quantity and client_rate:
            return round(quantity * client_rate, 2)
        return None


class WorkLogBulkSendSerializer(serializers.Serializer):
    requests = WorkLogActionRemarksSerializer(many=True, write_only=True, fields=('worklog', ))

    def create(self, validated_data):
        instance = list()
        for req in validated_data.get('requests'):
            worklog_action = WorkLogAction.objects.filter(
                worklog=req.get('worklog')
            ).order_by('-modified_at').first()
            if not worklog_action:
                raise ValidationError("Worklog action not found.")
            if worklog_action.action != CONFIRMED:
                raise ValidationError(
                    "Worklog must be in confirmed state before sending to payroll."
                )
            instance.append(
                WorkLogAction(
                    action_performed_by=self.context.get('user'),
                    worklog=req.get('worklog'),
                    remarks=f"Sent by {self.context.get('user')} to payroll",
                    action=SENT,
                    action_date=datetime.now(KTM)
                )
            )
        created = WorkLogAction.objects.bulk_create(instance)
        return created
