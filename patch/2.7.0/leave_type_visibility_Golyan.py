"""
This patch is intended to make listed Leave Type for all organizations
Visible or Invisible.
"""
from irhrs.leave.models import MasterSetting, LeaveType
from irhrs.organization.models import Organization

leave_type_visibility_map = {
    "Paternity Leave": False,
    "Mourning Leave": False,
    "Maternity Leave (Paid)": False,
    "Maternity Leave (Unpaid)": False,
    "Marriage Leave": False,
    "Leave Without Pay": False
}
max_len = 0


def stack_print(*args, clear=False):
    global max_len
    if clear:
        max_len = max(map(lambda g: len(str(g)), args)) + 15
    print(' '*4, *map(lambda content: str(content).ljust(max_len)[:max_len], args))


following_organizations_only = []
if following_organizations_only:
    selected_organizations = Organization.objects.filter(
        slug__in=following_organizations_only
    )
else:
    selected_organizations = Organization.objects.all()

stack_print('Organization', 'Leave Type', 'Old Value', 'New Value', clear=True)
active_master_settings = MasterSetting.objects.filter(
    organization__in=selected_organizations
).active()
for org in selected_organizations:
    for leave_type_name, new_value in leave_type_visibility_map.items():
        leave_type = LeaveType.objects.filter(
            master_setting__in=active_master_settings,
            master_setting__organization=org,
            name=leave_type_name
        ).first()
        if leave_type:
            old_value = leave_type.visible_on_default
            leave_type.visible_on_default = new_value
            # leave_type.save(update_fields=['visible_on_default'])
        else:
            old_value = 'N/A'
        stack_print(
            org.name,
            leave_type_name,
            old_value,
            new_value
        )
