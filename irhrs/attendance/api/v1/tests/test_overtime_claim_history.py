from irhrs.common.api.tests.common import BaseTestCase as TestCase

from django.db.models import Sum, F
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from irhrs.attendance.api.v1.tests.factory import IndividualAttendanceSettingFactory, \
    OvertimeSettingFactory, WorkShiftFactory
from irhrs.attendance.api.v1.tests.test_overtime_claim_requests import OvertimeTestGenericMixin
from irhrs.attendance.constants import DAILY, REQUESTED, REQUESTED, FORWARDED, APPROVED, \
    DECLINED, CONFIRMED, UNCLAIMED
from irhrs.attendance.models import TimeSheet, IndividualUserShift, OvertimeClaim, OvertimeEntry, WorkDay
from irhrs.attendance.models.overtime import OvertimeEntryDetail
from irhrs.attendance.tasks.overtime import generate_overtime
from irhrs.core.utils.common import humanize_interval
from irhrs.organization.api.v1.tests.factory import OrganizationFactory
from irhrs.users.api.v1.tests.factory import UserFactory


class TestOvertimeHistory(OvertimeTestGenericMixin, TestCase):

    @property
    def url(self):
        return reverse(
            'api_v1:attendance:overtime-claims-list',
            kwargs={'organization_slug': self.user.detail.organization.slug}
        )

    def test_overtime_claim_history_stats(self):
        TimeSheet.objects.all().delete()
        self.user = UserFactory()
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
        self.organization = self.user.detail.organization
        self.client.force_login(self.user)
        self.assign_supervisor()
        self.create_experience()
        self.populate_timesheets()
        generate_overtime(
            timezone.now().date()-timezone.timedelta(days=10),
            timezone.now().date(),
            DAILY
        )
        # claim overtime
        # The process of request/approve/forward/deny/re-claim will be tested
        # thru supervisor's side, for now status will be hacked and set manually.

        self.tst_overtime_hours()
        for status_ in [
            REQUESTED,
            FORWARDED,
            APPROVED,
            DECLINED,
            CONFIRMED,
            UNCLAIMED,
        ]:
            OvertimeClaim.objects.filter(
                overtime_entry__user=self.user
            ).update(status=status_)
            self.tst_overtime_hours()

    def tst_overtime_hours(self):
        response = self.client.get(
            self.url,
            data={
                'user': self.user.id,
            }
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        overtime_stats = response.json()
        for status_ in [
            REQUESTED,
            FORWARDED,
            APPROVED,
            DECLINED,
            CONFIRMED,
            UNCLAIMED,
        ]:
            qs = OvertimeEntryDetail.objects.filter(
                overtime_entry__user=self.user,
                overtime_entry__claim__status=status_
            )
            total = qs.aggregate(
                minutes=Sum(F('punch_in_overtime') + F('punch_out_overtime'))
            ).get('minutes')
            total_normalized = qs.aggregate(
                minutes=Sum(F('normalized_overtime'))
            ).get('minutes')
            self.assertEqual(
                humanize_interval(total),
                overtime_stats.get(f'{status_}_minutes'.lower())
            )
            self.assertEqual(
                humanize_interval(total_normalized),
                overtime_stats.get(f'{status_}_normalized_minutes'.lower())
            )
            self.assertEqual(
                set(qs.values_list('overtime_entry__claim', flat=True)),
                {
                    j.get('id') for j in self.client.get(
                        self.url,
                        data={
                            'user': self.user.id,
                            'status': status_
                        }
                    ).json().get(
                        'results'
                    )
                }
            )
