import logging
import pickle

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse
from django.urls import reverse

from irhrs.core.mixins.admin import AdminFormMixin
from irhrs.core.utils.common import get_today
from irhrs.core.utils.common_utils import nested_getattr
from irhrs.leave.forms import MasterSettingExportForm, MasterSettingImportForm
from irhrs.leave.models import MasterSetting, LeaveType
from irhrs.leave.models.rule import CompensatoryLeaveCollapsibleRule, LeaveIrregularitiesRule, AccumulationRule, \
    RenewalRule, DeductionRule, YearsOfServiceRule, CompensatoryLeave, TimeOffRule, \
    LeaveRule, CreditHourRule

logger = logging.getLogger(__name__)


lt_fields = [
    'name',
    'description',
    'applicable_for_gender',
    'applicable_for_marital_status',
    'category',
    'email_notification',
    'sms_notification',
    'visible_on_default',
    'multi_level_approval',
]

lr_fields = [
    'name',
    'irregularity_report',
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
    'year_of_service',
    'holiday_inclusive',
    'inclusive_leave',
    'inclusive_leave_number',
    'is_paid',
    'proportionate_on_joined_date',
    'proportionate_on_contract_end_date',
    'can_apply_half_shift',
    'employee_can_apply',
    'admin_can_assign',
    'can_apply_beyond_zero_balance',
    'beyond_limit',
    'required_experience',
    'required_experience_duration',
    'require_prior_approval',
    'require_docs',
    'require_docs_for',
    'start_date',
    'end_date',
    'depletion_required',
    # 'depletion_leave_types',  # Handled separately
    'adjacent_offday_inclusive',
    'adjacent_offday_inclusive_type',
    # 'adjacent_offday_inclusive_leave_types',
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
    'exclude_absent_days',
    'exclude_off_days',
    'count_if_present_in_off_day',
    'exclude_holidays',
    'count_if_present_in_holiday',
    'exclude_unpaid_leave',
    'exclude_paid_leave',
    'exclude_half_leave'
]

renewal_rule = [
    'duration',
    'duration_type',
    'initial_balance',
    'max_balance_encashed',
    'max_balance_forwarded',
    'is_collapsible',
    'back_to_default_value'
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
    {
        'balance_to_grant',
        'hours_in_off_day'
    } 
],

collapsible_rule = {
    'collapse_after',
    'collapse_after_unit'
},

time_off_rule = [
    'total_late_minutes',
    'leave_type',
    'reduce_leave_by'
]

credit_hour_rule = [
    'minimum_request_duration_applicable',
    'minimum_request_duration',
    'maximum_request_duration_applicable',
    'maximum_request_duration'
]

extra_rules = {
    "leave_irregularity": irregularity_fields,
    "accumulation_rule": accumulation_fields,
    "renewal_rule": renewal_rule,
    "deduction_rule": deduction_rule,
    "yos_rule": yos_rules,
    "compensatory_rule": compensatory_rules,
    "collapsible_rule": collapsible_rule,
    'time_off_rule': time_off_rule,
    'credit_hour_rule': credit_hour_rule
}
master_setting_fields = [
    'name',
    'description',
    'organization',
    # 'effective_from', --> do not set effective from
    # 'effective_till', --> do not set effective till
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
    'credit_hour',
    # 'cloned_from'
]

model_map = {
    'leave_irregularity': LeaveIrregularitiesRule,
    'accumulation_rule': AccumulationRule,
    'renewal_rule': RenewalRule,
    'deduction_rule': DeductionRule,
    'yos_rule': YearsOfServiceRule,
    'compensatory_rule': CompensatoryLeave,
    'collapsible_rule': CompensatoryLeaveCollapsibleRule,
    'time_off_rule': TimeOffRule,
    'credit_hour_rule': CreditHourRule
}


class MasterSettingExportView(AdminFormMixin):
    form_class = MasterSettingExportForm
    extra_context = {
        "title": "Export Master Setting"
    }

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        ctx.update(admin.site.each_context(self.request))
        return ctx

    def form_valid(self, form):
        master_setting = form.cleaned_data.get('master_setting')
        dump = self.dump_leave_data(master_setting)
        filename = f'{master_setting} - {get_today()} - leaves'
        return self.get_pickle_response(dump, filename)

    @staticmethod
    def dump_leave_data(master_setting):
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
                lr = {
                    f: getattr(leave_rule, f, None) for f in lr_fields
                }

                # handling depletion types
                lr['depletion_leave_types'] = list(
                    leave_rule.depletion_leave_types.all().values_list('name', flat=True)
                )
                lr['adjacent_offday_inclusive_leave_types'] = list(
                    leave_rule.reduction_leave_types.all().order_by('order_field').values_list(
                        'leave_type__name', flat=True
                    )
                )
                lr['compensatory_leave_types'] = list(
                    leave_rule.compensatory_rules.all().values_list(
                        'rule__leave_type__name', flat=True
                    )
                )

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

        return pickle.dumps(master_setting_data)

    @staticmethod
    def get_pickle_response(content, filename):
        response = HttpResponse(
            content,
            content_type="application/octet-stream",
        )
        response['Content-Disposition'] = \
            f'attachment; filename="{filename}.pickle"'
        return response


