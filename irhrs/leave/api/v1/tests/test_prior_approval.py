from django.urls import reverse
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.leave.api.v1.tests.factory import (
    LeaveAccountFactory,
    LeaveRuleFactory,
    LeaveTypeFactory,
    MasterSettingFactory,
)
from rest_framework import status
from irhrs.leave.models.rule import PriorApprovalRule


class TestRequirePriorApproval(RHRSAPITestCase):

    users = [
        ("normal@gmail.com", "password", "male")
    ]
    organization_name = "AayuBank"

    def setUp(self):
        super().setUp()
        self.client.force_login(self.created_users[0])
        self.master_setting = MasterSettingFactory(
            organization=self.organization,
            require_prior_approval=True,
            admin_can_assign=True,
            paid=True,
        )
        self.leave_type = LeaveTypeFactory(master_setting=self.master_setting)
        self.leave_rule = LeaveRuleFactory(
            leave_type=self.leave_type,
            require_prior_approval=True
        )
        self.leave_account = LeaveAccountFactory(
            rule=self.leave_rule, user=self.created_users[0]
        )

        self.url = reverse(
            "api_v1:leave:leave-type-detail",
            kwargs={
                "organization_slug": self.organization.slug,
                "pk": self.leave_rule.id,
            },
        )
        self.prior_approvals = [
            {
                "prior_approval_request_for": 2,
                "prior_approval": 4,
                "prior_approval_unit": "Days",
            },
            {
                "prior_approval_request_for": 5,
                "prior_approval": 97,
                "prior_approval_unit": "Hours",
            },
        ]

    def payload(self, approval):
        return {
            "name": "Timeoff rule",
            "description": "This is time of rule",
            "is_paid": True,
            "employee_can_apply": False,
            "admin_can_assign": True,
            "require_prior_approval": True,
            "leave_type": self.leave_type.id,
            "depletion_leave_types": [],
            "prior_approval_rules": approval,
        }
    
    def test_valid_prior_approval_rule(self):
        response = self.client.put(
            self.url, self.payload(self.prior_approvals), format="json"
        )
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data
        )

        prior_rule = list(
            PriorApprovalRule.objects.values_list(
                "prior_approval_request_for", "prior_approval", "prior_approval_unit"
            )
        )

        self.assertEqual(prior_rule, [(2, 4, "Days"), (5, 97, "Hours")])

    def test_invalid_prior_approval_rule(self):
        invalid_approval_rule = [
            {
                "prior_approval_request_for": 2,
                "prior_approval": 2,
                "prior_approval_unit": "Hours",
            },
            {
                "prior_approval_request_for": 1,
                "prior_approval": 1,
                "prior_approval_unit": "Minutes",
            },
        ]

        response = self.client.put(
            self.url, self.payload(invalid_approval_rule), format="json"
        )
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, response.data
        )

        self.assertEqual(
            response.json().get("prior_approval_request_for")[1],
            "Must be greater than previous prior approval request for.",
        )

        self.assertEqual(
            response.json().get("prior_approval")[1],
            "Must be greater than previous prior approval."
        )

    def test_get_prior_approval_request(self):
        self.client.put(
            self.url, self.payload(self.prior_approvals), format="json"
        )
        response = self.client.get(self.url)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data
        )

        self.assertEqual(
            response.json().get("prior_approval_rules"), self.prior_approvals
        )

    def test_prior_approval_rule_cannot_be_zero_or_less(self):
        url = reverse(
            "api_v1:leave:leave-type-list",
            kwargs={
                'organization_slug': self.organization.slug
            }
        )

        zero_rule = [
            {
                "prior_approval_request_for": 0,
                "prior_approval": 1,
                "prior_approval_unit": "Days"
            }
        ]

        response = self.client.post(url, self.payload(zero_rule), format="json")
        self.assertEqual(
            response.status_code, 400, response.data
        )
        self.assertEqual(
            response.json().get("prior_approval_request_for"), 
            ["Only positive value is supported."]
        )



