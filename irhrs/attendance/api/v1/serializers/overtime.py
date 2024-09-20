import datetime
import re
from datetime import timedelta, time

from dateutil.parser import parse
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField

from irhrs.attendance.constants import (
    REQUESTED, FORWARDED, APPROVED, DECLINED, CONFIRMED,
    UNCLAIMED, OVERTIME_CALCULATION_CHOICES, DAILY)
from irhrs.attendance.models import OvertimeClaimHistory, TimeSheet
from irhrs.attendance.models.overtime import OvertimeEntryDetail, \
    OvertimeEntryDetailHistory
from irhrs.attendance.utils.attendance import humanize_interval
from irhrs.attendance.utils.helpers import get_overtime_recipient, \
    validate_appropriate_actor, get_weekday
from irhrs.attendance.utils import helpers
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer, \
    DummySerializer
from irhrs.core.utils import nested_getattr, get_system_admin, subordinates, get_patch_attr
from irhrs.core.utils.common import DummyObject, combine_aware
from irhrs.core.utils.subordinates import find_immediate_subordinates
from irhrs.core.validators import validate_past_date
from irhrs.organization.api.v1.serializers.organization import \
    OrganizationSerializer
from irhrs.users.api.v1.serializers.thin_serializers import \
    UserThinSerializer
from irhrs.users.models import UserSupervisor
from ....models import (
    OvertimeSetting, OvertimeRate, OvertimeClaim, OvertimeEntry
)
from ....utils.validators import validate_overtime_delta

User = get_user_model()


class TimeSheetSerializer(DynamicFieldsModelSerializer):
    leave_coefficient = SerializerMethodField()

    class Meta:
        model = TimeSheet
        fields = (
            'punch_in', 'punch_out', 'leave_coefficient'
        )

    def get_leave_coefficient(self, instance):
        return instance.get_leave_coefficient_display()


class OvertimeRateSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = OvertimeRate
        fields = (
            'overtime_after', 'rate', 'rate_type',
        )


NO_MATCH, HOUR_MATCH, RATE_MATCH, OFF_DAY_MATCH = (
    'No Match', 'Hour Match', 'Rate Match', 'Off Day Match'
)


