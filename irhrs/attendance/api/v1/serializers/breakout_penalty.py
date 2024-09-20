from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import Serializer

from irhrs.attendance.constants import P_MONTH, P_DAYS, CONFIRMED
from irhrs.attendance.models import BreakOutPenaltySetting
from irhrs.attendance.models.breakout_penalty import TimeSheetUserPenalty, \
    TimeSheetUserPenaltyStatusHistory, PenaltyRule, BreakoutPenaltyLeaveDeductionSetting
from irhrs.attendance.utils.breakout_penalty_report import reduce_penalty_from_leave
from irhrs.core.constants.organization import LEAVE_DEDUCTION_ON_PENALTY
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer, DummySerializer
from irhrs.core.utils import HumanizedDurationField
from irhrs.core.utils.email import send_email_as_per_settings
from irhrs.core.validators import validate_natural_number
from irhrs.organization.models import FiscalYear, FiscalYearMonth
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer


class PenaltyRuleSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = PenaltyRule
        fields = (
            'id',
            'penalty_duration_in_days',
            'penalty_counter_value',
            'penalty_counter_unit',
            'calculation_type',
            'tolerated_duration_in_minutes',
            'tolerated_occurrences',
            'consider_late_in',
            'consider_early_out',
            'consider_in_between_breaks',
            'penalty_accumulates',
        )

    def get_fields(self):
        fields = super().get_fields()
        fields['id'] = serializers.PrimaryKeyRelatedField(
            # this serializer will be nested.
            # `id` isn't required, and will be created.
            # when available, this field will carry its own instance,
            # and its attributes will be updated.
            queryset=PenaltyRule.objects.filter(
                penalty_setting__organization=self.context['organization']
            ),
            allow_null=True,
            required=False,
        )
        return fields

    def validate(self, attrs):
        penalty_counter_unit = attrs.get('penalty_counter_unit')
        penalty_counter_value = attrs.get('penalty_counter_value')

        if penalty_counter_value <= 0:
            raise ValidationError(
                "Can not set aggregator to less than 0."
            )

        if penalty_counter_unit == P_MONTH and penalty_counter_value > 1:
            raise ValidationError(
                "Can not set aggregator for more than 1 month."
            )
        if penalty_counter_unit == P_DAYS and penalty_counter_value > 29:
            raise ValidationError(
                "Can not set aggregator for more than 29 days."
            )
        return super().validate(attrs)

    @staticmethod
    def validate_penalty_duration_in_days(penalty_duration_in_days):
        if penalty_duration_in_days <= 0:
            raise ValidationError(
                "Penalty Duration must be greater than 0."
            )
        if not (penalty_duration_in_days % 0.5 == 0):
            raise ValidationError(
                "Penalty Duration must be in increment of 0.5."
            )
        return penalty_duration_in_days

    @staticmethod
    def validate_tolerated_duration_in_minutes(threshold):
        if threshold < 0:
            raise ValidationError(
                "The threshold must be greater than 0."
            )
        return threshold


class BreakoutPenaltyLeaveDeductionSettingSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = BreakoutPenaltyLeaveDeductionSetting
        fields = (
            'id',
            'leave_type_to_reduce',
            # 'order',
        )

    def get_fields(self):
        fields = super().get_fields()
        fields['id'] = serializers.PrimaryKeyRelatedField(
            queryset=BreakoutPenaltyLeaveDeductionSetting.objects.filter(
                penalty_setting__organization=self.context['organization']
            ),
            allow_null=True,
            required=False,
        )
        return fields


class BreakOutPenaltySettingSerializer(DynamicFieldsModelSerializer):
    rules = PenaltyRuleSerializer(many=True)
    leave_types_to_reduce = BreakoutPenaltyLeaveDeductionSettingSerializer(many=True)

    class Meta:
        model = BreakOutPenaltySetting
        fields = (
            'id',
            'title',
            'leave_types_to_reduce',
            'rules',
            'is_archived',
        )

    def validate(self, attrs):
        exclude = {}
        title = attrs.get('title')
        org = self.context.get('organization')
        if self.instance:
            exclude = {'id': self.instance.id}
        if BreakOutPenaltySetting.objects.exclude(**exclude).filter(
            title=title, organization=org
        ).exists():
            raise ValidationError({
                'title': 'A penalty setting with title `%s` already exists for %s.' % (title, org)
            })
        return super().validate(attrs)

    def create(self, validated_data):
        validated_data['organization'] = self.context.get('organization')
        rules = validated_data.pop('rules')
        leave_types_to_reduce = validated_data.pop('leave_types_to_reduce')
        obj = super().create(validated_data)
        self.nested_update(obj, rules, 'rules')
        self.nested_update(obj, leave_types_to_reduce, 'leave_types_to_reduce')
        return obj

    def update(self, instance, validated_data):
        rules = validated_data.pop('rules')
        leave_types_to_reduce = validated_data.pop('leave_types_to_reduce')
        ret = super().update(instance, validated_data)
        self.nested_update(instance, rules, 'rules')
        self.nested_update(instance, leave_types_to_reduce, 'leave_types_to_reduce')
        return ret

    @staticmethod
    def nested_update(instance, data, relation):
        nested_manager = getattr(instance, relation)
        old_instances = set(nested_manager.all().values_list('id', flat=True))
        refreshed_objects = set()
        for datum in data:
            previous_instance = datum.pop('id', None)
            if previous_instance:
                for attr, value in datum.items():
                    setattr(previous_instance, attr, value)
                previous_instance.save()
                refreshed_objects.add(previous_instance.id)
            else:
                nested_manager.create(**datum)
        nested_manager.filter(
            id__in=old_instances-refreshed_objects
        ).delete()


