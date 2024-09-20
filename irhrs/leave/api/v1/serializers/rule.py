from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils import HumanizedDurationField
from django.utils.translation import gettext_lazy as _
from irhrs.leave.constants.model_constants import EXPIRED, IDLE, EXCLUDE_HOLIDAY_AND_OFF_DAY, \
    CREDIT_HOUR, DAYS, GENERAL, YEARS_OF_SERVICE, COMPENSATORY
from irhrs.leave.models import LeaveRule, AccumulationRule, RenewalRule, \
    DeductionRule, LeaveType

from irhrs.leave.models.rule import (
    PriorApprovalRule, YearsOfServiceRule,
    CompensatoryLeave, CompensatoryLeaveCollapsibleRule, 
    LeaveIrregularitiesRule, TimeOffRule, CreditHourRule
)
from irhrs.leave.utils.validations import (
    LeaveRuleValidator,
    get_prior_approval_rule_errors,
    get_compensatory_rule_errors
)

class AccumulationRuleSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = AccumulationRule
        exclude = ('rule',)

    def validate(self, attrs):
        duration_type = attrs.get('duration_type')

        errors = dict()

        if duration_type != DAYS:
            for field in [
                'exclude_absent_days',
                'exclude_off_days',
                'count_if_present_in_off_day',
                'exclude_holidays',
                'count_if_present_in_holiday',
                'exclude_unpaid_leave',
                'exclude_paid_leave',
                'exclude_half_leave'
            ]:
                if attrs.get(field):
                    errors[field] = _("This field can not be set when duration is not days.")

        if errors:
            raise ValidationError(errors)

        for dependent, dependency in (
            ('count_if_present_in_off_day', 'exclude_off_days'),
            ('count_if_present_in_holiday', 'exclude_holidays')
        ):
            if attrs.get(dependent) and not attrs.get(dependency):
                errors[dependent] = _(
                    f"This value can not be set when {dependency.replace('_', ' ')} is not set."
                )

        if errors:
            raise ValidationError(errors)

        if attrs.get('exclude_half_leave') and not (
            attrs.get('exclude_unpaid_leave') or attrs.get('exclude_paid_leave')
        ):
            raise ValidationError({'exclude_half_leave': _(
                "To set this value at least one of 'exclude unpaid leave' or 'exclude paid leave'"
                "must be set."
            )})
        return attrs


class RenewalRuleSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = RenewalRule
        exclude = ('rule',)


class DeductionRuleSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = DeductionRule
        exclude = ('rule',)


class YearsOfServiceRuleSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = YearsOfServiceRule
        exclude = ('rule',)


class CompensatoryLeaveSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = CompensatoryLeave
        fields = (
            'balance_to_grant', 'hours_in_off_day'
        )

class CompensatoryLeaveCollapsibleRuleSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = CompensatoryLeaveCollapsibleRule
        fields = (
            'collapse_after', 'collapse_after_unit'
        )

class LeaveIrregularitiesSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = LeaveIrregularitiesRule
        fields = (
            'weekly_limit', 'fortnightly_limit', 'monthly_limit',
            'quarterly_limit', 'semi_annually_limit', 'annually_limit',
        )

    def validate(self, attrs):
        weekly_limit = attrs.get('weekly_limit', 0) or 0
        fortnightly_limit = attrs.get(
            'fortnightly_limit', weekly_limit
        ) or weekly_limit
        monthly_limit = attrs.get(
            'monthly_limit', fortnightly_limit
        ) or fortnightly_limit
        quarterly_limit = attrs.get(
            'quarterly_limit', monthly_limit
        ) or monthly_limit
        semi_annually_limit = attrs.get(
            'semi_annually_limit', quarterly_limit
        ) or quarterly_limit
        annually_limit = attrs.get(
            'annually_limit', semi_annually_limit
        ) or semi_annually_limit
        if not (
                weekly_limit
                <= fortnightly_limit
                <= monthly_limit
                <= quarterly_limit
                <= semi_annually_limit
                <= annually_limit
        ):
            raise ValidationError(
                'The higher periods limits must be greater than lower '
                'periods.'
            )
        return attrs


class TimeOffRuleSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = TimeOffRule
        exclude = ('rule',)


class CreditHourRuleSerializer(DynamicFieldsModelSerializer):
    minimum_request_duration = HumanizedDurationField(required=False, allow_null=True)
    maximum_request_duration = HumanizedDurationField(required=False, allow_null=True)

    class Meta:
        model = CreditHourRule
        exclude = ('rule',)


class PriorApprovalRuleSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = PriorApprovalRule
        fields = (
            'prior_approval_request_for', 'prior_approval',
            'prior_approval_unit'
        )


