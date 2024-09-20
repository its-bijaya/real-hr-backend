from datetime import timedelta

from django.db.models.signals import post_save
from django.utils import timezone
from django.urls import reverse
from rest_framework import status

from irhrs.attendance.api.v1.tests.factory import OvertimeSettingFactory, TimeSheetFactory, \
    WorkShiftFactory
from irhrs.attendance.constants import REQUESTED
from irhrs.attendance.models import OvertimeEntry, OvertimeClaim
from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.core.utils.common import get_today
from irhrs.payroll.models import UserExperiencePackageSlot, PackageHeading, GENERATED
from irhrs.payroll.signals import create_update_report_row_user_experience_package, \
    update_package_heading_rows
from irhrs.payroll.tests.factory import OrganizationPayrollConfigFactory, \
    UserExperiencePackageSlotFactory, PackageFactory, PayrollFactory
from irhrs.organization.api.v1.tests.factory import FiscalYearFactory
from irhrs.leave.api.v1.tests.factory import LeaveRequestFactory


class TestPayrollGeneration(RHRSTestCaseWithExperience):
    users = [
        ('hr@email.com', 'secret', 'Male', 'Programmer'),
        ('finance@email.com', 'secret', 'Female', 'Accountant'),
        ('general@email.com', 'secret', 'Female', 'Accountant')
    ]
    organization_name = 'Organization'

    def setUp(self):
        # disconnected by runner so needed to connect here
        post_save.disconnect(
            create_update_report_row_user_experience_package, sender=UserExperiencePackageSlot
        )
        post_save.disconnect(update_package_heading_rows, sender=PackageHeading)
        super().setUp()
        fiscal_year = FiscalYearFactory(
            start_at=timezone.now().date() - timedelta(days=200),
            end_at=timezone.now().date() + timedelta(days=200),
            applicable_from=timezone.now().date() - timedelta(days=200),
            applicable_to=timezone.now().date() + timedelta(days=200),
            organization=self.organization,
        )
        organization_payroll_config = OrganizationPayrollConfigFactory(
            start_fiscal_year=fiscal_year,
            organization=self.organization,
        )
        self.client.force_login(self.admin)

    @property
    def generate_payroll_url(self):
        return reverse(
            "api_v1:payroll:payrolls-list",
        ) + f'?as=hr&organization__slug={self.organization.slug}'

    # def test_payroll_generation_does_not_throw_errors(self):
    #     payload = {
    #         "from_date": timezone.now().date() - timedelta(days=30),
    #         "to_date": timezone.now().date() + timedelta(days=30),
    #         "exclude_not_eligible":True,
    #         "employees_filter":{
    #             "detail__organization__slug":self.organization.slug,
    #             "id__excludes":[]
    #         },
    #         "organization_slug":self.organization.slug,
    #         "initial_extra_headings":[]
    #     }
    #     response = self.client.post(
    #         self.generate_payroll_url,
    #         data=payload,
    #         format='json'
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         status.HTTP_200_OK
    #     )

    def payload(self):
        return {
            "from_date": timezone.now().date() - timedelta(days=30),
            "to_date": timezone.now().date() + timedelta(days=30),
            "title": "Payroll Generation Title.",
            "exclude_not_eligible": False,
            "employees_filter": {
                "detail__organization__slug":self.organization.slug,
                "id__in": [self.created_users[1].id]
            },
            "organization_slug": self.organization.slug,
            "initial_extra_headings": []
        }

    def test_payroll_generation_with_pending_leave_request_throws_error(self):
        today = get_today()
        LeaveRequestFactory(
            start=today - timedelta(days=2),
            end=today - timedelta(days=1),
            user=self.created_users[1]
        )
        response = self.client.post(
            self.generate_payroll_url,
            data=self.payload(),
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            response.json()['preparation_sheet']['leave_requests_summary']['pending'],
            1
        )

    # def test_payroll_generation_with_excluded_user_pending_leave_request_does_not_throw_error(self):
    #     leave_request = LeaveRequestFactory(
    #         user = self.created_users[1]
    #     )
    #     payload = {
    #         "from_date": timezone.now().date() - timedelta(days=30),
    #         "to_date": timezone.now().date() + timedelta(days=30),
    #         "exclude_not_eligible":True,
    #         "employees_filter":{
    #             "detail__organization__slug":self.organization.slug,
    #             "id__excludes":[self.created_users[1].id]
    #         },
    #         "organization_slug":self.organization.slug,
    #         "initial_extra_headings":[]
    #     }
    #     response = self.client.post(
    #         self.generate_payroll_url,
    #         data=payload,
    #         format='json'
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         status.HTTP_200_OK
    #     )

    def test_payroll_generation_with_included_user_has_pending_leave_request_and_excluded_user_exists_throws_error(self):
        today = get_today()
        LeaveRequestFactory(
            start=today - timedelta(days=2),
            end=today - timedelta(days=1),
            user=self.created_users[1]
        )
        payload = self.payload()
        payload["employees_filter"]['id__excludes'] = [self.created_users[2].id]
        response = self.client.post(
            self.generate_payroll_url,
            data=payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            response.json()['preparation_sheet']['leave_requests_summary']['pending'],
            1
        )

    def test_do_not_stop_payroll_generation_when_overtime_is_in_requested_state(self):
        overtime_setting = OvertimeSettingFactory(
            organization=self.organization
        )
        user_experience = self.created_users[1].user_experiences.first()
        package = PackageFactory(organization=self.organization)
        UserExperiencePackageSlotFactory(
            user_experience=user_experience,
            package=package,
            active_from_date=user_experience.start_date
        )
        shift = WorkShiftFactory(
            name="Regular Shift",
            organization=self.organization
        )
        timesheet = TimeSheetFactory(
            timesheet_user=self.created_users[1],
            work_shift=shift
        )
        overtime_entry = OvertimeEntry.objects.create(
            user=self.created_users[1],
            overtime_settings=overtime_setting,
            timesheet=timesheet
        )

        OvertimeClaim.objects.create(
            overtime_entry=overtime_entry,
            description="OT claim for today.",
            status=REQUESTED,
            recipient=self.admin
        )

        response = self.client.post(
            self.generate_payroll_url,
            data=self.payload(),
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.json().get('message'),
            'Payroll has been sent for background processing'
        )

    def assign_package_to_user(self, user):
        user_experience = user.user_experiences.first()
        package = PackageFactory(organization=self.organization)
        UserExperiencePackageSlotFactory(
            user_experience=user_experience,
            package=package,
            active_from_date=user_experience.start_date
        )

    def payroll_add_employee_url(self, payroll_id):
        return reverse(
            "api_v1:payroll:payrolls-add-employees",
            kwargs={'pk': payroll_id}
        ) + f'?as=hr&organization__slug={self.organization.slug}'

    def test_add_employee_in_payroll_collection(self):
        self.assign_package_to_user(self.created_users[1])
        payload = self.payload()
        payroll = PayrollFactory(title="test payroll", organization=self.organization,
                                 from_date=payload.get('from_date'),
                                 to_date=payload.get('to_date'), status=GENERATED)
        url = self.payroll_add_employee_url(payroll.id)
        response = self.client.post(
            url,
            data=payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.json().get("message"),
            'Employee adding process has been sent for background processing.'
        )
        self.assertEqual(payroll.added_employees.count(), 1)  # check history count