class TimeSheetUserPenaltyStatusHistorySerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = TimeSheetUserPenaltyStatusHistory
        fields = (
            "status",
            "remarks",
            "old_loss_accumulated",
            "new_loss_accumulated",
            "old_lost_days_count",
            "new_lost_days_count",
            "old_penalty_accumulated",
            "new_penalty_accumulated",
        )


class TimeSheetUserPenaltySerializer(DynamicFieldsModelSerializer):
    user = UserThinSerializer(read_only=True)
    loss_accumulated = SerializerMethodField()
    histories = TimeSheetUserPenaltyStatusHistorySerializer(
        read_only=True,
        many=True
    )
    penalty_setting = serializers.SerializerMethodField()
    fiscal_month = serializers.SerializerMethodField()

    class Meta:
        model = TimeSheetUserPenalty
        fields = (
            'id',
            'user',
            'start_date',
            'end_date',
            'fiscal_month',
            'loss_accumulated',
            'penalty_accumulated',
            'lost_days_count',
            'rule',
            'status',
            'remarks',
            'penalty_setting',
            'histories',
        )
        read_only_fields = (
            'id',
            'user',
            'start_date',
            'end_date',
            'fiscal_month',
            'rule',
            'status',
            'histories',
            'loss_accumulated',
            'lost_days_count',
        )

    def get_loss_accumulated(self, instance):
        if instance.loss_accumulated:
            return instance.loss_accumulated.total_seconds() / 60

    def get_penalty_setting(self, instance):
        return instance.rule.penalty_setting.title

    def get_fiscal_month(self, instance):
        return {
            "id": instance.fiscal_month.id,
            "name": instance.fiscal_month.display_name,
            "fiscal_year": instance.fiscal_month.fiscal_year.name,
            "fiscal_year_id": instance.fiscal_month.fiscal_year.id
        } if instance.fiscal_month else None

    def validate(self, attrs):
        status = self.instance.status
        if status == CONFIRMED:
            raise ValidationError(
                "Confirmed penalty records cant be edited."
            )
        return attrs

    def update(self, instance, validated_data):
        remarks = validated_data['remarks']
        history = TimeSheetUserPenaltyStatusHistory(
            break_out_user_record=instance,
            status=instance.status,
            remarks=remarks,
            old_loss_accumulated=instance.loss_accumulated,
            old_lost_days_count=instance.lost_days_count,
            old_penalty_accumulated=instance.penalty_accumulated,
        )
        instance = super().update(instance, validated_data)
        instance.refresh_from_db()
        history.new_loss_accumulated = instance.loss_accumulated
        history.new_lost_days_count = instance.lost_days_count
        history.new_penalty_accumulated = instance.penalty_accumulated
        has_changed = any([
            getattr(history, o) != getattr(history, n)
            for o, n in
            (
                ('old_loss_accumulated', 'new_loss_accumulated'),
                ('old_lost_days_count', 'new_lost_days_count'),
                ('old_penalty_accumulated', 'new_penalty_accumulated'),
            )
        ])
        if has_changed:
            history.save()
        return instance


class TimeSheetUserPenaltyGroupByUserSerializer(serializers.Serializer):
    user = serializers.SerializerMethodField()
    total_loss_accumulated = serializers.SerializerMethodField()
    total_lost_days_count = serializers.SerializerMethodField()
    total_penalty_accumulated = serializers.SerializerMethodField()

    def get_user(self, obj):
        return UserThinSerializer(obj).data

    def get_total_loss_accumulated(self, obj):
        return str(
            round(
                obj.total_loss_accumulated.total_seconds() / 60, 2
            ) if obj.total_loss_accumulated is not None else 0
        )

    def get_total_lost_days_count(self, obj):
        return obj.total_lost_days_count

    def get_total_penalty_accumulated(self, obj):
        return obj.total_penalty_accumulated


