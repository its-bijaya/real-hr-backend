import logging
import os
import pickle

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.utils import timezone

from irhrs.attendance.models import WorkShift, WorkTiming, WorkDay
from irhrs.leave.models import MasterSetting, LeaveType, LeaveRule, AccumulationRule
from irhrs.leave.models.rule import LeaveIrregularitiesRule, RenewalRule, DeductionRule, \
    YearsOfServiceRule, CompensatoryLeave, TimeOffRule, CreditHourRule

from irhrs.organization.models import FiscalYear, FiscalYearMonth

logger = logging.getLogger(__name__)


def seed_default_data_for(target_organization):
    org_specific = [
        'division',
        'employment_level',
        'employment_type',
        'job_title',
        'separation_type',
        'employment_review',
    ]

    for file in org_specific:
        with open(
                os.path.join(
                    settings.PROJECT_DIR,
                    f'fixtures/org/{file}.pkl',
                ),
                'rb'
        ) as fp:
            objects = pickle.load(fp)
        for q in objects:
            if file == 'employment_level':# and 'level' in [g.name for g in q._meta.fields]:
                q.level = ''
            try:
                q.organization = target_organization
                q.save()
            except Exception as e:
                pass

    # WORKSHIFT
    with open(
            os.path.join(
                settings.PROJECT_DIR,
                'fixtures/org/workshift.pkl'
            ), 'rb'
    ) as fp:
        shifts = pickle.load(fp)

    for ws in shifts:
        work_days = ws.pop('work_days', [])
        try:
            work_shift = WorkShift.objects.create(**{
            'organization': target_organization,
            **ws
        })
        except Exception as e:
            pass
        for wd in work_days:
            timings = wd.pop('timings', [])
            try:
                work_day = WorkDay.objects.create(**{
                    'shift': work_shift,
                    **wd
                })
            except Exception as e:
                pass
            for tm in timings:
                try:
                    WorkTiming.objects.create(**{
                        'work_day': work_day,
                        **tm
                    })
                except Exception as e:
                    logger.info(e)

    # FISCAL YEAR
    with open(
            os.path.join(
                settings.PROJECT_DIR,
                'fixtures/org/fiscal.pkl'
            ), 'rb'
    ) as fp:
        fiscal_years = pickle.load(fp)

    for fy in fiscal_years:
        months = fy.pop('months', [])
        try:
            fy.pop('organization', None)
            fiscal_year = FiscalYear.objects.create(
                **{
                    'organization': target_organization,
                    **fy
                }
            )
        except Exception as e:
            logger.info(f'Failed create Fiscal Year {fy.get("name")}')
            continue

        for fm in months:
            fm.update({
                'fiscal_year': fiscal_year
            })
            try:
                fiscal_month = FiscalYearMonth.objects.create(**fm)
            except:
                logger.info(f'Failed Create Fiscal Month {fm.get("name")}')

    # Master Setting & Leave

    seed_leave_data(target_organization)


def seed_leave_data(organization):
    with open(
            os.path.join(
                settings.PROJECT_DIR,
                'fixtures/org/leaves.pkl'
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
        'back_to_default_value',
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
        'time_off_rule': TimeOffRule,
        'credit_hour_rule': CreditHourRule
    }

    credit_hour_rule = [
        'minimum_request_duration_applicable',
        'minimum_request_duration',
        'maximum_request_duration_applicable',
        'maximum_request_duration',
    ]

    extra_rules = {
        "leave_irregularity": irregularity_fields,
        "accumulation_rule": accumulation_fields,
        "renewal_rule": renewal_rule,
        "deduction_rule": deduction_rule,
        "yos_rule": yos_rules,
        "compensatory_rule": compensatory_rules,
        'time_off_rule': time_off_rule,
        'credit_hour_rule': credit_hour_rule
    }
    for master_setting in all_master_settings_data:
        all_leave_types = master_setting.pop('leave_types', [])
        master_setting.update({
            'organization': organization,
            'effective_from': None,
            'effective_till': None
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
