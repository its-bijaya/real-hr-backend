import json
import random
from irhrs.common.api.tests.common import BaseTestCase as TestCase

from dateutil.parser import parse
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from irhrs.attendance.api.v1.tests.factory import IndividualAttendanceSettingFactory, \
    OvertimeSettingFactory, WorkShiftFactory
from irhrs.attendance.api.v1.tests.test_attendance_adjustments import stringify_date
from irhrs.attendance.api.v1.tests.test_overtime_claim_requests import OvertimeTestGenericMixin
from irhrs.attendance.constants import (
    REQUESTED, FORWARDED, APPROVED, DECLINED, CONFIRMED, UNCLAIMED, PUNCH_IN, PUNCH_OUT
)
from irhrs.attendance.models import TimeSheet, IndividualUserShift, AttendanceAdjustment
from irhrs.users.api.v1.tests.factory import UserFactory


class TestAttendanceAdjustmentReport(OvertimeTestGenericMixin, TestCase):

    def test_adjustment_for_valid_scenarios(self):
        self.user = UserFactory()
        IndividualUserShift.objects.create(
            individual_setting=IndividualAttendanceSettingFactory(
                user=self.user,
            ),
            shift=WorkShiftFactory(work_days=7),
            applicable_from=timezone.now() - timezone.timedelta(days=365)
        )
        self.client.force_login(self.user)
        self.assign_supervisor()
        self.create_experience()
        self.populate_timesheets()
        for timesheet in self.user.timesheets.all():
            npi, npo = timesheet.punch_in + timezone.timedelta(
                minutes=random.randint(-60, 60)
            ), timesheet.punch_out + timezone.timedelta(
                minutes=random.randint(-60, 60)
            )
            response = self.create_adjustment(
                timesheet,
                npi,
                npo
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            for result, adj in zip((npi, npo), timesheet.adjustment_requests.order_by('timestamp')):
                detail_url = reverse(
                    'api_v1:attendance:adjustments-detail',
                    kwargs={
                        'organization_slug': self.user.detail.organization.slug,
                        'pk': adj.pk
                    }
                )
                response = self.client.get(detail_url)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(
                    parse(response.json().get('timestamp')),
                    result.astimezone()
                )

    def test_adjustment_for_invalid_scenarios(self):
        TimeSheet.objects.all().delete()
        self.user = UserFactory()
        IndividualUserShift.objects.create(
            individual_setting=IndividualAttendanceSettingFactory(
                user=self.user,
            ),
            shift=WorkShiftFactory(work_days=7),
            applicable_from=timezone.now() - timezone.timedelta(days=365)
        )
        self.client.force_login(self.user)
        self.assign_supervisor()
        self.create_experience()
        self.populate_timesheets()
        for timesheet in self.user.timesheets.all():
            npi, npo = (timezone.now() + timezone.timedelta(10),) * 2
            response = self.create_adjustment(timesheet, npi, npo)
            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
                "Adjustments for future date should be invalid."
            )
            self.assertIn(
                'timestamp', response.json().get('adjustments')[0]
            )

    def test_attendance_adjustment_per_category(self):
        TimeSheet.objects.all().delete()
        self.user = UserFactory()
        IndividualUserShift.objects.create(
            individual_setting=IndividualAttendanceSettingFactory(
                user=self.user,
            ),
            shift=WorkShiftFactory(work_days=7),
            applicable_from=timezone.now() - timezone.timedelta(days=365)
        )
        self.client.force_login(self.user)
        self.assign_supervisor()
        self.create_experience()
        self.populate_timesheets()
        for timesheet in self.user.timesheets.all():
            npi, npo = timesheet.punch_in + timezone.timedelta(
                minutes=random.randint(-60, 60)
            ), timesheet.punch_out + timezone.timedelta(
                minutes=random.randint(-60, 60)
            )
            response = self.create_adjustment(
                timesheet,
                npi,
                npo
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.verify_status_counts()

        for status_ in (REQUESTED, FORWARDED, APPROVED, DECLINED):
            AttendanceAdjustment.objects.filter(
                timesheet__timesheet_user=self.user
            ).update(
                status=status_
            )
            self.verify_status_counts()

    def create_adjustment(self, timesheet, new_punch_in, new_punch_out):
        user = self.user
        url = reverse(
            'api_v1:attendance:adjustments-bulk-list',
            kwargs={
                'organization_slug': user.detail.organization.slug
            }
        )
        data = {
            'adjustments': [
                {
                    'timesheet': timesheet.id,
                    'timestamp': stringify_date(new_punch_in),
                    'category': PUNCH_IN,
                    'description': 'remarks'
                },
                {
                    'timesheet': timesheet.id,
                    'timestamp': stringify_date(new_punch_out),
                    'category': PUNCH_OUT,
                    'description': 'remarks'
                },

            ]
        }
        return self.client.post(
            url,
            data=data,
            content_type='application/json'
        )

    def verify_status_counts(self):
        url = reverse(
            'api_v1:attendance:adjustments-list',
            kwargs={
                'organization_slug': self.user.detail.organization.slug
            }
        )
        response = self.client.get(url)
        counts = response.json().get('counts')
        for status_ in (REQUESTED, FORWARDED, APPROVED, DECLINED):
            self.assertEqual(
                counts.get(status_),
                AttendanceAdjustment.objects.filter(
                    status=status_,
                    timesheet__timesheet_user=self.user
                ).count()
            )
