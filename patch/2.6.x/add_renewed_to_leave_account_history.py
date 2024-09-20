import re

from django.db.models import Q
from django.db.models.signals import post_save

from irhrs.leave.models import LeaveAccountHistory
from irhrs.leave.signals import create_leave_balance_update_notification


post_save.disconnect(receiver=create_leave_balance_update_notification, sender=LeaveAccountHistory)
additives = re.compile(
    r'Renewed {balance_to_add} balance '
    r'(and carry added {carry_forward} balance )?'
    r'(and encashed {encashment_balance} balance )?'
    r'(and collapsed {balance_in_hand} balance )?'
    r'by the System under Renewal'.format(
        balance_to_add=r'(?P<renewed>\d+\.?\d*)',
        carry_forward=r'(?P<carry_forward>\d+\.?\d*)',
        encashment_balance=r'(?P<encashed>\d+\.?\d*)',
        balance_in_hand=r'(?P<deducted>\d+\.?\d*)',
    )
)

for leave_account_history in LeaveAccountHistory.objects.all().filter(
        Q(remarks__icontains='renewed', )
):
    attrs = [
        'renewed',
        'carry_forward',
        'encashed',
        'deducted',
    ]
    match = additives.match(leave_account_history.remarks)
    save = False
    for attr in attrs:
        value = match.groupdict().get(attr)
        if value:
            setattr(leave_account_history, attr, value)
            save = True
    if save:
        leave_account_history.save()

for proportionate_leave_account_history in LeaveAccountHistory.objects.all().filter(
        Q(remarks__icontains='Proportionate Leave by the System')
):
    balance_added = (
            proportionate_leave_account_history.new_balance - proportionate_leave_account_history.previous_balance
    )
    proportionate_leave_account_history.renewed = balance_added
    proportionate_leave_account_history.save()

post_save.connect(receiver=create_leave_balance_update_notification, sender=LeaveAccountHistory)
