"""@irhrs_docs"""
from datetime import timedelta
from functools import reduce

from django.forms.utils import pretty_name
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _



def raise_no_exception(func, *args, **kwargs):
    """
    Catches ValidationError and returns error message
    """
    try:
        func(*args, **kwargs)
        return

    except ValidationError as err:
        error = err.args[0]
        return error if isinstance(error, list) else _(error)


def validate_required_together(fields, data, errors=None):
    """
    Validate require together
    appends to error if any of the field is not set
    NOTE: allows all fields empty or None or 0
    """
    errors = errors or dict()

    filled = []
    unfilled = []

    for field in fields:
        if data.get(field):
            filled.append(field)
        else:
            unfilled.append(field)

    # if either if filled or unfilled is empty then is valid
    if filled and unfilled:
        for field in unfilled:
            errors.update({field: [
                f'{field.title().replace("_", " ")} is required'
            ]})
    return errors


def validate_at_least_one_required(fields, data, errors=None, prefix=None):
    errors = errors or dict()
    non_field_errors = errors.get('non_field_errors', [])
    if not reduce(
            lambda value, field: value or data.get(field),
            [False] + fields
    ):
        fields_title = ", ".join(
            [field.title().replace("_", " ") for field in fields]
        )
        message = f'At least one of {fields_title} must be set.'
        if prefix:
            message = prefix + message
        non_field_errors.append(message)

    if non_field_errors:
        errors["non_field_errors"] = non_field_errors

    return errors


