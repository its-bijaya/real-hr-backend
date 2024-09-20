"""
Look at account histories,
If new_usable and new_balance is not reflected in subsequent history, mark the difference.
Leave Request Pending Count should be the difference in
account balance and account usable balance.
"""
FILE_POINTER = open('message.out', 'w')


def filewriter(*message):
    # FILE_POINTER.write("\t".join(map(str, message)))
    # FILE_POINTER.write("\n")
    print("\t".join(map(str, message)))
    print("\n")


from django.db.models import F

from irhrs.leave.models import LeaveAccount


def find_leave_account_with_balance_issues():
    # these accounts dont have balance equal to usable balance.
    # Leave Requests could be the reason, but instead of testing for pending leave requests
    # process everything. Correct ones will be ignored.
    return LeaveAccount.objects.exclude(
        usable_balance=F('balance')
    )


NA = None


def find_balance_usable_balance_shift(leave_account):
    # Process a single leave account here.
    # sort the histories from start..end
    # for each iteration, look at the new balance & new usable balance
    # find delta for the next iteration.
    # Ignore the possibility of pending leave requests.
    base_qs = leave_account.history.order_by('id')
    initial = base_qs.first()
    if not initial:
        print('No histories', leave_account)
        return NA, NA
    old_balance = initial.new_balance
    old_usable = initial.new_usable_balance
    balance_diff_recorder = []
    usable_diff_recorder = []
    for history in base_qs.exclude(id=initial.id).order_by('id'):
        s = '\t'.join(
            map(lambda s: s.ljust(10),
            map(str, [history.action, history.previous_balance, history.previous_usable_balance,
                    history.new_balance, history.new_usable_balance, history.remarks])
        ))
        diff = old_balance - history.previous_balance
        to_fix = diff + sum(balance_diff_recorder)
        balance_diff_recorder.append(diff)
        old_balance = history.new_balance
        usable_diff = old_usable - history.previous_usable_balance
        usable_fix = usable_diff + sum(usable_diff_recorder)
        usable_diff_recorder.append(usable_diff)
        old_usable = history.new_usable_balance
        filewriter(to_fix, usable_fix, s)
        history.previous_usable_balance += usable_fix
        history.new_usable_balance += usable_fix
        history.previous_balance += to_fix
        history.new_balance += to_fix
        s = '\t'.join(
            map(lambda s: s.ljust(10),
                map(str, [history.action, history.previous_balance, history.previous_usable_balance,
                          history.new_balance, history.new_usable_balance, history.remarks])
                ))
        filewriter('---', '---', s)
        # history.save()
    return balance_diff_recorder, usable_diff_recorder


def run():
    #   leave_accounts = find_leave_account_with_balance_issues()
    leave_accounts = LeaveAccount.objects.filter(id__in=[383, 405])
    for leave_account in leave_accounts:
        balance_diff, usable_diff = find_balance_usable_balance_shift(leave_account)
        filewriter(
            str(leave_account),
            sum(balance_diff) if balance_diff else NA,
            sum(usable_diff) if usable_diff else NA
        )
        if balance_diff:
            leave_account.balance += sum(balance_diff)
            filewriter('Fixed balance', leave_account.balance)
        if usable_diff:
            leave_account.usable_balance += sum(usable_diff)
            filewriter('Fixed usable balance', leave_account.usable_balance)
        # leave_account.save()
