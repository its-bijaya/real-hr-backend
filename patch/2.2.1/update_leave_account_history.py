import re

from irhrs.core.utils import get_system_admin as bot
from irhrs.leave.models import LeaveAccountHistory

history_regex = re.compile(
    "Renewed (?P<renewed>.*?) balance "
    "(and carry added (?P<carry_forward>.*?) balance )?"
    "(and encashed (?P<encashed>.*?) balance )?"
    "(and collapsed (?P<deducted>.*?) balance )?"
    "by the System under Renewal"
)
for lah in LeaveAccountHistory.objects.filter(
        actor=bot(),
        remarks__startswith='Renewed'
):
    x = history_regex.match(lah.remarks)
    result = x.groupdict() if x else {}
    [setattr(lah, field, value) for field, value in result.items()]
    lah.save(update_fields=['renewed', 'carry_forward', 'encashed', 'deducted'])
