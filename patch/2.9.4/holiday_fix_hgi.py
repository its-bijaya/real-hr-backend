"""
HGI Specific Holiday Patch.
Request: Removal of assigned branches and division
"""
HOLIDAY_SLUG = 'gaura-parwa'
NEW_HOLIDAY_NAME = 'Gaura Parwa/Krishna Janmasthami'
NEW_HOLIDAY_SLUG = 'gaura-parwa-krishna-janmasthami'

from irhrs.organization.models import Holiday, HolidayRule

selected_holiday = Holiday.objects.get(slug=HOLIDAY_SLUG)
holiday_rule = selected_holiday.rule

# clear branch
#holiday_rule.branch.clear()

# clear division
#holiday_rule.division.clear()

# clear ethnicity
#holiday_rule.ethnicity.clear()

# clear religion
#holiday_rule.religion.clear()

Holiday.objects.filter(slug=HOLIDAY_SLUG).update({
    'name': NEW_HOLIDAY_NAME,
    'slug': NEW_HOLIDAY_SLUG
})

from irhrs.attendance.tasks.timesheets import populate_timesheets
populate_timesheets(date_='')