# New Bulk Action Serializer Created
# class BreakOutPenaltyActionSerializer(Serializer):
#     remarks = serializers.CharField(
#         max_length=255
#     )
#
#     def validate(self, attrs):
#         status = self.instance.status
#         if status == CONFIRMED:
#             raise ValidationError(
#                 "Processed penalty records cant be edited."
#             )
#         return attrs
#
#     def update(self, instance, validated_data):
#         remarks = validated_data.get('remarks')
#         status = self.context.get('status')
#         instance.status = status
#         instance.remarks = remarks
#         instance.save()
#         TimeSheetUserPenaltyStatusHistory.objects.create(
#             break_out_user_record=instance,
#             status=status,
#             remarks=remarks,
#             old_loss_accumulated=instance.loss_accumulated,
#             new_loss_accumulated=instance.loss_accumulated,
#             old_lost_days_count=instance.lost_days_count,
#             new_lost_days_count=instance.lost_days_count,
#             old_penalty_accumulated=instance.penalty_accumulated,
#             new_penalty_accumulated=instance.penalty_accumulated,
#         )
#         if instance.status == CONFIRMED:
#             reduce_penalty_from_leave(instance)
#         return instance
#
#     def create(self, validated_data):
#         pass


class BreakOutPenaltyBulkActionSerializer(Serializer):
    _CONFIRMED = 'Confirmed'
    _CANCELLED = 'Cancelled'
    _ACTION_CHOICES = (
        (_CONFIRMED, _CONFIRMED),
        (_CANCELLED, _CANCELLED)
    )
    status = serializers.ChoiceField(choices=_ACTION_CHOICES, write_only=True)
    remarks = serializers.CharField(max_length=255, write_only=True)

    def get_fields(self):
        fields = super().get_fields()
        fields['penalty'] = serializers.PrimaryKeyRelatedField(
            queryset=TimeSheetUserPenalty.objects.filter(
                user__detail__organization=self.context.get('organization')
            ).select_related(
                'user',
                'user__detail',
                'user__detail__employment_level',
                'user__detail__job_title',
                'user__detail__organization',
                'user__detail__division',
                'fiscal_month',
                'fiscal_month__fiscal_year',
                'rule',
                'rule__penalty_setting'
            ),
            write_only=True
        )
        return fields

    def validate(self, attrs):
        penalty = attrs['penalty']
        if penalty.status == CONFIRMED:
            raise ValidationError(
                "Processed penalty records cant be edited."
            )
        return attrs

    def create(self, validated_data):
        penalty = validated_data.get('penalty')
        remarks = validated_data.get('remarks')
        status = validated_data.get('status')

        penalty.status = status
        penalty.remarks = remarks
        penalty.save()
        TimeSheetUserPenaltyStatusHistory.objects.create(
            break_out_user_record=penalty,
            status=status,
            remarks=remarks,
            old_loss_accumulated=penalty.loss_accumulated,
            new_loss_accumulated=penalty.loss_accumulated,
            old_lost_days_count=penalty.lost_days_count,
            new_lost_days_count=penalty.lost_days_count,
            old_penalty_accumulated=penalty.penalty_accumulated,
            new_penalty_accumulated=penalty.penalty_accumulated,
        )
        if penalty.status == CONFIRMED:
            reduce_penalty_from_leave(penalty)
            send_email_as_per_settings(
                recipients=self.context.get('hrs'),
                subject=f"Leave balance deduction of {penalty.user}",
                email_text=(
                    f'Leave balance of {penalty.user} has decremented by '
                    f'{penalty.penalty_accumulated} due to penalty.'
                ),
                email_type=LEAVE_DEDUCTION_ON_PENALTY
            )
        return penalty


class FiscalMonthSelectionSerializer(DummySerializer):
    def get_fields(self):
        return {
            'fiscal_year': serializers.SlugRelatedField(
                slug_field='slug',
                queryset=FiscalYear.objects.filter(
                    organization=self.context['organization']
                ),
            ),
            'fiscal_month': serializers.PrimaryKeyRelatedField(
                queryset=FiscalYearMonth.objects.filter(
                    fiscal_year__organization=self.context['organization']
                ).select_related('fiscal_year'),
            )
        }

    def validate(self, attrs):
        fiscal_year = attrs.get('fiscal_year')
        fiscal_month = attrs.get('fiscal_month')
        if fiscal_month not in fiscal_year.fiscal_months.all():
            raise ValidationError({
                'fiscal_month': "Fiscal Month was not found for Fiscal Year: %s" % fiscal_year.name
            })
        return super().validate(attrs)
