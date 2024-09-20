import random

from datetime import timedelta
from dateutil.parser import parse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.db.models import OuterRef, Exists, Q
from django.urls import reverse
from django.utils import timezone
from faker import Factory
from rest_framework import status
from rest_framework.test import APIClient

from irhrs.attendance.api.v1.tests.factory import (IndividualAttendanceSettingFactory,
                                                   WorkShiftFactory2)
from irhrs.attendance.constants import (WORKDAY, NO_LEAVE, PUNCH_IN, PUNCH_OUT, EARLY_OUT,
                                        LATE_IN)
from irhrs.attendance.models import TimeSheet, IndividualUserShift
from irhrs.common.api.tests.common import BaseTestCase as TestCase
from irhrs.core.constants.user import GENDER_CHOICES
from irhrs.core.utils import get_system_admin, nested_get, nested_getattr
from irhrs.core.utils.common import get_today, get_yesterday
from irhrs.core.utils.subordinates import set_subordinate_cache
from irhrs.leave.api.v1.serializers.leave_request import LeaveRequestSerializer
from irhrs.leave.api.v1.tests.factory import (LeaveAccountFactory, LeaveRuleFactory,
                                              LeaveTypeFactory, MasterSettingFactory)
from irhrs.leave.constants.model_constants import APPROVED, FULL_DAY
from irhrs.notification.test_utils import disable_notification
from irhrs.organization.api.v1.tests.factory import OrganizationFactory
from irhrs.permission.constants.groups import ADMIN
from irhrs.permission.constants.permissions import USER_PROFILE_PERMISSION, ATTENDANCE_PERMISSION, \
    ATTENDANCE_REPORTS_PERMISSION, LEAVE_PERMISSION, LEAVE_REPORT_PERMISSION
from irhrs.permission.models import HRSPermission
from irhrs.permission.models.hrs_permisssion import OrganizationGroup
from irhrs.users.models import UserDetail, UserSupervisor, UserExperience

User = get_user_model()