class OvertimeSettingSerializer(DynamicFieldsModelSerializer):
    organization = serializers.SerializerMethodField()
    rates = OvertimeRateSerializer(many=True)
    editable = serializers.ReadOnlyField()
    applicable_before = serializers.IntegerField(
        default=0, required=False, min_value=0, validators=[validate_overtime_delta]
    )
    applicable_after = serializers.IntegerField(
        default=0, required=False, min_value=0, validators=[validate_overtime_delta]
    )
    overtime_calculation = serializers.ChoiceField(
        required=False,
        choices=OVERTIME_CALCULATION_CHOICES,
        default=DAILY
    )

    class Meta:
        model = OvertimeSetting
        fields = (
            'organization', 'name',
            'daily_overtime_limit_applicable',
            'daily_overtime_limit',
            'weekly_overtime_limit_applicable',
            'weekly_overtime_limit',
            'monthly_overtime_limit_applicable',
            'monthly_overtime_limit',
            'off_day_overtime',
            'off_day_overtime_limit',
            'applicable_before', 'applicable_after',
            'overtime_calculation',
            'paid_holiday_affect_overtime',
            'leave_affect_overtime',
            'leave_overtime_limit',
            'holiday_overtime_limit',
            'rates', 'editable', 'slug',
            'flat_reject_value', 'require_dedicated_work_time',
            'overtime_after_offday',
            'overtime_after_holiday',
            'deduct_overtime_after_for', 'overtime_applicable_only_after',
            'claim_expires', 'expires_after', 'expires_after_unit',
            'require_prior_approval',
            'require_post_approval_of_pre_approved_overtime',
            'grant_compensatory_time_off_for_exceeded_minutes',
            'reduce_ot_if_actual_ot_lt_approved_ot',
            'actual_ot_if_actual_gt_approved_ot',
            'allow_edit_of_pre_approved_overtime',
            'minimum_request_duration',
            'calculate_overtime_in_slots',
            'slot_duration_in_minutes',
            'slot_behavior_for_remainder',
        )
        prior_approval_fields = (
            # Show N/A when prior_approval is false.
            'require_post_approval_of_pre_approved_overtime',
            'grant_compensatory_time_off_for_exceeded_minutes',
            'reduce_ot_if_actual_ot_lt_approved_ot',
            'allow_edit_of_pre_approved_overtime',
            'minimum_request_duration',
            'require_post_approval_of_pre_approved_overtime',
            'grant_compensatory_time_off_for_exceeded_minutes',
            'reduce_ot_if_actual_ot_lt_approved_ot',
            'actual_ot_if_actual_gt_approved_ot',
            'allow_edit_of_pre_approved_overtime',
            'minimum_request_duration'
        )
        non_prior_approval_fields = (
            # Show N/A when prior approval is true
            'deduct_overtime_after_for',
            'applicable_before',
            'applicable_after',
            'overtime_calculation',
            'paid_holiday_affect_overtime',
            'leave_affect_overtime',
            'leave_overtime_limit',
            'holiday_overtime_limit',
            'flat_reject_value',
            'overtime_after_offday',
            'overtime_after_holiday',
            'overtime_applicable_only_after',
            'claim_expires',
            'expires_after',
            'expires_after_unit',
        )
        read_only_fields = ('slug',)

    def validate(self, data):
        overtime_test = (
            ('off_day_overtime', 'off_day_overtime_limit'),
            ('leave_affect_overtime', 'leave_overtime_limit'),
            ('paid_holiday_affect_overtime', 'holiday_overtime_limit'),
            ('daily_overtime_limit_applicable', 'daily_overtime_limit'),
            ('weekly_overtime_limit_applicable', 'weekly_overtime_limit'),
            ('monthly_overtime_limit_applicable', 'monthly_overtime_limit'),
            ('calculate_overtime_in_slots', 'slot_duration_in_minutes'),
            ('calculate_overtime_in_slots', 'slot_behavior_for_remainder'),
        )
        errors = dict()
        for day, limit in overtime_test:
            if bool(data.get(day)) != bool(data.get(limit)):
                if data.get(day):
                    errors.update({
                        limit: [f'{limit} is required']
                    })
                else:
                    errors.update({
                        limit: [
                            f'Can not set {limit}'
                        ]
                    })
        errors.update(
            self.validate_daily_lt_weekly(data)
        )
        if errors:
            raise ValidationError(errors)
        self.validate_pre_approval_child_settings(data)
        return data

    def validate_name(self, name):
        if self.request and self.request.method.upper() == 'POST':
            if OvertimeSetting.objects.filter(
                name=name,
                organization=self.context.get('organization')
            ).exists():
                raise ValidationError(
                    "Overtime Setting `%s` already exists for this organization." % name
                )
        return name

    def validate_pre_approval_child_settings(self, data):
        parent = get_patch_attr('require_prior_approval', data, self)
        child_fields = (
            'require_post_approval_of_pre_approved_overtime',
            'grant_compensatory_time_off_for_exceeded_minutes',
            'reduce_ot_if_actual_ot_lt_approved_ot',
            'allow_edit_of_pre_approved_overtime',
            'minimum_request_duration'
        )
        errors = dict()
        for child_field in child_fields:
            child = get_patch_attr(child_field, data, self)
            if bool(child) and not bool(parent):
                errors.update({
                    child_field: "Can not set this value as `require_prior_approval` \
                         is not enabled."
                })
        if errors:
            raise ValidationError(errors)

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method == 'GET':
            fields.update({
                'daily_overtime_limit': SerializerMethodField(
                    method_name='get_daily'
                ),
                'weekly_overtime_limit': SerializerMethodField(
                    method_name='get_weekly'
                ),
                'monthly_overtime_limit': SerializerMethodField(
                    method_name='get_monthly'
                ),
                'holiday_overtime_limit': SerializerMethodField(
                    method_name='get_holiday'
                ),
                'off_day_overtime_limit': SerializerMethodField(
                    method_name='get_offday'
                ),
                'leave_overtime_limit': SerializerMethodField(
                    method_name='get_leave'
                ),
                'slot_duration_in_minutes': SerializerMethodField(
                    method_name='get_slot_duration'
                )
            })
        return fields

    def _split_hour_minutes(self, minutes_):
        if not minutes_:
            return {
                'hours': None,
                'minutes': None
            }
        minutes = int(minutes_)
        hr, mins = divmod(minutes, 60)
        return {
            'hours': hr,
            'minutes': mins
        }

    def get_daily(self, instance):
        return self._split_hour_minutes(
            getattr(instance, 'daily_overtime_limit')
        )

    def get_weekly(self, instance):
        return self._split_hour_minutes(
            getattr(instance, 'weekly_overtime_limit')
        )

    def get_monthly(self, instance):
        return self._split_hour_minutes(
            getattr(instance, 'monthly_overtime_limit')
        )

    def get_holiday(self, instance):
        return self._split_hour_minutes(
            getattr(instance, 'holiday_overtime_limit')
        )

    def get_offday(self, instance):
        return self._split_hour_minutes(
            getattr(instance, 'off_day_overtime_limit')
        )

    def get_leave(self, instance):
        return self._split_hour_minutes(
            getattr(instance, 'leave_overtime_limit')
        )

    def get_slot_duration(self, instance):
        return self._split_hour_minutes(
            getattr(instance, 'slot_duration_in_minutes')
        )

    @property
    def _get_next_week_start_date(self):
        """
        week day.
        """
        day = get_weekday(timezone.now())
        return timezone.now() + timezone.timedelta(days=8 - day)

    @transaction.atomic()
    def create(self, validated_data):
        validated_data.update({
            'organization': self.context.get('organization')
        })
        rates_data = validated_data.pop('rates')
        overtime_setting_object = super().create(validated_data)
        rates = list()
        for data in rates_data:
            data.update({
                'overtime_settings': overtime_setting_object
            })
            rates.append(
                OvertimeRate(**data)
            )
        OvertimeRate.objects.bulk_create(rates)
        return overtime_setting_object

    def update(self, instance, validated_data):
        rates = validated_data.pop('rates')
        current_list = [
            r.get('overtime_after') for r in rates
        ]
        for rate in rates:
            # handle with `update_or_create`
            multiplier = rate.pop('rate', None)
            instance.rates.update_or_create(
                **rate, defaults={'rate': multiplier}
            )
        updated = super().update(instance, validated_data)
        instance.rates.exclude(
            overtime_after__in=current_list
        ).delete()
        return updated

    def get_organization(self, instance):
        if instance:
            return OrganizationSerializer(
                instance.organization,
                fields=['name', 'slug']).data
        return {}

    @staticmethod
    def validate_daily_lt_weekly(data):
        def pretty(usv):
            return ' '.join(usv.split('_'))

        errors = dict()
        weekly_limit = data.get('weekly_overtime_limit')
        monthly_limit = data.get('monthly_overtime_limit')
        test_against = None, None
        if monthly_limit:
            test_against = monthly_limit, 'monthly_overtime_limit'
        if weekly_limit:
            if test_against[0] and (weekly_limit > test_against[0]):
                errors.update({
                    'weekly_overtime_limit': f'Make sure weekly limit is less than '
                                             f'{pretty(test_against[1])}.'
                })
            test_against = weekly_limit, 'weekly_overtime_limit'
        sequence_test = (
            'daily_overtime_limit',
            'off_day_overtime_limit',
            'holiday_overtime_limit',
            'leave_overtime_limit',
        )
        if not test_against[0]:
            return {}
        for daily_limit_field in sequence_test:
            val = data.get(daily_limit_field)
            if val and (val > test_against[0]):
                errors.update({
                    daily_limit_field: f'Make sure {pretty(daily_limit_field)} '
                                       f'is less than {pretty(test_against[1])}.'
                })
        return errors


