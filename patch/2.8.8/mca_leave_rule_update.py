
from irhrs.leave.constants.model_constants import INCLUDE_HOLIDAY_AND_OFF_DAY
from irhrs.leave.models import LeaveRule

task = """
Type `y` and press `Enter`
Covid leave should be include holiday and offday
"""

# covid_leave = LeaveRule.objects.get(id=18)
changes = dict(
    holiday_inclusive=True,
    inclusive_leave=INCLUDE_HOLIDAY_AND_OFF_DAY,
    inclusive_leave_number=1,
)
if input(task) == 'y':
    import json
    if input(json.dumps(changes)) == 'y':
        qs = LeaveRule.objects.filter(id=18)
        if qs:
            if input(", ".join([str(x) for x in qs])) == 'y':
                res = qs.update(**changes)
                print(res, 'updated')

task = """
Type `y` and press `Enter`
Proportionate leave on contract end date should be enabled in Sick and Annual leave rules
"""

if input(task) == 'y':
    import json
    changes = dict(proportionate_on_contract_end_date=True)
    if input(json.dumps(changes)) == 'y':
        qs = LeaveRule.objects.filter(
            id__in=[1, 2]
        )
        if qs:
            if input("\n".join([str(x) for x in qs])) == 'y':
                res = qs.update(
                    proportionate_on_contract_end_date=True
                )
                print(res, 'updated')