class MasterSettingImportView(AdminFormMixin):
    form_class = MasterSettingImportForm
    extra_context = {
        "title": "Import Master Setting"
    }

    def get_success_url(self):
        return reverse('admin:leave_mastersetting_changelist')

    def form_valid(self, form):
        try:
            self.load_master_setting(
                form.cleaned_data.get('organization'),
                form.cleaned_data.get('name'),
                form.cleaned_data.get('import_file')
            )
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)
        return super().form_valid(form)

    @staticmethod
    def load_master_setting(organization, name, import_file):
        try:
            master_setting = pickle.load(import_file)
            previous_organization=master_setting.get("organization")

            all_leave_types = master_setting.pop('leave_types', [])
            master_setting.update({
                'organization': organization,
                'effective_from': None,
                'effective_till': None,
                'name': name
            })
            rule_depletion_types = []  # [(LeaveRule, [Type1, Type2]), ...]
            offday_inclusive_leave_types = []
            compensatory_leave_types = []
            with transaction.atomic():
                try:

                    master_setting_object = MasterSetting.objects.create(
                        **master_setting
                    )
                except Exception as e:
                    logger.error(e, exc_info=True)
                    raise ValidationError(
                        f"Failed create master setting {master_setting.get('name')}"
                    )

                def save_compensatory_leave_rule(instance, leave_rule, previous_organization_slug):
                    organization_slug = nested_getattr(
                        instance, 'rule.leave_type.master_setting.organization.slug'
                    )
                    if organization_slug and organization_slug==previous_organization_slug:
                        instance.pk = None
                        instance.rule = leave_rule
                        instance.save()

                errors = []
                for leave_type in all_leave_types:
                    leave_rules = leave_type.pop('rules', {})
                    leave_type.update({
                        'master_setting': master_setting_object
                    })
                    try:
                        leave_type_object = LeaveType.objects.create(
                            **leave_type)
                    except Exception as e:
                        logger.error(e, exc_info=True)

                        errors.append(
                            f"Create Leave Type failed for {leave_type.get('name')}"
                        )
                        continue

                    for leave_rule in leave_rules:
                        additional_rules = dict()

                        depletion_types = leave_rule.pop(
                            'depletion_leave_types', [])

                        adjacent_offday_inclusive_leave_types = leave_rule.pop(
                            'adjacent_offday_inclusive_leave_types', []
                        )
                        compensatory_types = leave_rule.pop(
                            'compensatory_leave_types', []
                        )

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
                            leave_rule_object = LeaveRule.objects.create(
                                **leave_rule)
                        except Exception as e:
                            logger.error(e, exc_info=True)

                            errors.append(
                                f'Create Leave Rule Failed for {leave_rule.get("name")}')
                            continue

                        if depletion_types:
                            rule_depletion_types.append(
                                (leave_rule_object, depletion_types))

                        if adjacent_offday_inclusive_leave_types:
                            offday_inclusive_leave_types.append(
                                (leave_rule_object,
                                 adjacent_offday_inclusive_leave_types)
                            )
                        if compensatory_types:
                            compensatory_leave_types.append(leave_rule_object)

                        for rule, rule_data in additional_rules.items():
                            if rule == 'leave_irregularity':
                                # exception case
                                rule_data.update({
                                    'leave_rule': leave_rule_object
                                })
                            else:
                                rule_data.update({
                                    'rule': leave_rule_object
                                })
                            model = model_map.get(rule)
                            try:
                                model.objects.create(
                                    **rule_data
                                )
                            except Exception as e:
                                logger.error(e, exc_info=True)
                                errors.append(
                                    'Create additional Leave Rule Failed for' +
                                    str(model.__name__) + 'for leave rule' +
                                    leave_rule.get('name')
                                )

                for leave_rule, depletion_types in rule_depletion_types:
                    leave_types = master_setting_object.leave_types.filter(
                        name__in=depletion_types
                    )
                    leave_rule.depletion_leave_types.set(leave_types)

                for leave_rule, offday_inclusive_leave_type in offday_inclusive_leave_types:
                    leave_types = master_setting_object.leave_types.filter(
                        name__in=offday_inclusive_leave_type
                    )
                    for order, leave_type, in enumerate(leave_types):
                        leave_rule.adjacent_offday_inclusive_leave_types.create(
                            leave_rule=leave_rule,
                            order_field=order,
                            leave_type=leave_type
                        )

                for leave_rule in compensatory_leave_types:
                    for instance in CompensatoryLeave.objects.filter(rule__name=leave_rule.name):
                        save_compensatory_leave_rule(instance, leave_rule, previous_organization.slug)
                       
                    for instance in CompensatoryLeaveCollapsibleRule.objects.filter(
                        rule__name=leave_rule.name
                    ):
                        save_compensatory_leave_rule(instance, leave_rule, previous_organization.slug)
                              
                if errors:
                    raise ValidationError(errors)
        except ValidationError as e:
            raise e

        except Exception as e:
            logger.error(e, exc_info=True)
            raise ValidationError(
                'Corrupt File Loaded',
                code='invalid'
            )
