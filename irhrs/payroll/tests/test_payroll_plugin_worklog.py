from datetime import datetime

from irhrs.core.constants.payroll import APPROVED
from irhrs.core.utils.common import get_today
from django.test import tag

from irhrs.payroll.tests.test_payroll_calculator_internal_plugins import \
    TestCalculatorInternalPluginsBase
from irhrs.payroll.tests.utils import PackageUtil
from irhrs.reimbursement.api.v1.tests.factory import ExpenseSettlementFactory
from irhrs.reimbursement.models import SettlementHistory
from irhrs.task.api.v1.tests.factory import WorkLogFactory, ProjectFactory, ActivityFactory
from irhrs.task.models import WorkLogAction, SENT
from irhrs.task.models.settings import UserActivityProject


class TestWorkLogPlugin(TestCalculatorInternalPluginsBase):
    class package_util_class(PackageUtil):
        RULE_CONFIG = {
            'addition_with_plugin': {
                # __TEST_PLUG_TITLE__ is a plugin
                'rules': ['__EMPLOYEE_AMOUNT_FROM_WORKLOG__ * 10'],
                'payroll_setting_type': 'Salary Structure', 'type': 'Addition',
                'duration_unit': 'Monthly', 'taxable': True,
                'absent_days_impact': True
            }
        }

    def data_setup_before_generation(self):
        tzinfo = get_today(with_time=True).tzinfo
        employee = self.employee

        self.project = ProjectFactory(is_billable=False)
        self.activity = ActivityFactory(unit="hour")
        UserActivityProject.objects.create(
            user=self.employee,
            project=self.project,
            activity=self.activity,
            is_billable=True
        )
        self.worklog1 = WorkLogFactory(
            sender=employee, project=self.project, total_amount=500, activity=self.activity
        )
        self.worklog_action = WorkLogAction.objects.create(
            worklog=self.worklog1,
            action=SENT,
            remarks="Sending worklog to payroll.",
            action_performed_by=self.admin,
            action_date=datetime(2017, 1, 1, 10, 0, tzinfo=tzinfo)
        )

        self.project2 = ProjectFactory(is_billable=False)
        self.activity2 = ActivityFactory(unit="hour")
        UserActivityProject.objects.create(
            user=self.employee,
            project=self.project2,
            activity=self.activity,
            is_billable=False
        )
        UserActivityProject.objects.create(
            user=self.employee,
            project=self.project2,
            activity=self.activity2,
            is_billable=True
        )

        self.worklog2 = WorkLogFactory(
            sender=employee, project=self.project2, total_amount=1500, activity=self.activity2
        )
        WorkLogAction.objects.create(
            worklog=self.worklog2,
            action=SENT,
            remarks="Sending worklog to payroll.",
            action_performed_by=self.admin,
            action_date=datetime(2017, 1, 1, 10, 0, tzinfo=tzinfo)
        )

    @tag("plugin")
    def test_expense_settlement_plugin(self):
        expected = self.worklog1.total_amount + self.worklog2.total_amount
        self.assertEquals(
            self.get_heading_value('Addition with plugin')['amount'],
            expected * 10  # we have * 10 in rule
        )
