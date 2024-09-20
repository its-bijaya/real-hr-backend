"""
The branches for Master Setting is as follows:
Master Setting
    | - Leave Type 1
    | - Leave Type 2
    | - Leave Type 3
    | - Leave Type 4
        | - Leave Rule 1
        | - Leave Rule 2
        | - Leave Rule 3
        | - Leave Rule 4

"""
import logging

import os
import pickle

from dateutil.parser import parse
from django.conf import settings
from django.db import transaction

from irhrs.core.utils.common import get_today
from irhrs.organization.models import Organization
from irhrs.leave.models.rule import LeaveIrregularitiesRule, RenewalRule, DeductionRule, \
    YearsOfServiceRule, CompensatoryLeave, TimeOffRule
from irhrs.leave.models import MasterSetting, LeaveType, LeaveRule, AccumulationRule

logger = logging.getLogger(__name__)
source_org_slug = 'westar-galaxy-trading-pvt-ltd'
source_organization = Organization.objects.get(slug=source_org_slug)
target_organization_slugs = [
    'golyan-agro-pvt-ltd',
    'golyan-group',
    'tricot-industries-pvt-ltd',
    'westar-properties-pvt-ltd',
    'golyan-tower-pvt-ltd',
    'city-hotel-ltd',
    'pure-energy-pvt-ltd'
]

today = get_today()
effective_from_date = parse('2019-07-21').date()

lt_fields = [
    'name',
    'description',
    'applicable_for_gender',
    'applicable_for_marital_status',
    'category',
    'email_notification',
    'sms_notification',
    'visible_on_default',
]

lr_fields = [
    'irregularity_report',
    'name',
    'description',
    'is_archived',
    'limit_leave_to',
    'limit_leave_duration',
    'limit_leave_duration_type',
    'min_balance',
    'max_balance',
    'limit_leave_occurrence',
    'limit_leave_occurrence_duration',
    'limit_leave_occurrence_duration_type',
    'maximum_continuous_leave_length',
    'minimum_continuous_leave_length',
    'holiday_inclusive',
    'is_paid',
    'proportionate_on_joined_date',
    'can_apply_half_shift',
    'employee_can_apply',
    'admin_can_assign',
    'can_apply_beyond_zero_balance',
    'beyond_limit',
    'required_experience',
    'required_experience_duration',
    'require_prior_approval',
    'prior_approval_days',
    'require_docs',
    'require_docs_for',
    'start_date',
    'end_date',
    # 'depletion_required',
    # 'depletion_leave_types',  # The challenge is real
]

irregularity_fields = [
    'weekly_limit',
    'fortnightly_limit',
    'monthly_limit',
    'quarterly_limit',
    'semi_annually_limit',
    'annually_limit',
]

accumulation_fields = [
    'duration',
    'duration_type',
    'balance_added',
]

renewal_rule = [
    'duration',
    'duration_type',
    'initial_balance',
    'max_balance_encashed',
    'max_balance_forwarded',
    'is_collapsible',
]

deduction_rule = [
    'rule',
    'duration',
    'duration_type',
    'balance_deducted'
]

yos_rules = [
    'years_of_service',
    'balance_added',
    'collapse_after',
    'collapse_after_unit'
]

compensatory_rules = [
    'balance_to_grant',
    'hours_in_off_day',
    'collapse_after',
    'collapse_after_unit'
]

time_off_rule = [
    'total_late_minutes',
    'leave_type',
    'reduce_leave_by'
]

extra_rules = {
    "leave_irregularity": irregularity_fields,
    "accumulation_rule": accumulation_fields,
    "renewal_rule": renewal_rule,
    "deduction_rule": deduction_rule,
    "yos_rule": yos_rules,
    "compensatory_rule": compensatory_rules,
    'time_off_rule': time_off_rule,
}
master_setting_fields = [
    'name',
    'description',
    'effective_from',
    'effective_till',
    'accumulation',
    'renewal',
    'deductible',
    'paid',
    'unpaid',
    'half_shift_leave',
    'occurrences',
    'beyond_balance',
    'proportionate_leave',
    'depletion_required',
    'require_experience',
    'require_time_period',
    'require_prior_approval',
    'require_document',
    'leave_limitations',
    'leave_irregularities',
    'employees_can_apply',
    'admin_can_assign',
    'continuous',
    'holiday_inclusive',
    'encashment',
    'carry_forward',
    'collapsible',
    'years_of_service',
    'time_off',
    'compensatory',
    'cloned_from'
]


