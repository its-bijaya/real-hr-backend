from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.urls import reverse

from irhrs.attendance.api.v1.tests.factory import WorkShiftFactory, OvertimeSettingFactory
from irhrs.attendance.constants import WH_WEEKLY, WH_DAILY, WH_MONTHLY
from irhrs.attendance.models import IndividualUserShift
from irhrs.attendance.signals import create_attendance_setting
from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.core.utils.common import get_today, get_tomorrow, get_yesterday
from irhrs.users.api.v1.tests.factory import UserFactory

USER = get_user_model()


class TestIndividualSettings(RHRSTestCaseWithExperience):
    """
    Individual Attendance Settings
    1. When a new user is added, Attendance Setting must be immediately made.
    2. When a shift is assigned,
        -: If No previous shift, applicable from today,
        -: If previous shift, applicable from tomorrow,
    3. When a shift is removed,
        -: Future applicable should be deleted,
        -: Applicable since past should be terminated today.
    4. When overtime is assigned,
        -: Overtime setting should prevail.
        -: overtime flag (i.e. `enable_overtime` must be true)
    5. When overtime is removed,
        -: Overtime setting should be None
        -: Overtime flag (i.e. `enable_overtime` should be false).
    """
    organization_name = 'Attendance Setting Corp'
    users = [
        ('username@email.com', 'password', 'Female', 'Lottery Wi'),
        ('usernamea@email.com', 'password', 'Female', 'Lottery W'),
        ('usernameb@email.com', 'password', 'Female', 'Lottery Winn'),
        ('usernamec@email.com', 'password', 'Female', 'Lottery era'),
        ('usernamed@email.com', 'password', 'Female', 'Lottery ren'),
    ]

    def setUp(self):
        # disconnected by runner so needed to connect here
        post_save.connect(create_attendance_setting, sender=USER)
        super().setUp()

    def test_attendance_setting_created_when_user_is_added(self):
        """
        Create User and Attendance Setting must be made immediately.
        :return:
        """
        user = UserFactory()
        self.assertIsNotNone(
            getattr(user, 'attendance_setting', None)
        )

    def test_assign_shift(self):
        """
        Tests Shift assign in bulk for some users.
        """
        url = reverse(
            'api_v1:attendance:individual-settings-list',
            kwargs={
                'organization_slug': self.organization.slug
            }
        )
        work_shift = WorkShiftFactory(
            organization=self.organization
        )
        self.client.force_login(
            self.created_users[0]
        )
        response = self.client.post(
            url,
            data={
                'work_shift': work_shift.id,
                'users': [x.id for x in self.created_users[1:]]
            }
        )
        self.assertEqual(
            response.status_code,
            self.status.HTTP_201_CREATED
        )

        # check if out of range hours throws validation error
        # during bulk assign
        self.client.force_login(
            self.created_users[0]
        )
        response = self.client.post(
            url,
            data={
                'users': [self.created_users[-2].id],
                'working_hours': 7000,
                'working_hours_duration': WH_WEEKLY
            }
        )
        self.assertEqual(
            response.status_code,
            self.status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            response.json()['working_hours'],
            ['Set working hours less than 168 for weekly.']
        )

        for user in self.created_users[1:]:
            self.assertIsNone(
                user.attendance_setting.work_shift_for(get_yesterday())
            )
            self.assertEqual(
                user.attendance_setting.work_shift_for(get_today()),
                work_shift
            )
            self.assertEqual(
                user.attendance_setting.work_shift_for(get_tomorrow()),
                work_shift
            )

        """
            Test Shift Unassigned,
            When shift is unassigned:-
                I-: If applicable_from is lte today, it will be set till today.
                II-: If applicable_from is gt today, it will be deleted.
        """
        # Case - I
        response = self.client.post(
            url,
            data={
                'remove_shift': True,
                'users': [x.id for x in self.created_users[1:-1]]
            }
        )
        self.assertEqual(
            response.status_code,
            self.status.HTTP_201_CREATED
        )
        for user in self.created_users[1:-1]:
            yesterday_shift = user.attendance_setting.work_shift_for(
                get_yesterday()
            )
            today_shift = user.attendance_setting.work_shift_for(
                get_today()
            )
            tomorrow_shift = user.attendance_setting.work_shift_for(
                get_tomorrow()
            )

            self.assertIsNone(yesterday_shift)
            self.assertEqual(today_shift, work_shift)
            self.assertIsNone(tomorrow_shift)

        # Case - II
        # Assign New Shift
        shift_2 = WorkShiftFactory(organization=self.organization)
        last_user = self.created_users[-1]
        resp = self.client.post(
            url,
            data={
                'work_shift': shift_2.pk,
                'users': [last_user.id]
            }
        )
        self.assertEqual(
            resp.status_code,
            self.status.HTTP_201_CREATED
        )

        # Last user's yesterday shift should be null, today's shift should be `work_shift`,
        # starting tomorrow, this user's shift should be shift2
        yesterday_shift = last_user.attendance_setting.work_shift_for(
            get_yesterday()
        )
        today_shift = last_user.attendance_setting.work_shift_for(
            get_today()
        )
        tomorrow_shift = last_user.attendance_setting.work_shift_for(
            get_tomorrow()
        )

        self.assertIsNone(yesterday_shift)
        self.assertEqual(today_shift, work_shift)
        self.assertEqual(
            tomorrow_shift,
            shift_2,
            "The user's new shift should be applicable from tomorrow"
        )
        upcoming_shift = self.client.get(
            reverse(
                'api_v1:attendance:individual-settings-detail',
                kwargs={
                    'organization_slug': self.organization.slug,
                    'pk': last_user.attendance_setting.id
                }
            ),
            data={
                'search': last_user.first_name
            }
        ).json().get(
            'upcoming_shift'
        )
        self.assertEqual(
            upcoming_shift[0].get('id'),
            shift_2.id
        )

        # Now, remove shift
        self.client.post(
            url,
            data={
                'remove_shift': True,
                'users': [last_user.id]
            }
        )

        # This Shift should not exist in user's map
        self.assertIsNone(
            last_user.attendance_setting.work_shift_for(get_tomorrow())
        )
        self.assertFalse(
            IndividualUserShift.objects.filter(
                individual_setting__user=last_user,
                shift=shift_2
            ).exists()
        )

        # Test Overtime Setting Assign
        overtime_setting = OvertimeSettingFactory(
            organization=self.organization
        )
        resp = self.client.post(
            url,
            data={
                'overtime_setting': overtime_setting.slug,
                'users': [x.id for x in self.created_users[1:-1]]
            }
        )
        self.assertEqual(
            resp.status_code,
            self.status.HTTP_201_CREATED
        )
        for user in self.created_users[1:-1]:
            user.refresh_from_db()
            self.assertEqual(
                user.attendance_setting.overtime_setting,
                overtime_setting
            )
            self.assertTrue(user.attendance_setting.enable_overtime)

        # Remove Overtime
        resp = self.client.post(
            url,
            data={
                'remove_overtime': True,
                'users': [x.id for x in self.created_users[1:-1]]
            }
        )
        self.assertEqual(
            resp.status_code,
            self.status.HTTP_201_CREATED
        )
        for user in self.created_users[1:-1]:
            user.refresh_from_db()
            self.assertIsNone(user.attendance_setting.overtime_setting)
            self.assertFalse(user.attendance_setting.enable_overtime)

    def test_setting_update_for_past_user(self):
        # should not be allowed;
        url = reverse(
            'api_v1:attendance:individual-settings-list',
            kwargs={
                'organization_slug': self.organization.slug
            },
        )
        self.client.force_login(
            self.created_users[0]
        )
        request = self.client.post(f'{url}?user_status=past', data={})
        self.assertEqual(request.status_code, 403)

        request = self.client.post(f'{url}?user_status=all', data={})
        self.assertEqual(request.status_code, 403)

        request = self.client.post(f'{url}?user_status=current', data={})
        self.assertNotEqual(request.status_code, 403)

    def tearDown(self) -> None:
        post_save.disconnect(create_attendance_setting, sender=USER)