class OvertimeEntryDetailSerializer(DynamicFieldsModelSerializer):
    remarks = serializers.CharField(max_length=200, write_only=True)

    class Meta:
        model = OvertimeEntryDetail
        fields = (
            'punch_in_overtime', 'punch_out_overtime', 'claimed_overtime',
            'remarks'
        )
        read_only_fields = (
            'claimed_overtime',
        )

    def get_fields(self):
        fields = super().get_fields()
        if self.request.method.upper() == 'GET':
            fields['punch_in_overtime'] = serializers.SerializerMethodField()
            fields['punch_out_overtime'] = serializers.SerializerMethodField()

        return fields

    def get_punch_in_overtime(self, instance):
        return humanize_interval(instance.punch_in_overtime)

    def get_punch_out_overtime(self, instance):
        return humanize_interval(instance.punch_out_overtime)

    def validate(self, attrs):
        claim_status = nested_getattr(
            self,
            'instance.overtime_entry.claim.status'
        )
        if claim_status and claim_status not in [UNCLAIMED, DECLINED]:
            raise ValidationError(
                f"Cannot edit overtime details if the status is not in "
                f"{UNCLAIMED} or {DECLINED}"
            )
        return super().validate(attrs)

    @staticmethod
    def _validate_overtime(overtime, previous, system_generated_ot):
        if overtime.total_seconds() < 0:
            return overtime
        elif overtime > system_generated_ot:
            raise ValidationError(
                f"You set the overtime to {humanize_interval(overtime)}. "
                f"Cannot set beyond {humanize_interval(system_generated_ot)}."
            )
        return overtime

    def validate_punch_in_overtime(self, overtime):
        instance = getattr(self, 'instance', None)
        if instance:
            # Check history:
            # Checking history will allow user to update
            # `10:00:00` to '05:00:00` and increase to `06:00:00` not
            # exceeding the ultimate limit `10:00:00`
            overtime_entry_detail = instance.overtime_entry.overtime_detail
            punch_in_ot = abs(instance.overtime_entry.timesheet.punch_in_delta)
            first_history = overtime_entry_detail.histories.filter(
                actor=get_system_admin()
            ).order_by(
                '-created_at'
            ).first()
            if first_history:
                old_overtime = getattr(
                    first_history,
                    'current_punch_in_overtime'
                )
            else:
                old_overtime = getattr(
                    overtime_entry_detail,
                    'punch_in_overtime'
                ) or timedelta(0)
            return self._validate_overtime(
                overtime, old_overtime, punch_in_ot
            )
        return overtime

    def validate_punch_out_overtime(self, overtime):
        instance = getattr(self, 'instance', None)
        if instance:
            overtime_entry_detail = instance.overtime_entry.overtime_detail
            punch_out_ot = abs(instance.overtime_entry.timesheet.punch_out_delta)
            first_history = overtime_entry_detail.histories.filter(
                actor=get_system_admin()
            ).order_by(
                '-created_at'
            ).first()
            if first_history:
                old_overtime = getattr(
                    first_history,
                    'current_punch_out_overtime'
                )
            else:
                old_overtime = getattr(
                    overtime_entry_detail,
                    'punch_out_overtime'
                ) or timedelta(0)
            return self._validate_overtime(
                overtime, old_overtime, punch_out_ot
            )
        return overtime

    @transaction.atomic()
    def update(self, instance, validated_data):
        remarks = validated_data.pop('remarks', '')
        previous_pi, previous_po = instance.punch_in_overtime, \
            instance.punch_out_overtime
        instance = super().update(instance, validated_data)
        computed = {
            'normalized_overtime': timedelta(
                seconds=instance.normalized_overtime_seconds
            ),
            'claimed_overtime': timedelta(
                seconds=instance.get_claimable_overtime(format=False)
            )
        }
        for attr, value in computed.items():
            setattr(instance, attr, value)
        instance.save()
        if (
                instance.punch_in_overtime != previous_pi or
                instance.punch_out_overtime != previous_po
        ):
            instance.histories.create(
                actor=self.request.user,
                previous_punch_in_overtime=previous_pi,
                previous_punch_out_overtime=previous_po,
                current_punch_in_overtime=instance.punch_in_overtime,
                current_punch_out_overtime=instance.punch_out_overtime,
                remarks=remarks
            )
        return instance


