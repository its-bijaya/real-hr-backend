from irhrs.organization.models import Organization
from irhrs.organization.utils.holiday import refresh_timesheets


def past_holiday_delete_post_action(date, organization_slug):
    organization = Organization.objects.get(slug=organization_slug)
    refresh_timesheets(timesheet_for=date, organization=organization)


DATE = "2020-02-10"
ORGANIZATION_SLUG = "himalayan-general-insurance-co-ltd"

past_holiday_delete_post_action(DATE, ORGANIZATION_SLUG)

