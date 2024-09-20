from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, SerializerMethodField, \
    ReadOnlyField

from irhrs.attendance.api.v1.serializers.attendance import TimeSheetSerializer, \
    TimeSheetEntrySerializer
from irhrs.attendance.constants import (
    REQUESTED, DECLINED, FORWARDED,
    UPDATE, DELETE, APPROVED, UNCLAIMED
)
from irhrs.attendance.models import AttendanceAdjustment, \
    AttendanceAdjustmentHistory, TimeSheet, TimeSheetEntry
from irhrs.attendance.utils import attendance as attendance_utils
from irhrs.core.constants.common import ATTENDANCE
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer, \
    DummySerializer
from irhrs.core.utils.common import DummyObject
from irhrs.core.utils import subordinates, nested_getattr
from irhrs.core.utils.user_activity import create_user_activity
from irhrs.leave.utils.leave_request import test_if_payroll_is_generated
from irhrs.payroll.utils.generate import \
    raise_validation_error_if_payroll_in_generated_or_processing_state
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer


class AttendanceAdjustmentCreateSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = AttendanceAdjustment
        fields = [
            'id',
            'timestamp',
            'timesheet_entry',
            'category',
            'action',
            'description'
        ]

    def validate(self, attrs):
        # punch_in = attrs.get('new_punch_in')
        # punch_out = attrs.get('new_punch_out')
        timestamp = attrs.get('timestamp')

        if not timestamp:
            raise ValidationError('At least one of `Punch In` or `Punch Out` must be set.')

        time_sheet = self.context.get('time_sheet')

        # if time_sheet.adjustment_requests.exclude(status=DECLINED).count() >= 2:
        #     raise ValidationError('Attendance already adjusted two times.')

        sender = time_sheet.timesheet_user
        raise_validation_error_if_payroll_in_generated_or_processing_state(
            organization=self.context["organization"],
            date=timestamp.date()
        )

        receiver = attendance_utils.get_adjustment_request_receiver(time_sheet.timesheet_user)
        if not receiver:
            raise ValidationError('Supervisor is not assigned. Please assign '
                                  'supervisor.')
        return attrs

    def create(self, validated_data):
        sender = self.request.user
        time_sheet = self.context.get('time_sheet')
        receiver = attendance_utils.get_adjustment_request_receiver(time_sheet.timesheet_user)

        validated_data.update({
            "sender": sender,
            "timesheet": time_sheet,
            "receiver": receiver,
            "status": REQUESTED
        })

        adjustment = super().create(validated_data)

        AttendanceAdjustmentHistory.objects.create(
            adjustment=adjustment,
            action_performed=REQUESTED,
            action_performed_by=sender,
            action_performed_to=receiver,
            remark=adjustment.description
        )

        return adjustment


class AttendanceAdjustmentDetailSerializer(DynamicFieldsModelSerializer):
    user = UserThinSerializer(
        source="timesheet.timesheet_user",
        read_only=True
    )
    supervisor = SerializerMethodField(read_only=True)
    timesheet_entry = TimeSheetEntrySerializer(exclude_fields=['latitude', 'longitude'])
    sender = UserThinSerializer(read_only=True)
    timesheet = TimeSheetSerializer(exclude_fields=['can_adjust'])
    status = SerializerMethodField()

    receiver = UserThinSerializer(allow_null=True)

    permissions = ReadOnlyField(allow_null=True)

    class Meta:
        model = AttendanceAdjustment
        fields = (
            'id',
            'user',
            'timesheet',
            'timestamp',
            'category',
            'timesheet_entry',
            'action',
            'description',
            'status',
            'sender',
            'created_at',
            'receiver',
            'supervisor',
            'permissions',
        )

    @staticmethod
    def get_status(obj):
        return obj.get_status_display()

    @staticmethod
    def get_supervisor(obj):
        supervisor = obj.timesheet.timesheet_user.first_level_supervisor
        supervisor = get_user_model().objects.filter(id=supervisor.id) \
            .select_related('detail', 'detail__organization',
                            'detail__job_title',
                            'detail__employment_level').first() if supervisor else None
        return UserThinSerializer(
            supervisor
        ).data if supervisor else None


class AttendanceAdjustmentBulkCreateSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = AttendanceAdjustment
        fields = [
            'id',
            'category',
            'timestamp',
            'timesheet_entry',
            'action',
            'description',
            'timesheet'
        ]

    def get_fields(self):
        fields = super().get_fields()
        fields.update({
            "timesheet": serializers.PrimaryKeyRelatedField(
                queryset=TimeSheet.objects.filter(
                    timesheet_user=self.request.user
                ),
                write_only=True
            )
        })
        return fields

    def validate(self, attrs):
        timestamp = attrs.get('timestamp')
        category = attrs.get('category')

        if not timestamp:
            raise ValidationError('Timestamp must be set')

        if not category:
            raise ValidationError('Timesheet category must be set')

        time_sheet = attrs.get('timesheet')

        # if time_sheet.adjustment_requests.exclude(status=DECLINED).count() >= 2:
        #     raise ValidationError('Attendance already adjusted two times.')
        sender = time_sheet.timesheet_user
        raise_validation_error_if_payroll_in_generated_or_processing_state(
            organization=self.context["organization"],
            sender=sender,
            date=time_sheet.timesheet_for
        )
        receiver = attendance_utils.get_adjustment_request_receiver(time_sheet.timesheet_user)
        if not receiver:
            raise ValidationError('Supervisor is not assigned. Please assign '
                                  'supervisor.')
        return attrs


