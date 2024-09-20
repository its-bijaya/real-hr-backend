"""
This patch is intended to make listed Leave Type for all organizations
Visible or Invisible.
"""
from irhrs.leave.constants.model_constants import MONTHS, DAYS
from irhrs.leave.models import MasterSetting, LeaveType
from irhrs.organization.models import Organization

leave_type_accumulation_rule_map = {
    "Sick Leave": {
        'duration': 1,
        'duration_type': MONTHS,
        'balance_added': 1,
    },
    "Home Leave": {
        'duration': 20,
        'duration_type': DAYS,
        'balance_added': 1,
    },
}
following_organizations_only = []
if following_organizations_only:
    selected_organizations = Organization.objects.filter(
        slug__in=following_organizations_only
    )
else:
    selected_organizations = Organization.objects.all()

active_master_settings = MasterSetting.objects.filter(
    organization__in=selected_organizations
).active()
for org in selected_organizations:
    for leave_type_name, accumulation_rule in leave_type_accumulation_rule_map.items():
        leave_type = LeaveType.objects.filter(
            master_setting__in=active_master_settings,
            master_setting__organization=org,
            name=leave_type_name
        ).first()
        if not leave_type:
            print(org, leave_type_name, 'Not Found')
            continue
        leave_rules = leave_type.leave_rules.all()
        for leave_rule in leave_rules:
            accumulation_rule_object = getattr(leave_rule, 'accumulation_rule', None)
            if not accumulation_rule_object:
                print(org, leave_type_name, 'Accumulation Not Found')
                continue
            for attr, value in accumulation_rule.items():
                setattr(accumulation_rule_object, attr, value)
            print('Set', org, leave_rule, 'successfully')
            # accumulation_rule_object.save(update_fields=list(accumulation_rule.keys()))