@disable_notification
class TestNoticeboardAttendanceAndLeave(TestCase):
    client = APIClient()
    fake = Factory.create()
    gender = list(dict(GENDER_CHOICES).keys())
    SYS_USER = []
    ACTIONS = ['early_out', 'late_in', 'absent', 'leave']

    def setUp(self):
        self.SYS_ADMIN = get_system_admin()
        self.organization = OrganizationFactory()
        self.SYS_USER = self.create_users()
        self.USER = self.SYS_USER[0]
        self.assign_supervisor()
        self.create_individual_user_shift()
        group, _ = Group.objects.update_or_create(name=ADMIN)
        self.USER.groups.add(group)
        org_group, _ = OrganizationGroup.objects.update_or_create(
            organization=self.organization,
            group=group
        )
        for perm in [
            USER_PROFILE_PERMISSION,
            ATTENDANCE_PERMISSION,
            ATTENDANCE_REPORTS_PERMISSION,
            LEAVE_PERMISSION,
            LEAVE_REPORT_PERMISSION,
        ]:
            perm, _ = HRSPermission.objects.update_or_create(**perm)
            org_group.permissions.add(perm)
        for action in self.ACTIONS:
            getattr(self, f'generate_{action}')()
        self.client.force_login(user=self.USER)

    def create_users(self):
        users = get_user_model().objects.bulk_create(
            [
                get_user_model()(
                    email=self.fake.email(),
                    first_name=self.fake.first_name(),
                    last_name=self.fake.first_name(),
                    password='defaultpassword',
                    is_active=True,
                    is_blocked=False
                ) for _ in range(50)
            ]
        )
        UserDetail.objects.bulk_create([
            UserDetail(
                user=u,
                date_of_birth=get_today(),
                organization=self.organization
            )
            for u in users
        ])
        UserExperience.objects.bulk_create([
            UserExperience(
                user=u,
                is_current=True,
                current_step=1,
                start_date=get_today()
            ) for u in users
        ])
        UserDetail.objects.filter(user__in=users).update(organization=self.organization)
        return users

    def assign_supervisor(self):
        subordinates = self.SYS_USER[1:]
        supervisor = self.USER
        UserSupervisor.objects.bulk_create(
            [
                UserSupervisor(
                    user=subordinate, supervisor=supervisor,
                    authority_order=1, forward=True,
                    approve=True, deny=True
                ) for subordinate in subordinates
            ]
        )

        set_subordinate_cache()

    def create_individual_user_shift(self):
        work_shift = WorkShiftFactory2(work_days=7, organization=self.organization)
        for user in self.SYS_USER:
            IndividualUserShift.objects.create(
                individual_setting=IndividualAttendanceSettingFactory(
                    user=user,
                ),
                shift=work_shift,
                applicable_from=timezone.now() - timezone.timedelta(days=365)
            )

    @staticmethod
    def make_attendance(users, punch_in, punch_out):
        for user in users:
            # for punch in
            TimeSheet.objects.clock(
                user=user,
                date_time=punch_in,
                entry_method='Web App',
                entry_type=PUNCH_IN
            )

            # for punch out
            _punch_out_ts = TimeSheet.objects.clock(
                user=user,
                date_time=punch_out,
                entry_method='Web App',
                entry_type=PUNCH_OUT
            )

    def generate_leave(self):
        users = self.SYS_USER[1:10]
        for user in users:
            next_week = get_today() + timedelta(days=7)
            last_week = get_today() - timedelta(days=7)
            ser = LeaveRequestSerializer(
                context={
                    'request': type(
                        'Request',
                        (object,),
                        {
                            'method': 'POST',
                            'user': user,
                        }
                    ),
                    'organization': self.organization
                },
                data=dict(
                    balance=1,
                    start=get_today(),
                    end=get_today(),
                    part_of_day=FULL_DAY,
                    leave_account=LeaveAccountFactory(
                        user=user,
                        rule=LeaveRuleFactory(
                            employee_can_apply=True,
                            can_apply_half_shift=True,
                            leave_type=LeaveTypeFactory(
                                master_setting=MasterSettingFactory(
                                    half_shift_leave=True,
                                    effective_from=last_week,
                                    effective_till=next_week,
                                    organization=user.detail.organization
                                )
                            )
                        )
                    ).id,
                    details="testing for leave",
                )
            )
            ser.is_valid(raise_exception=True)
            ser.save(status=APPROVED)

    def generate_absent(self):
        _ = TimeSheet.objects.bulk_create(
            [
                TimeSheet(
                    timesheet_user=user,
                    timesheet_for=get_today()
                ) for user in self.SYS_USER[10:20]
            ]
        )

    def generate_late_in(self):
        self.make_attendance(
            users=self.SYS_USER[20:30],
            punch_in=get_today(with_time=True).replace(
                hour=random.randint(10, 11),
                minute=random.randint(15, 30)
            ),
            punch_out=get_today(with_time=True).replace(
                hour=18,
                minute=random.randint(15, 30)
            ),
        )

    def generate_early_out(self):
        self.make_attendance(
            users=self.SYS_USER[30:40],
            punch_in=get_yesterday(with_time=True).replace(
                hour=8,
                minute=random.randint(49, 58)
            ),
            punch_out=get_yesterday(with_time=True).replace(
                hour=random.randint(15, 17),
                minute=random.randint(15, 30)
            ),
        )

    def test_noticeboard_attendance_and_leave(self):
        """
        this test covers test of apis  used for displaying absent, leave, late in and early out
        information of subordinates
        :return:
        """
        for action in self.ACTIONS:
            getattr(self, f'_test_for_{action}')()

    def _test_for_early_out(self):
        """
        test case for testing early out api used in Noticeboard for supervisor
        :return:
        """
        fil = dict(
            timesheet_entries__entry_type=PUNCH_OUT,
            timesheet_entries__category=EARLY_OUT,
            timesheet_for=get_yesterday()
        )
        self.validate_late_in_and_early_out(fil=fil, category='early-out')

    def _test_for_late_in(self):
        """
        test case for testing late out api used in Noticeboard for supervisor
        :return:
        """
        fil = dict(
            timesheet_entries__entry_type=PUNCH_IN,
            timesheet_entries__category=LATE_IN,
            timesheet_for=get_today()
        )
        self.validate_late_in_and_early_out(fil=fil, category='late-in')

    def _test_for_absent(self):
        """
        test case for testing absent user api used in Noticeboard for supervisor
        :return:
        """
        is_present = User.objects.all().current().filter(
            id=OuterRef("id"),
            timesheets__timesheet_for=get_today(),
            timesheets__is_present=True,
            timesheets__coefficient=WORKDAY,
            timesheets__leave_coefficient=NO_LEAVE
        )
        qs = User.objects.all().filter(
            user_experiences__is_current=True,
            detail__organization=self.organization,
            id__in=self.USER.subordinates_pks,
        )
        absent_data = qs.annotate(
            is_present=Exists(is_present)
        ).filter(
            Q(is_present=False) and
            Q(
                timesheets__timesheet_for=get_today(),
                timesheets__coefficient=WORKDAY,
                timesheets__leave_coefficient=NO_LEAVE,
                timesheets__is_present=False
            )
        ).distinct()

        response = self.client.get(
            reverse(
                'api_v1:attendance:attendance-summary-information-detail',
                kwargs={
                    'organization_slug': self.organization.slug,
                    'category': 'absent'
                }
            ),
            data={
                'supervisor': self.USER.id
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('count'), absent_data.count())
        results = response.json().get('results')
        for index, data in enumerate(absent_data):
            self.validate_absent_data(instance=data, result=results[index])

    def _test_for_leave(self):
        """
        test case for testing user on leave api used in Noticeboard for supervisor
        :return:
        """
        qs_data = User.objects.all().current().filter(
            id__in=self.USER.subordinates_pks,
            detail__organization=self.organization,
            leave_requests__status=APPROVED,
            leave_requests__start__date__lte=get_today(),
            leave_requests__end__date__gte=get_today(),
        ).order_by('id')
        response = self.client.get(
            reverse(
                'api_v1:leave:on-leave-users-list',
                kwargs={
                    'organization_slug': self.organization.slug
                }
            ),
            data={
                'supervisor': self.USER.id,
                'leave_for': 'today'
            }
        )
        results = response.json().get('results')
        for index, data in enumerate(qs_data):
            self.validate_absent_data(data, results[index], leave=True)

    def validate_absent_data(self, instance, result, leave=False):
        user_organization = nested_getattr(instance, 'detail.organization')
        self.assertEqual(
            instance.id,
            result.get('id'),
            'Id must be equal'
        )
        self.assertEqual(
            user_organization.slug,
            nested_get(result, 'organization.slug'),
            'Organization must be equal'
        )
        if not leave:
            self.assertTrue(
                user_organization.work_shifts.filter(
                    id=nested_get(result, 'work_shift.id')).exists(),
                'Work shift must exist within organization'
            )
        else:
            self.assertEqual(
                result.get('num_leaves'),
                1.0,
                'Number of leave balance must be equal to 1'
            )
            self.assertEqual(
                result.get('count_leaves'),
                1,
                'Count of leaves must be equal to 1'
            )

    def validate_late_in_and_early_out(self, fil: dict, category):
        qs_data = TimeSheet.objects.filter(
            timesheet_user_id__in=self.USER.subordinates_pks,
            timesheet_user__detail__organization=self.organization,
            timesheet_user__user_experiences__is_current=True,
            **fil
        )
        response = self.client.get(
            reverse(
                'api_v1:attendance:attendance-by-category-list',
                kwargs={
                    'organization_slug': self.organization.slug,
                    'category': category
                }
            ),
            data={
                'supervisor': self.USER.id
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('count'), qs_data.count())
        results = response.json().get('results')
        for index, datum in enumerate(qs_data):
            punch_in = datum.timesheet_entries.last().timestamp  # returns punch in entry
            punch_out = datum.timesheet_entries.first().timestamp  # returns punch out entry
            self.assertEqual(
                nested_get(results[index], 'user.id'),
                nested_getattr(datum, 'timesheet_user.id')
            )
            self.assertEqual(
                parse(results[index].get('punch_in')),
                punch_in
            )
            self.assertEqual(
                parse(results[index].get('punch_out')),
                punch_out
            )