class OvertimeEntrySerializer(DynamicFieldsModelSerializer):
    user = UserThinSerializer(read_only=True)
    timesheet = TimeSheetSerializer()
    total_overtime = serializers.SerializerMethodField()
    supervisor = UserThinSerializer(source='user.first_level_supervisor')
    date = serializers.SerializerMethodField()
    overtime_detail = OvertimeEntryDetailSerializer(read_only=True)
    claimable_overtime = serializers.ReadOnlyField(
        source='overtime_detail.claimable_overtime'
    )
    normalized_overtime = serializers.SerializerMethodField()

    class Meta:
        model = OvertimeEntry
        fields = (
            'user', 'timesheet', 'total_overtime', 'supervisor', 'date',
            'overtime_detail', 'claimable_overtime', 'normalized_overtime'
        )

    @staticmethod
    def get_date(instance):
        if instance and instance.timesheet:
            return instance.timesheet.timesheet_for
        return None

    @staticmethod
    def get_total_overtime(instance, humanize=True):
        if instance and instance.overtime_detail:
            total_seconds = instance.overtime_detail.total_seconds
            # see https://stackoverflow.com/questions/775049
            if humanize:
                m, s = divmod(total_seconds, 60)
                h, m = divmod(m, 60)
                return '{:d}:{:02d}:{:02d}'.format(h, m, s)
            else:
                return int(total_seconds / 60)
        return None

    def get_normalized_overtime(self, instance):
        normalized = instance.overtime_detail.normalized_overtime
        ret = normalized.total_seconds() or 0
        m, s = divmod(int(ret), 60)
        h, m = divmod(m, 60)
        return '{:d}:{:02d}:{:02d}'.format(h, m, s)


