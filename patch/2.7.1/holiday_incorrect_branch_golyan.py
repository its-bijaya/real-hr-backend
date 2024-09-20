"""
2. Tricot Industries Pvt. Ltd. ---> slug = "gai-jatra" ---> rule.branch = "head-office", "new-road-store"
5. Golyan Agro Pvt. Ltd. ---> slug = "gai-jatra-4" ---> rule.branch = "head-office-2", "warehouse", "sanepa-store", "narayanthan-store"


3. Westar Properties Pvt. Ltd. ---> slug = "gai-jatra-2" ---> rule.branch = "All"
4. Westar Galaxy Trading Pvt. Ltd. ---> slug = "gai-jatra-3" ---> rule.branch = "All"
6. Golyan Tower Pvt. Ltd. ---> slug = "gai-jatra-5" ---> rule.branch = "All"
7. city Hotel Ltd. ---> slug = "gai-jatra-6" ---> rule.branch = "All"
8. Pure Energy Pvt. Ltd. ---> slug = "gai-jatra-7" ---> rule.branch = "All"
"""
from irhrs.attendance.constants import HOLIDAY, OFFDAY, WORKDAY
from irhrs.attendance.models import TimeSheet
from irhrs.attendance.tasks.timesheets import populate_timesheets
from irhrs.organization.models import Holiday, Organization, OrganizationBranch

BRANCH_WITH = [{
    "org_name": "Tricot Industries Pvt. Ltd.",
    "holiday_slug": "gai-jatra",
    "branches": ['head-office', 'new-road-store'],
}, {
    "org_name": "Golyan Agro Pvt. Ltd.",
    "holiday_slug": "gai-jatra-4",
    "branches": [
        "head-office-2", "warehouse", "sanepa-store", "narayanthan-store"
    ],
}]

for branch_data in BRANCH_WITH:
    holiday_slug = branch_data.get('holiday_slug')
    holiday = Holiday.objects.get(
        slug=holiday_slug
    )
    holiday_rule = holiday.rule
    branches = map(
        lambda s: OrganizationBranch.objects.get(slug=s),
        branch_data.get('branches')
    )
    holiday_rule.branch.clear()
    for b in branches:
        holiday_rule.branch.add(b)

for ts in TimeSheet.objects.filter(
        timesheet_for='2020-08-04',
        timesheet_user__detail__organization__name__in=[
            "Tricot Industries Pvt. Ltd.",
            "Golyan Agro Pvt. Ltd.",
        ]
):
    user = ts.timesheet_user
    date = ts.timesheet_for

    def rebuild_coefficient():
        if user.is_holiday(date):
            return HOLIDAY
        elif user.is_offday(date):
            return OFFDAY
        else:
            return WORKDAY

    ts.coefficient = rebuild_coefficient()
    ts.punch_in_delta = ts.punch_out_delta = ts.punctuality = None
    ts.save()
    ts.fix_entries()

# BRANCH_LESS = [
#     {
#         "name": "Westar Properties Pvt. Ltd.",
#         'slug': "gai-jatra-2"
#     },
#     {
#         "name": "Westar Galaxy Trading Pvt. Ltd.",
#         'slug': "gai-jatra-3"
#     },
#     {
#         "name": "Golyan Tower Pvt. Ltd.",
#         'slug': "gai-jatra-5"
#     },
#     {
#         "name": "city Hotel Ltd.",
#         'slug': "gai-jatra-6"
#     },
#     {
#         "name": "Pure Energy Pvt. Ltd.",
#         'slug': "gai-jatra-7"
#     },
# ]
#
# for branch_data in BRANCH_LESS:
#     # organization = Organization.objects.get(
#     #     name=branch_data.get('name')
#     # )
#     holiday = Holiday.objects.get(
#         slug=branch_data.get('slug')
#     )
#     holiday_rule = holiday.rule
#     holiday_rule.branch.clear()
#
# # FINALLY,
# for ts in TimeSheet.objects.filter(
#     timesheet_for='2020-08-04'
# ):
#     user = ts.timesheet_user
#     date = ts.timesheet_for
#
#     def rebuild_coefficient():
#         if user.is_holiday(date):
#             return HOLIDAY
#         elif user.is_offday(date):
#             return OFFDAY
#         else:
#             return WORKDAY
#
#     ts.coefficient = rebuild_coefficient()
#     ts.punch_in_delta = ts.punch_out_delta = ts.punctuality = None
#     ts.save()
#     ts.fix_entries()
