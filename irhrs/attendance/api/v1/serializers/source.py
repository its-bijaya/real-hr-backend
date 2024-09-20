from django.conf import settings
from django.utils import timezone
from django_q.models import Schedule
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.attendance.constants import ADMS, DIRSYNC
from irhrs.attendance.models import AttendanceSource
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer

ADMS_ENABLED = settings.USING_ADMS


class AttendanceSourceSerializer(DynamicFieldsModelSerializer):
    last_activity = serializers.DateTimeField(read_only=True)
    total_sync = serializers.ReadOnlyField()
    ip = serializers.IPAddressField(protocol='ipv4', required=False, allow_null=True)
    port = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = AttendanceSource
        fields = (
            'id', 'name', 'serial_number', 'last_activity', 'sync_method',
            'ip', 'port', 'disable_device', 'clear_device', 'total_sync',
            'timezone'
        )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs.get('sync_method') == ADMS and not attrs.get('timezone'):
            raise ValidationError({
                'timezone': 'Timezone must be provided for ADMS devices.'
            })
        if attrs.get('sync_method') == DIRSYNC:
            errors = dict()
            if not attrs.get('ip'):
                errors['ip'] = 'IP is required.'
            if not attrs.get('port'):
                errors['port'] = 'Port is required.'
            if errors:
                raise ValidationError(errors)
        return attrs

    @staticmethod
    def validate_port(port):
        if port is None or port == '':
            return port
        if 0 < port < 65535:
            return port
        raise ValidationError("The port must be between 1-65535")

    def create(self, validated_data):
        instance = super().create(validated_data)
        if getattr(settings, 'USING_ADMS', False) and instance.sync_method == ADMS:
            self.feed_tasks(instance, created=True)
        return instance

    def update(self, instance, validated_data):
        old_method = instance.sync_method
        instance = super().update(instance, validated_data)
        new_method = instance.sync_method
        if getattr(settings, 'USING_ADMS', False) and ADMS in [old_method, new_method]:
            self.feed_tasks(instance, old_method=old_method, new_method=new_method)
        return instance

    @staticmethod
    def feed_tasks(instance, **kwargs):
        return
        # if instance.sync_method == ADMS:
        #     func = 'irhrs.attendance.utils.attendance_pull_mechanisms.sync_adms_devices'
        #     if not Schedule.objects.filter(
        #         func=func
        #     ).exists():
        #         tz_now = timezone.now().astimezone() + timezone.timedelta(minutes=2)
        #         Schedule.objects.update_or_create(
        #             func=func,
        #             defaults=dict(
        #                 name='Pull Attendance Data from ADMS Direct.',
        #                 minutes=2,
        #                 repeats=-1,
        #                 schedule_type=Schedule.MINUTES,
        #                 next_run=tz_now,
        #             ),
        #         )

    @staticmethod
    def validate_sync_method(sync_method):
        if sync_method == ADMS and not ADMS_ENABLED:
            raise ValidationError('ADMS is disabled.')
        return sync_method