class OvertimeClaimSerializer(DynamicFieldsModelSerializer):
    overtime_entry = OvertimeEntrySerializer(read_only=True)
    work_shift = serializers.SerializerMethodField()
    edited = serializers.ReadOnlyField()
    claimed_on = serializers.DateTimeField(
        allow_null=True,
        read_only=True
    )
    permissions = serializers.ReadOnlyField()

    class Meta:
        model = OvertimeClaim
        fields = (
            'status', 'description', 'id', 'work_shift', 'overtime_entry',
            'edited', 'claimed_on', 'permissions'
        )

    def validate(self, attrs):
        params = nested_getattr(self, 'request.query_params')
        mode = params.get('as', 'user') if params else 'user'
        validate_appropriate_actor(
            nested_getattr(
                self, 'request.user'
            ),
            self.instance, attrs, mode=mode
        )
        if self.instance:
            is_archived = self.instance.is_archived
            if is_archived:
                raise ValidationError(
                    "Updates to expired claims is not permitted."
                )
            status = attrs.get('status')
            action_performed_to = get_overtime_recipient(self.instance, status, self.instance.status)
            if action_performed_to is None:
                raise ValidationError(
                    f"Cannot act as no supervisor is assigned for this action."
                )
            self._recipient = action_performed_to
        return super().validate(attrs)

    def validate_status(self, status):
        # maintain order of status updates.
        # the serializer is called for update only.
        status_order = [
            UNCLAIMED, REQUESTED, FORWARDED, APPROVED, CONFIRMED, DECLINED
        ]
        if self.instance:
            modified_by = self.instance.modified_by
            request = self.context['request']
            supervisor = request.GET.get('supervisor')
            if supervisor and supervisor == str(modified_by.id):
                raise ValidationError('You have already '
                                      'respond to this request')

            old_status = self.instance.status
            if not old_status:
                return status
            if old_status == CONFIRMED:
                raise ValidationError(
                    f"The {old_status} requests cannot have their status changed."
                )
            if old_status == DECLINED and status == REQUESTED:
                return status
            if status_order.index(old_status) > status_order.index(status):
                raise ValidationError(
                    "The status updates must be in the order"
                    "Requested->Forwarded->Approved->Confirmed/Declined"
                    "->Confirmed"
                )
        return status

    def update(self, instance, validated_data):
        rec = self._recipient if self._recipient else get_overtime_recipient(
            self.instance, validated_data.get('status')
        )
        validated_data.update({
            'recipient': rec
        })
        obj = super().update(instance, validated_data)

        history_to = rec if obj.status != DECLINED else obj.overtime_entry.user

        request = self.context.get('request')
        if request and request.user:
            instance.overtime_histories.create(
                action_performed=instance.status,
                action_performed_by=request.user,
                action_performed_to=history_to,
                remark=validated_data.get('description')
            )
        return obj

    @staticmethod
    def get_work_shift(instance):
        wshift = getattr(instance.overtime_entry.timesheet, '_wshift', None)
        if wshift:
            start_time = wshift.start_time
            end_time = wshift.end_time
            name = wshift.name
        else:
            timesheet = instance.overtime_entry.timesheet
            try:
                start_time = timesheet.work_time.start_time
                end_time = timesheet.work_time.end_time
                name = timesheet.work_shift.name
            except AttributeError:
                return None
        return {
            'start_time': start_time,
            'end_time': end_time,
            'shift_name': name
        }


class BulkOvertimeClaimsSerializer(DynamicFieldsModelSerializer):
    claim = serializers.PrimaryKeyRelatedField(
        queryset=OvertimeClaim.objects.all()
    )

    class Meta:
        model = OvertimeClaim
        fields = (
            'claim', 'description', 'status'
        )

    def get_fields(self):
        fields = super().get_fields()

        fields['claim'] = serializers.PrimaryKeyRelatedField(
            queryset=OvertimeClaim.objects.all().filter(overtime_entry__user=self.request.user)
        )

        return fields

    def validate(self, attrs):
        status = attrs.get('status')

        instance = attrs.get('claim')

        old_status = instance.status

        if not old_status:
            return status

        if status != old_status and status != REQUESTED:
            raise ValidationError({'status': ["Can only change status to 'Requested'"]})

        if status == REQUESTED:
            ot_detail = attrs.get('claim').overtime_entry.overtime_detail
            claimable = ot_detail.get_claimable_overtime(format=False)
            claimed = ot_detail.claimed_overtime.total_seconds()
            diff = claimed - claimable
            if diff > 0:
                raise ValidationError(
                    f"Only {humanize_interval(claimable)} can be claimed."
                )
        return attrs