def dump_leave_data(src):
    all_master_settings_data = list()

    for master_setting in MasterSetting.objects.filter(
            organization=src
    ):
        master_setting_data = {
            f: getattr(master_setting, f) for f in master_setting_fields
        }
        all_leave_types = list()
        for leave_type in master_setting.leave_types.all():
            lt = {
                f: getattr(leave_type, f, None) for f in lt_fields
            }
            rules = list()
            for leave_rule in leave_type.leave_rules.all():
                if getattr(leave_rule, 'depletion_required', False):
                    leave_types = getattr(leave_rule, 'depletion_leave_types', [])
                lr = {
                    f: getattr(leave_rule, f, None) for f in lr_fields
                }
                for extra_rule in extra_rules:
                    extra_o_o = getattr(leave_rule, extra_rule, None)
                    if extra_o_o:
                        lr[extra_rule] = {
                            f: getattr(
                                extra_o_o, f, None
                            ) for f in extra_rules.get(extra_rule)
                        }
                rules.append(lr)
            lt['rules'] = rules
            all_leave_types.append(lt)
        master_setting_data['leave_types'] = all_leave_types
        all_master_settings_data.append(master_setting_data)

    with open(
            os.path.join(
                settings.PROJECT_DIR,
                f'fixtures/org/{src.slug}-{today}-leaves.pkl'
            ), 'wb') as fp:
        pickle.dump(all_master_settings_data, fp)


def seed_leave_data(organization):
    with open(
            os.path.join(
                settings.PROJECT_DIR,
                f'fixtures/org/{source_organization.slug}-{today}-leaves.pkl'
            ), 'rb'
    ) as fp:
        all_master_settings_data = pickle.load(fp)

    irregularity_fields = [
        'weekly_limit',
        'fortnightly_limit',
        'monthly_limit',
        'quarterly_limit',
        'semi_annually_limit',
        'annually_limit',
    ]

    accumulation_fields = [
        'duration',
        'duration_type',
        'balance_added',
    ]

    renewal_rule = [
        'duration',
        'duration_type',
        'initial_balance',
        'max_balance_encashed',
        'max_balance_forwarded',
        'is_collapsible',
    ]

    deduction_rule = [
        'rule',
        'duration',
        'duration_type',
        'balance_deducted'
    ]

    yos_rules = [
        'years_of_service',
        'balance_added',
        'collapse_after',
        'collapse_after_unit'
    ]

    compensatory_rules = [
        'balance_to_grant',
        'hours_in_off_day',
        'collapse_after',
        'collapse_after_unit'
    ]

    time_off_rule = [
        'total_late_minutes',
        'leave_type',
        'reduce_leave_by'
    ]

    model_map = {
        'leave_irregularity': LeaveIrregularitiesRule,
        'accumulation_rule': AccumulationRule,
        'renewal_rule': RenewalRule,
        'deduction_rule': DeductionRule,
        'yos_rule': YearsOfServiceRule,
        'compensatory_rule': CompensatoryLeave,
        'time_off_rule': TimeOffRule
    }

    extra_rules = {
        "leave_irregularity": irregularity_fields,
        "accumulation_rule": accumulation_fields,
        "renewal_rule": renewal_rule,
        "deduction_rule": deduction_rule,
        "yos_rule": yos_rules,
        "compensatory_rule": compensatory_rules,
        'time_off_rule': time_off_rule,
    }
    for master_setting in all_master_settings_data:
        all_leave_types = master_setting.pop('leave_types', [])
        master_setting.update({
            'organization': organization,
            'effective_from': effective_from_date
        })
        try:
            master_setting_object = MasterSetting.objects.create(
                **master_setting
            )
        except:
            logger.info(f"Failed create master setting {master_setting.get('name')}")
            continue
        for leave_type in all_leave_types:
            leave_rules = leave_type.pop('rules', {})
            leave_type.update({
                'master_setting': master_setting_object
            })
            try:
                leave_type_object = LeaveType.objects.create(**leave_type)
            except:
                logger.info(
                    f"Create Leave Type failed for {leave_type.get('name')}"
                )
                continue

            additional_rules = dict()
            for leave_rule in leave_rules:
                for extra_rule in extra_rules:
                    extra_o_o = leave_rule.pop(extra_rule, {})
                    if extra_o_o:
                        additional_rules.update({
                            extra_rule: extra_o_o
                        })
                leave_rule.update({
                    'leave_type': leave_type_object
                })
                try:
                    leave_rule_object = LeaveRule.objects.create(**leave_rule)
                except:
                    logger.info(f'Create Leave Rule Failed for {leave_rule.get("name")}')
                    continue
                for rule, rule_data in additional_rules.items():
                    rule_data.update({
                        'rule': leave_rule_object
                    })
                    model = model_map.get(rule)
                    try:
                        model.objects.create(
                            **rule_data
                        )
                    except:
                        logger.info(
                            'Create additional Leave Rule Failed for' +
                            str(model.__name__) + 'for leave rule' +
                            leave_rule.get('name')
                        )


def delete_all_master_settings_for(organization_):
    for master_setting in MasterSetting.objects.filter(organization=organization_):
        print('Delete', organization_.name, master_setting)
        master_setting.delete()


proceed = True
for org in Organization.objects.filter(slug__in=target_organization_slugs):
    # ensure no Master Settings.
    count = MasterSetting.objects.filter(organization=org).count()
    print(org.name, count)
    if count:
        proceed = False


with transaction.atomic():
    if not proceed:
        for org in Organization.objects.filter(slug__in=target_organization_slugs):
            delete_all_master_settings_for(org)
    dump_leave_data(source_organization)
    for org in Organization.objects.filter(slug__in=target_organization_slugs):
        # backup just in case
        dump_leave_data(org)
        print(org.name, 'Leave Data Seed')
        seed_leave_data(org)
