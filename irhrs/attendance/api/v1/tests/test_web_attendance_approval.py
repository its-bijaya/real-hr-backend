from copy import deepcopy

from django.urls import reverse
from django.utils import timezone

from irhrs.attendance.api.v1.tests.factory import TimeSheetFactory, \
    IndividualAttendanceSettingFactory
from irhrs.attendance.constants import WEB_APP, PUNCH_IN, REQUESTED, APPROVED, DECLINED, FORWARDED
from irhrs.attendance.models import TimeSheet, TimeSheetEntryApproval
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.utils.common import get_today


class TestWebAttendanceApproval(RHRSAPITestCase):
    organization_name = 'ALPL'
    users = [
        ('hr@email.com', 'password', 'Female'),
        ('supervisorone@email.com', 'password', 'Female'),
        ('supervisortwo@email.com', 'password', 'Male'),
        ('normal@email.com', 'password', 'Male'),
    ]
    kwargs = {}

    def setUp(self):
        super().setUp()
        self.timesheet = TimeSheetFactory(timesheet_user=self.user)
        IndividualAttendanceSettingFactory(user=self.user)

    @property
    def data(self):
        return dict(
            user=self.user,
            date_time=get_today(with_time=True),
            entry_method=WEB_APP,
            entry_type=PUNCH_IN,
            supervisor=None,
            remarks='Test timesheet approval',
            remark_category=PUNCH_IN,
            latitude=1.1,
            longitude=2.2
        )

    @property
    def user(self):
        return self.created_users[-1]

    @property
    def first_supervisor(self):
        return self.created_users[1]

    @property
    def second_supervisor(self):
        return self.created_users[1]

    @property
    def hr(self):
        return self.admin

    def test_web_attendance_approval(self):
        data = deepcopy(self.data)
        TimeSheet.objects.generate_approvals(timesheet=self.timesheet, **data)
        timesheet_approval = TimeSheetEntryApproval.objects.filter(
            timesheet_approval__timesheet__timesheet_user=self.user
        )
        data['status'] = REQUESTED
        self.validate_data([data], timesheet_approval)

    @property
    def approval_url(self):
        return reverse(
            'api_v1:attendance:attendance-request-action',
            kwargs=self.kwargs
        )

    def test_action_on_web_attendance_approval(self):
        data = deepcopy(self.data)
        for index in range(1, 4):
            data['date_time'] = get_today(with_time=True) + timezone.timedelta(hours=index)
            TimeSheet.objects.generate_approvals(timesheet=self.timesheet, **data)

        timesheet_approval = self.timesheet.timesheet_approval
        timesheet_entries = timesheet_approval.timesheet_entry_approval.all()
        status_list = [APPROVED, DECLINED, FORWARDED]

        self.client.force_login(user=self.hr)
        self.kwargs = {
            'organization_slug': self.organization.slug,
            'pk': timesheet_approval.id
        }

        # by hr
        # positive test case while performing action on requested attendance
        for index, status in enumerate(status_list[:-1], start=0):
            response = self.client.post(
                self.approval_url + '?as=hr',
                data={
                    "status": status,
                    "timesheet": [timesheet_entries[index].id]
                }
            )
            self.assertEqual(response.status_code, 200)

        # hr tries to forward the request
        response = self.client.post(
            self.approval_url + '?as=hr',
            data={
                "status": FORWARDED,
                "timesheet": [timesheet_entries[2].id]
            }
        )
        self.assertEqual(response.status_code, 400)

        # tries to act on already acted data
        response = self.client.post(
            self.approval_url + '?as=hr',
            data={
                "status": APPROVED,
                "timesheet": [timesheet_entries[0].id]
            }
        )
        self.assertEqual(response.status_code, 400)