class BulkOvertimeUnExpireSerializer(DynamicFieldsModelSerializer):
    claims = serializers.PrimaryKeyRelatedField(
        queryset=OvertimeClaim.objects.all(),
        many=True
    )
    updated_count = serializers.ReadOnlyField()

    class Meta:
        model = OvertimeClaim
        fields = ('claims', 'updated_count')

    def create(self, validated_data):
        updated_count = OvertimeClaim.objects.filter(
            id__in=[obj.id for obj in validated_data.get('claims')],
            is_archived=True
        ).update(
            is_archived=False
        )
        return DummyObject(**validated_data, updated_count=updated_count)


class OvertimeClaimBulkSerializer(
    serializers.Serializer
):

    def get_fields(self):
        fields = super().get_fields()
        fields.update({
            'claims': BulkOvertimeClaimsSerializer(
                many=True,
                context=self.context
            )
        })
        return fields

    @transaction.atomic()
    def create(self, validated_data):
        # perform update of Overtime Claims
        claims = validated_data.get('claims')
        parsed_claims = list()
        for claim_data in claims:
            obj = claim_data.get('claim')
            if obj.id in parsed_claims:
                continue
            self.update_overtime(obj, claim_data)
            parsed_claims.append(obj.id)
        return DummyObject(**validated_data)

    def update_overtime(self, instance, validated_data):
        # get the authority for `action_performed_to`
        status = validated_data.get('status')
        action_performed_to = get_overtime_recipient(instance, status)
        request = self.context.get('request')

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        setattr(instance, 'recipient', action_performed_to)
        instance.save()

        if action_performed_to is None:
            raise ValidationError(
                    f"Cannot act as no supervisor is assigned for this action."
                )

        if request and request.user:
            instance.overtime_histories.create(
                action_performed=status,
                action_performed_by=request.user,
                action_performed_to=action_performed_to,
                remark=validated_data.get('description')
            )

        return instance


class OvertimeClaimHistorySerializer(DynamicFieldsModelSerializer):
    action_performed_by = UserThinSerializer()
    action_performed_to = UserThinSerializer()

    class Meta:
        model = OvertimeClaimHistory
        fields = (
            'action_performed_by', 'action_performed', 'action_performed_to',
            'remark', 'id', 'created_at'
        )
        read_only_fields = 'created_at',


class OvertimeActionsPerformedSerializer(OvertimeClaimHistorySerializer):
    overtime = OvertimeClaimSerializer()

    class Meta:
        model = OvertimeClaimHistory
        fields = (
            'overtime', 'remark', 'created_at'
        )


class OvertimeClaimEditHistorySerializer(DynamicFieldsModelSerializer):
    actor = UserThinSerializer()

    class Meta:
        model = OvertimeEntryDetailHistory
        fields = (
            'actor', 'previous_punch_in_overtime',
            'previous_punch_out_overtime', 'current_punch_in_overtime',
            'current_punch_out_overtime', 'remarks',
        )