class LeaveRuleValidator:

    def __init__(self, organization, initial_data):
        self.errors = dict()
        self.initial_data = initial_data
        initial_data = dict(initial_data)
        self.organization = organization

        self.accumulation_rule = initial_data.pop('accumulation_rule', None)
        self.renewal_rule = initial_data.pop('renewal_rule', None)
        self.deduction_rule = initial_data.pop('deduction_rule', None)
        self.yos_rule = initial_data.pop('yos_rule', None)
        self.compensatory_rule = initial_data.pop('compensatory_rule', None)
        self.time_off_rule = initial_data.pop('time_off_rule', None)
        self.credit_hour_rule = initial_data.pop('credit_hour_rule', None)
        self.irregularities = initial_data.pop('leave_irregularity', None)

        self.rule_data = initial_data
        self.master_setting = getattr(
            self.rule_data.get('leave_type'),
            'master_setting'
        )

    def validate(self):
        # TODO: @Shital validate field values also
        # TODO: @Shital validate fields from leave type as well
        self.validate_with_master_settings()

        if self.accumulation_rule:
            self.validate_accumulation()

        if self.renewal_rule:
            self.validate_renewal()

        if self.deduction_rule:
            self.validate_deduction()

        if self.compensatory_rule:
            self.validate_compensatory()

        if self.yos_rule:
            self.validate_yos()

        if self.time_off_rule:
            self.validate_time_off()

        if self.credit_hour_rule:
            self.validate_credit_hour()

        if self.errors:
            raise serializers.ValidationError(self.errors)

        self.validate_required_together()
        self.validate_at_least_one_required()

        if self.errors:
            raise serializers.ValidationError(self.errors)

    def validate_with_master_settings(self):

        master_setting_self_map = (
            # master setting field, self_field
            ("accumulation", "accumulation_rule", ),
            ("renewal", "renewal_rule",),
            ("time_off", "time_off_rule", ),
            ("leave_irregularities", "irregularities",),
            ("years_of_service", "yos_rule",),
            ("compensatory", "compensatory_rule",),
            ("deductible", "deduction_rule", ),
            ("credit_hour", "credit_hour_rule"),
        )
        master_setting_rule_data_map = (
            # master setting field, leave rule fields
            ('leave_limitations', (
                'min_balance',
                'max_balance',
                'limit_leave_to',
                'limit_leave_duration',
                'limit_leave_duration_type',
                'limit_leave_occurrence',
                'limit_leave_occurrence_duration',
                'limit_leave_occurrence_duration_type',
                'maximum_continuous_leave_length',
                'minimum_continuous_leave_length',
            )),
            ('occurrences', (
                'limit_leave_occurrence',
                'limit_leave_occurrence_duration',
                'limit_leave_occurrence_duration_type',
            )),
            ('beyond_balance', (
                'can_apply_beyond_zero_balance',
                'beyond_limit',
            )),
            ('proportionate_leave', (
                'proportionate_on_joined_date',
                'proportionate_on_contract_end_date',
            )),
            ('depletion_required', (
                'depletion_required',
                'depletion_leave_types',
            )),
            ('require_experience', (
                'required_experience',
                'required_experience_duration',
            )),
            ('require_time_period', (
                'start_date',
                'end_date',
            )),
            ('require_prior_approval', (
                'require_prior_approval',
            )),
            ('require_document', (
                'require_docs',
                'require_docs_for',
            )),
            ('holiday_inclusive', (
                'holiday_inclusive',
            )),
            ('employees_can_apply', (
                'employee_can_apply',
            )),
            ('admin_can_assign', (
                'admin_can_assign',
            )),
            ('half_shift_leave', (
                'can_apply_half_shift',
            )),
            ('continuous', (
                'maximum_continuous_leave_length',
                'minimum_continuous_leave_length',
            ))
        )

        for master_setting_field, rule_field in master_setting_self_map:
            if getattr(self, rule_field, None) and not getattr(
                self.master_setting, master_setting_field, None
            ):
                self.errors.update({
                    rule_field: [
                        f'{pretty_name(rule_field)} not enabled in master setting.'
                    ]
                })
        for master_setting_field, rule_fields in master_setting_rule_data_map:
            if not getattr(self.master_setting, master_setting_field, None):
                for field in rule_fields:
                    self.error_if_true(field, master_setting_field=master_setting_field)

        # couple of exceptions
        if self.rule_data.get('is_paid') and not self.master_setting.paid:
            self.errors.update({'is_paid': ['Paid is not enabled in master setting']})

        if not self.rule_data.get('is_paid') and not self.master_setting.unpaid:
            self.errors.update({'is_paid': ['Unpaid is not enabled in master setting']})

        if self.errors:
            raise serializers.ValidationError(self.errors)

    def validate_required_together(self):
        required_together = [
            (
                'limit_leave_to',
                'limit_leave_duration',
                'limit_leave_duration_type'
            ),
            (
                'limit_leave_occurrence',
                'limit_leave_occurrence_duration',
                'limit_leave_occurrence_duration_type'
            ),
            (
                'required_experience',
                'required_experience_duration'
            ),
            (
                'require_prior_approval'
            ),
            (
                'require_docs',
                'require_docs_for'
            ),
            (
                'depletion_required',
                'depletion_leave_types'
            ),
            (
                'adjacent_offday_inclusive',
                'adjacent_offday_inclusive_type',
                'adjacent_offday_inclusive_leave_types',
            )
        ]
        for fields in required_together:
            self.errors = validate_required_together(
                fields=fields,
                data=self.rule_data,
                errors=self.errors
            )

    def validate_at_least_one_required(self):
        required_at_least_one = [
            ["employee_can_apply", "admin_can_assign"]
        ]
        for fields in required_at_least_one:
            self.errors = validate_at_least_one_required(fields,
                                                         self.rule_data,
                                                         self.errors)

    def validate_accumulation(self):
        # -- Master Setting currently has no related fields in accumulation
        pass

    def validate_renewal(self):
        errors = dict()
        master_settings_renewal_map = (
            ('carry_forward', 'max_balance_forwarded'),
            ('encashment', 'max_balance_encashed'),
            ('collapsible', 'is_collapsible')
        )
        for master_setting_field, rule_field in master_settings_renewal_map:
            if not getattr(self.master_setting, master_setting_field, None):
                self.error_if_true(
                    rule_field,
                    data=self.accumulation_rule,
                    errors=errors,
                    master_setting_field=master_setting_field
                )

        if errors:
            self.errors.update({'renewal_rule': errors})
        else:
            errors = validate_at_least_one_required(
                ['max_balance_encashed', 'max_balance_forwarded',
                 'is_collapsible'],
                self.renewal_rule,
                errors,
                "Renewal Rule: "
            )
            if errors:
                self.errors.update({'renewal_rule': errors})

    def validate_deduction(self):
        pass

    def validate_yos(self):
        errors = dict()
        if not self.master_setting.collapsible:
            self.error_if_true(
                'collapse_after',
                data=self.yos_rule,
                errors=errors
            )
            self.error_if_true(
                'collapse_after_unit',
                data=self.yos_rule,
                errors=errors
            )
        if errors:
            self.errors.update({'yos_rule': errors})

    def validate_compensatory(self):
        errors = dict()
        if not self.master_setting.collapsible:
            self.error_if_true(
                'collapse_after',
                data=self.compensatory_rule,
                errors=errors
            )
            self.error_if_true(
                'collapse_after_unit',
                data=self.compensatory_rule,
                errors=errors
            )
        if errors:
            self.errors.update({'compensatory_rule': errors})

    def validate_time_off(self):
        errors = dict()

        leave_type = self.rule_data.get('leave_type')
        if self.time_off_rule.get('leave_type') == leave_type:
            errors.update({'leave_type': ['Can not set to same leave '
                                          'type']})
        if errors:
            self.errors.update({
                'time_off': errors
            })

    def validate_credit_hour(self):

        def get_value(attr):
            return self.credit_hour_rule.get(attr)

        errors = dict()
        flag_is_set_map = (
            ('minimum_request_duration_applicable', 'minimum_request_duration'),
            ('maximum_request_duration_applicable', 'maximum_request_duration'),
        )
        for flag, is_set in flag_is_set_map:
            if get_value(flag) and not get_value(is_set):
                # Flag was set, Value was not
                errors[is_set] = '{} needs to be set.'.format(is_set)
            elif not get_value(flag) and get_value(is_set):
                # Flag was not set, value was
                errors[is_set] = '{} can not be set.'.format(is_set)

        # Ensure Maximum Leave Limit does not exceed 24 hours.
        cap_limit = get_value('maximum_request_duration')
        if cap_limit and cap_limit > timedelta(hours=24):
            errors['maximum_request_duration'] = 'Maximum limit can not be more than 24 hours.'

        if get_value('minimum_request_duration') and get_value('maximum_request_duration'):
            if get_value('minimum_request_duration') > get_value('maximum_request_duration'):
                if 'maximum_request_duration' not in errors:
                    errors['maximum_request_duration'] = 'Maximum limit needs'
                    'to be smaller than minimum limit.'
        if errors:
            self.errors.update({
                'credit_hour': errors
            })

    def error_if_true(self, field, data=None, errors=None, master_setting_field=None):
        data = data or self.rule_data
        if errors is None:
            errors = self.errors
        if data.get(field):
            error = self.errors.get(field, [])
            error.append(
                f'{pretty_name(master_setting_field)} not enabled in Master Setting.'
                if master_setting_field else 'Feature not enabled in master setting.'
            )
            errors.update({
                field: error
            })


