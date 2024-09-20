import factory
from factory.django import DjangoModelFactory

from irhrs.reimbursement.models import ExpenseApprovalSetting, AdvanceExpenseRequest, \
    ExpenseSettlement
from irhrs.reimbursement.models.setting import ReimbursementSetting
from irhrs.core.constants.payroll import PENDING


class ExpenseApprovalSettingFactory(DjangoModelFactory):
    class Meta:
        model = ExpenseApprovalSetting

class ReimbursementSettingFactory(DjangoModelFactory):
    class Meta:
        model = ReimbursementSetting

class AdvanceExpenseRequestFactory(DjangoModelFactory):
    class Meta:
        model = AdvanceExpenseRequest


class AdvanceExpenseRequestApprovalFactory(DjangoModelFactory):
    pass


class AdvanceExpenseRequestHistoryFactory(DjangoModelFactory):
    pass


def expense_settlement_detail(number):
    data = {
        "reason": "Medical expenses during survey.",
        "heading": 'Medical expense',
        "particulars": 'Paracetamol',
        "quantity": number,
        "rate": 120 * number,
        "remarks": "Cost was more than expected.",
        "bill_no": 'A23112E3'
    }
    return data


class ExpenseSettlementFactory(DjangoModelFactory):
    detail = factory.Sequence(expense_settlement_detail)

    class Meta:
        model = ExpenseSettlement

    @factory.post_generation
    def recipient(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for recipient in extracted:
                self.recipient.add(recipient)

        self.approvals.create(
            status=PENDING,
            level=1,
        )
