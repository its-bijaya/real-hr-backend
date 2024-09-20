from django.contrib.auth import get_user_model

from rest_framework import serializers

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer, \
    DummySerializer
from irhrs.hris.api.v1.serializers.core_task import CoreTaskSerializer
from irhrs.hris.models import CoreTask
from irhrs.task.constants import RESPONSIBLE_PERSON, COMPLETED
from ....models.task import TaskAssociation, TaskVerificationScore, MAX_LIMIT_OF_TASK_SCORING_CYCLE
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer

USER = get_user_model()


class TaskVerificationScoreSerializer(DynamicFieldsModelSerializer):
    scored_by = UserThinSerializer(source='created_by', read_only=True)
    scored_at = serializers.DateTimeField(source='created_at', read_only=True)
    remarks = serializers.CharField(max_length=1000)
    ack_remarks = serializers.CharField(max_length=1000, required=False)

    class Meta:
        model = TaskVerificationScore
        fields = ('score', 'remarks', 'ack', 'ack_remarks',
                  'scored_by', 'scored_at',)

    def validate(self, attrs):
        if 'ack' in attrs.keys():
            if not attrs.get('ack'):
                if not attrs.get('ack_remarks'):
                    raise serializers.ValidationError(
                        {"ack_remarks": f"Remarks is required if declined"}
                    )
        return attrs


class TaskAssociationSerializer(DynamicFieldsModelSerializer):
    core_tasks = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=CoreTask.objects.all()),
        write_only=True, required=False)
    verification_score = TaskVerificationScoreSerializer(
        read_only=True, source='scores', many=True
    )
    ack = serializers.NullBooleanField(source='_ack')
    cycle_status = serializers.SerializerMethodField()
    _total_cycle = serializers.IntegerField(source='total_cycle')

    @staticmethod
    def get_fields_(thin_view=False, exclude_fields: tuple = ()):
        if thin_view:
            return ['user', 'read_only']
        _fields = list(
            TaskAssociationSerializer.Meta.fields
        )
        if exclude_fields:
            for _f in exclude_fields:
                _fields.remove(_f)
        return _fields

    class Meta:
        model = TaskAssociation
        _extra_fields = ('efficiency_from_priority', 'efficiency_from_timely',
                         'efficiency_from_score', 'efficiency',
                         'verification_score', 'current_score', 'ack',
                         '_total_cycle', 'cycle_status')

        fields = ('user', 'association', 'task', 'core_tasks',
                  'created_at', 'read_only') + _extra_fields

        read_only_fields = ('task', 'read_only') + _extra_fields

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == 'get':
            fields['user'] = UserThinSerializer(read_only=True)
            fields['core_tasks'] = CoreTaskSerializer(many=True,
                                                      read_only=True,
                                                      fields=('id', 'title',
                                                              'description',
                                                              'order',
                                                              'result_area',))
            from .task import TaskThinSerializer
            fields['task'] = TaskThinSerializer()
        return fields

    @staticmethod
    def get_cycle_status(obj):
        # Score Not Provided
        # Forwarded To HR
        # Approved By HR
        # Acknowledged
        # Not Acknowledged
        # Acknowledge Pending
        # Approval Pending

        if obj.task.status != COMPLETED:
            return None
        return obj.cycle_status

    def create(self, validated_data):
        core_tasks = None
        if 'core_tasks' in validated_data.keys():
            core_tasks = validated_data.pop('core_tasks', None)
        validated_data.update({
            'task': self.context.get('task')
        })
        assoc = super().create(validated_data)
        if core_tasks:
            assoc.core_tasks.add(*core_tasks)
            self.fields['core_tasks'] = CoreTaskSerializer(many=True)
        return assoc

    def update(self, instance: TaskAssociation, validated_data):
        if 'core_tasks' in validated_data.keys():
            core_tasks = validated_data.pop('core_tasks', None)
            if core_tasks:
                instance.core_tasks.clear()
                instance.core_tasks.add(*core_tasks)
            else:
                instance.core_tasks.clear()
            self.fields['core_tasks'] = CoreTaskSerializer(many=True)
        return super().update(instance, validated_data)
