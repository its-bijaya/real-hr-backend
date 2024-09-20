from datetime import date, time, timedelta
from unittest.mock import patch

from irhrs.common.api.tests.common import BaseTestCase
from irhrs.core.constants.organization import LEAVE as LEAVE_FISCAL_CATEGORY
from irhrs.core.utils.common import combine_aware
from irhrs.hris.api.v1.serializers.onboarding_offboarding import EmploymentReviewSerializer
from irhrs.hris.api.v1.tests.factory import ChangeTypeFactory
from irhrs.leave.api.v1.tests.factory import MasterSettingFactory, LeaveTypeFactory, \
    LeaveRuleFactory, RenewalRuleFactory, LeaveAccountFactory
from irhrs.leave.tasks import renew_leave_balance
from irhrs.organization.api.v1.tests.factory import FiscalYearFactory
from irhrs.users.api.v1.tests.factory import UserFactory


class TestProportionateBalanceForContractRenewal(BaseTestCase):

    def test_proportionate_balance_for_renewal(self):
        # user joined the company and details were fed.
        user = UserFactory()
        current_experience = user.current_experience
        detail = user.detail

        start, end = date(2017, 1, 1), date(2017, 12, 31)
        detail.joined_date = date(2017, 1, 1)
        current_experience.start_date = date(2017, 1, 1)
        current_experience.end_date = date(2017, 6, 30)
        initial_balance = 365
        current_experience.save()
        detail.save()

        FiscalYearFactory(
            organization=user.detail.organization,
            start_at=start,
            applicable_from=start,
            end_at=end,
            applicable_to=end,
            category=LEAVE_FISCAL_CATEGORY
        )

        master_setting = MasterSettingFactory(
            organization=user.detail.organization,
            effective_from=start,
            renewal=True,
            proportionate_leave=True,
        )
        leave_type = LeaveTypeFactory(master_setting=master_setting)
        leave_rule = LeaveRuleFactory(
            leave_type=leave_type,
            is_paid=True,
            proportionate_on_joined_date=True,
            proportionate_on_contract_end_date=True,
        )
        RenewalRuleFactory(rule=leave_rule, duration=1, initial_balance=initial_balance)
        LeaveAccountFactory(
            rule=leave_rule,
            user=user,
            usable_balance=0,
            balance=0,
            last_accrued=None,
            next_accrue=None,
            last_renewed=None,
            next_renew=None,
            last_deduction=None,
            next_deduction=None,
        )
        # at night, the tasks ran, and granted balance according to the end date.
        with patch(
            'django.utils.timezone.now',
            return_value=combine_aware(start, time(10, 0))
        ):
            renew_leave_balance()
        usable_balance = user.leave_accounts.values_list('usable_balance', flat=True).first()
        self.assertEqual(
            usable_balance,
            (current_experience.end_date - start).days + 1
        )

        # time passed, one day HR decided to renew the contract 1 month before contract expiration.
        one_month_before_contract_expiry = current_experience.end_date - timedelta(days=30)
        change_type = ChangeTypeFactory(
            organization=user.detail.organization,
            affects_experience=True,
            affects_leave_balance=True,
        )
        review = EmploymentReviewSerializer().create(
            {
                'employee': user,
                'change_type': change_type
            }
        )
        review_detail = review.detail
        current_experience.id = None
        current_experience.end_date = end
        current_experience.start_date = one_month_before_contract_expiry
        current_experience.upcoming = True
        current_experience.save()
        review_detail.new_experience = current_experience
        review_detail.save()
        with patch(
            'django.utils.timezone.now',
            return_value=combine_aware(one_month_before_contract_expiry, time(10, 0))
        ):
            EmploymentReviewSerializer.calculate_proportionate_leave_balance(review)
            final_balance = review_detail.leave_changes.values_list('update_balance',
                                                                    flat=True).first()
            self.assertEqual(final_balance, initial_balance)
