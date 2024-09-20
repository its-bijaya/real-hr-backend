import random

from django.contrib.auth import get_user_model
from django.urls import reverse
from faker import Factory
from rest_framework import status

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.core.constants.payroll import SUPERVISOR, EMPLOYEE
from irhrs.organization.api.v1.tests.factory import EmploymentStatusFactory
from irhrs.payroll.models import AdvanceSalarySetting, ApprovalSetting, AmountSetting
from irhrs.payroll.tests.factory import HeadingFactory


class TestEligibilitySetting(RHRSTestCaseWithExperience):
    users = [
        ('checktest@gmail.com', 'secretWorldIsThis', 'Male', 'Manager'),
    ]
    organization_name = "Google"
    division_name = "Programming"
    branch_name = "Kathmandu"
    division_ext = 123
    fake = Factory.create()
    user = get_user_model()
    kwargs = {}

    def setUp(self):
        super().setUp()
        self.employment_types = [EmploymentStatusFactory(organization=self.organization) for _ in
                                 range(3)]
        self.client.login(email=self.users[0][0], password=self.users[0][1])

    @property
    def advance_salary_url(self):
        return reverse(
            "api_v1:payroll:eligibility-setting-list",
            kwargs=self.kwargs
        )

    def test_advance_salary_create(self):
        """
        test creating setting for advance salary
        :return:
        """
        self.kwargs = {
            'organization_slug': self.organization.slug,
        }

        self._test_create_eligibility_setting()
        self._test_create_disbursement_setting()
        # self._test_create_limit_upto_setting()

    def _test_create_eligibility_setting(self):
        """
        create new eligibility setting
        :return:
        """
        self.kwargs.update({
            'setting_type': 'eligibility'
        })
        request_limit = random.randint(1, 12)
        _data = {
            "time_of_service_completion": random.randint(1, 365),
            "request_limit": request_limit,
            "request_interval": 365 // request_limit,
            "complete_pre_request": random.choice([True, False]),
            "excluded_employment_type": [
                employment_type.slug for employment_type in self.employment_types
            ]
        }
        response = self.client.post(
            self.advance_salary_url,
            data=_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        employment_type = _data.pop('excluded_employment_type')

        instance = AdvanceSalarySetting.objects.filter(organization=self.organization).first()
        self.validate_data(
            [_data],
            [instance]
        )
        self.assertSetEqual(
            set(employment_type),
            set(instance.excluded_employment_type.all().values_list('slug', flat=True))
        )

        """
        trying to update eligibility setting
        """
        _data.update({
            "request_limit": 2,
            "request_interval": 182,
            "excluded_employment_type": [self.employment_types[0].slug]
        })

        response = self.client.post(
            self.advance_salary_url,
            data=_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        employment_type = _data.pop('excluded_employment_type')

        instance = AdvanceSalarySetting.objects.filter(organization=self.organization).first()
        self.validate_data(
            [_data],
            [instance]
        )
        self.assertSetEqual(
            set(employment_type),
            set(instance.excluded_employment_type.all().values_list('slug', flat=True))
        )

        self._test_advance_salary_retrive()

    def _test_create_disbursement_setting(self):
        self.kwargs.update({
            'setting_type': 'disbursement'
        })

        _data = {
            "disbursement_limit_for_repayment": random.randint(1, 6),
            "deduction_heading": HeadingFactory(organization=self.organization).id
        }

        response = self.client.post(
            self.advance_salary_url,
            data=_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        instance = AdvanceSalarySetting.objects.filter(organization=self.organization).first()
        self.validate_data(
            [_data],
            [instance]
        )

        """
        trying to update disbursement setting
        """
        _data.update({
            "disbursement_limit_for_repayment": random.randint(1, 6),
            "deduction_heading": HeadingFactory(organization=self.organization).id
        })

        response = self.client.post(
            self.advance_salary_url,
            data=_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        instance = AdvanceSalarySetting.objects.filter(organization=self.organization).first()
        self.validate_data(
            [_data],
            [instance]
        )
        self._test_advance_salary_retrive()

    def _test_create_limit_upto_setting(self):
        self.kwargs.update({
            'setting_type': 'amount/limit'
        })

        _data = {
            "limit_upto": 100000
        }

        response = self.client.post(
            self.advance_salary_url,
            data=_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        instance = AdvanceSalarySetting.objects.filter(organization=self.organization).first()
        self.assertEqual(
            _data.get('limit_upto'),
            instance.limit_upto
        )

        """
        trying to update limit to setting
        """
        _data.update({
            "limit_upto": 320000
        })
        response = self.client.post(
            self.advance_salary_url,
            data=_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        instance = AdvanceSalarySetting.objects.filter(organization=self.organization).first()
        self.assertEqual(
            _data.get('limit_upto'),
            instance.limit_upto
        )

        self._test_advance_salary_retrive()

    def _test_advance_salary_retrive(self):
        response = self.client.get(
            self.advance_salary_url
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data
        if 'organization' in result:
            organization = result.pop('organization')
            self.assertEqual(
                organization.get('slug'),
                self.organization.slug
            )

        self.validate_data(
            [result],
            AdvanceSalarySetting.objects.filter(organization=self.organization)
        )


class TestAmountSetting(RHRSTestCaseWithExperience):
    # To be continued
    users = [
        ('checktest@gmail.com', 'secretWorldIsThis', 'Male', 'Manager'),
    ]
    organization_name = "Google"
    division_name = "Programming"
    branch_name = "Kathmandu"
    division_ext = 123
    fake = Factory.create()
    user = get_user_model()
    kwargs = {}

    def setUp(self):
        super().setUp()
        self.client.login(email=self.users[0][0], password=self.users[0][1])
        heading_rule = [
            {
                "condition": None,
                "rule": "equation",
                "rule_validator": {
                    "editable": True,
                    "numberOnly": True
                },
                "tds_type": "22"
            },
        ]
        self.payroll_headings = [HeadingFactory(
            organization=self.organization,
            rules=heading_rule
        ) for _ in range(3)]
        self.kwargs.update({
            'organization_slug': self.organization.slug
        })

    @property
    def amount_setting_url(self):
        action = ('list', 'detail')['pk' in self.kwargs]
        return reverse(
            f'api_v1:payroll:amount-setting-{action}',
            kwargs=self.kwargs
        )

    def test_create_action_for_amount_setting(self):
        _data = {
            'payroll_heading': [{
                'payroll_heading': heading.id,
                'multiple': random.randint(1, 4)
            } for heading in self.payroll_headings],
            'limit_upto': {
                'limit_upto': None
            }
        }
        response = self.client.post(
            self.amount_setting_url,
            data=_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.validate_data(
            results=_data.get('payroll_heading'),
            data=AmountSetting.objects.filter(
                advance_salary_setting__organization=self.organization
            ).order_by('payroll_heading')
        )

        self.validate_data(
            results=[_data.get('limit_upto')],
            data=AdvanceSalarySetting.objects.filter(
                organization=self.organization
            )
        )

        # invalid condition
        # pre-existing payroll heading
        _data.get('payroll_heading').append(
            {
                'payroll_heading': self.payroll_headings[0].id,
                'multiple': 3
            }
        )
        response = self.client.post(
            self.amount_setting_url,
            data=_data,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            'Amount Setting got similar payroll heading'
        )

        # try to submit empty data
        _data.update({
            'payroll_heading': [],
            'limit_upto': {
                'limit_upto': None
            }
        })

        response = self.client.post(
            self.amount_setting_url,
            data=_data,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            'Must provide at least one of the configuration value.'
        )

        self._test_list_action_for_amount_setting()

    def _test_list_action_for_amount_setting(self):
        response = self.client.get(
            self.amount_setting_url
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payroll_heading = response.json().get('payroll_heading')
        self.validate_data(
            results=payroll_heading,
            data=AmountSetting.objects.filter(
                advance_salary_setting__organization=self.organization
            )
        )

        limit_upto = response.json().get('limit_upto')
        self.validate_data(
            results=[limit_upto],
            data=AdvanceSalarySetting.objects.filter(
                organization=self.organization
            )
        )


class TestApprovalSetting(RHRSTestCaseWithExperience):
    users = [
        ('checktest@gmail.com', 'secretWorldIsThis', 'Male', 'Manager'),
        ('checktestabc@gmail.com', 'secretWorldIsThis', 'Male', 'Managera'),
    ]
    organization_name = "Google"
    division_name = "Programming"
    branch_name = "Kathmandu"
    division_ext = 123
    fake = Factory.create()
    user = get_user_model()
    kwargs = {}

    def setUp(self):
        super().setUp()
        self.client.login(email=self.users[0][0], password=self.users[0][1])
        self.kwargs.update({
            'organization_slug': self.organization.slug
        })

    @property
    def approval_setting_url(self):
        action = ('list', 'detail')['pk' in self.kwargs]
        return reverse(
            f'api_v1:payroll:approval-setting-{action}',
            kwargs=self.kwargs
        )

    def test_create_approval_setting(self):
        # valid dataset
        _data = {
            "approvals": [
                {
                    "approve_by": SUPERVISOR,
                    "supervisor_level": "First",
                    "approval_level": 1
                },
                {
                    "approve_by": EMPLOYEE,
                    "employee": self.user.objects.get(email=self.users[0][0]).id,
                    "approval_level": 2
                },
                {
                    "approve_by": EMPLOYEE,
                    "employee": self.user.objects.get(email=self.users[1][0]).id,
                    "approval_level": 3
                }
            ]
        }

        self._valid_create_action(data=_data)

        # invalid conditions

        # supervisor level field is required if approve by is selected as supervisor
        _data = {
            "approvals": [
                {
                    "approve_by": SUPERVISOR,
                    "approval_level": 4
                }
            ]
        }
        self._invalid_create_action(
            data=_data,
            field='supervisor_level',
            message='This field is required if approve_by is set to supervisor.'
        )

        # employee field is required if approve by is selected as employee
        _data = {
            "approvals": [
                {
                    "approve_by": EMPLOYEE,
                    "approval_level": 5
                }
            ]
        }
        self._invalid_create_action(
            data=_data,
            field='employee',
            message='This field is required if approve_by is set to employee.'
        )

        self._test_list_action_of_approval_setting()

    def _valid_create_action(self, data):
        response = self.client.post(
            self.approval_setting_url,
            data=data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        queryset = ApprovalSetting.objects.filter(
            advance_salary_setting__organization=self.organization
        ).order_by('approval_level')

        self.validate_data(
            data.get('approvals'),  # expected result
            queryset
        )

    def _invalid_create_action(self, data, field, message=None):
        response = self.client.post(
            self.approval_setting_url,
            data=data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        if message:
            self.assertEqual(response.json().get('approvals')[0].get(field)[0], message)

    def _test_list_action_of_approval_setting(self):
        response = self.client.get(
            self.approval_setting_url
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.validate_data(
            results=response.json().get('results'),
            data=ApprovalSetting.objects.filter(
                advance_salary_setting__organization=self.organization
            ).order_by('approval_level')
        )

    def test_same_employee_for_same_approval_setting(self):
        data = {
            "approvals": [
                {
                    "approve_by": EMPLOYEE,
                    "employee": self.user.objects.get(email=self.users[0][0]).id,
                    "approval_level": 2
                },
                {
                    "approve_by": EMPLOYEE,
                    "employee": self.user.objects.get(email=self.users[0][0]).id,
                    "approval_level": 3
                }
            ]
        }
        response = self.client.post(
            self.approval_setting_url,
            data=data,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            response.json().get('approvals'),
            ['Approval Setting got similar employee.']
        )
