from django.urls import reverse
from django.utils import timezone

from irhrs.attendance.api.v1.tests.factory import TimeSheetFactory, \
    IndividualAttendanceSettingFactory, TimeSheetEntryFactory
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.utils.common import get_today
from irhrs.users.models import UserSupervisor


class TimeSheetEntryDeleteAPITest(RHRSAPITestCase):
    organization_name = "Google Inc."
    users = [
        ("userone@example.com", "password", "Male"),
        ("normaluser@example.com", "strongpassword", "Male")
    ]

    def setUp(self):
        super().setUp()

        self.timesheet = TimeSheetFactory(
            is_present=True,
            timesheet_user=self.admin
        )
        self.attendance_settings = IndividualAttendanceSettingFactory(
            user=self.admin)

        today = get_today(with_time=True)
        self.dt1 = timezone.datetime(year=today.year, month=today.month, day=today.day, hour=9,
                                     minute=0, tzinfo=today.tzinfo)
        self.dt2 = timezone.datetime(year=today.year, month=today.month, day=today.day, hour=10,
                                     minute=0, tzinfo=today.tzinfo)
        self.entry1 = TimeSheetEntryFactory(
            timesheet=self.timesheet,
            timestamp=self.dt1,
            entry_method='Web App'
        )
        self.entry2 = TimeSheetEntryFactory(
            timesheet=self.timesheet,
            timestamp=self.dt2,
            entry_method='Web App'
        )
        self.timesheet.fix_entries()
        UserSupervisor.objects.create(
            user=self.admin,
            supervisor=self.created_users[1],
            authority_order=1,
            approve=True,
            deny=True,
            forward=True
        )

        # setup check
        self.assertEqual(self.timesheet.punch_in, self.dt1)
        self.assertEqual(self.timesheet.punch_out, self.dt2)

    @property
    def adjustment_list_url(self):
        return reverse(
            'api_v1:attendance:adjustments-list',
            kwargs={
                'organization_slug': self.organization.slug
            }
        )

    def assert_cancel_action(self, url):
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            200
        )
        self.assertEqual(
            response.json().get('count'),
            1
        )
        self.assertEqual(
            response.json().get('counts'),
            {
                'Requested': 0,
                'Forwarded': 0,
                'Approved': 0,
                'Declined': 0,
                'Cancelled': 1,
                'All': 1
            }
        )
        self.assertEqual(
            response.json().get('results')[0].get('timesheet').get('id'),
            self.timesheet.id
        )

    def test_delete_entry(self):
        self.client.force_login(self.admin)

        entry = self.entry1
        url = reverse(
            'api_v1:attendance:timesheet-entry-delete',
            kwargs={
                'organization_slug': self.organization.slug,
                'pk': self.timesheet.id,
                'timesheet_entry_id': entry.id
            }
        )
        response = self.client.post(url, {"description": "New remarks field required."})
        self.assertEqual(response.status_code, 200)

        entry.refresh_from_db()
        self.assertTrue(entry.is_deleted)

        adjustment_list_url = self.adjustment_list_url + "?as=hr&status=Cancelled"
        self.assert_cancel_action(adjustment_list_url)

        self.client.logout()

        # view as supervisor
        self.client.force_login(self.created_users[1])
        adjustment_list_url = self.adjustment_list_url + "?as=supervisor&status=Cancelled"
        self.assert_cancel_action(adjustment_list_url)

        # try deleting again
        self.client.force_login(self.admin)
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json().get('non_field_errors'),
            ['Entry already deleted']
        )

        # view as user
        adjustment_list_url = self.adjustment_list_url + "?as=&status=Cancelled"
        self.assert_cancel_action(adjustment_list_url)

    def test_undo_delete_entry(self):
        self.client.force_login(self.admin)

        self.entry1.soft_delete()
        entry = self.entry1

        url = reverse(
            'api_v1:attendance:timesheet-entry-undo-delete',
            kwargs={
                'organization_slug': self.organization.slug,
                'pk': self.timesheet.id,
                'timesheet_entry_id': entry.id
            }
        )

        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)

        entry.refresh_from_db()
        self.assertFalse(entry.is_deleted)

        # try undo delete again
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 400)

    def test_delete_timesheet_entry_by_user(self):
        timesheet2 = TimeSheetFactory(
            is_present=True,
            timesheet_user=self.created_users[1]
        )
        entry3 = TimeSheetEntryFactory(
            timesheet=timesheet2,
            timestamp=self.dt1,
            entry_method='Web App'
        )
        self.client.force_login(self.created_users[1])
        url = reverse(
            'api_v1:attendance:update-entries-list',
            kwargs={
                'adjustment_action': 'delete',
                'organization_slug': self.organization.slug
            }
        )
        payload = {
            "timesheet": timesheet2.id,
            "timesheet_entry": entry3.id,
            "description": "This is description"
        }
        response = self.client.post(
            url,
            payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            201
        )
        user_adjustment_url = self.adjustment_list_url + "?status=Requested"
        response = self.client.get(user_adjustment_url)

        self.assertEqual(
            response.status_code,
            200
        )
        self.assertEqual(
            response.json().get('count'),
            1
        )
        self.assertEqual(
            response.json().get('counts'),
            {
                'Requested': 1,
                'Forwarded': 0,
                'Approved': 0,
                'Declined': 0,
                'Cancelled': 0,
                'All': 1
            }
        )
        self.assertEqual(
            response.json().get('results')[0].get('timesheet').get('id'),
            timesheet2.id
        )
        self.assertEqual(
            response.json().get('results')[0].get('timesheet_entry').get('id'),
            entry3.id
        )