class OverTimeClaimActionSerializer(DummySerializer):
    _APPROVE = 'approve'
    _DENY = 'deny'
    _FORWARD = 'forward'
    _CONFIRM = 'confirm'
    _UNCLAIMED = 'unclaimed'

    _ACTION_CHOICES = (
        (_APPROVE, _APPROVE),
        (_DENY, _DENY),
        (_FORWARD, _FORWARD),
        (_CONFIRM, _CONFIRM),
        (_UNCLAIMED, _UNCLAIMED)
    )

    ACTION_STATUS_MAP = {
        _APPROVE: APPROVED,
        _DENY: DECLINED,
        _FORWARD: FORWARDED,
        _CONFIRM: CONFIRMED,
        _UNCLAIMED: UNCLAIMED
    }

    action = serializers.ChoiceField(choices=_ACTION_CHOICES, write_only=True)
    remark = serializers.CharField(max_length=255, write_only=True)

    @property
    def mode(self):
        return self.context['view'].mode

    @property
    def request(self):
        return self.context['request']

    def get_fields(self):
        fields = super().get_fields()
        fields['overtime_claim'] = serializers.PrimaryKeyRelatedField(
            queryset=self.context.get('overtime_claims'),
            write_only=True
        )
        return fields

    def validate_action(self, action):
        if self.mode == 'supervisor' and action == self._CONFIRM:
            raise ValidationError(_('Supervisor can not confirm requests.'))
        elif self.mode == 'hr' and action == self._FORWARD:
            raise ValidationError(_('HR can not forward requests.'))
        return action

    def validate(self, attrs):
        status_order = [
            UNCLAIMED, REQUESTED, FORWARDED, APPROVED, CONFIRMED, DECLINED
        ]
        instance = attrs['overtime_claim']
        action = attrs['action']

        old_status = instance.status
        status = self.ACTION_STATUS_MAP[action]
        instance_user = instance.overtime_entry.user

        if old_status == status and action != self._FORWARD:
            raise ValidationError(_(f"Already {status}."))

        if self.mode == 'supervisor':
            if old_status == 'Unclaimed':
                immediate_subordinates_id = find_immediate_subordinates(self.request.user.id)
                if instance_user.id not in immediate_subordinates_id:
                    raise ValidationError(_("You are not the right supervisor"))

            elif instance.recipient != self.request.user:
                raise ValidationError(_("You are not the right recipient"))

            if old_status == APPROVED:
                raise ValidationError({'action': _(f"Already acted")})

            if not subordinates.authority_exists(
                instance_user, self.request.user, action
            ):
                raise serializers.ValidationError({
                    'action': _(f"You can not {action} this request.")
                })

            if action == self._FORWARD or old_status == UNCLAIMED:
                action_performed_to = helpers.get_overtime_recipient(instance, status, old_status)
                if action_performed_to is None:
                    raise ValidationError(
                        f"Cannot act as no supervisor is assigned for this action."
                    )
                attrs['action_performed_to'] = action_performed_to

        elif self.mode == 'hr'and old_status == UNCLAIMED :
            action_performed_to = helpers.get_overtime_recipient(instance, status, old_status)
            if action_performed_to is None:
                raise ValidationError(f"Cannot act as no supervisor is assigned for {instance.overtime_entry.user}")
            attrs['action_performed_to'] = action_performed_to

        # for all
        if old_status in [CONFIRMED, DECLINED]:
            raise ValidationError({'action': _(f"Already acted.")})

        if status_order.index(old_status) > status_order.index(status):
            raise ValidationError({
                'action': _(
                    "The status updates must be in the order"
                    "Requested->Forwarded->Approved->Confirmed/Declined"
                    "->Confirmed"
                )
            })
        return attrs

    def create(self, validated_data):
        instance = validated_data['overtime_claim']
        action = validated_data['action']
        remarks = validated_data['remark']
        old_status = instance.status

        instance.status = self.ACTION_STATUS_MAP[action]
        if (action == self._FORWARD or old_status == UNCLAIMED) \
            and validated_data.get('action_performed_to'):
            instance.recipient = validated_data['action_performed_to']

        instance.save()

        history_to = instance.recipient if instance.status != DECLINED \
            else instance.overtime_entry.user

        request = self.request
        if request and request.user:
            instance.overtime_histories.create(
                action_performed=instance.status,
                action_performed_by=request.user,
                action_performed_to=history_to,
                remark=remarks
            )
        return None


