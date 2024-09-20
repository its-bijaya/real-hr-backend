from datetime import time
from unittest.mock import patch

from django.contrib.auth.models import Group

from irhrs.common.api.tests.common import BaseTestCase as TestCase, RHRSTestCaseWithExperience

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.db import transaction
from django.test.client import Client
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from rest_framework import status

from irhrs.attendance.api.v1.tests.factory import IndividualAttendanceSettingFactory, \
    WorkShiftFactory, TimeSheetFactory, AttendanceAdjustmentFactory
from irhrs.attendance.constants import DEVICE, APPROVED, CANCELLED, PUNCH_IN, PUNCH_OUT
from irhrs.attendance.models import TimeSheet, IndividualUserShift
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.utils.common import combine_aware
from irhrs.permission.constants.groups import ADMIN
from irhrs.permission.constants.permissions import ATTENDANCE_PERMISSION, ATTENDANCE_ADJUSTMENTS_REQUEST_PERMISSION
from irhrs.permission.models import HRSPermission
from irhrs.permission.models.hrs_permisssion import OrganizationGroup
from irhrs.users.api.v1.tests.factory import UserFactory
from irhrs.users.models import UserSupervisor


USER = get_user_model()


def timestamp(days=0, hours=0):
    return timezone.now() + timezone.timedelta(days=days) + timezone.timedelta(hours=hours)


def stringify_date(stamp):
    if not stamp:
        return None
    return stamp.strftime('%Y-%m-%dT%H:%M%z')


class TestAttendanceAdjustment(RHRSTestCaseWithExperience):
    """
    Will Test the wide range of attendance adjustments that can be sent.
    Its effect, such as overtime will not be tested at all.
    """
    organization_name = 'ZK Tech'
    users = [
        ('testey@examplex.com', 'helloSecretWorld', 'Female', 'Developer'),
    ]

    def setUp(self):
        super().setUp()
        self.client.login(
            email=self.users[0][0],
            password=self.users[0][1]
        )
        self.assign_supervisors()

    def assign_supervisors(self):
        users = self.created_users
        supervisors = list()
        for user in users:
            supervisors.append(
                UserSupervisor(
                    user=user,
                    supervisor=UserFactory(),
                    approve=True, deny=True, forward=False
                )
            )
        UserSupervisor.objects.bulk_create(supervisors)

    @cached_property
    def timesheet_scenarios(self):
        timesheets = dict()

        # Data
        # missing punch out yesterday
        timesheets['missing'] = TimeSheet.objects.clock(
            self.created_users[0],
            timezone.now() - timezone.timedelta(days=1),
            DEVICE
        )

        stamp = (timezone.now() - timezone.timedelta(days=2)).replace(
            hour=10,
            minute=0,
            second=0,
            microsecond=0
        )

        timesheets['late_punch_in'] = TimeSheet.objects.clock(
            self.created_users[0],
            stamp,
            DEVICE
        )
        TimeSheet.objects.clock(
            self.created_users[0],
            stamp + timezone.timedelta(hours=9),
            DEVICE
        )

        stamp = stamp - timezone.timedelta(days=1)
        timesheets['early_punch_out'] = TimeSheet.objects.clock(
            self.created_users[0],
            stamp,
            DEVICE
        )
        TimeSheet.objects.clock(
            self.created_users[0],
            stamp + timezone.timedelta(hours=9),
            DEVICE
        )
        return timesheets

    @staticmethod
    def generate_payload(
            timesheet,
            new_punch_in=None,
            new_punch_out=None,
            remarks='Remarks'
    ):
        return {
            'adjustments': [x for x in [{
                'timesheet': timesheet.id,
                'timestamp': stringify_date(new_punch_in),
                'category': PUNCH_IN,
                'description': remarks
            }, {
                'timesheet': timesheet.id,
                'timestamp': stringify_date(new_punch_out),
                'category': PUNCH_OUT,
                'description': remarks
            }] if x['timestamp']]
        }

    def test_adjustment_scenarios(self):
        user = self.created_users[0]
        setting = IndividualAttendanceSettingFactory(user=user)

        IndividualUserShift.objects.create(
            individual_setting=setting,
            shift=WorkShiftFactory(work_days=7),
            applicable_from=timezone.now()-timezone.timedelta(days=365)
        )
        for scenario, timesheet in self.timesheet_scenarios.items():
            url = reverse(
                'api_v1:attendance:adjustments-bulk-list',
                kwargs={
                    'organization_slug': self.created_users[0].detail.organization.slug
                }
            )
            payload = self.generate_payload(
                timesheet,
                new_punch_out=combine_aware(
                    timesheet.timesheet_for,
                    time(18, 0)
                ),
                remarks=scenario
            )
            response = self.client.post(
                url,
                data=payload,
                format='json'
            )
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED
            )
            self.assertEqual(
                response.json().get('new_punch_out'),
                payload.get('new_punch_out')
            )

            payload = self.generate_payload(
                timesheet,
                new_punch_out=timezone.now() + timezone.timedelta(days=10),
                remarks=scenario
            )
            response = self.client.post(
                url,
                data=payload,
                format='json'
            )
            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST
            )
            self.assertEqual(
                response.json().get('adjustments')[0].get('timestamp')[0],
                'The time must be past.'
            )

    @property
    def user(self):
        return get_user_model().objects.get(email=self.users[0][0])


