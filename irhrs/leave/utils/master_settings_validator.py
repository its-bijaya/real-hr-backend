import functools

from django.db.models import Q

from irhrs.leave.models import LeaveRule


class MasterSettingUpdateValidator:
    """
    Master Setting Validator

    Validates master setting update action with existing leave rules and leave
    types
    """
    # master setting field, leave rule fields
    master_setting_leave_rule_map = dict([
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
        )),

        # FK relations
        ("accumulation", ("accumulation_rule",)),
        ("renewal", ("renewal_rule",)),
        ("time_off", ("time_off_rule",)),
        ("leave_irregularities", ("leave_irregularity",)),
        ("years_of_service", ("yos_rule",)),
        ("compensatory", ("compensatory_rules",)),
        ("deductible", ("deduction_rule",))


    ])

    child_rules_ms_maps = {
        'renewal_rule': dict([
            ('carry_forward', ('max_balance_forwarded', )),
            ('encashment', ('max_balance_encashed', )),
            ('collapsible', ('is_collapsible',))
        ]),
        'yos_rule': {
            'collapsible': ('collapse_after', 'collapse_after_unit')
        },
        'leave_collapsible_rule': {
            'collapsible': ('collapse_after', 'collapse_after_unit')
        }
    }

    bool_fields = (
        'can_apply_half_shift',
        'admin_can_assign',
        'employee_can_apply',
        'holiday_inclusive',
        'require_docs',
        'require_experience',
        'can_apply_beyond_zero_balance',
        'require_prior_approval',
        'proportionate_on_joined_date',
        "depletion_required",
        "can_apply_half_shift"
    )

    @classmethod
    def validate(cls, instance, data):
        # master_setting_leave_rule_map = cls.master_setting_leave_rule_map
        error_dict = dict()
        is_valid = True

        for field, value in data.items():

            # if previously set and now trying to unset check
            fields = cls.master_setting_leave_rule_map.get(field, [])
            query = functools.reduce(
                lambda q, field_: q | Q(
                    **({
                        f"{field_}__isnull": False
                    } if field_ not in cls.bool_fields else {f"{field_}": True})), fields, Q()
            ) if fields else None
            filtered = False

            qs = LeaveRule.objects.filter(leave_type__master_setting=instance)

            # two exception paid and unpaid leaves
            if field == 'paid':
                qs = qs.filter(is_paid=True)
                filtered = True
            elif field == 'unpaid':
                qs = qs.filter(is_paid=False)
                filtered = True
            elif query:
                qs = qs.filter(query)
                filtered = True

            if not value and getattr(instance, field) and filtered \
                    and qs.exists():
                error_dict = cls.set_error_dict(field, error_dict)
                is_valid = False

            if is_valid:
                is_valid, error_dict = cls.validate_child_rules(
                    instance, data, error_dict, qs
                )

        return is_valid, error_dict

    @classmethod
    def validate_child_rules(cls, instance, data, error_dict, qs):
        is_valid = True

        for field, fields_map in cls.child_rules_ms_maps.items():
            for ms_field, child_fields in fields_map.items():
                # if master setting is to be set false then only check
                if getattr(instance, ms_field) and not data.get(ms_field):
                    for child_field in child_fields:
                        if qs.filter(
                                **{f"{field}__{child_field}__isnull": False}):
                            error_dict = cls.set_error_dict(
                                ms_field, error_dict
                            )
                            is_valid = False
                            break

        return is_valid, error_dict

    @staticmethod
    def set_error_dict(field, error):
        error.update({
            field: ["Can not unset this. Rules with this policy exists."]
        })
        return error
