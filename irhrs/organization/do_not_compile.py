from irhrs.organization.utils.holiday import past_holiday_added_post_action
from irhrs.organization.api.v1.serializers.branch import OrganizationBranchImportSerializer as\
    _OrganizationBranchImportSerializer


def async_past_holiday_added_post_action(holiday):
    past_holiday_added_post_action(holiday)


OrganizationBranchImportSerializer = _OrganizationBranchImportSerializer
