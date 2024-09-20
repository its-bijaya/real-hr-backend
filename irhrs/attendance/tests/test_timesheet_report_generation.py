from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from irhrs.attendance.api.v1.tests.factory import(
    IndividualAttendanceSettingFactory, IndividualUserShiftFactory, 
    TimeSheetFactory, WorkShiftFactory
)
from irhrs.attendance.constants import GENERATED
from irhrs.attendance.models.timesheet_report_request import TimeSheetReportRequest
from irhrs.attendance.models.timesheet_report_settings import TimeSheetRegistrationReportSettings
from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.core.constants.organization import GLOBAL
from irhrs.core.utils.common import get_today
from irhrs.organization.api.v1.tests.factory import FiscalYearFactory, FiscalYearMonthFactory
from rest_framework import status
from irhrs.attendance.tasks.timesheet_requests import generate_timesheet_requests
from irhrs.users.models.experience import UserExperience
from irhrs.users.models.user import UserDetail


class TimeSheetReportGeneration(RHRSTestCaseWithExperience):
    organization_name ="Aayulogic"

    users=[
        ("admin@gmail.com", "admin", "Female", "hr"),
        ("anish@gmail.com", "userone", "Male", "trainee"),
        ("sara@gmail.com", "usertwo", "Female", "trainee"),
        ("sarita@gmail.com", "usertwo", "Female", "trainee")
    ]

    def setUp(self):
        super().setUp()
        self.client.force_login(self.created_users[2])
        self.fiscal_year = FiscalYearFactory(
            name="2079/80",
            start_at=timezone.now().date() - timedelta(days=365),
            end_at=timezone.now().date(),
            applicable_from=timezone.now().date() - timedelta(days=365),
            applicable_to=timezone.now().date(),
            organization=self.organization,
            category=GLOBAL
        )
        self.fiscal_month = FiscalYearMonthFactory(
            fiscal_year=self.fiscal_year,
            month_index=1,
            start_at=timezone.now().date() - timedelta(days=365),
            end_at=timezone.now().date()
        )
        self.work_shift = WorkShiftFactory(
            name="Standard shift",
            work_days=5,
            organization=self.organization   
        )
        self.ias = IndividualAttendanceSettingFactory(
            user=self.created_users[0],
            work_shift=self.work_shift
        )
        IndividualUserShiftFactory(
            shift=self.work_shift,
            individual_setting=self.ias,
            applicable_from=get_today() - timedelta(days=30)
        )
        TimeSheetFactory(
            timesheet_user=self.created_users[1],
            work_shift=self.work_shift
        )

        TimeSheetRegistrationReportSettings.objects.create(
            headers={
                "report_title": "Timesheet Report",
                "full_name": "Name",
                "employee_code": "SAP Number#",
                "employment_type": "Employment Type",
                "division": "Division",
                "job_title": "Job Title",
                "branch": "Branch",
                "contract_start": "Contract Start",
                "contract_end": "Contract End",
                "bio_user_id": "Bio User Id",
                "proportionate_rate": "Proportionate Rate"
            },
            primary_legend={},
            leave_legend=[],
            organization_id=self.organization.id,
            approval_required=True,
            fiscal_year_category=GLOBAL
        )
       
        past_user=UserExperience.objects.get(user=self.created_users[2])
        past_user.start_date=self.fiscal_year.start_at
        past_user.end_date=timezone.now().date() - timedelta(days=20)
        past_user.save()

        self.timesheet_request=TimeSheetReportRequest.objects.create(
            user_id=self.created_users[2].id,
            status=GENERATED,
            report_data={},
            settings_data={},
            fiscal_month=self.fiscal_month,
            month_name=self.fiscal_month.display_name,
            month_from_date=self.fiscal_month.start_at,
            month_to_date=self.fiscal_month.end_at,
            year_name=self.fiscal_year.name,
            year_from_date=self.fiscal_year.start_at,
            year_to_date=self.fiscal_year.end_at
        )
        generate_timesheet_requests()

        self.url = reverse(
            "api_v1:attendance:timesheet-report-request-list",
            kwargs={
                "organization_slug": self.organization.slug
            }
        )
       
    def payload(self):
        return {
            "results": {
                "user": {
                    self.created_users[2].id
                },
                "status": GENERATED,
                "month_name": self.fiscal_month.display_name,
                "month_from_date": self.fiscal_month.start_at,
                "month_to_date": self.fiscal_month.end_at,
                "year_name": self.fiscal_year.name,
                "year_from_date": self.fiscal_year.start_at,
                "year_to_date": self.fiscal_year.end_at,
                "has_supervisor": False 
            }
        }
        
    def test_timesheet_requests(self):
        response = self.client.get(
            self.url, data=self.payload(), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.json()['results'][0]['status'], 'Generated'
        )
        self.assertEqual(
            response.json()['counts']['Generated'], 1
        )
        self.assertEqual(
            response.json()['results'][0]['user']['full_name'], 'sara sara'
        )
    
    def test_timesheet_report_request_for_upcoming_employee(self):
        # Timesheet of employee having future join date should not be generated
        future_user=UserDetail.objects.get(user=self.created_users[3])
        future_user.joined_date=self.fiscal_year.end_at + timedelta(days=2)
        future_user.save()

        user_experience = UserExperience.objects.get(user=self.created_users[3])
        user_experience.start_date=future_user.joined_date
        user_experience.end_date=timezone.now().date() + timedelta(days=200)

        self.timesheet_request.user_id=self.created_users[3].id
        self.timesheet_request.save()

        response = self.client.get(
            self.url, data=self.payload(), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.json()['counts']['Generated'], 0
        )