class AttendanceAdjustmentBulkSerializer(DummySerializer):
    adjustments = AttendanceAdjustmentBulkCreateSerializer(many=True)

    def validate(self, data):
        adjustments = data.get('adjustments')
        timestamps = {adjustment.get('timestamp') for adjustment in adjustments}
        if len(timestamps) < len(adjustments):
            raise ValidationError(
                'Multiple adjustments with same time is not allowed.'
            )
        return data

    def create(self, validated_data):
        for adjustment_data in validated_data.get('adjustments'):
            timesheet = adjustment_data.pop('timesheet')
            category = adjustment_data.pop('category')
            timestamp = adjustment_data.pop('timestamp')
            sender = self.context.get('request').user
            receiver = attendance_utils.get_adjustment_request_receiver(
                timesheet.timesheet_user
            )
            adjustment_data.update({
                "sender": sender,
                "timesheet": timesheet,
                "receiver": receiver,
                "category": category,
                "timestamp": timestamp,
                "status": REQUESTED
            })
            adjustment = AttendanceAdjustment.objects.create(
                **adjustment_data
            )
            AttendanceAdjustmentHistory.objects.create(
                adjustment=adjustment,
                action_performed=REQUESTED,
                action_performed_by=sender,
                action_performed_to=receiver,
                remark=adjustment.description
            )
        return DummyObject(**validated_data)


class AttendanceAdjustmentDeclineSerializer(DummySerializer):
    remark = CharField(max_length=255)


class AttendanceAdjustmentHistorySerializer(DynamicFieldsModelSerializer):
    action_performed = ReadOnlyField()
    action_performed_by = UserThinSerializer()
    action_performed_to = UserThinSerializer(allow_null=True)
    remark = ReadOnlyField()

    class Meta:
        model = AttendanceAdjustmentHistory
        fields = ('action_performed', 'action_performed_by',
                  'action_performed_to', 'remark', 'created_at')
        read_only_fields = 'created_at',


class AttendanceAdjustmentActionSerializer(DummySerializer):
    _APPROVE = 'approve'
    _DENY = 'deny'
    _FORWARD = 'forward'

    _ACTION_CHOICES = (
        (_APPROVE, _APPROVE),
        (_DENY, _DENY),
        (_FORWARD, _FORWARD)
    )

    action = serializers.ChoiceField(choices=_ACTION_CHOICES, write_only=True)
    remark = CharField(max_length=255, write_only=True)

    @property
    def mode(self):
        return self.context['view'].mode

    @property
    def request(self):
        return self.context['request']

    def get_fields(self):
        fields = super().get_fields()
        fields['adjustment'] = serializers.PrimaryKeyRelatedField(
            queryset=self.context.get('adjustments'),
            write_only=True
        )
        return fields

    def validate(self, attrs):
        adjustment = attrs['adjustment']
        action = attrs['action']

        if adjustment.status not in [REQUESTED, FORWARDED]:
            raise serializers.ValidationError(
                _("Can not act on already acted adjustment.")
            )

        if self.mode == 'hr' and action == self._FORWARD:
            raise serializers.ValidationError({
                'action': _("HR can not forward request.")
            })

        elif self.mode == 'supervisor':
            if not adjustment.receiver == self.request.user:
                # FAIL SAFE
                raise serializers.ValidationError(
                    _("You are not the right recipient for this request.")
                )

            if not subordinates.authority_exists(adjustment.sender, adjustment.receiver, action):
                raise serializers.ValidationError({
                    'action': _(f"You can not {action} this request.")
                })

        if action == self._FORWARD:
            next_authority = attendance_utils.get_adjustment_request_forwarded_to(adjustment)
            if not next_authority:
                raise serializers.ValidationError({
                    'action': _("Next level supervisor not found to forward.")
                })
            attrs['next_authority'] = next_authority
        # if action
        return attrs

    def create(self, validated_data):
        adjustment = validated_data['adjustment']
        action = validated_data['action']
        remark = validated_data['remark']

        if action == self._APPROVE:
            adjustment.approve(approved_by=self.request.user, remark=remark)
            create_user_activity(
                self.request.user,
                f"approved an adjustment request.",
                ATTENDANCE
            )

        elif action == self._FORWARD:
            next_authority = validated_data['next_authority']
            adjustment.receiver = next_authority.supervisor
            adjustment.status = FORWARDED
            adjustment.save()

            AttendanceAdjustmentHistory.objects.create(
                adjustment=adjustment,
                action_performed_by=self.request.user,
                action_performed_to=next_authority.supervisor,
                action_performed=FORWARDED,
                remark=remark
            )

            create_user_activity(
                self.request.user,
                f"forwarded an adjustment request.",
                ATTENDANCE
            )

        elif action == self._DENY:
            adjustment.status = DECLINED
            adjustment.save()

            AttendanceAdjustmentHistory.objects.create(
                adjustment=adjustment,
                action_performed_by=self.request.user,
                action_performed_to=self.request.user,
                action_performed=DECLINED,
                remark=remark
            )

            create_user_activity(
                self.request.user,
                "declined an adjustment request.",
                ATTENDANCE
            )

        return


class AttendanceAdjustmentUpdateEntrySerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = AttendanceAdjustment
        fields = [
            'id',
            'timesheet',
            'timesheet_entry',
            'category',
            'description'
        ]

    def get_fields(self):
        fields = super().get_fields()
        timesheet_queryset = TimeSheet.objects.filter(
            timesheet_user=self.request.user
        ).select_related(
            'timesheet_user',
            'timesheet_user__detail',
        )
        fields.update({
            "timesheet": serializers.PrimaryKeyRelatedField(
                queryset=timesheet_queryset,
                write_only=True
            ),
            'timesheet_entry': serializers.PrimaryKeyRelatedField(
                queryset=TimeSheetEntry.objects.filter(
                    timesheet__in=timesheet_queryset
                ).select_related(
                    'timesheet',
                    'timesheet__timesheet_user',
                    'timesheet__timesheet_user__detail',
                )
            ),
        })
        return fields

    def create(self, validated_data):
        timesheet = validated_data['timesheet']
        sender = self.request.user
        receiver = attendance_utils.get_adjustment_request_receiver(
            timesheet.timesheet_user
        )
        action = self.context.get('adjustment_action', UPDATE)
        validated_data.update({
            "sender": sender,
            "receiver": receiver,
            "status": REQUESTED,
            "action": action,
            "timestamp": validated_data.get('timesheet_entry').timestamp,
            "description": self.initial_data.get("description")
        })
        adjustment = AttendanceAdjustment.objects.create(
            **validated_data
        )
        AttendanceAdjustmentHistory.objects.create(
            adjustment=adjustment,
            action_performed=REQUESTED,
            action_performed_by=sender,
            action_performed_to=receiver,
            remark=adjustment.description
        )
        return adjustment

    def validate(self, attrs):
        timesheet = attrs.get('timesheet')
        timesheet_entry = attrs.get('timesheet_entry')
        if timesheet_entry not in timesheet.timesheet_entries.all():
            raise serializers.ValidationError({
                'timesheet_entry': 'Timesheet entry does not exist for selected date.'
            })

        existing = AttendanceAdjustment.objects.filter(
            timesheet=attrs.get('timesheet'),
            timesheet_entry=attrs.get('timesheet_entry')
        ).exclude(status__in=[DECLINED, APPROVED]).first()
        if existing:
            raise ValidationError(
                f"{existing.get_action_display()} Attendance Adjustment for this timesheet exists "
                f"in {existing.get_status_display()} state."
            )

        sender = timesheet.timesheet_user
        raise_validation_error_if_payroll_in_generated_or_processing_state(
            organization=sender.detail.organization, date=timesheet.timesheet_for
        )
        return super().validate(attrs)

    @staticmethod
    def validate_timestamp(timestamp):
        if not timestamp:
            raise ValidationError('Timestamp may not be null')
        return timestamp


class AttendanceAdjustmentDeleteEntrySerializer(AttendanceAdjustmentUpdateEntrySerializer):

    def create(self, validated_data):
        self.context['adjustment_action'] = DELETE
        validated_data['category'] = ''
        return super().create(validated_data)

    def validate(self, attrs):
        entry = attrs.get(
            'timesheet_entry'
        )

        if entry and entry.entry_method not in settings.DELETE_ALLOWED_TIMESHEET_ENTRY_METHODS:
            raise ValidationError(f"{entry.entry_method} entries can not be removed.")

        overtime_status = nested_getattr(entry.timesheet, 'overtime.claim.status')
        if overtime_status and overtime_status != UNCLAIMED:
            raise ValidationError(
                f"Cannot remove entries with overtime in {overtime_status} status"
            )
        credit_entries = getattr(entry.timesheet, 'credit_entries', None)
        if credit_entries:
            credit_entry = credit_entries.first()
            credit_hour_request = getattr(
                credit_entry, 'credit_request', None
            )
            credit_hour_status = getattr(credit_hour_request, 'status', None)

            is_deleted = getattr(credit_hour_request, 'is_deleted', False)
            if credit_hour_status == APPROVED and not is_deleted:
                raise ValidationError(
                    f"Cannot remove entries with credit hour in {credit_hour_status} status"
                )
        return super().validate(attrs)

