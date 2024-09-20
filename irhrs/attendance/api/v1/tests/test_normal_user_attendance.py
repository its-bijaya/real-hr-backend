from datetime import datetime, time
from dateutil.parser import parse
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from rest_framework import status

from irhrs.attendance.api.v1.tests.factory import IndividualAttendanceSettingFactory, \
    WorkShiftFactory2 as WorkShiftFactory
from irhrs.attendance.models import TimeSheet, IndividualUserShift, TimeSheetEntry
from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.attendance.constants import PUNCH_IN, DEVICE
from irhrs.users.api.v1.tests.factory import UserMinimalFactory
from irhrs.core.utils.common import get_today


class TestNormalUserTodayLog(RHRSTestCaseWithExperience):
    organization_name = 'ZK Tech'
    users = [
        ('test@example.com', 'helloSecretWorld', 'Male', 'Developer')
    ]

    def setUp(self):
        super().setUp()
        self.client.login(
            email=self.users[0][0],
            password=self.users[0][1],
        )

    @cached_property
    def user(self):
        return get_user_model().objects.get(
            email=self.users[0][0]
        )

    @property
    def url(self):
        return reverse('api_v1:attendance:web-attendance-list')

    @property
    def timesheets_url(self):
        return reverse(
            'api_v1:attendance:user-timesheets-list'
        )

    @staticmethod
    def payload(remark=PUNCH_IN):
        return {
            "message": remark,
            "remark_category": remark
        }

    def test_log(self):
        # Missing Attendance Setting
        # Disabled web attendance or Missing Attendance Setting
        response = self.client.post(
            self.url,
            self.payload()
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Create Attendance Setting.
        setting = IndividualAttendanceSettingFactory(
            user=self.user,
            web_attendance=True
        )
        setting.ip_filters.create(
            cidr='127.0.0.1'
        )
        response = self.client.post(
            self.url,
            self.payload()
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(
            self.url,
            data={}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_entries(self):
        IndividualUserShift.objects.create(
            individual_setting=IndividualAttendanceSettingFactory(
                user=self.user,
                web_attendance=True
            ),
            shift=WorkShiftFactory(work_days=7),
            applicable_from=timezone.now() - timezone.timedelta(days=365)
        )

        today = timezone.now().date().strftime('%Y-%m-%d')
        timesheets_url = reverse(
            'api_v1:attendance:user-timesheets-list',
            kwargs={
                'user_id': self.user.id
            }
        )
        rounded_microsecond_now = timezone.now().astimezone().replace(
            microsecond=0,
            hour=8
        )
        # Ensured no chances of failure due to microsecond mismatch [Failure to preserve
        # microseconds in DRF timestamp info].

        stamps = [
            rounded_microsecond_now - timezone.timedelta(hours=3),
            rounded_microsecond_now - timezone.timedelta(hours=4),
            rounded_microsecond_now - timezone.timedelta(hours=5),

            rounded_microsecond_now + timezone.timedelta(hours=3),
            rounded_microsecond_now + timezone.timedelta(hours=4),
            rounded_microsecond_now + timezone.timedelta(hours=5),
        ]

        for stamp in stamps:
            ts = TimeSheet.objects.clock(self.user, stamp, DEVICE)
        response = self.client.get(
            timesheets_url,
            data={
                'timesheet_for': today
            }
        )
        id_ = [x.get('id') for x in response.json().get('results')]
        self.assertEqual(
            len(id_),
            1,
            "Multiple Timesheets should not have been generated"
        )
        timesheet_entries_url = reverse(
            'api_v1:attendance:user-timesheets-entries',
            kwargs={
                'user_id': self.user.id,
                'pk': id_[0]
            }
        )
        results = [
            parse(res.get('timestamp')) for res in self.client.get(
                timesheet_entries_url
            ).json().get('results')
        ]
        self.assertEqual(set(results), set(stamps))

    def test_no_entries(self):
        user = UserMinimalFactory()
        self.client.force_login(user)
        today = timezone.now().date().strftime('%Y-%m-%d')
        response = self.client.get(
            reverse(
                'api_v1:attendance:user-timesheets-list',
                kwargs={
                    'user_id': user.id
                }
            ),
            data={
                'timesheet_for': today
            }
        )
        self.assertEqual(response.data.get('count'), 0)

    def test_24_hours_clock_behavior_on_timesheet(self):
        IndividualUserShift.objects.create(
            individual_setting=IndividualAttendanceSettingFactory(
                user=self.user,
                web_attendance=True
            ),
            shift=WorkShiftFactory(work_days=7),
            applicable_from=timezone.now() - timezone.timedelta(days=365)
        )
        today_time_sheets = TimeSheet.objects.filter(
            timesheet_user=self.user,
            timesheet_for=get_today()
        )
        TimeSheet.objects._create_or_update_timesheet_for_profile(
            user=self.user,
            date_=get_today()
        )
        first = today_time_sheets.first()
        expected_in = first.expected_punch_in
        expected_out = first.expected_punch_out

        # from range of -23 to +23 there should be no second timesheet
        for hour in range(0, 23):
            TimeSheet.objects.clock(
                user=self.user,
                date_time=expected_in - timezone.timedelta(hours=hour),
                entry_method='Device'
            )
            TimeSheet.objects.clock(
                user=self.user,
                date_time=expected_out + timezone.timedelta(hours=hour),
                entry_method='Device'
            )
        self.assertEqual(
            today_time_sheets.count(),
            1,
            "There shouldn't be a duplicate timesheet"
            # other entries will be attributed to previous and tomorrow's timesheet.
        )

        # from irhrs.core.utils.common import format_timezone
        # print()
        # for ts in self.user.timesheets.order_by('timesheet_for'):
        #     print(
        #         '------------------',
        #         ts.timesheet_for,
        #         '------------------',
        #         format_timezone(ts.expected_punch_in) if ts.expected_punch_in else 'N/A',
        #         '------------------',
        #         format_timezone(ts.expected_punch_out) if ts.expected_punch_out else 'N/A',
        #     )
        #     for tse in ts.timesheet_entries.order_by('timestamp'):
        #         print(format_timezone(tse.timestamp.astimezone()))

    def test_24_hours_clock_behavior_on_timesheet_with_shift_extends(self):
        shift = WorkShiftFactory(work_days=7)
        IndividualUserShift.objects.create(
            individual_setting=IndividualAttendanceSettingFactory(
                user=self.user,
                web_attendance=True
            ),
            shift=shift,
            applicable_from=timezone.now() - timezone.timedelta(days=365)
        )

        # override timings to be 2100 to 0600, extend=True
        from irhrs.attendance.models.workshift import WorkTiming
        WorkTiming.objects.filter(
            work_day__shift=shift
        ).update(
            start_time=time(21, 0),
            end_time=time(6, 0),
            extends=True,
        )
        today_time_sheets = TimeSheet.objects.filter(
            timesheet_user=self.user,
            timesheet_for=get_today()
        )
        TimeSheet.objects._create_or_update_timesheet_for_profile(
            user=self.user,
            date_=get_today()
        )
        first = today_time_sheets.first()
        expected_in = first.expected_punch_in
        expected_out = first.expected_punch_out

        # from range of -23 to +23 there should be no second timesheet
        for hour in range(0, 23):
            TimeSheet.objects.clock(
                user=self.user,
                date_time=expected_in - timezone.timedelta(hours=hour),
                entry_method='Device'
            )
            TimeSheet.objects.clock(
                user=self.user,
                date_time=expected_out + timezone.timedelta(hours=hour),
                entry_method='Device'
            )
        self.assertEqual(
            today_time_sheets.count(),
            1,
            "There shouldn't be a duplicate timesheet"
        )
        # from irhrs.core.utils.common import format_timezone
        # print()
        # for ts in self.user.timesheets.order_by('timesheet_for'):
        #     print(
        #         '-------- Shift Extends ----------',
        #         ts.timesheet_for,
        #         '------------------',
        #         format_timezone(ts.expected_punch_in) if ts.expected_punch_in else 'N/A',
        #         '------------------',
        #         format_timezone(ts.expected_punch_out) if ts.expected_punch_out else 'N/A',
        #     )
        #     for tse in ts.timesheet_entries.order_by('timestamp'):
        #         print(format_timezone(tse.timestamp.astimezone()))
