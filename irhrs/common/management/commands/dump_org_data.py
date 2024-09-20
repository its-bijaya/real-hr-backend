import os
import pickle

from django.conf import settings

from irhrs.attendance.models import WorkShift
from irhrs.common.models import HolidayCategory, Disability, DocumentCategory
from irhrs.core.constants.organization import GLOBAL

from irhrs.hris.models import EmployeeSeparationType, ChangeType
from irhrs.leave.models import MasterSetting

from irhrs.organization.models import OrganizationDivision, Organization, EmploymentLevel, \
    EmploymentStatus, EmploymentJobTitle, FiscalYear

required_dirs = ['fixtures', 'fixtures/org', 'fixtures/commons']

for directory in required_dirs:
    absolute = os.path.join(
        settings.PROJECT_DIR,
        directory
    )
    if not os.path.exists(absolute):
        os.makedirs(absolute)

# RUN THIS FROM DEMO SERVER 192.168.99.71
twitter = Organization.objects.get(pk=17)

org_models = {
    'division': OrganizationDivision.objects.filter(
        organization=twitter
    ),
    'employment_level': EmploymentLevel.objects.filter(
        organization=twitter
    ),
    'employment_type': EmploymentStatus.objects.filter(
        organization=twitter
    ),
    'job_title': EmploymentJobTitle.objects.filter(
        organization=twitter
    ),
    'separation_type': EmployeeSeparationType.objects.filter(
        organization=twitter
    ),
    'employment_review': ChangeType.objects.filter(
        organization=twitter
    )
}

for file, query in org_models.items():
    res = list()
    for q in query:
        q.organization = q.id = q.created_at = q.edited_at = q.created_by = q.modified_by = None
        res.append(q)
    with open(
            os.path.join(
                settings.PROJECT_DIR,
                f'fixtures/org/{file}.pkl'
            ), 'wb'
    ) as fp:
        pickle.dump(
            res,
            fp
        )

common_models = {
    'holiday_category': HolidayCategory.objects.all(),
    'disability': Disability.objects.all(),
    'document_category': DocumentCategory.objects.all(),
}

# working_shift
shifts = []
for ws in WorkShift.objects.filter(
        organization=twitter
):
    all_work_shift = {}
    fields = [
        'name', 'start_time_grace', 'end_time_grace', 'is_default'
    ]
    for f in fields:
        all_work_shift[f] = getattr(ws, f, None)

    wds = []
    for wd in ws.work_days.all():
        f_fields = [
            'start_time', 'end_time', 'extends', 'working_minutes'
        ]
        tms = list()
        for tm in wd.timings.all():
            timings = {}
            for ff in f_fields:
                timings[ff] = getattr(tm, ff, None)
            tms.append(timings)
        wds.append({
            'day': wd.day,
            'timings': tms
        })
    all_work_shift['work_days'] = wds
    shifts.append(all_work_shift)

with open(
        os.path.join(
            settings.PROJECT_DIR,
            'fixtures/org/workshift.pkl'
        ), 'wb') as fp:
    pickle.dump(shifts, fp)

# fiscal_year
fiscal_years = list()
for fy in FiscalYear.objects.filter(
        organization=twitter,
        category=GLOBAL
):
    months = []
    for fm in fy.fiscal_months.all():
        mth = {}
        for f in [
            'fiscal_year',
            'month_index',
            'display_name',
            'start_at',
            'end_at',
        ]:
            mth[f] = getattr(fm, f, None)
        mth['fiscal_year'] = None
        months.append(mth)
    fiscal_data = {}
    for f in [
        'organization',
        'name',
        'start_at',
        'end_at',
        'description',
        'applicable_from',
        'applicable_to',
    ]:
        fiscal_data[f] = getattr(fy, f, None)
    fiscal_data['months'] = months
    fiscal_years.append(fiscal_data)

with open(
        os.path.join(
            settings.PROJECT_DIR,
            'fixtures/org/fiscal.pkl'
        ), 'wb') as fp:
    pickle.dump(fiscal_years, fp)

for file, query in common_models.items():
    res = list()
    for q in query:
        q.id = q.created_at = q.edited_at = q.created_by = q.modified_by = None
        res.append(q)
    with open(
            os.path.join(
                settings.PROJECT_DIR,
                f'fixtures/commons/{file}.pkl',
            ), 'wb'
    ) as fp:
        pickle.dump(
            res,
            fp
        )

lt_fields = [
    'name',
    'description',
    'applicable_for_gender',
    'applicable_for_marital_status',
    'category',
    'email_notification',
    'sms_notification',
    'is_archived',
    'visible_on_default',
    'multi_level_approval',
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
    'year_of_service',
    'holiday_inclusive',
    'inclusive_leave',
    'inclusive_leave_number',
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
    'prior_approval',
    'prior_approval_unit',
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
    'back_to_default_value',
]

deduction_rule = [
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
    'credit_hour',
    'cloned_from'
]

all_master_settings_data = list()

for master_setting in MasterSetting.objects.filter(
    organization=twitter
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
            'fixtures/org/leaves.pkl'
        ), 'wb') as fp:
    pickle.dump(all_master_settings_data, fp)
