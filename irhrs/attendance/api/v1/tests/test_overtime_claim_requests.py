import json
import uuid
from datetime import time

from django.contrib.auth.models import Group
from django.test import TransactionTestCase

from irhrs.common.api.tests.common import BaseTestCase as TestCase

import faker
from dateutil.rrule import rrule, DAILY as R_DAILY
from django.db import transaction
from django.test.client import Client
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from irhrs.attendance.api.v1.tests.factory import IndividualAttendanceSettingFactory, \
    WorkShiftFactory2 as WorkShiftFactory, OvertimeSettingFactory
from irhrs.attendance.constants import DEVICE, REQUESTED, DAILY, UNCLAIMED
from irhrs.attendance.models import TimeSheet, IndividualUserShift, OvertimeClaim, WorkDay
from irhrs.attendance.tasks.overtime import generate_overtime
from irhrs.core.utils import nested_get
from irhrs.core.utils.common import combine_aware, humanize_interval
from irhrs.organization.api.v1.tests.factory import OrganizationFactory, OrganizationDivisionFactory
from irhrs.organization.models import EmploymentJobTitle, get_user_model
from irhrs.permission.constants.groups import ADMIN
from irhrs.permission.constants.permissions import ATTENDANCE_PERMISSION, ATTENDANCE_OVERTIME_CLAIM_PERMISSION
from irhrs.permission.models.hrs_permisssion import OrganizationGroup, HRSPermission
from irhrs.users.api.v1.tests.factory import UserFactory
from irhrs.users.models import UserSupervisor, UserExperience

timedelta = timezone.timedelta


def timestamp(days=0, hours=0):
    return timezone.now() + timezone.timedelta(days=days) + timezone.timedelta(hours=hours)


def stringify_date(stamp):
    if not stamp:
        return None
    return stamp.strftime('%Y-%m-%dT%H:%M%z')


class OvertimeTestGenericMixin:
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.user = UserFactory()
        self.organization = OrganizationFactory()
        self.client.force_login(self.user)
        self.assign_supervisor()
        self.create_experience()

    @staticmethod
    def generate_payload(
            claim,
            status_=REQUESTED,
            remarks='Remarks'
    ):
        return {
            'claims': [{
                'claim': claim,
                'status': status_,
                'description': remarks
            }]
        }

    @staticmethod
    def load_interval(string_interval):
        hh, mm, ss = string_interval.split(':')
        return timezone.timedelta(
            hours=int(hh),
            minutes=int(mm),
            seconds=int(ss),
        )

    def populate_timesheets(self):
        user = self.user
        dates = list(
            map(
                lambda x: x.date(),
                rrule(
                    dtstart=timezone.now().date()-timezone.timedelta(days=10),
                    freq=R_DAILY,
                    count=4
                )
            )
        )
        punch_times = [
            (time(9, 0), time(18, 0)),
            (time(8, 0), time(16, 0)),
            (time(12, 0), time(20, 0)),
            (time(6, 0), time(21, 0)),  # 9-3, 8+3
        ]
        for index, timesheet_for in enumerate(dates):
            for time_ in punch_times[index]:
                TimeSheet.objects.clock(
                    user,
                    combine_aware(
                        timesheet_for,
                        time_
                    ),
                    DEVICE
                )

    def create_experience(self):
        job_title = EmploymentJobTitle.objects.create(
            organization=self.organization,
            title=uuid.uuid4().hex[:5]
        )
        self.division = OrganizationDivisionFactory(
            organization=self.organization
        )

        if not self.division.head:
            self.division.head = self.user
            self.division.save()

        UserExperience.objects.create(
            **{
                "organization": self.organization,
                "user": self.user,
                "job_title": job_title,
                "division": self.division,
                "start_date": timezone.now().date() - timezone.timedelta(days=10),
                "is_current": True,
                "current_step": 1
            }
        )
        self.user.detail.organization = self.organization
        self.user.detail.save()

    def assign_supervisor(self):
        UserSupervisor.objects.create(
            user=self.user,
            supervisor=UserFactory(),
            approve=True, deny=True, forward=False
        )


