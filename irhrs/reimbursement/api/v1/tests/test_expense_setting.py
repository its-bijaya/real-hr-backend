from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience, RHRSAPITestCase
from irhrs.reimbursement.constants import TRAVEL, OTHER
from irhrs.reimbursement.models import ExpenseApprovalSetting
from irhrs.reimbursement.utils.helper import calculate_total, calculate_advance_amount


class TestEmployeeEducationDetail(RHRSTestCaseWithExperience):
    organization_name = 'Facebook'

    users = [
        ('emaila@test.com', 'password', 'Male', 'Clerka'),
        ('emailb@test.com', 'password', 'Male', 'Clerkb'),
        ('emailc@test.com', 'password', 'Male', 'Clerkc'),
        ('emaild@test.com', 'password', 'Male', 'Clerkd'),
    ]

    def setUp(self):
        super().setUp()
        self.kwargs = {
            'organization_slug': self.organization.slug
        }
        self.client.force_login(self.admin)

    @property
    def expense_setting_url(self):
        return reverse(
            'api_v1:reimbursement:reimbursement-setting-list',
            kwargs=self.kwargs
        )

    @property
    def data(self):
        return {
            "advance_code": "111",
            "approve_multiple_times": False,
            "options": [
                "Cash",
                "Cheque",
                "Transfer",
                "Deposit"
            ],
            "approvals": [
                {
                    "approve_by": "Employee",
                    "employee": [self.created_users[1].id]
                },
                {
                    "approve_by": "Employee",
                    "employee": [self.created_users[2].id]
                },
                {
                    "approve_by": "Employee",
                    "employee": [self.created_users[3].id]
                }
            ],
            "settlement_approvals": [
                {
                    "approve_by": "Employee",
                    "employee": [self.created_users[1].id]
                },
                {
                    "approve_by": "Employee",
                    "employee": [self.created_users[2].id]
                }
            ]
        }

    def test_create_action(self):
        """
        Create setting with HR
        """
        """
        Create by admin with all permission
        """
        data = self.data.copy()
        approvals = data.get('approvals')
        response = self.client.post(
            path=self.expense_setting_url,
            data=data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED) 
        # qs = ExpenseApprovalSetting.objects.filter(organization=self.organization)
        # self.validate_data(results=data.get('approvals'), data=qs)

        """
        Try to create with duplicate data
        """
        approvals += [
            {
                "approve_by": "Supervisor",
                'supervisor_level': 'Second'
            },
            {
                "approve_by": "Supervisor",
                'supervisor_level': 'Second'
            }
        ]
        response = self.client.post(
            path=self.expense_setting_url,
            data=data,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            'Approval Setting got similar supervisor level.'
        )
        self.assertDictEqual(
            response.json(),
            {'approvals': ['Approval Setting got similar supervisor level.']}
        )

        """
        Try to create more then 5 data on approval setting
        """
        extra_data = [
            {
                "approve_by": "Supervisor",
                "supervisor_level": "First",
                "employee": []
            },
            {
                "approve_by": "Employee",
                "supervisor_level": None,
                "employee": [self.created_users[3].id]
            },
            {
                "approve_by": "Employee",
                "supervisor_level": None,
                "employee": [self.created_users[2].id]
            },
        ]
        data.update({
            'approvals': approvals + extra_data
        })
        response = self.client.post(
            path=self.expense_setting_url,
            data=data,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            'Approval Hierarchy can\'t be less than 1 or more than 5.'
        )
        self.assertDictEqual(
            response.json(),
            {'approvals': ["Approval Hierarchy can't be less than 1 or more than 5."]}
        )
        self._test_list_action()

    def _test_list_action(self):
        """
        validate list action of approval setting
        """
        response = self.client.get(path=self.expense_setting_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestReimbursementAmountCalculator(RHRSAPITestCase):
    organization_name = 'Organization'
    users = [
        ('admin@email.com', 'password', 'male'),
    ]

    def setUp(self):
        super().setUp()

    @staticmethod
    def get_detail(detail_type):
        if detail_type == 'Travel':
            return [
                       {
                           "detail_type": "Per diem",
                           "rate_per_day": 5,
                           "day": 7,
                       },
                       {
                           "detail_type": "Lodging",
                           "rate_per_day": 8,
                           "day": 12
                       },
                       {
                           "detail_type": "Other",
                           "day": 26,
                           "rate_per_day": 99,
                       }
                   ], 2705
        else:
            return [
                       {
                           "quantity": 7,
                           "rate": 10,
                       },
                       {
                           "quantity": 4,
                           "rate": 52,
                       }
                   ], 278

    @staticmethod
    def get_advance_data(detail_type):
        if detail_type == 'Travel':
            return [
                       {
                           "detail_type": "Per diem",
                           "rate_per_day": 5,
                           "day": 7,
                       },
                       {
                           "detail_type": "Lodging",
                           "rate_per_day": 8,
                           "day": 12
                       },
                       {
                           "detail_type": "Other",
                           "day": 26,
                           "rate_per_day": 99,
                       }
                   ], 2028.75
        else:
            return [
                       {
                           "quantity": 7,
                           "rate": 10,
                       },
                       {
                           "quantity": 4,
                           "rate": 52,
                       }
                   ], 278

    def test_case_for_calculate_total_utils(self):
        for detail_type in [TRAVEL, OTHER]:
            detail_type_data, total_amount = self.get_detail(detail_type)
            calculated_total_amount = calculate_total(
                detail_type_data,
                detail_type
            )
            self.assertEqual(calculated_total_amount, total_amount)

    def test_case_for_calculate_advance_amount_utils(self):
        with patch('irhrs.reimbursement.utils.helper.get_rate_per_type', return_value=0.75):
            for detail_type in [TRAVEL, OTHER]:
                advance_data, advance_amount = self.get_advance_data(detail_type)
                calculated_advance_amount = calculate_advance_amount(
                    advance_data,
                    detail_type,
                    organization=self.organization
                )
                self.assertEqual(calculated_advance_amount, advance_amount)
