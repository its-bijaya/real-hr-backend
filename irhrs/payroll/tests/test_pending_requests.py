from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from irhrs.attendance.api.v1.tests.factory import (
    AttendanceAdjustmentFactory, TimeSheetFactory, WorkShiftFactory
)
from irhrs.attendance.models.approval import TimeSheetApproval
from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.core.utils.common import get_today
from irhrs.leave.api.v1.tests.factory import LeaveRequestFactory
from irhrs.organization.api.v1.tests.factory import FiscalYearFactory
from irhrs.payroll.tests.factory import (
    OrganizationPayrollConfigFactory, PackageFactory,
    UserExperiencePackageSlotFactory
)


class TestPendingRequests(RHRSTestCaseWithExperience):
    users = [
        ("admin@gmail.com", "admin", "Female", "hr"),
        ("ram@gmail.com", "ram", "Male", "assistant")
    ]

    organization_name = "Aayulogic"

    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)
        fiscal_year = FiscalYearFactory(
            start_at=timezone.now().date() - timedelta(days=100),
            end_at=timezone.now().date() + timedelta(days=100),
            applicable_from=timezone.now().date() - timedelta(days=100),
            applicable_to=timezone.now().date() + timedelta(days=100),
            organization=self.organization,
        )
        self.organization_payroll_config = OrganizationPayrollConfigFactory(
            start_fiscal_year=fiscal_year,
            organization=self.organization,
        )
        self.url = reverse(
            "api_v1:payroll:payrolls-list"
        ) + f'?as=hr&organization__slug={self.organization.slug}'

        self.payload = {
            "from_date": timezone.now().date() - timedelta(days=30),
            "to_date": timezone.now().date() + timedelta(days=30),
            "title": "Payroll Generation Title.",
            "exclude_not_eligible": False,
            "employees_filter": {
                "detail__organization__slug": self.organization.slug,
                "id__in": [self.created_users[1].id]
            },
            "organization_slug": self.organization.slug,
            "initial_extra_headings": []
        }

    def test_pending_leaves_while_generating_payroll(self):
        today = get_today()
        self.leave_request = LeaveRequestFactory(
            start=today - timedelta(days=2),
            end=today - timedelta(days=1),
            user=self.created_users[1]
        )

        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.json()['preparation_sheet']['leave_requests_summary']
            ['pending_users'][0]['full_name'],
            'ram ram'
        )
        self.assertEqual(
            response.json()['preparation_sheet']['leave_requests_summary']['pending'],
            1
        )

    def test_payroll_generation(self):
        # generating payroll when user has no pending leave requests
        today = get_today()
        self.leave_request = LeaveRequestFactory(
            user=self.created_users[1],
            start=today - timedelta(days=2),
            end=today - timedelta(days=1),
            status="approved"
        )

        user_experience = self.created_users[1].user_experiences.first()
        package = PackageFactory(organization=self.organization)
        UserExperiencePackageSlotFactory(
            user_experience=user_experience,
            package=package,
            active_from_date=user_experience.start_date
        )
        shift = WorkShiftFactory(
            name="Standard Shift",
            organization=self.organization
        )
        self.timesheet = TimeSheetFactory(
            timesheet_user=self.created_users[1],
            work_shift=shift
        )

        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json()['message'],
            'Payroll has been sent for background processing'
        )

    def test_pending_attendance_adjustment(self):
        today = get_today()
        timesheet = TimeSheetFactory(
            timesheet_user=self.created_users[1],
            timesheet_for=today - timedelta(days=1)
        )
        self.adjustment = AttendanceAdjustmentFactory(
            timesheet=timesheet,
            receiver=self.admin,
            new_punch_in=timezone.now(),
            sender=self.created_users[1]
        )

        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.json()['preparation_sheet']['adjustment_requests_summary']
            ['pending_users'][0]['full_name'],
            'ram ram'
        )
        self.assertEqual(
            response.json()['preparation_sheet']['adjustment_requests_summary']['pending'],
            1
        )

    def test_pending_web_attendance_while_generating_payroll(self):
        timesheet = TimeSheetFactory(
            timesheet_user=self.created_users[1],
            timesheet_for=get_today() - timedelta(days=1)
        )
        TimeSheetApproval.objects.create(
            timesheet=timesheet,
            status="Requested"
        )
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.json()['preparation_sheet']['attendance_request']['pending_users'][0]['full_name'],
            'ram ram'
        )
        self.assertEqual(
            response.json()['preparation_sheet']['attendance_request']['pending'],
            1
        )
