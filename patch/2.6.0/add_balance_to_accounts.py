import json

from django.db import transaction

from irhrs.core.utils import get_system_admin
from irhrs.core.utils.common import DummyObject, humanize_interval
from irhrs.leave.api.v1.serializers.account import LeaveAccountBulkUpdateSerializer
from irhrs.leave.constants.model_constants import GENERAL, CREDIT_HOUR
from irhrs.leave.models import LeaveAccount, MasterSetting


def generate_payload(leave_accounts, balance_to_add):
    def get_display(leave_acc):
        if leave_acc.rule.leave_type.category == GENERAL:
            return balance_to_add
        if leave_acc.rule.leave_type.category == CREDIT_HOUR:
            return humanize_interval(balance_to_add * 60)
        return balance_to_add

    all_leave_account_payload = [
        {
            "leave_account": leave_account.id,
            "remark": f"Added {get_display(leave_account)} as starting balance.",
            "balance": balance_to_add,
        } for leave_account in leave_accounts
    ]
    payload = {
      "leave_accounts": all_leave_account_payload
    }
    return payload


def run():
    valid_leave_accounts = LeaveAccount.objects.filter(
        is_archived=False,
        rule__leave_type__master_setting__in=MasterSetting.objects.all().active()
    )
    general_leave_accounts = valid_leave_accounts.filter(
        rule__leave_type__category=GENERAL
    )
    serializer = LeaveAccountBulkUpdateSerializer(
        data=generate_payload(general_leave_accounts, 25),
        context={
            'request': DummyObject(
                user=get_system_admin()
            )
        }
    )
    if serializer.is_valid():
        serializer.save()
    else:
        print('Invalid for general with')
        print(
            json.dumps(
                serializer.errors,
                indent=3
            )
        )

    credit_leave_accounts = valid_leave_accounts.filter(
        rule__leave_type__category=CREDIT_HOUR
    )
    fifty_hours = 50 * 60
    serializer = LeaveAccountBulkUpdateSerializer(
        data=generate_payload(credit_leave_accounts, fifty_hours),
        context={
            'request': DummyObject(
                user=get_system_admin()
            )
        }
    )
    if serializer.is_valid():
        serializer.save()
    else:
        print('Invalid for credit hour with')
        print(
            json.dumps(
                serializer.errors,
                indent=3
            )
        )


with transaction.atomic():
    run()
