from irhrs.organization.models import Holiday, HolidayRule

for holiday in Holiday.objects.filter(rule__isnull=True):
    HolidayRule.objects.create(
        holiday=holiday,
        gender='All'
    )
