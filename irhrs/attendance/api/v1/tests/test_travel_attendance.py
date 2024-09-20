import datetime

from django.urls import reverse
from rest_framework import status

from irhrs.attendance.api.v1.tests.factory import IndividualUserShiftFactory, \
    IndividualAttendanceSettingFactory, WorkShiftFactory
from irhrs.attendance.constants import FULL_DAY, REQUESTED, APPROVED
from irhrs.attendance.models import TravelAttendanceSetting, TravelAttendanceRequest
from irhrs.attendance.models.attendance import IndividualUserShift
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.utils.common import get_today
from irhrs.users.models import UserSupervisor



class TestTravelAttendanceRequest(RHRSAPITestCase):
    users = [
        ('admin@email.com', "password", "Male"),
        ('normal@email.com', "password", "Male"),
        ('normalone@email.com', "password", "Male")
    ]
    organization_name = 'Google'

    def setUp(self):
        super().setUp()
        self.normal=self.created_users[1]
        self.client.force_login(self.normal)
        TravelAttendanceSetting.objects.create(
            organization=self.organization,
            can_apply_in_offday=True,
            can_apply_in_holiday=False
        )
        individual_setting = IndividualAttendanceSettingFactory(
                user=self.normal
        )
        shift = WorkShiftFactory(
            organization=self.organization
        )
        IndividualUserShiftFactory(
            individual_setting=individual_setting,
            shift=shift
        )
        UserSupervisor.objects.create(
            user=self.normal,
            supervisor=self.admin,
            approve=True,
            deny=True,
            forward=False
        )

    def test_travel_attendance_request(self):
        url = reverse(
            'api_v1:attendance:travel-attendance-list',
            kwargs={
                'organization_slug': self.organization.slug
            }
        ) + "?organization_specific=true"
        start = get_today()+ datetime.timedelta(days=2)
        dummy_time = get_today(with_time=True).time()
        end =  get_today() + datetime.timedelta(days=3)

        payload = {
            "request_remarks": "Travel Attendance Remarks",
            "location": "Kathmandu",
            "start": start,
            "start_time": dummy_time,
            "end":end,
            "end_time": dummy_time,
            "working_time": FULL_DAY
        }

        response = self.client.post(
            url,
            payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )
        self.assertEqual(
            response.json().get('status'),
            REQUESTED
        )
        self.assertEqual(
            response.json().get('request_remarks'),
            payload.get("request_remarks")
        )

        # check for stats api
        stats_url = reverse(
            'api_v1:attendance:travel-attendance-stats',
            kwargs={
                'organization_slug': self.organization.slug
            }
        ) + "?organization_specific=true&as=hr"
        self.client.force_login(self.admin)
        response = self.client.get(stats_url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.json(),
            {'pending': 1, 'approved': 0}
        )

        common_url = reverse(
            "api_v1:commons:travel-attendance-summary-stats"
        )
        response = self.client.get(common_url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.json(),
            {'pending': 1, 'approved': 0}
        )

        TravelAttendanceRequest.objects.bulk_create([
            TravelAttendanceRequest(
                user=self.normal,
                start=start + datetime.timedelta(days=index*2),
                start_time=dummy_time,
                end=end + datetime.timedelta(days=index*2),
                end_time=dummy_time,
                status=item,
                balance=1,
                recipient=self.admin
            ) for index, item in enumerate([APPROVED, REQUESTED, APPROVED], 1)     
        ])

        response = self.client.get(stats_url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        # Requested 2 (1 through API and 1 from direct create)
        self.assertEqual(
            response.json(),
            {'pending': 2, 'approved': 2}
        )

        common_url = reverse(
            "api_v1:commons:travel-attendance-summary-stats"
        )
        response = self.client.get(common_url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.json(),
            {'pending': 2, 'approved': 2}
        )

    def url(self,mode):
        return reverse(
            'api_v1:attendance:travel-attendance-list',
            kwargs={
                'organization_slug': self.organization.slug
            }
        ) + f"?as={mode}"
 
    def payload(self, user):
        start = get_today()+ datetime.timedelta(days=2)
        dummy_time = get_today(with_time=True).time()
        end =  get_today() + datetime.timedelta(days=3)
        return {
            "request_remarks": "Travel Attendance Remarks",
            "location": "Kathmandu",
            "start": start,
            "start_time": dummy_time,
            "end":end,
            "end_time": dummy_time,
            "working_time": FULL_DAY,
            "employee":user.id
        }

    def test_travel_attendance_request_on_behalf_of_employee(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            self.url('hr'),
            self.payload(self.normal),
            format="json"
        )
        self.assertEqual(
            response.status_code,
            201
            )
        self.assertTrue(
            TravelAttendanceRequest.objects.filter(
                user=self.normal.id
                ).exists()
                )

    def test_travel_attendance_request_on_behalf_of_employee_without_supervisor(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            self.url('supervisor'),
            self.payload(self.created_users[2]),
            format="json"
        )
        self.assertEqual(
            response.status_code,
            400
            )
        self.assertEqual(
            response.json()['non_field_errors'],
            [f'You are not the right supervisor for {self.created_users[2]}.'],
        )