def validate_rule_limits(value):
    """
    Validation to prevent cases of unacceptable timedelta
    eg. timedelta(years=123456) results in Date Out of Range error.
    Value has been predefined to [1, 1000]
    :return: None
    """
    lower_bound, upper_bound = 1, 1000
    if value and not lower_bound <= value <= upper_bound:
        raise ValidationError(
            f"Ensure the value lies between {lower_bound} and {upper_bound}"
        )
    return value


def convert_rules_to_minutes(rules: list):
    """
    Converts prior_approval_rules to minutes.
    """
    units = {
        "Days": 24 * 60,
        "Hours": 60,
        "Minutes": 1
    }
    prior_rules = []

    for prior_rule in rules:
        unit = prior_rule['prior_approval_unit']
        prior_approval_request_for = prior_rule['prior_approval_request_for']
        prior_approval = prior_rule['prior_approval'] * units[unit]

        rule = {
            'prior_approval_request_for': prior_approval_request_for,
            'prior_approval': prior_approval,
            'prior_approval_unit': "Minutes"

        }
        prior_rules.append(rule)
        
    return prior_rules


def get_prior_approval_rule_errors(rules):
    require_prior_approval_fields = {
        'prior_approval_request_for', 
        'prior_approval',
        'prior_approval_unit'
    }
        
    def filter_valid_rules(element):
        if set(element.keys()) != require_prior_approval_fields:
            return False

        for key, value in element.items():
            if value == "":
                return False
        return True

    filtered_rules = list(filter(filter_valid_rules, rules))
    if len(filtered_rules) < len(rules):
        raise ValidationError({
            "require_prior_approval": 
            "Require Prior Approval fields cannot be null or zero."
        })

    prior_errors = {
        "prior_approval_request_for": [],
        "prior_approval": []
    }
    has_errors = False
    rules = convert_rules_to_minutes(rules)

    # The field for the 1st rule cannot be zero. i.e Prior approval Request For
    # and Prior approval 
    for key in prior_errors:
        if rules[0][key] <= 0:
            has_errors = True
            prior_errors[key].append("Only positive value is supported.")
        
        if not prior_errors[key]:
            prior_errors[key].append("")
        
    for i in range(1, len(rules)):
        for key in prior_errors:
            request_for_error_message = ""
            if rules[i][key] <= rules[i - 1][key]:
                has_errors = True
                field_name = str(key).replace("_", " ")
                request_for_error_message = f"Must be greater than previous {field_name}."
            prior_errors[key].append(request_for_error_message)
    return has_errors, prior_errors


def get_compensatory_rule_errors(compensatory_rules: list):
    """Get compensatory rules error

    Compensatory leave rule field cannot be zero or shouldn't take any negative
    value. If any of these fields are zero or negative this method appends error
    message sending cannot be zero or less. Also, this method returns error message
    if previous rule is greater than current rule by preserving the index(order).
    :param compensatory_rules: frontend payload about compensatory details(i.e 
    balance_to_grant and hour_in_off_day)
    :returns : list of errors if exists

    """
    compensatory_errors = {
        "balance_to_grant": [],
        "hours_in_off_day": []
    }
    has_errors = False
    for key in compensatory_errors:
        if compensatory_rules[0][key] <= 0:
            has_errors = True
            compensatory_errors[key].append("This field cannot be zero or less.")
        else:
            compensatory_errors[key].append("")
        
    for i in range(1, len(compensatory_rules)):
        for key in compensatory_errors:
            error_message = ""
            if compensatory_rules[i][key] <= compensatory_rules[i - 1][key]:
                has_errors = True
                field_name = str(key).replace("_", " ")
                error_message = f"Must be greater than previous {field_name}."
            compensatory_errors[key].append(error_message)
    return has_errors, compensatory_errors
