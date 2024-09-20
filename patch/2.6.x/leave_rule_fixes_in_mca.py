"""
Changes to be done by Aayulogic in leave master settings

Credit Hour
    Maximum request applicable 24 hours
    Max Balance - 24 hour
    Require Prior Approval - 2 Hour

Flexible Public Holiday
    Can apply half day / shift leave - Only full day apply (Disable it)

Special Leave
    Employee can Apply for Leave - Disable it
    Initial balance in renewable should be 180 days

Paternity Leave
    Holiday Inclusive - false
    Can apply half day / shift leave - true

Maternity Leave
    Prior Approval - 3 Months

Leave without Pay
    Set Multilevel Approval required
    Renewal - 30 days in a year

Funeral Leave
    - Renewable - collapse true

Compassionate for Mourning
    - Renewable - collapse true

Sick Leave
    Require Document for 3 days
    Proportionate true

Annual Leave
    Proportionate true
"""
from datetime import timedelta

from irhrs.leave.models import LeaveType, MasterSetting, LeaveRule, RenewalRule

leave_rule_value_map = {
    "Credit Hour": {
        "max_balance": 24*60,
        # "credit_hour_rule": {
        #     "maximum_request_duration_applicable": True,
        #     "maximum_request_duration": timedelta(hours=24)
        # }
    },
    "Flexible Public Holiday": {
        "can_apply_half_shift": False,
    },
    "Special leave": {
        "employee_can_apply": False,
        "renewal_rule": {
            "initial_balance": 180,
        }
    },
    "Paternity Leave": {
        "holiday_inclusive": False,
        "can_apply_half_shift": True,
    },
    "Maternity Leave": {
        "require_prior_approval": True,
        "prior_approval": 90,
        "prior_approval_unit": "Days"
    },
    # "Leave without Pay": {
    #     "leave_type": {
    #         "multi_level_approval": True,
    #     },
    #     "renewal_rule": {
    #         # create
    #         "initial_balance": 30
    #     }
    # },
    "Funeral Leave": {
        "renewal_rule": {
            "is_collapsible": True
        }
    },
    "Compassionate for Mourning": {
        "renewal_rule": {
            "is_collapsible": True
        }
    },
    "Sick Leave": {
        "require_docs": True,
        "require_docs_for": 3,
        "proportionate_on_joined_date": True,
    },
    "Annual Leave": {
        "proportionate_on_joined_date": True
    }
}

org_slug = 'mca-nepal'
for leave_type, data_json in leave_rule_value_map.items():
    print('\n\n=====================\nGetting', leave_type)
    try:
        leave_type_object = LeaveRule.objects.filter(
            leave_type__master_setting__in=MasterSetting.objects.filter(
                organization__slug=org_slug
            ).active()
        ).get(name=leave_type)
    except LeaveRule.DoesNotExist:
        print(leave_type, 'DOES Not Exist')
        continue
    for attribute, value in data_json.items():
        if isinstance(value, dict):
            print('Getting Sub Attr', attribute, end='\t')
            sub_attr = getattr(leave_type_object, attribute, None)
            print('Found' if sub_attr else 'Not Found')
            for sub_attribute, sub_value in value.items():
                print(
                    f'{attribute}.{sub_attribute}',
                    'old value',
                    getattr(sub_attr, sub_attribute, None),
                    'new value',
                    sub_value
                )
                setattr(sub_attr, sub_attribute, sub_value)
                sub_attr.save()
        else:
            print(
                attribute,
                'old value',
                getattr(leave_type_object, attribute, None),
                'new value',
                value
            )
            setattr(leave_type_object, attribute, value)
            leave_type_object.save()


lwp = "Leave without Pay"
lwp_leave_rule = LeaveRule.objects.filter(
    leave_type__master_setting__in=MasterSetting.objects.filter(
        organization__slug=org_slug
    ).active()
).get(name=lwp)
lwp_leave_type = lwp_leave_rule.leave_type
lwp_leave_type.multi_level_approval = True
lwp_leave_type.save()
lwp_new_accumulation = {
    "rule": lwp_leave_rule,
    "duration": 1,
    "duration_type": "Years",
    "initial_balance": 30,
    "max_balance_encashed": 0,
    "max_balance_forwarded": 0,
    "is_collapsible": True,
    "back_to_default_value":  False,
}

RenewalRule.objects.create(**lwp_new_accumulation)
