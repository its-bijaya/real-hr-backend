import datetime

from django.utils import timezone

from irhrs.common.api.tests.common import BaseTestCase
from irhrs.core.utils import get_system_admin
from irhrs.core.utils.common import get_today
from irhrs.hris.api.v1.tests.factory import EmployeeSeparationFactory
from irhrs.hris.models import LeaveEncashmentOnSeparation
from irhrs.hris.utils import encash_leave_on_separation
from irhrs.leave.api.v1.tests.factory import LeaveAccountFactory, RenewalRuleFactory, \
    LeaveRequestFactory, LeaveTypeFactory, LeaveRuleFactory
from irhrs.leave.constants.model_constants import APPROVED, GENERATED, EMPLOYEE_SEPARATION
from irhrs.leave.models import LeaveSheet, LeaveAccountHistory
from irhrs.leave.models.account import LeaveEncashment, LeaveEncashmentHistory
from irhrs.organization.api.v1.tests.factory import FiscalYearFactory
from irhrs.users.api.v1.tests.factory import UserFactory


class LeaveEncashmentOnSeparationTestMixin:
    def set_up_separation_data(self):
        fiscal_start_at = datetime.date(get_today().year, 1, 1)
        fiscal_end_at = datetime.date(get_today().year, 12, 31)

        self.normal = self.created_users[1]
        self.separation = EmployeeSeparationFactory(
            employee=self.normal,
            release_date=datetime.date(fiscal_end_at.year, 11, 30)
        )

        self.fiscal_year = FiscalYearFactory(
            organization=self.organization,
            start_at=fiscal_start_at,
            end_at=fiscal_end_at,
            applicable_from=fiscal_start_at,
            applicable_to=fiscal_end_at
        )

        self.leave_account = LeaveAccountFactory(
            user=self.normal,
            balance=20,
            usable_balance=20
        )

        master_setting = self.leave_account.rule.leave_type.master_setting
        master_setting.effective_from = timezone.now().date()
        master_setting.save()

        self.master_setting = master_setting

        # this leave account is unpaid leave and should be excluded
        leave_type = LeaveTypeFactory(master_setting=master_setting)
        leave_rule = LeaveRuleFactory(leave_type=leave_type, is_paid=False)
        self.unpaid_leave_account = LeaveAccountFactory(user=self.normal, rule=leave_rule)

        self.leave_rule = self.leave_account.rule
        self.leave_rule.is_paid = True
        self.leave_rule.save()

        self.renewal_rule = RenewalRuleFactory(initial_balance=365, rule=self.leave_rule)

        self.leave_request = LeaveRequestFactory(
            user=self.normal,
            recipient=self.admin,
            leave_rule=self.leave_rule,
            leave_account=self.leave_account,
            balance=5,
            status=APPROVED
        )
        LeaveSheet.objects.bulk_create(
            [
                LeaveSheet(
                    request=self.leave_request,
                    leave_for=self.fiscal_year.start_at + timezone.timedelta(days=i),
                    balance=1,

                    # ignored details, just set because not null
                    start=timezone.now(),
                    end=timezone.now()
                )
                for i in range(1, 6)
            ]
        )
        LeaveAccountHistory.objects.create(
            account=self.leave_account,
            user=self.normal,
            actor=self.admin,
            action="Added",
            renewed=365,
            carry_forward=10,
            previous_balance=10,
            previous_usable_balance=10,
            new_balance=375,
            new_usable_balance=375
        )

        user_detail = self.normal.detail
        user_detail.joined_date = datetime.date(fiscal_start_at.year, 2, 1)
        user_detail.save()

        days_in_that_year = (self.fiscal_year.end_at - self.fiscal_year.start_at).days + 1
        effective_days = days_in_that_year - 31 - 31
        self.expected_proportionate = round(365 / days_in_that_year * effective_days, 2)


class EncashLeaveOnSeparationTestCase(LeaveEncashmentOnSeparationTestMixin, BaseTestCase):
    def setUp(self) -> None:
        normal = UserFactory()
        self.organization = normal.detail.organization

        self.admin = UserFactory(_organization=self.organization)
        self.created_users = [self.admin, normal]
        self.set_up_separation_data()

    def test_encash_leave_on_separation(self):
        encash_leave_on_separation(self.separation)

        encashment = LeaveEncashment.objects.filter(
            user=self.normal,
            account=self.leave_account
        ).first()
        self.assertIsNotNone(encashment, LeaveEncashment.objects.all())
        self.assertEqual(encashment.status, GENERATED)
        self.assertEqual(encashment.balance, round(self.expected_proportionate + 10 - 5, 2))
        self.assertEqual(encashment.source, EMPLOYEE_SEPARATION)

        self.assertTrue(
            LeaveEncashmentHistory.objects.filter(
                actor=get_system_admin(),
                encashment=encashment,
                action=GENERATED,
                previous_balance=None,
                new_balance=encashment.balance,
                remarks="encashed during employee separation"
            )
        )

        # -- leave encashment should create records for encashment_edit_on_separation --
        # When off boarding is applied, leave accounts are archived, but they should be displayed
        # completed this feature in two parts
        # 1. create LeaveEncashmentOnSeparation while applying off boarding if not exists already
        #     (This Case)
        # 2. Display leave accounts whose LeaveEncashmentOnSeparation exists regardless of their
        #    account status
        #    (Satisfied in Report API)
        encashment_edit = LeaveEncashmentOnSeparation.objects.filter(
            separation=self.separation,
            leave_account=self.leave_account,
            encashment_balance=encashment.balance
        ).first()
        self.assertIsNotNone(encashment_edit, LeaveEncashmentOnSeparation.objects.all())

        self.assertTrue(
            encashment_edit.history.filter(
                actor=get_system_admin(),
                previous_balance=encashment.balance,
                new_balance=encashment.balance,
                remarks='Recorded while applying off-boarding'
            ).exists(),
            encashment_edit.history.all()
        )

    def test_encash_with_no_renewal_rule(self):
        self.renewal_rule.delete()
        encash_leave_on_separation(self.separation)

        encashment = LeaveEncashment.objects.filter(
            user=self.normal,
            account=self.leave_account
        ).first()
        self.assertIsNotNone(encashment, LeaveEncashment.objects.all())
        self.assertEqual(encashment.status, GENERATED)
        self.assertEqual(encashment.balance, round(self.leave_account.usable_balance))
        self.assertEqual(encashment.source, EMPLOYEE_SEPARATION)
