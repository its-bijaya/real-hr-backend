from datetime import timedelta
from irhrs.users.api.v1.tests.factory import UserFactory
from irhrs.common.api.tests.common import BaseTestCase


from irhrs.attendance.api.v1.tests.utils import create_credit_hour_request, punch_for_credit_hour
from irhrs.attendance.tasks.credit_hours import generate_credit_hours_for_approved_credit_hours
from irhrs.attendance.utils.credit_hours import get_credit_leave_account_qs
from irhrs.core.utils.common import get_yesterday

from irhrs.leave.constants.model_constants import ADDED


class TestCreditHourForLeaveDays(BaseTestCase):

    def _test_credit_hour_for_leave_is_granted(self):
        # TODO: @ravi fix this test and enable it
        test_cases = [
            # approved leave, approve credit, than work for credit hours only
            {
                'desc': "request: 2, worked:2, grant: 2",
                'early_delta': 60 * 5,  # 5 hour late in
                'late_delta': 60 * 2,  # 2 hour overtime
                'leave_max_balance': 180,
                'existing_balance': 0,
                'requested_duration': timedelta(hours=2),
                'expected_balance_added': 120,
            },
        ]
        for test_case in test_cases:
            user = UserFactory()
            date = get_yesterday()
            early_delta = test_case['early_delta']
            late_delta = test_case['late_delta']
            leave_max_balance = test_case['leave_max_balance']
            existing_balance = test_case['existing_balance']
            requested_duration = test_case['requested_duration']
            expected_balance_added = test_case['expected_balance_added']

            create_credit_hour_request(
                user,
                date,
                requested_duration,
                leave_max_balance=leave_max_balance,
                balance=existing_balance
            )
            timesheet = punch_for_credit_hour(
                user, date, early_delta, late_delta)
            timesheet.leave_coefficient = 'Full Leave'
            timesheet.save()

            generate_credit_hours_for_approved_credit_hours()

            leave_account = get_credit_leave_account_qs().filter(user=user).first()
            assert leave_account, "Leave account does not exist"
            history = leave_account.history.difference().first()
            self.assertEqual(history.added, expected_balance_added,
                             test_case.get('desc'))
            self.assertEqual(history.action, ADDED,
                             test_case.get('desc'))