class TestAttendanceAdjustmentAggregateData(
    TestCase
):
    """
    This will test the average data shown above the attendance adjustment page,
    viz. Average In, Average Out, Average Worked Time
    The Punch In time is arranged as 9:00, 10:00, 11:00 with 9 hours each.
    """
    organization_name = 'Org'
    users = [
        ['egexample@sb.icc', 'psw$5asd', 'Male']
    ]
    required_permissions_for_test = [
        ATTENDANCE_PERMISSION,
        ATTENDANCE_ADJUSTMENTS_REQUEST_PERMISSION
    ]

    @cached_property
    def user(self):
        return UserFactory()

    @transaction.atomic()
    def populate_timestamps(self, in_time):
        setting = IndividualAttendanceSettingFactory(
            user=self.user
        )
        IndividualUserShift.objects.create(
            individual_setting=setting,
            shift=WorkShiftFactory(work_days=7),
            applicable_from=in_time-timezone.timedelta(days=10)
        )
        self.assertIsNot(TimeSheet.objects.clock(
            self.user,
            in_time,
            DEVICE
        ), False)
        self.assertIsNot(TimeSheet.objects.clock(
            self.user,
            in_time + relativedelta(hours=9),
            DEVICE
        ), False)

        self.assertIsNot(TimeSheet.objects.clock(
            self.user,
            in_time + relativedelta(days=1, hours=1),
            DEVICE
        ), False)
        self.assertIsNot(TimeSheet.objects.clock(
            self.user,
            in_time + relativedelta(days=1, hours=10),
            DEVICE
        ), False)

        self.assertIsNot(TimeSheet.objects.clock(
            self.user,
            in_time + relativedelta(days=2, hours=2),
            DEVICE
        ), False)
        self.assertIsNot(TimeSheet.objects.clock(
            self.user,
            in_time + relativedelta(days=2, hours=11),
            DEVICE
        ), False)

    def test_aggregate_info(self):
        in_time = timezone.now().astimezone().replace(
            month=1, day=1, hour=9, minute=0, second=0, microsecond=0
        )
        self.populate_timestamps(in_time)
        start_date = in_time.date().strftime('%Y-%m-%d')
        end_date = (in_time + relativedelta(days=2)).date().strftime('%Y-%m-%d')
        average_data_url = reverse(
            'api_v1:attendance:user-timesheets-list',
            kwargs={
                'user_id': self.user.id
            }
        )
        client = Client()
        client.force_login(self.user)
        self.setup_permission()
        response = client.get(
            average_data_url,
            data={
                'start_date': start_date,
                'end_date': end_date,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        avg_in = response.json().get('average_in')
        self.assertEqual(
            avg_in,
            '10:00:00'  # it was designed as 9,10,11
        )

        avg_out = response.json().get('average_out')
        self.assertEqual(
            avg_out,
            '19:00:00'
        )

        avg_work_time = response.json().get('average_work_time')
        self.assertEqual(
            avg_work_time,
            '09:00:00'
        )

    def setup_permission(self):
        admin_group, _ = Group.objects.update_or_create(name=ADMIN)
        self.user.groups.add(admin_group)
        og = OrganizationGroup.objects.create(
            organization=self.user.detail.organization,
            group=admin_group
        )
        for perm in self.required_permissions_for_test:
            permission = HRSPermission.objects.create(**perm)
            og.permissions.add(permission)


# class TestAttendanceAdjustmentCancel(RHRSAPITestCase):
#     organization_name = 'ZK Tech'
#     users = [
#         ('one@example.com', 'helloSecretWorld', 'Female'),
#         ('two@example.com', 'helloSecretWorld', 'Female'),
#         ('three@example.com', 'helloSecretWorld', 'Female'),
#     ]
#
#     @property
#     def normal(self):
#         return USER.objects.get(email='two@example.com')
#
#     @property
#     def supervisor1(self):
#         return USER.objects.get(email='three@example.com')
#
#     def setUp(self):
#         super().setUp()
#         IndividualAttendanceSettingFactory(user=self.normal)
#         self.timesheet = TimeSheetFactory(timesheet_user=self.normal)
#
#     def get_cancel_url(self, adjustment, mode=None):
#         url = reverse(
#             'api_v1:attendance:adjustments-cancel',
#             kwargs={
#                 'organization_slug': self.organization.slug,
#                 'pk': adjustment.id
#             }
#         )
#         if mode:
#             url = f"{url}?as={mode}"
#         return url
#
#     # def test_cancel(self):
#     #     adjustment = AttendanceAdjustmentFactory(
#     #             timesheet=self.timesheet,
#     #             receiver=self.supervisor1,
#     #             new_punch_in=timezone.now(),
#     #             new_punch_out=timezone.now() + timezone.timedelta(hours=8),
#     #             sender=self.normal,
#     #         )
#     #     adjustment.approve(approved_by=self.admin, remark="Approved")
#     #     punch_in_entry = self.timesheet.timesheet_entries.get(
#     #         timestamp=self.timesheet.punch_in, timesheet=self.timesheet)
#     #     punch_out_entry = self.timesheet.timesheet_entries.get(
#     #         timestamp=self.timesheet.punch_out, timesheet=self.timesheet)
#     #
#     #     soft_delete_called_with_id = []
#     #     expected_soft_delete_called_with_id = [punch_in_entry.id, punch_out_entry.id]
#     #
#     #     # mock function that records timesheet entry id it is called with
#     #     # couldn't use is_called_with because it does not return self argument
#     #     def mocked_soft_delete(s):
#     #         soft_delete_called_with_id.append(s.id)
#     #
#     #     self.client.force_login(self.admin)
#     #     url = self.get_cancel_url(adjustment, mode='hr')
#     #     with patch(
#     #         'irhrs.attendance.models.attendance.TimeSheetEntry.soft_delete', mocked_soft_delete
#     #     ):
#     #         response = self.client.post(url, data={'remark': 'Cancelled'})
#     #         self.assertEqual(response.status_code, 200)
#     #
#     #         # don't need to test soft delete as it is already tested
#     #         # just checking soft delete is called with right arguments
#     #         self.assertEqual(soft_delete_called_with_id, expected_soft_delete_called_with_id)
#     #
#     #         # check history is maintained or not
#     #         adjustment.adjustment_histories.filter(
#     #             action_performed=CANCELLED,
#     #             action_performed_by=self.admin,
#     #             remark='Cancelled'
#     #         )
#
#     # def test_cancel_not_approved_requests(self):
#     #     adjustment = AttendanceAdjustmentFactory(
#     #         timesheet=self.timesheet,
#     #         receiver=self.supervisor1,
#     #         new_punch_in=timezone.now(),
#     #         new_punch_out=timezone.now() + timezone.timedelta(hours=8),
#     #         sender=self.normal,
#     #     )
#     #     # checking status is not approved
#     #     self.assertNotEqual(adjustment.status, APPROVED)
#     #
#     #     self.client.force_login(self.admin)
#     #     url = self.get_cancel_url(adjustment, mode='hr')
#     #
#     #     response = self.client.post(url, data={'remark': 'Cancelled'})
#     #     self.assertEqual(response.status_code, 400)
#     #     self.assertIn("Only approved requests can be cancelled.",
#     #                   response.data['non_field_errors'])
#     #
#     # def test_cancel_by_non_admin_user(self):
#     #     adjustment = AttendanceAdjustmentFactory(
#     #         timesheet=self.timesheet,
#     #         receiver=self.supervisor1,
#     #         new_punch_in=timezone.now(),
#     #         new_punch_out=timezone.now() + timezone.timedelta(hours=8),
#     #         sender=self.normal,
#     #     )
#     #
#     #     self.client.force_login(self.normal)
#     #     url = self.get_cancel_url(adjustment)
#     #     response = self.client.post(url, data={'remark': 'Cancelled'})
#     #     self.assertEqual(response.status_code, 403)
#     #
#     #     self.client.force_login(self.supervisor1)
#     #     url = self.get_cancel_url(adjustment, mode="supervisor")
#     #     response = self.client.post(url, data={'remark': 'Cancelled'})
#     #     self.assertEqual(response.status_code, 403)
