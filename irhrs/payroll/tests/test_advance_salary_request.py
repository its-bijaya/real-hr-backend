from unittest import mock
from unittest.mock import patch

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.payroll.tests.factory import AdvanceSalarySettingsFactory
from irhrs.payroll.tests.factory import HeadingFactory, UserExperiencePackageSlotFactory
from irhrs.payroll.tests.utils import PackageUtil
from datetime import date, timedelta
from django.urls import reverse
from rest_framework import status
from django.utils import timezone

from irhrs.users.models import UserSupervisor
from irhrs.users.models.experience import UserExperience
from irhrs.payroll.models.advance_salary_settings import AdvanceSalarySetting, ApprovalSetting, \
    AmountSetting
from irhrs.core.constants.payroll import SUPERVISOR, EMPLOYEE, FIRST, \
    REQUESTED, APPROVED, DENIED, CANCELED

from irhrs.payroll.tests.factory import OrganizationPayrollConfigFactory
from irhrs.organization.api.v1.tests.factory import FiscalYearFactory
from irhrs.core.utils.common import get_today


class AdvanceSalaryRequestTest(RHRSTestCaseWithExperience):
    users = [
        ('hr@user.com', 'password', 'Female', 'hr'),
        ('approverfirst@user.com', 'password', 'Male', 'Tech'),
        ('approversecond@user.com', 'password', 'Male', 'Normal'),
        ('approverthird@user.com', 'password', 'Female', 'trainee'),
        ('normal@user.com', 'password', 'Female', 'Tcch'),
        ('supervisor@user.com', 'password', 'Female', 'Normal'),
    ]
    organization_name = 'Google'
    division_name = "Programming"
    branch_name = "Kathmandu"
    division_ext = 123
    kwargs = {}

    TIME_OF_SERVICE_COMPLETION = 0
    REQUEST_LIMIT = 6
    REQUEST_INTERVAL = 60
    COMPLETE_PREVIOUS_REQUEST = True
    EXCLUDE_EMPLOYMENT_TYPE = True
    LIMIT_UPTO = 100000
    DISBURSEMENT_LIMIT_FOR_REPAYMENT = 6
    DEDUCTION_HEADING = None

    def _login(self, username):
        self.client.login(email=f"{username}@user.com", password='password')

    def _logout(self):
        self.client.logout()

    @property
    def payload(self):
        return {
            'disbursement_count_for_repayment': 6,
            'repayment_plan': [1, 1, 1, 1, 1, 1],
            'amount': 6,
            'requested_for': get_today(),
            'reason_for_request': "this remaks is for test",
            'documents': [],
        }

    def advance_salary_request_url(self, method, kwargs, mode=' '):
        return reverse(
            f"api_v1:payroll:advance-salary-request-{method}",
            kwargs=kwargs
        ) + f"?as={mode}"

    def _get_pk(self, data):
        return data['results'][0]['id']

    @property
    def advance_salary_frontend_url(self):
        return reverse(
            "api_v1:commons:frontend_links-list",
            kwargs={'type': 'advance-salary'}
        )

    def _create_advance_salary_settings(self):
        setting_fields = [
            'time_of_service_completion',
            'request_limit',
            'request_interval',
            'complete_previous_request',
            'limit_upto',
            'disbursement_limit_for_repayment',
            'deduction_heading'
        ]

        # as -> AdvacnceSalary
        as_setting_kwargs = {
            field: getattr(self, field.upper())
            for field in setting_fields
        }

        return AdvanceSalarySettingsFactory(
            organization=self.organization,
            **as_setting_kwargs
        )

    def _create_package(self):
        pass

    def setUp(self):
        super().setUp()
        self._login('hr')
        _timedelta = timedelta(days=200)
        today = get_today()
        fiscal_year = FiscalYearFactory(
            start_at=today - _timedelta,
            end_at=today + _timedelta,
            applicable_from=today - _timedelta,
            applicable_to=today + _timedelta,
            organization=self.organization,
        )
        OrganizationPayrollConfigFactory(
            start_fiscal_year=fiscal_year,
            organization=self.organization
        )
        heading = HeadingFactory(organization=self.organization)
        package = self.package_util
        normal_user_experience = UserExperience.objects.get(user=self.created_users[4])

        UserExperiencePackageSlotFactory(
            user_experience=normal_user_experience,
            package=package,
            active_from_date=normal_user_experience.start_date
        )

        UserSupervisor.objects.create(
            user=self.created_users[4],
            supervisor=self.created_users[2],
            user_organization=self.organization,
            supervisor_organization=self.organization,
            approve=True,
            deny=True,
            forward=True,
        )

        advance_salary_setting = AdvanceSalarySetting.objects.create(
            organization=self.organization,
            time_of_service_completion=0,
            request_limit=10,
            request_interval=0,
            complete_previous_request=True,
            limit_upto=100000,
            disbursement_limit_for_repayment=6,
            deduction_heading=heading,

        )
        AmountSetting.objects.create(
            advance_salary_setting=advance_salary_setting,
            payroll_heading=heading,
            multiple=300,

        )
        ApprovalSetting.objects.create(
            advance_salary_setting=advance_salary_setting,
            approve_by=EMPLOYEE,
            employee=self.created_users[1],
            approval_level=1
        )
        ApprovalSetting.objects.create(
            advance_salary_setting=advance_salary_setting,
            approve_by=SUPERVISOR,
            supervisor_level=FIRST,
            employee=self.created_users[2],
            approval_level=2
        )

    @property
    def package_util(self):
        return PackageUtil(organization=self.organization).create_package()


    def check_advance_salary_request_as_hr(self):
        self._login('hr')
        self.kwargs = {
            'organization_slug': self.organization.slug,
        }
        url = self.advance_salary_request_url('list', self.kwargs, "hr")
        response = self.client.get(
            url,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json()
        )
        request_status = response.data['results'][0]['status']
        self._logout()
        return request_status


    def _request_advance_salary(self):
        self.kwargs = {
            'organization_slug': self.organization.slug,
        }
        url = self.advance_salary_request_url('list', self.kwargs)
        with patch("irhrs.payroll.utils.advance_salary.AdvanceSalaryRequestValidator.limit_amount",
                   new_callable=mock.PropertyMock) as limit_amount, \
            patch(
                "irhrs.payroll.utils.advance_salary.AdvanceSalaryRequestValidator.salary_payable",
                new_callable=mock.PropertyMock) as salary_payable:
            limit_amount.return_value = 10000
            salary_payable.return_value = 200000
            response = self.client.post(
                url,
                data=self.payload,
                format='json'
            )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.json()
        )

        response = self.client.get(
            url,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json()
        )

    def test_approve_advance_salary_request(self):
        self._login('normal')
        self._request_advance_salary()
        self._logout()

        response_status = self.check_advance_salary_request_as_hr()
        self.assertEqual(
            response_status,
            REQUESTED
        )

        # To approve request as -> EMPLOYEE 
        self._login('approverfirst')
        response = self.client.get(
            self.advance_salary_frontend_url,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json()
        )
        self.assertEqual(
            response.data['stats']['Requested'],
            1,
        )
        pk = self._get_pk(response.data)
        self.kwargs['pk'] = pk
        url = self.advance_salary_request_url('detail', self.kwargs, "approver")
        response = self.client.get(
            url,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json()
        )
        self.assertEqual(
            response.data['approvals'][0].get('role'),
            'Employee',
            response.json()
        )

        # Approving advance salary request as -> approver 

        url = self.advance_salary_request_url('approve', self.kwargs, "approver")
        response = self.client.post(
            url,
            data={'remarks': 'Test remarks'},
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json()
        )
        self.assertEqual(
            response.data['message'],
            'Approved Request.'
        )
        self._logout()

        # View Request as -> Supervisor from extra app icon
        self._login('approversecond')
        response = self.client.get(
            self.advance_salary_frontend_url,
            format='json'
        )
        self.assertEqual(
            response.data['stats']['Requested'],
            1
        )

        pk = self._get_pk(response.data)
        self.kwargs['pk'] = pk
        url = self.advance_salary_request_url('detail', self.kwargs, "approver")
        response = self.client.get(
            url,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json()
        )
        self.assertEqual(
            response.data['approvals'][1].get('role'),
            'Supervisor',
            response.json()
        )

        # Request Advance Salary request as -> Supervisor from Supervisor section
        self.kwargs = {
            'organization_slug': self.organization.slug,
        }
        url = self.advance_salary_request_url('list', self.kwargs, "supervisor")
        response = self.client.get(
            url,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json()
        )

        pk = self._get_pk(response.data)
        self.kwargs['pk'] = pk
        url = self.advance_salary_request_url('detail', self.kwargs, "supervisor")
        response = self.client.get(
            url,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json()
        )
        self.assertEqual(
            response.data['approvals'][1].get('role'),
            'Supervisor',
            response.json()
        )

        # Approve Advance Salary request as supervisor 
        url = self.advance_salary_request_url('approve', self.kwargs, "supervisor")
        response = self.client.post(
            url,
            data={'remarks': 'Test remarks from Supervisor'},
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json()
        )
        self.assertEqual(
            response.data['message'],
            'Approved Request.'
        )
        self._logout()

        # Deny or Proceed Advance Salary request as HR 
        response_status = self.check_advance_salary_request_as_hr()
        self.assertEqual(
            response_status,
            APPROVED
        )

    def test_deny_advance_salary_request_as_approver(self):
        self._login('normal')
        self._request_advance_salary()
        self._logout()

        response_status = self.check_advance_salary_request_as_hr()
        self.assertEqual(
            response_status,
            REQUESTED
        )

        # To Deny request as -> EMPLOYEE 
        self._login('approverfirst')
        response = self.client.get(
            self.advance_salary_frontend_url,
            format='json'
        )
        self.assertEqual(
            response.data['stats']['Requested'],
            1,
            response.json()
        )
        pk = self._get_pk(response.data)
        self.kwargs['pk'] = pk
        url = self.advance_salary_request_url('detail', self.kwargs, "approver")
        response = self.client.get(
            url,
            format='json'
        )

        self.assertEqual(
            response.data['approvals'][0].get('role'),
            'Employee',
            response.json()
        )

        url = self.advance_salary_request_url('deny', self.kwargs, "approver")
        response = self.client.post(
            url,
            data={'remarks': 'Request is denied'},
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json()
        )
        self.assertEqual(
            response.data['message'],
            'Declined Request.'
        )
        self._logout()
        response_status = self.check_advance_salary_request_as_hr()
        self.assertEqual(
            response_status,
            DENIED
        )

    def test_deny_advance_salary_request_as_supervisor(self):
        self._login('normal')
        self._request_advance_salary()
        self._logout()

        response_status = self.check_advance_salary_request_as_hr()
        self.assertEqual(
            response_status,
            REQUESTED
        )

        # To Approve request as -> EMPLOYEE 

        self._login('approverfirst')
        response = self.client.get(
            self.advance_salary_frontend_url,
            format='json'
        )
        pk = self._get_pk(response.data)
        self.kwargs['pk'] = pk
        url = self.advance_salary_request_url('detail', self.kwargs, "approver")
        self.client.get(
            url,
            format='json'
        )
        url = self.advance_salary_request_url('approve', self.kwargs, "approver")
        self.client.post(
            url,
            data={'remarks': 'Request is approved'},
            format='json'
        )
        self._logout()

        # Request Advance Salary request as -> Supervisor from Supervisor section
        self._login('approversecond')
        self.kwargs = {
            'organization_slug': self.organization.slug,
        }
        url = self.advance_salary_request_url('list', self.kwargs, "supervisor")
        response = self.client.get(
            url,
            format='json'
        )
        pk = self._get_pk(response.data)
        self.kwargs['pk'] = pk
        url = self.advance_salary_request_url('detail', self.kwargs, "supervisor")
        self.client.get(
            url,
            format='json'
        )
        # Deny Advance Salary request as supervisor 
        url = self.advance_salary_request_url('deny', self.kwargs, "supervisor")
        response = self.client.post(
            url,
            data={'remarks': 'Your request is denied'},
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json()
        )
        self.assertEqual(
            response.data['message'],
            'Declined Request.'
        )
        self._logout()
        response_status = self.check_advance_salary_request_as_hr()
        self.assertEqual(
            response_status,
            DENIED
        )

    def test_deny_own_advance_salary_request(self):
        self._login('normal')
        self.kwargs = {
            'organization_slug': self.organization.slug,
        }
        url = self.advance_salary_request_url('list', self.kwargs)
        with patch("irhrs.payroll.utils.advance_salary.AdvanceSalaryRequestValidator.limit_amount",
                   new_callable=mock.PropertyMock) as limit_amount, \
            patch(
                "irhrs.payroll.utils.advance_salary.AdvanceSalaryRequestValidator.salary_payable",
                new_callable=mock.PropertyMock) as salary_payable:
            limit_amount.return_value = 10000
            salary_payable.return_value = 200000
            self.client.post(
                url,
                data=self.payload,
                format='json'
            )
        response = self.client.get(
            url,
            format='json'
        )
        pk = self._get_pk(response.data)
        self.kwargs['pk'] = pk
        url = self.advance_salary_request_url('cancel', self.kwargs)
        response = self.client.post(
            url,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json()
        )
        self.assertEqual(
            response.data['detail'],
            'Successfully canceled request.',
            response.json()
        )
        self._logout()
        response_status = self.check_advance_salary_request_as_hr()
        self.assertEqual(
            response_status,
            CANCELED
        )

    def test_deny_advance_salary_request_as_hr(self):
        self._login('normal')
        self._request_advance_salary()
        self._logout()
        response_status = self.check_advance_salary_request_as_hr()
        self.assertEqual(
            response_status,
            REQUESTED
        )
        self._login('hr')
        self.kwargs = {
            'organization_slug': self.organization.slug,
        }
        url = self.advance_salary_request_url('list', self.kwargs, "hr")
        response = self.client.get(
            url,
            format='json'
        )
        pk = self._get_pk(response.data)
        self.kwargs['pk'] = pk
        url = self.advance_salary_request_url('deny', self.kwargs, "hr")
        response = self.client.post(
            url,
            data={'remarks': 'Deny by HR'},
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json()
        )
        self.assertEqual(
            response.data['message'],
            'Declined Request.',
            response.json()
        )
        response_status = self.check_advance_salary_request_as_hr()
        self.assertEqual(
            response_status,
            DENIED
        )

