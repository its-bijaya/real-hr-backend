from irhrs.common.api.tests.common import BaseTestCase as TestCase

from irhrs.leave.tasks import calculate_collapse_balance


class TestLeaveUtils(TestCase):

    def test_pending_compensatory_leave_collapse(self):
        reversed_date_grants = [1, 1, 1, 1]
        result = list()
        pending = 1
        for collapse in reversed_date_grants:
            pending, col = calculate_collapse_balance(pending, collapse)
            result.append(col)
        self.assertEqual(result, [0, 1, 1, 1])

        reversed_date_grants = [1, 1, 1, 1]
        result = list()
        pending = 2.5
        for collapse in reversed_date_grants:
            pending, col = calculate_collapse_balance(pending, collapse)
            result.append(col)
        self.assertEqual(result, [0, 0, 0.5, 1])

        reversed_date_grants = [0.5, 1, 1, 1]
        result = list()
        pending = 2.5
        for collapse in reversed_date_grants:
            pending, col = calculate_collapse_balance(pending, collapse)
            result.append(col)
        self.assertEqual(result, [0, 0, 0, 1])