class TestOvertimeRequest(OvertimeTestGenericMixin, TestCase):
    """
    Will Test the wide range of attendance adjustments that can be sent.
    Its effect, such as overtime will not be tested at all.
    """
    organization_name = 'ZK Tech'
    users = [
        ('alexa@alexa.com', 'helloSecretWorld', 'Female'),
    ]
    required_permissions_for_test = [
        ATTENDANCE_PERMISSION,
        ATTENDANCE_OVERTIME_CLAIM_PERMISSION
    ]

    def setUp(self):
        super().setUp()
        self.setup_permission()

    def test_overtime_edit(self):
        self.setup_permission()
        TimeSheet.objects.all().delete()
        ius = IndividualUserShift.objects.create(
            individual_setting=IndividualAttendanceSettingFactory(
                user=self.user,
                enable_overtime=True,
                overtime_setting=OvertimeSettingFactory(),
            ),
            shift=WorkShiftFactory(work_days=7),
            applicable_from=timezone.now()-timezone.timedelta(days=365)
        )
        WorkDay.objects.filter(shift=ius.shift).update(applicable_from=ius.applicable_from)
        self.populate_timesheets()
        generate_overtime(
            timezone.now().date()-timezone.timedelta(days=10),
            timezone.now().date(),
            DAILY
        )
        for overtime in OvertimeClaim.objects.all():
            pk = overtime.id
            edit_url = reverse(
                'api_v1:attendance:overtime-claim-detail',
                kwargs={
                    'organization_slug': self.organization.slug,
                    'claim': pk
                }
            )
            payload = self.client.get(
                edit_url
            ).json()
            # edit payload and resend
            pi, po = payload.get('punch_in_overtime'), payload.get('punch_out_overtime')
            punch_in, punch_out = self.load_interval(pi), self.load_interval(po)

            # decrease overtime [VALID]
            npi = (
                    punch_in - timedelta(minutes=5)
            ) if punch_in > timedelta(minutes=5) else punch_in
            npo = (
                    punch_out - timedelta(minutes=5)
            ) if punch_out > timedelta(minutes=5) else punch_out

            response = self.client.put(
                edit_url,
                data={
                    'punch_in_overtime': humanize_interval(npi),
                    'punch_out_overtime': humanize_interval(npo),
                    'remarks': 'remarks'
                },
                content_type='application/json'
            )
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK
            )
            self.assertEqual(
                response.json().get('punch_in_overtime'),
                humanize_interval(npi)
            )
            self.assertEqual(
                response.json().get('punch_out_overtime'),
                humanize_interval(npo)
            )

            # increase overtime [INVALID]
            response = self.client.put(
                edit_url,
                data={
                    'punch_in_overtime': humanize_interval(
                        punch_in + timedelta(minutes=5)
                    ),
                    'punch_out_overtime': humanize_interval(
                        punch_out + timedelta(minutes=5)
                    ),
                    'remarks': 'remarks'
                },
                content_type='application/json'
            )
            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST
            )
            self.assertEqual(
                humanize_interval(punch_in),
                pi
            )
            self.assertEqual(
                humanize_interval(punch_out),
                po
            )

    def test_overtime_request(self):
        TimeSheet.objects.all().delete()
        ius = IndividualUserShift.objects.create(
            individual_setting=IndividualAttendanceSettingFactory(
                user=self.user,
                enable_overtime=True,
                overtime_setting=OvertimeSettingFactory(),
            ),
            shift=WorkShiftFactory(work_days=7),
            applicable_from=timezone.now()-timezone.timedelta(days=365)
        )
        WorkDay.objects.filter(shift=ius.shift).update(applicable_from=ius.applicable_from)
        request_url = reverse(
            'api_v1:attendance:overtime-claims-bulk-update-list',
            kwargs={
                'organization_slug': self.user.detail.organization.slug
            }
        )

        # Overtime
        self.populate_timesheets()
        overtime_result = generate_overtime(
            timezone.now().date()-timezone.timedelta(days=10),
            timezone.now().date(),
            DAILY
        )

        self.assertEqual(
            overtime_result.get('created_count'),
            3  # out of 4 entries, 1 would not create an overtime.
        )

        response = self.client.get(
            reverse(
                'api_v1:attendance:overtime-claims-list',
                kwargs={'organization_slug': self.user.detail.organization.slug}
            ),
            data={
                'user': self.user.id,
                'status': UNCLAIMED
            }
        )
        overtime_results = response.json()
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(overtime_results.get('count'), 3)
        self.assertEqual(nested_get(overtime_results, 'counts.Unclaimed'), 3)

        for overtime in overtime_results.get('results'):
            punch_in_overtime = nested_get(
                overtime, 'overtime_entry.overtime_detail.punch_in_overtime'
            )
            punch_out_overtime = nested_get(
                overtime, 'overtime_entry.overtime_detail.punch_out_overtime'
            )
            pk = overtime.get('id')
            overtime_detail = OvertimeClaim.objects.get(pk=pk).overtime_entry.overtime_detail
            self.assertEqual(
                humanize_interval(overtime_detail.punch_in_overtime),
                punch_in_overtime
            )
            self.assertEqual(
                humanize_interval(overtime_detail.punch_out_overtime),
                punch_out_overtime
            )

            payload = self.generate_payload(
                pk
            )
            response = self.client.post(
                request_url,
                data=payload,
                format='json',
                content_type='application/json'
            )
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED
            )

    def setup_permission(self):
        admin_group, _ = Group.objects.update_or_create(name=ADMIN)
        self.user.groups.add(admin_group)
        og = OrganizationGroup.objects.create(
            organization=self.user.detail.organization,
            group=admin_group
        )
        for perm in self.required_permissions_for_test:
            permission, _ = HRSPermission.objects.update_or_create(**perm)
            og.permissions.add(permission)
