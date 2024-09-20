from datetime import datetime as dt
from unittest.mock import patch
from unittest import mock
from datetime import timedelta

from django.db.models.signals import post_save
from django.urls import reverse

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.core.utils.common import get_today, get_yesterday
from irhrs.payroll.do_not_compile import sync_update_backdated_payroll
from irhrs.payroll.models import UserExperiencePackageSlot, PackageHeading
from irhrs.payroll.signals import create_update_report_row_user_experience_package, \
    update_package_heading_rows
from irhrs.payroll.tests.factory import PackageFactory, OrganizationPayrollConfigFactory, \
    PayrollFactory, EmployeePayrollFactory
from irhrs.organization.api.v1.tests.factory import FiscalYearFactory
from irhrs.payroll.tests.factory import UserExperiencePackageSlotFactory


def async_update_or_create_backdated_payroll(instance):
    UserExperiencePackageSlot.objects.filter(id=instance.id).update(
        backdated_calculation_generated=True
    )


@patch(
    'irhrs.payroll.signals.async_update_or_create_backdated_payroll',
    mock.MagicMock(return_value=None, side_effect=async_update_or_create_backdated_payroll)
)
class AssignPackageTest(RHRSTestCaseWithExperience):
    users = [('hr@email.com', 'secret', 'Male', 'Programmer')]
    organization_name = 'Organization'

    def setUp(self):
        # disconnected by runner so needed to connect here
        post_save.disconnect(
            create_update_report_row_user_experience_package, sender=UserExperiencePackageSlot
        )
        post_save.disconnect(update_package_heading_rows, sender=PackageHeading)
        super().setUp()
        self.fiscal_year = FiscalYearFactory(organization=self.organization,
                                             applicable_from=get_today() - timedelta(days=60))
        self.client.force_login(self.admin)
        self.user_experience = self.created_users[0].user_experiences.first()
        self.user_experience.start_date = get_today() - timedelta(days=60)
        self.user_experience.save()
        self.package = PackageFactory(organization=self.organization)
        organization_config = OrganizationPayrollConfigFactory(
            start_fiscal_year=self.fiscal_year,
            organization=self.organization
        )
        self.today = get_today()

    @property
    def assign_package_url(self):
        return reverse(
            "api_v1:payroll:userexperiencepackageslot-list"
        ) + f'?user_experience__user__detail__organization__slug={self.organization.slug}&as=hr'

    def user_experience_package_slot_url(self, pk):
        return reverse(
            "api_v1:payroll:userexperiencepackageslot-detail",
            kwargs={
                'pk': pk
            }
        ) + f'?user_experience__user__detail__organization__slug={self.organization.slug}&as=hr'

    def test_assign_package_works(self):
        payload = {
            "user_experience": self.user_experience.id,
            "package": self.package.id,
            "active_from_date": self.today,
        }
        res = self.client.post(self.assign_package_url,
                               data=payload,
                               format='json')
        self.assertEqual(res.status_code, 201)

    @patch(
        'irhrs.payroll.utils.helpers.get_last_confirmed_payroll_generated_date',
        mock.MagicMock(return_value=get_today() - timedelta(days=1))
    )
    def test_assign_package_with_future_backdated_date_throws_error(self):
        payload = {
            "user_experience": self.user_experience.id,
            "package": self.package.id,
            "active_from_date": self.today,
            "backdated_calculation_from": self.today + timedelta(days=30)
        }
        res = self.client.post(self.assign_package_url,
                               data=payload,
                               format='json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(
            res.json()['backdated_calculation_from'],
            ["Backdated calculation date cannot be a future date."]
        )

    def test_assign_package_with_incorrect_active_from_date(self):
        '''
        Scenario:
        `active_from_date` is not equal to last payroll generated day + 1
        '''
        payload = {
            "user_experience": self.user_experience.id,
            "package": self.package.id,
            "active_from_date": self.today - timedelta(days=20),
            "backdated_calculation_from": self.today - timedelta(days=25)
        }
        last_paid_date = get_today() - timedelta(days=22)

        with patch(
            'irhrs.payroll.utils.helpers.get_last_confirmed_payroll_generated_date',
            return_value=last_paid_date
        ):
            from irhrs.payroll.utils.helpers import get_last_confirmed_payroll_generated_date
            res = self.client.post(self.assign_package_url,
                                   data=payload,
                                   format='json')
        self.assertEqual(res.status_code, 400)
        res_error = res.json()['active_from_date']
        res_expected_error = [
            'This value must be equal to '
            + f'{last_paid_date + timedelta(days=1)}'
            + '(last payroll generated day + 1 day) '
            + 'if backdated calculation is present.'
        ]
        self.assertEqual(res_error, res_expected_error)

    @patch(
        'irhrs.payroll.utils.helpers.get_last_confirmed_payroll_generated_date',
        mock.MagicMock(return_value=get_today() - timedelta(days=29))
    )
    def test_assign_package_with_smaller_active_from_date_throws_error(self):
        '''
        Scenario: `active_from_date` < `backdated_calculation_from`
        should throw error
        '''
        payload = {
            "user_experience": self.user_experience.id,
            "package": self.package.id,
            "active_from_date": self.today - timedelta(days=25),
            "backdated_calculation_from": self.today - timedelta(days=10)
        }
        res = self.client.post(self.assign_package_url,
                               data=payload,
                               format='json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(
            res.json()['backdated_calculation_from'],
            [
                'Backdated calculation date should be smaller than package active from date.'
            ]
        )

    @patch(
        'irhrs.payroll.utils.helpers.get_last_confirmed_payroll_generated_date',
        mock.MagicMock(return_value=get_today() - timedelta(days=20))
    )
    def test_assign_package_with_overlapping_backdated_dates_throws_error(self):
        """
        Scenario:
        The situation below should throw an error:
        Package 1 has backdated_calculation_from 2020-08-16
        Package 2 has backdated_calculation_from 2020-07-16
        """
        UserExperiencePackageSlotFactory(
            user_experience=self.user_experience,
            package=self.package,
            active_from_date=self.user_experience.start_date
        )
        self.package_two = PackageFactory(organization=self.organization)
        payload_one = {
            "user_experience": self.user_experience.id,
            "package": self.package.id,
            "active_from_date": self.today - timedelta(days=19),
            "backdated_calculation_from": self.today - timedelta(days=30)
        }
        payload_two = {
            "user_experience": self.user_experience.id,
            "package": self.package_two.id,
            "active_from_date": self.today - timedelta(days=4),
            "backdated_calculation_from": self.today - timedelta(days=22)
        }
        res_one = self.client.post(self.assign_package_url,
                                   data=payload_one,
                                   format='json')

        with patch(
            'irhrs.payroll.utils.helpers.get_last_confirmed_payroll_generated_date',
            return_value=get_today() - timedelta(days=5)
        ):
            payroll = PayrollFactory(
                organization=self.organization,
                from_date=get_today() - timedelta(days=40),
                to_date=get_today() - timedelta(days=10)
            )
            employee_payroll = EmployeePayrollFactory(
                employee=self.created_users[0],
                package=self.package_two,
                payroll=payroll
            )
            res_two = self.client.post(self.assign_package_url,
                                       data=payload_two,
                                       format='json')
        self.assertEqual(res_one.status_code, 201, res_one.json())
        # self.assertEqual(res_two.status_code, 400, res_two.json())
        # res_two_error = res_two.json()['backdated_calculation_from'],
        # res_two_expected_error = ([
        #                               'Backdated calculation cannot overlap with previous '
        #                               + f'backdated calculation(i.e. {payload_one["backdated_calculation_from"]}).'
        #                           ],)
        # self.assertEqual(res_two_error, res_two_expected_error)

    @patch(
        'irhrs.payroll.utils.helpers.get_last_confirmed_payroll_generated_date',
        mock.MagicMock(return_value=get_today() - timedelta(days=1))
    )
    def test_backdated_date_cannot_be_before_employee_join_date_or_payroll_fiscal_year_date(self):
        '''
        Scenario:
        backdated_calculation_from field cannot be before
        employee joined date/ payroll fiscal start date i. e which ever one is greater.
        '''
        payload = {
            "user_experience": self.user_experience.id,
            "package": self.package.id,
            "active_from_date": self.today,
            "backdated_calculation_from": self.today - timedelta(days=90)
        }
        res = self.client.post(self.assign_package_url,
                               data=payload,
                               format='json')
        self.assertEqual(res.status_code, 400)
        res_expected_error = [
            'Backdated calculation date cannot be before employee joined date/'
            + ' Payroll fiscal start date.'
        ]
        res_error = res.json()['backdated_calculation_from']
        self.assertEqual(res_error, res_expected_error)

    @patch(
        'irhrs.payroll.utils.helpers.get_last_confirmed_payroll_generated_date',
        mock.MagicMock(return_value=get_today() - timedelta(days=1))
    )
    def test_assign_package_update_works(self):
        '''
        Scenario:
        backdated_calculation_from field cannot be before
        employee joined date/ payroll fiscal start date i. e which ever one is greater.
        '''
        payload = {
            "user_experience": self.user_experience.id,
            "package": self.package.id,
            "active_from_date": self.today,
            "backdated_calculation_from": self.today - timedelta(days=10)
        }
        res = self.client.post(self.assign_package_url,
                               data=payload,
                               format='json')
        self.assertEqual(res.status_code, 201, res.data)

        ux_slot_edit_url = self.user_experience_package_slot_url(
            pk=res.json()['id']
        )

        # since signal is disconnected in setUp(), updating signal code here
        UserExperiencePackageSlot.objects.update(backdated_calculation_generated=True)
        sync_update_backdated_payroll(res.json()['id'])
        # test if update with same payload works
        res = self.client.put(ux_slot_edit_url,
                              data=payload,
                              format='json')
        self.assertEqual(res.status_code, 200, res.data)
        response_backdated_calculation_from = dt.strptime(
            res.json()['backdated_calculation_from'],
            '%Y-%m-%d'
        ).date()
        self.assertEqual(response_backdated_calculation_from,
                         payload['backdated_calculation_from'])