class LeaveRuleSerializer(DynamicFieldsModelSerializer):
    accumulation_rule = AccumulationRuleSerializer(
        required=False, allow_null=True
    )
    renewal_rule = RenewalRuleSerializer(
        required=False, allow_null=True
    )
    deduction_rule = DeductionRuleSerializer(
        required=False, allow_null=True
    )
    yos_rule = YearsOfServiceRuleSerializer(
        required=False, allow_null=True
    )
    compensatory_rules = CompensatoryLeaveSerializer(
        required=False, allow_null=True, many=True
    )
    leave_collapsible_rule = CompensatoryLeaveCollapsibleRuleSerializer(
        required=False, allow_null=True
    )
    leave_irregularity = LeaveIrregularitiesSerializer(
        required=False, allow_null=True
    )
    time_off_rule = TimeOffRuleSerializer(
        required=False, allow_null=True
    )
    credit_hour_rule = CreditHourRuleSerializer(
        required=False, allow_null=True
    )
    adjacent_offday_inclusive_leave_types = serializers.PrimaryKeyRelatedField(
        queryset=LeaveType.objects.all(),
        many=True,
        required=False,
        allow_null=True,
        allow_empty=True,
    )
    prior_approval_rules = PriorApprovalRuleSerializer(
        required=False, allow_null=True, many=True
    )

    class Meta:
        model = LeaveRule
        fields = '__all__'
        extra_kwargs = {
            'depletion_leave_types': {
                'allow_empty': True
            },
        }
        create_only_fields = 'cloned_from',

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method == 'GET':
            fields['adjacent_offday_inclusive_leave_types'] = serializers.SerializerMethodField()
        return fields

    def validate(self, attrs):
        leave_type = attrs.get('leave_type')
        master_setting_status = leave_type.master_setting.status
        holiday_inclusive = leave_type.master_setting.holiday_inclusive
        inclusive_leave = attrs.get('inclusive_leave')
        inclusive_leave_number = attrs.get('inclusive_leave_number')
        update = bool(self.instance)
        errors = dict()
        if master_setting_status == EXPIRED:
            raise ValidationError(
                "Can not work on expired master settings."
            )
        if update and master_setting_status != IDLE:
            raise ValidationError(
                "Can not update leave rules unless master setting is idle."
            )

        # validate name here.
        queryset = LeaveRule.objects.filter(
            name__iexact=attrs.get('name'),
            leave_type=leave_type
        )
        if self.instance:
            queryset = queryset.exclude(
                pk=self.instance.pk
            )
        if queryset.exists():
            raise ValidationError({
                'name': 'A leave rule with this name already exists for this leave type.'
            })

        default_null_fields = [
            'required_experience',
            'required_experience_duration',
            'require_docs_for',
            'limit_leave_occurrence_duration',
            'limit_leave_occurrence_duration_type',
            'limit_leave_occurrence',
            'min_balance',
            'max_balance',
            'beyond_limit',
            'minimum_continuous_leave_length',
            'maximum_continuous_leave_length',
            'year_of_service'
        ]

        for field in default_null_fields:
            if field not in attrs:
                attrs[field] = None

        leave_type_category = leave_type.category
        # validate if holiday_inclusive is checked and inclusive_leave is blank
        # Also, if the leave_type_category is `Credit Hour` then ignore inclusive_leave
        if holiday_inclusive and leave_type_category != CREDIT_HOUR and not inclusive_leave:
            errors.update({
                "inclusive_leave": _("This field may not be blank")
            })

        if holiday_inclusive and (
            inclusive_leave and inclusive_leave != EXCLUDE_HOLIDAY_AND_OFF_DAY
        ) and not inclusive_leave_number:
            errors.update({
                "inclusive_leave_number": _("This field may not be blank")
            })

        adjacent_offday_inclusive = attrs.get('adjacent_offday_inclusive')
        adjacent_allowed_leave_type_categories = (GENERAL, YEARS_OF_SERVICE, COMPENSATORY)
        if (
            adjacent_offday_inclusive
            and leave_type.category not in adjacent_allowed_leave_type_categories
        ):
            errors['adjacent_offday_inclusive'] = _(
                "This field may be set on the following leave types only: %s" % ", ".join(
                    adjacent_allowed_leave_type_categories
                )
            )
        _leave_types = attrs.get('adjacent_offday_inclusive_leave_types')
        if _leave_types and leave_type in _leave_types:
            errors['adjacent_offday_inclusive_leave_types'] = 'Cannot select self.'
        if errors:
            raise ValidationError(errors)
        
        prior_approval_rules = attrs.get('prior_approval_rules')
        if prior_approval_rules:
            has_error, prior_errors = get_prior_approval_rule_errors(prior_approval_rules)
            if has_error:
                raise ValidationError(prior_errors)
            

        compensatory_rules = attrs.get('compensatory_rules')
        if compensatory_rules:
            get_errors, compensatory_errors = get_compensatory_rule_errors(
                compensatory_rules)
            if get_errors:
                raise ValidationError(
                    compensatory_errors
                )
        validator = LeaveRuleValidator(
            organization=self.context.get('organization'),
            initial_data=attrs)
        validator.validate()

        # This step ensures that during master settings clone,
        # Leave Types from old master Setting should not be valid.
        depletion_leave_types = attrs.get('depletion_leave_types')
        master_settings = set(map(lambda lt: lt.master_setting, depletion_leave_types))
        if master_settings - {leave_type.master_setting}:
            raise ValidationError({
                'depletion_leave_types':
                    'Depletion leave Types Should be selected from same master settings only.'
            })

        year_of_service = attrs.get('year_of_service')
        min_continuous_leave_length = attrs.get('minimum_continuous_leave_length')
        max_continuous_leave_length = attrs.get('maximum_continuous_leave_length')

        if year_of_service and year_of_service > 0:
            if not min_continuous_leave_length and not max_continuous_leave_length:
                raise ValidationError({
                    'detail': 'You must provide either maximum continuous leave'
                              ' length or minimum continuous leave length.'
                })
        return attrs

    def validate_leave_type(self, leave_type):
        view = self.context.get("view")
        organization = view.get_organization() if view else None
        if leave_type.master_setting.organization != organization:
            raise ValidationError("This type does not exist for the organization.")
        return leave_type

    def create(self, validated_data):
        accumulation_rule = validated_data.pop('accumulation_rule', None)
        renewal_rule = validated_data.pop('renewal_rule', None)
        deduction_rule = validated_data.pop('deduction_rule', None)
        yos_rule = validated_data.pop('yos_rule', None)
        compensatory_rules = validated_data.pop('compensatory_rules', None)
        leave_collapsible_rule = validated_data.pop('leave_collapsible_rule', None)
        leave_irregularity = validated_data.pop('leave_irregularity', None)
        irregularity_report = validated_data.get('leave_irregularity')
        time_off_rule = validated_data.pop('time_off_rule', None)
        credit_hour_rule = validated_data.pop('credit_hour_rule', None)
        adjacent_leave_types = validated_data.pop('adjacent_offday_inclusive_leave_types', None)
        prior_approval_rules = validated_data.pop('prior_approval_rules', None)

        rule = super().create(validated_data)

        if irregularity_report and leave_irregularity:
            LeaveIrregularitiesRule.objects.create(
                leave_rule=rule,
                **leave_irregularity
            )

        if accumulation_rule:
            AccumulationRule.objects.create(rule=rule, **accumulation_rule)

        if renewal_rule:
            RenewalRule.objects.create(rule=rule, **renewal_rule)

        if deduction_rule:
            DeductionRule.objects.create(rule=rule, **deduction_rule)

        if yos_rule:
            YearsOfServiceRule.objects.create(
                rule=rule,
                **yos_rule
            )
        if leave_collapsible_rule:
            CompensatoryLeaveCollapsibleRule.objects.create(
                    rule=rule,
                    **leave_collapsible_rule
            )

        if compensatory_rules:
                CompensatoryLeave.objects.bulk_create([
                    CompensatoryLeave(
                        rule=rule,
                        **compensatory_rule
                    ) for compensatory_rule in compensatory_rules
                ])

        if time_off_rule:
            TimeOffRule.objects.create(rule=rule, **time_off_rule)

        if credit_hour_rule:
            CreditHourRule.objects.create(rule=rule, **credit_hour_rule)

        if prior_approval_rules:
            for prior_approval_rule in prior_approval_rules:
                rule.prior_approval_rules.create(
                    **prior_approval_rule
                )
                
        if adjacent_leave_types:
            for order, leave_type in enumerate(adjacent_leave_types):
                rule.adjacent_offday_inclusive_leave_types.create(
                    leave_rule=rule,
                    order_field=order,
                    leave_type=leave_type
                )
        return rule

    def update(self, instance, validated_data):
        rules_for_update = [
            'accumulation_rule', 'renewal_rule', 'deduction_rule', 'yos_rule',
            'leave_irregularity', 'time_off_rule','leave_collapsible_rule'
        ]
        for attr in rules_for_update:
            if attr not in validated_data:
                # rules are not sent, delete if exists.
                if hasattr(instance, attr):
                    nested_rule = getattr(instance, attr)
                    nested_rule.delete()
                    setattr(instance, attr, None)
                    instance.save()

        accumulation_rule = validated_data.pop('accumulation_rule', None)
        renewal_rule = validated_data.pop('renewal_rule', None)
        deduction_rule = validated_data.pop('deduction_rule', None)
        yos_rule = validated_data.pop('yos_rule', None)
        compensatory_rules = validated_data.pop('compensatory_rules', None)
        leave_collapsible_rule = validated_data.pop('leave_collapsible_rule',None)
        leave_irregularity = validated_data.pop('leave_irregularity', None)
        time_off_rule = validated_data.pop('time_off_rule', None)
        credit_hour_rule = validated_data.pop('credit_hour_rule', None)
        adjacent_leave_types = validated_data.pop(
            'adjacent_offday_inclusive_leave_types', None
        )
        prior_approval_rules = validated_data.pop('prior_approval_rules', None)

        if leave_irregularity:
            if getattr(instance, "leave_irregularity", None):
                self.update_model(instance.leave_irregularity,
                                  leave_irregularity)
            else:
                setattr(
                    instance, 'leave_irregularity',
                    LeaveIrregularitiesRule.objects.create(
                        leave_rule=instance,
                        **leave_irregularity)
                )
                instance.save()
        else:
            # delete if not passed
            if getattr(instance, "leave_irregularity", None):
                instance.leave_irregularity.delete()

        if accumulation_rule:
            if hasattr(instance, "accumulation_rule"):
                self.update_model(instance.accumulation_rule, accumulation_rule)
            else:
                AccumulationRule.objects.create(rule=instance,
                                                **accumulation_rule)
        else:
            if hasattr(instance, "accumulation_rule"):
                instance.accumulation_rule.delete()

        if renewal_rule:
            if hasattr(instance, "renewal_rule"):
                self.update_model(instance.renewal_rule, renewal_rule)
            else:
                RenewalRule.objects.create(rule=instance, **renewal_rule)
        else:
            if hasattr(instance, "renewal_rule"):
                instance.renewal_rule.delete()
        if deduction_rule:
            if hasattr(instance, "deduction_rule"):
                self.update_model(instance.deduction_rule, deduction_rule)
            else:
                DeductionRule.objects.create(rule=instance, **deduction_rule)
        else:
            if hasattr(instance, "deduction_rule"):
                instance.deduction_rule.delete()

        if yos_rule:
            if hasattr(instance, "yos_rule"):
                self.update_model(instance.yos_rule, yos_rule)
            else:
                YearsOfServiceRule.objects.create(rule=instance, **yos_rule)
        else:
            if hasattr(instance, "yos_rule"):
                instance.yos_rule.delete()
        
        if leave_collapsible_rule:
            if hasattr(instance, "leave_collapsible_rule"):
                self.update_model(instance.leave_collapsible_rule, leave_collapsible_rule)
            else: 
                CompensatoryLeaveCollapsibleRule.objects.create(
                        rule=instance,
                        **leave_collapsible_rule
                    )
        else:
            CompensatoryLeaveCollapsibleRule.objects.filter(
                rule=instance
            ).delete()
        
        instance.compensatory_rules.all().delete()
        if compensatory_rules:
               CompensatoryLeave.objects.bulk_create([
                    CompensatoryLeave(
                        rule=instance,
                        **compensatory_rule
                    )  for compensatory_rule in compensatory_rules
               ])

        if credit_hour_rule:
            if hasattr(instance, "credit_hour_rule"):
                self.update_model(instance.credit_hour_rule, credit_hour_rule)
            else:
                CreditHourRule.objects.create(rule=instance, **credit_hour_rule)
        else:
            if hasattr(instance, "credit_hour_rule"):
                instance.credit_hour_rule.delete()

        if time_off_rule:
            if hasattr(instance, "time_off_rule"):
                self.update_model(instance.time_off_rule, time_off_rule)
            else:
                TimeOffRule.objects.create(rule=instance,
                                           **time_off_rule)
        else:
            if hasattr(instance, "time_off_rule"):
                instance.time_off_rule.delete()
        
        instance.prior_approval_rules.all().delete()
        if prior_approval_rules:
            for prior_approval_rule in prior_approval_rules:
                instance.prior_approval_rules.create(
                    **prior_approval_rule
                )
                
        if adjacent_leave_types:
            instance.adjacent_offday_inclusive_leave_types.all().delete()
            for order, leave_type, in enumerate(adjacent_leave_types):
                instance.adjacent_offday_inclusive_leave_types.create(
                    leave_rule=instance,
                    order_field=order,
                    leave_type=leave_type
                )
        return super().update(instance, validated_data)

    @staticmethod
    def update_model(instance, data):
        for field, value in data.items():
            setattr(instance, field, value)
        instance.save()
        return instance

    @staticmethod
    def get_adjacent_offday_inclusive_leave_types(leave_rule):
        return leave_rule.adjacent_offday_inclusive_leave_types.values_list(
            'leave_type', flat=True
        )
