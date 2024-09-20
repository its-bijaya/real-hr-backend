from django.utils.translation import gettext_lazy as _

NAME_ORGANIZATION_NOT_UNIQUE = _(
    "The name must be unique with organization"
)
PAID_OR_UNPAID_REQUIRED = _(
    "Can not set both `Paid` and 'Unpaid` settings turned off"
)
ONE_WAY_TO_APPLY_REQUIRED = _(
    "There is no way set to apply for the leave. Either `Employees Can Apply` "
    "or `Admin Can Assign` has to be set.")
MUST_SET_ACTION_FOR_REMAINING_BALANCE = _(
    "There is no actions defined for remaining balance. Please set at least "
    "one of `Encashment`, `Carry Forward` or `Collapsible`"
)
ALREADY_ONE_ACTIVE_SETTING = _(
    "There is already one setting active now. Please change effective from."
)
THERE_IDLE_IDLE_SETTING = _(
    "There is already an setting `Idle`. Please edit that setting."
)

SELECTED_CATEGORY_NOT_IN_MASTER_SETTING = _(
    "Selected category is not in Master Setting."
)

CAN_NOT_ASSOCIATE_TO_MASTER_SETTING = _(
    "Can not assign to `Master Setting` to expired settings."
)

MASTER_SETTING_UPDATE_BLOCKED = _(
    "Can not update master setting, leave rule with fields enabled exists."
)

APPROVAL_SETTING_NOT_SET = _(
    "Must contain at-least one employee as approver for multi approval level."
)