class OvertimeEntryImportSerializer(DynamicFieldsModelSerializer):
    user = serializers.CharField(max_length=255)
    # overtime_detail = OvertimeEntryDetailSerializer(
    #     fields=(
    #         'punch_in_overtime',
    #         'punch_out_overtime',
    #         # Auto Calculate below.
    #         # 'claimed_overtime',
    #         # 'normalized_overtime',
    #     )
    # )
    # overtime_claim = OvertimeClaimSerializer(
    #     fields=(
    #         'description',
    #         # 'status' # Lets make it confirmed.
    #         # recipient # lets make it 1st sup
    #     )
    # )
    # Because of the date's irregularity between str field and date field or datetime field.
    # We type-check date for accepting any format.
    # date = serializers.DateField(
    #     write_only=True,
    #     required=False,
    #     allow_null=True
    # )
    # punch_in_overtime = serializers.DurationField(
    #     allow_null=True,
    #     write_only=True,
    #     required=False
    # )
    # punch_out_overtime = serializers.DurationField(
    #     allow_null=True,
    #     write_only=True,
    #     required=False,
    # )
    description = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=True,
        allow_blank=True
    )

    class Meta:
        model = OvertimeEntry
        fields = (
            'user',
            # 'timesheet', # Parse from date.
            # 'overtime_settings  # use from att setting.
            # 'overtime_detail',
            # 'overtime_claim',
            'description',
        )

    def validate(self, attrs):
        attrs.update(
            self.parse_fields(
                'date', 'punch_in_overtime', 'punch_out_overtime'
            )
        )
        user = attrs.get('user')
        date = attrs.pop('date', None)
        if not user.attendance_setting.work_shift_for(date):
            raise ValidationError({
                'date': 'There is no shift for this date.'
            })
        timesheet = TimeSheet.objects.get_timesheet(
            user=user,
            timestamp=combine_aware(
                date,
                time(9, 0)
            )
        )
        if not timesheet:
            raise ValidationError(f"Valid TimeSheet for {date} could not be generated.")
        if getattr(timesheet, 'overtime', None):
            raise ValidationError(f"Overtime for {date} already exists.")
        self.validate_timesheet(timesheet)
        attrs['timesheet'] = timesheet
        return super().validate(attrs)

    @staticmethod
    def validate_timesheet(timesheet):
        exception = None
        if getattr(timesheet, 'overtime', None):
            exception = 'Overtime for this date exists.'
        if exception:
            raise ValidationError({'date': exception})

    def parse_field(self, field):
        field_value = self.initial_data.get(field)
        if not field_value:
            return False, 'This field is required.'
        if hasattr(self, f'validate_{field}'):
            field_value = getattr(self, f'validate_{field}')(field_value)
        else:
            field_value = field_value
        return True, field_value

    def parse_fields(self, *field_names):
        results = dict()
        errors = dict()
        for field in field_names:
            valid, value = self.parse_field(field)
            if valid:
                results[field] = value
            else:
                errors[field] = value
        if errors:
            raise ValidationError(errors)
        return results

    @transaction.atomic()
    def create(self, validated_data):
        entry_json = {
            'user': validated_data.get('user'),
            'timesheet': validated_data.get('timesheet'),
            'overtime_settings': self.overtime_setting(
                validated_data.get('user')
            ),
        }
        entry_object = super().create(entry_json)
        detail_json = {
            'overtime_entry': entry_object,
            'punch_in_overtime': validated_data.get('punch_in_overtime'),
            'punch_out_overtime': validated_data.get('punch_out_overtime'),
        }
        self.generate_overtime_entry_detail(detail_json)
        claim_json = dict(
            overtime_entry=entry_object,
            description=validated_data.get('description'),
            recipient=entry_object.user,
            status=CONFIRMED
        )
        self.generate_overtime_claim(claim_json)
        return entry_object

    def generate_overtime_claim(self, claim_data):
        overtime_claim = OvertimeClaim.objects.create(
            **claim_data
        )
        action_performed = overtime_claim.status
        overtime_claim.overtime_histories.create(
            action_performed=action_performed,
            action_performed_by=self.request.user,
            action_performed_to=overtime_claim.recipient,
            remark=f"Overtime {action_performed} by the System."
        )

    def validate_punch_in_overtime(self, punch_in_overtime):
        return self.parse_duration_field(punch_in_overtime)

    def validate_punch_out_overtime(self, punch_out_overtime):
        return self.parse_duration_field(punch_out_overtime)

    @staticmethod
    def validate_date(date):
        if isinstance(date, datetime.datetime):
            date_ = date.date()
        elif isinstance(date, datetime.date):
            date_ = date
        elif isinstance(date, str):
            try:
                date_ = parse(date)
                date_ = date_.date()
            except (TypeError, ValueError):
                raise ValidationError("Invalid date format was received.")
        else:
            raise ValidationError("Invalid date format was received.")
        validate_past_date(date_)
        return date_

    def validate_user(self, user):
        _user = User.objects.filter(Q(username=user) | Q(email=user)).first()
        if not self.overtime_setting(_user):
            raise ValidationError('Overtime Setting is not assigned.')
        return _user

    @staticmethod
    def overtime_setting(user):
        return nested_getattr(
            user, 'attendance_setting.overtime_setting'
        )

    @staticmethod
    def generate_overtime_entry_detail(detail_json):
        ot_detail = OvertimeEntryDetail.objects.create(**detail_json)
        ot_detail.claimed_overtime = ot_detail.claimable_overtime
        ot_detail.normalized_overtime = timedelta(
            seconds=ot_detail.normalized_overtime_seconds
        )
        ot_detail.save()

    @staticmethod
    def parse_duration_field(duration):
        # Use this into a new Field for import and use accordingly.
        if isinstance(duration, timedelta):
            return duration
        elif isinstance(duration, str):
            if re.fullmatch(pattern=r'\d\d:\d\d:\d\d', string=duration):
                hh, mm, ss = duration.split(':')
                return timedelta(
                    hours=int(hh),
                    minutes=int(mm),
                    seconds=int(ss)
                )
        elif isinstance(duration, time):
            return timedelta(
                hours=duration.hour,
                minutes=duration.minute,
                seconds=duration.second
            )
        raise ValidationError('Invalid Duration Format')
