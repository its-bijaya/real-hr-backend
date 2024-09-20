from django.utils import timezone
from rest_framework import serializers

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from irhrs.worklog.models.worklog import WorkLogAttachment, WorkLog, \
    WorkLogComment


class WorkLogCommentsSerializer(DynamicFieldsModelSerializer):
    created_by = UserThinSerializer(read_only=True)

    class Meta:
        model = WorkLogComment
        fields = '__all__'

    def create(self, validated_data):
        validated_data.update({'work_log': self.context['work_log']})
        return super().create(validated_data)


class WorkLogAttachmentSerializer(DynamicFieldsModelSerializer):
    description = serializers.CharField(max_length=5000)

    class Meta:
        model = WorkLogAttachment
        fields = 'id', 'log', 'attachment', 'description'

    def create(self, validated_data):
        validated_data.update({'log': self.context['work_log']})
        return super().create(validated_data)


class WorkLogSerializer(DynamicFieldsModelSerializer):
    description = serializers.CharField(max_length=5000)
    attachments = WorkLogAttachmentSerializer(source='_worklog_attachments',
                                              fields=(
                                                  'id', 'attachment',
                                                  'description'
                                              ),
                                              many=True, read_only=True
                                              )
    comments = WorkLogCommentsSerializer(source='_worklog_comments',
                                         many=True,
                                         read_only=True)

    status = serializers.ReadOnlyField()

    class Meta:
        model = WorkLog
        fields = ('id', 'date', 'description', 'score', 'score_remarks',
                  'verified_by', 'verified_at', 'attachments', 'comments',
                  'status')

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == 'get':
            fields['created_by'] = UserThinSerializer()
            fields['verified_by'] = UserThinSerializer()
        return fields

    def validate_date(self, attr):
        if attr > timezone.now().date():
            raise serializers.ValidationError("Should not be in future")
        if self.instance and self.instance.date == attr:
            return attr
        if WorkLog.objects.filter(created_by=self.request.user,
                                  date=attr).exists():
            raise serializers.ValidationError(
                "Work log Already exists for this date")
        return attr

    def update(self, instance, validated_data):
        if 'score' in validated_data.keys() or 'score_remarks' in validated_data.keys():
            if not validated_data.get('score'):
                raise serializers.ValidationError(
                    {'score': ["Score is Required"]}
                )
            if not validated_data.get('score_remarks'):
                raise serializers.ValidationError(
                    {'score_remarks': ["Score Remarks is Required"]}
                )
            validated_data.update(
                {
                    'verified_by': self.request.user,
                    'verified_at': timezone.now()
                }
            )
        return super().update(instance, validated_data)
