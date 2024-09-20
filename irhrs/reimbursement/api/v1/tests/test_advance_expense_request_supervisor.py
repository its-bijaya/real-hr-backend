from django.urls.base import reverse
from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.reimbursement.api.v1.tests.factory import (
    ExpenseApprovalSettingFactory,
    ReimbursementSettingFactory
)
from irhrs.reimbursement.models.reimbursement import AdvanceExpenseRequest
from irhrs.users.models.supervisor_authority import UserSupervisor

REQUESTED, EMPLOYEE, SUPERVISOR = "Requested", "Employee", "Supervisor"


class TestAdvanceExpenseRequestSupervisor(RHRSTestCaseWithExperience):
    organization_name = 'Facebook'

    users = [
        ('emaila@test.com', 'password', 'Male', 'Clerka'),
        ('emailb@test.com', 'password', 'Male', 'Clerkb'),
        ('emailc@test.com', 'password', 'Male', 'Clerkc')
    ]

    @property
    def data(self):
        data = {
            "reason": "Test expense",
            "type": "Other",
            "associates": self.created_users[2].id,
            "description": "Test Expense",
            "detail[0]heading": "heading 1",
            "detail[0]particulars": "particulars 1",
            "detail[0]quantity": 1,
            "detail[0]rate": 120,
            "detail[0]remarks": "asdasdsad",
            "detail[1]heading": "heading 2",
            "detail[1]particulars": "particulars 2",
            "detail[1]quantity": 3,
            "detail[1]rate": 120,
            "detail[1]remarks": "asdasdsad",
        }
        return data

    @property
    def advance_expense_request_url(self):
        return reverse(
            f'api_v1:reimbursement:advance-expense-request-list',
            kwargs={
                'organization_slug': self.organization.slug
            }
        )

    def create_supervisor_approval_setting(self):
        ExpenseApprovalSettingFactory(
            organization=self.organization,
            approve_by=SUPERVISOR,
            supervisor_level="First",
            approval_level=1
        )

    def setUp(self):
        super().setUp()
        self.client.force_login(self.created_users[1])
        ReimbursementSettingFactory(organization=self.organization)
 
    def test_advance_request_for_user_with_no_supervisor(self):
        """
        conditions:
        1. No supervisor assigned.
        2. Only approver is supervisor

        for above condition, the post request should be bad.(400)
        """
        self.create_supervisor_approval_setting()
        response = self.client.post(
            path=self.advance_expense_request_url,
            data=self.data
        )
        error = {"non_field_errors": "No matching supervisor found. Please contact HR."}
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), error)

    def test_advance_expense_request_for_user_with_supervisors(self):
        """
        conditions:
        1. First level supervisor assigned.
        2. Only approver is supervisor.

        for above condition, the post request should be created.(201)
        """
        self.create_supervisor_approval_setting()

        UserSupervisor.objects.create(
            user=self.created_users[1],
            supervisor=self.created_users[2],
            authority_order=1
        )

        response = self.client.post(
            path=self.advance_expense_request_url,
            data=self.data
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            AdvanceExpenseRequest.objects.filter(
                employee=self.created_users[1],
                status=REQUESTED, 
                reason=self.data["reason"],
                description=self.data["description"]
            ).exists()
        )

    def test_advance_expense_request_for_first_level_employee_setting(self):
        """
        conditions:
        1. No supervisor assigned.
        2. First approver is employee
        3. Second approver is supervisor

        for above condition, the post request should be created.(201)
        """
        approval_setting = ExpenseApprovalSettingFactory(
            organization=self.organization,
            approve_by=EMPLOYEE,
            approval_level=1
        )
        ExpenseApprovalSettingFactory(
            organization=self.organization,
            approve_by=SUPERVISOR,
            supervisor_level="First",
            approval_level=2
        )

        approval_setting.employee.add(self.admin)

        response = self.client.post(
            path=self.advance_expense_request_url,
            data=self.data
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            AdvanceExpenseRequest.objects.filter(
                employee=self.created_users[1],
                status=REQUESTED, 
                reason=self.data["reason"],
                description=self.data["description"]
            ).exists()
        )

    def test_advance_expense_request_with_first_level_supervisor_setting(self):
        """
        conditions:
        1. No supervisor assigned.
        2. First approver is supervisor
        3. Second approver is employee

        for above condition, the post request should be bad. (400)
        """
        approval_setting = ExpenseApprovalSettingFactory(
            organization=self.organization,
            approve_by=EMPLOYEE,
            approval_level=2
        )
        ExpenseApprovalSettingFactory(
            organization=self.organization,
            approve_by=SUPERVISOR,
            supervisor_level="First",
            approval_level=1
        )

        approval_setting.employee.add(self.admin)

        response = self.client.post(
            path=self.advance_expense_request_url,
            data=self.data
        )

        self.assertEqual(response.status_code, 400)
        error = {"non_field_errors": "No matching supervisor found. Please contact HR."}
        self.assertEqual(response.json(), error)
