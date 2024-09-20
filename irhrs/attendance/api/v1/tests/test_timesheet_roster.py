"""
-- Supervisor should be prompt with confirmation when assigning shifts to the subordinates.
-- Should display "-" in the rooster report with red background color if the user has not been assigned to any shift

TC-1 Unit Test Roster TimeSheet.
TC0 test_supervisor_can_assign_roster_to_subordinates Supervisor should be able to assign shifts to its subordinated.
TC1 test_supervisor_can_assign_roster_to_subordinates_across_organization Subordinates can be of any organization so should be able to access shift of any organization.
TC2 test_cannot_assign_roster_from_another_organization Shift should be assigned from only users dependent organization.
TC3 test_roster_overrides_shift_for_selected_date Supervisor should be able to override default shifts for each subordinates for selected days.
TC4 test_user_notified_after_roster_assigned. Subordinate and HR should be notified when the shift is assigned by the supervisor.
TC5 test_can_assign_roster_for_future Supervisor should be able to assign shift for future too.
TC6 test_can_filter_immediate_subordinates_only Supervisor should have option to list immediate subordinates with options to list all subordinates.
TC7 test_normal_user_can_view_roster_for_self Assigned shift should be displayed in user and HR section.
TC8 test_HR_can_view_roster_for_users_in_organization
TC9 test_can_bulk_assign_roster_for_bulk_users "Supervisor should be able to set shifts for multiple users and multiple days at one time. "If only the default shift is set, it should be shown in the rooster report.
TC10 test_cannot_assign_roster_to_past Supervisor should not be able to assign shift to past dates.
TC11 test_can_sort_list_with_full_name Should have option to sort the list with employee name.
TC12 test_supervisor_can_access_work_shift_page Supervisor should be able to view list of available shifts with its timings.
TC13 test_can_see_shifts_for_fiscal_month Should be able to select preferred months and dates to assign the shift.
TC14 test_can_see_timings_for_each_day_across_fiscal_month Report should display all the days in the selected months with available assigned shift to each individual for each days of the month.
TC15 test_can_paginate_API Should have option to paginated the list.
"""
from unittest.mock import patch, MagicMock

from datetime import timedelta
from random import randint

from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from irhrs.attendance.api.v1.tests.factory import IndividualAttendanceSettingFactory, \
    WorkShiftFactory
from irhrs.attendance.models import WorkDay
from irhrs.attendance.models.shift_roster import TimeSheetRoster
from irhrs.attendance.tasks.timesheets import populate_timesheet_for_user
from irhrs.common.api.tests.common import BaseTestCase
from irhrs.core.utils.common import get_today
from irhrs.notification.models import Notification
from irhrs.notification.models.notification import OrganizationNotification
from irhrs.organization.api.v1.tests.factory import FiscalYearFactory
from irhrs.permission.constants.permissions import ATTENDANCE_TIMESHEET_ROSTER_PERMISSION
from irhrs.users.api.v1.tests.factory import UserMinimalFactory, UserFactory
from irhrs.users.models import UserSupervisor
from irhrs.users.utils import set_user_organization_permission_cache

User = get_user_model()

# User.objects.all().__class__.current = User.objects.all


class TestTimeSheetRosterAPI(BaseTestCase):
    def setUp(self) -> None:
        super(TestTimeSheetRosterAPI, self).setUp()
        self.subordinate = UserFactory()
        self.subordinate2 = UserFactory()

        self.org = self.subordinate.detail.organization
        self.org2 = self.subordinate2.detail.organization

        self.supervisor = UserFactory(_organization=self.org)

        self.subordinate.supervisors.create(supervisor=self.supervisor)
        self.subordinate2.supervisors.create(supervisor=self.supervisor)

        IndividualAttendanceSettingFactory(user=self.subordinate)
        IndividualAttendanceSettingFactory(user=self.subordinate2)

        self.shift = WorkShiftFactory(organization=self.org)
        self.shift2 = WorkShiftFactory(organization=self.org2)

        self.fiscal_year = FiscalYearFactory(
            organization=self.org,
            start_at=timezone.now().date(),
            end_at=timezone.now().date() + relativedelta(years=1)
        )
        self.fiscal_year2 = FiscalYearFactory(
            organization=self.org2,
            start_at=timezone.now().date(),
            end_at=timezone.now().date() + relativedelta(years=1)
        )

        self.fiscal_month = self.fiscal_year.fiscal_months.filter(
            start_at__gt=get_today()
        ).first()
        self.fiscal_month2 = self.fiscal_year2.fiscal_months.filter(
            start_at__gt=get_today()
        ).first()

    def url(self, slug=None, fiscal_month=None, _as='supervisor', immediate='true'):
        slug = slug or self.org.slug
        fiscal_month = fiscal_month or self.fiscal_month
        return reverse(
            'api_v1:attendance:timesheet-roster-list',
            kwargs={
                'organization_slug': slug
            }
        ) + '?fiscal_month=%s&as=%s&immediate_subordinates=%s' % (fiscal_month.id, _as, immediate)

    def test_tc000_supervisor_can_assign_roster_to_subordinates(self):
        """
        supervisor should be able to assign shifts to its subordinates.
        """
        selected_date = self.random_date
        payload = {
            "data": [
                {
                    "user": self.subordinate.id,
                    "roster_list": [
                        {
                            "date": selected_date,
                            "shift": self.shift.id
                        }
                    ]
                }
            ]
        }
        self.client.force_login(self.supervisor)
        response = self.client.post(
            self.url(),
            data=payload,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            TimeSheetRoster.objects.filter(user=self.subordinate, date=selected_date).values_list(
                'shift', flat=True
            ).first(),
            self.shift.id
        )

    def test_tc001_supervisor_can_assign_roster_to_subordinates_across_organization(self):
        """
        subordinates can be of any organization so should be able to access shift of any
        organization.
        """
        selected_date = self.random_date
        payload = {
            "data": [
                {
                    "user": self.subordinate2.id,
                    "roster_list": [
                        {
                            "date": selected_date,
                            "shift": self.shift2.id
                        }
                    ]
                }
            ]
        }
        self.client.force_login(self.supervisor)
        response = self.client.post(
            self.url(slug=self.org2.slug, fiscal_month=self.fiscal_month2),
            data=payload,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            TimeSheetRoster.objects.filter(
                user=self.subordinate2,
                date=selected_date
            ).values_list(
                'shift',
                flat=True
            ).first(),
            self.shift2.id
        )

    def test_tc003_roster_overrides_shift_for_selected_date(self):
        """
        supervisor should be able to override default shifts for each subordinates for selected day
        """
        selected_date = self.random_date
        magical_shift = WorkShiftFactory(organization=self.org)
        magical_shift.work_days.update(applicable_from=selected_date)
        self.subordinate.attendance_setting.individual_setting_shift.create(
            shift=magical_shift,
            applicable_from=selected_date
        )
        payload = {
            "data": [
                {
                    "user": self.subordinate.id,
                    "roster_list": [
                        {
                            "date": selected_date,
                            "shift": self.shift.id
                        }
                    ]
                }
            ]
        }
        self.client.force_login(self.supervisor)
        post_response = self.client.post(
            self.url(),
            data=payload,
            content_type='application/json'
        )
        self.assertEqual(post_response.status_code, status.HTTP_201_CREATED)
        # after roster is created, other days should display magical_shift, whereas override
        # date should show selected shift.
        get_response = self.client.get(
            self.url(),
            content_type='application/json'
        )
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        results = get_response.json().get('results')
        roster_data = results[0].get('results')
        for date, roster in roster_data.items():
            lhs = roster.get('id')
            rhs = self.shift.id if date == str(selected_date) else magical_shift.id if parse(
                date
            ).date() >= selected_date else None
            self.assertEqual(lhs, rhs)

    def test_tc004_user_notified_after_roster_assigned(self):
        """
        subordinate and hr should be notified when the shift is assigned by the supervisor.
        """
        payload = {
            "data": [
                {
                    "user": self.subordinate.id,
                    "roster_list": [
                        {
                            "date": self.fiscal_month.start_at,
                            "shift": self.shift.id
                        }
                    ]
                }
            ]
        }
        self.client.force_login(self.supervisor)
        post_response = self.client.post(
            self.url(),
            data=payload,
            content_type='application/json'
        )
        self.assertEqual(post_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.subordinate,
                url='/user/attendance/reports/roster/?fiscal_month=%s' % self.fiscal_month.id,
                text='Your roster for the month of %s has been updated.' % (
                    self.fiscal_month.display_name
                )
            ).exists(),
        )
        self.assertTrue(
            OrganizationNotification.objects.filter(
                recipient=self.org,
                url='/admin/%s/attendance/reports/roster/?fiscal_month=%s' % (
                    self.org.slug,
                    self.fiscal_month.id
                ),
                text='TimeSheet Roster of %s for the month of %s has been updated' % (
                    self.subordinate.full_name,
                    self.fiscal_month.display_name
                )
            ).exists(),
        )

    # def test_tc005_can_assign_roster_for_future(self):
    #     """
    #     supervisor should be able to assign shift for future too.
    #     pass
    #     """
    #     Adding roster for past is not allowed / Ignored.

    def test_tc006_can_filter_immediate_subordinates_only(self):
        """
        supervisor should have option to list immediate subordinates with options to list all subordinates.
        """
        nested_subordinate = UserFactory(_organization=self.org)
        nested_subordinate.supervisors.create(supervisor=self.subordinate)
        IndividualAttendanceSettingFactory(user=nested_subordinate)
        self.client.force_login(self.supervisor)
        get_response = self.client.get(
            self.url(),
            content_type='application/json'
        )
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        results = get_response.json().get('results')
        user_ids = [result.get('id') for result in results]
        self.assertNotIn(
            member=nested_subordinate.id,
            container=user_ids
        )
        get_response = self.client.get(
            self.url(immediate='false'),
            content_type='application/json'
        )
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        results = get_response.json().get('results')
        user_ids = [result.get('id') for result in results]
        self.assertIn(
            member=nested_subordinate.id,
            container=user_ids
        )

    def test_tc007_normal_user_can_view_roster_for_self(self):
        """
        assigned shift should be displayed in user and hr section.
        """
        selected_date = self.random_date
        magical_shift = WorkShiftFactory(organization=self.org)
        magical_shift.work_days.update(applicable_from=selected_date)
        self.client.force_login(self.subordinate)
        self.subordinate.attendance_setting.individual_setting_shift.create(
            shift=magical_shift,
            applicable_from=selected_date
        )
        get_response = self.client.get(
            self.url(_as='user'),
            content_type='application/json'
        )
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        results_count = get_response.json().get('count')
        self.assertEqual(results_count, 1)
        self.assertEqual(get_response.json().get('results')[0].get('id'), self.subordinate.id)

    def test_tc008_hr_can_view_roster_for_users_in_organization(self):
        """
        HR Can view roster for users in organization.
        """
        admin = UserFactory(_organization=self.org)
        IndividualAttendanceSettingFactory(user=admin)
        IndividualAttendanceSettingFactory(user=self.supervisor)
        self.client.force_login(admin)
        with patch.object(
            get_user_model(),
            'get_hrs_permissions',
            return_value={ATTENDANCE_TIMESHEET_ROSTER_PERMISSION['code']}
        ):
            get_response = self.client.get(
                self.url(_as='hr'),
                content_type='application/json'
            )
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        results_count = get_response.json().get('count')
        self.assertEqual(results_count, 3)  # sub, supervisor, admin -- org, sub2 -- org2

    def test_tc009_can_bulk_assign_roster_for_bulk_users(self):
        """
        "supervisor should be able to set shifts for multiple users and multiple days at one time. "if only the default shift is set, it should be shown in the rooster report.
        """
        subordinate_x = UserFactory(_organization=self.org)
        subordinate_y = UserFactory(_organization=self.org)
        subordinate_z = UserFactory(_organization=self.org)
        from django.core.cache import cache
        # need to clear cache to set new immediate_supervisor again in cache
        cache.clear()
        UserSupervisor.objects.bulk_create(
            [
                UserSupervisor(supervisor=self.supervisor, user=user)
                for user in (subordinate_y, subordinate_x, subordinate_z)
            ]
        )
        
        selected_date = self.random_date
        payload = {
            "data": [
                {
                    "user": user.id,
                    "roster_list": [
                        {
                            "date": selected_date,
                            "shift": self.shift.id
                        }
                    ]
                }
                for user in (subordinate_y, subordinate_x, subordinate_z)
            ]
        }
        self.client.force_login(self.supervisor)
        post_response = self.client.post(
            self.url(),
            data=payload,
            content_type='application/json'
        )
        self.assertEqual(post_response.status_code, status.HTTP_201_CREATED)
        for user in (subordinate_y, subordinate_x, subordinate_z):
            self.assertEqual(
                TimeSheetRoster.objects.filter(user=user, date=selected_date).values_list(
                    'shift', flat=True
                ).first(),
                self.shift.id
            )

    def test_tc010_cannot_assign_roster_to_past(self):
        """
        supervisor should not be able to assign shift to past dates.
        """
        self.client.force_login(self.supervisor)
        payload = {
            "data": [
                {
                    "user": self.subordinate.id,
                    "roster_list": [
                        {
                            "date": self.random_date - timedelta(100),
                            "shift": self.shift.id
                        }
                    ]
                }
            ]
        }
        response = self.client.post(self.url(), payload, content_type='application/json')
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            response.json(),
            {'data': [{'roster_list': [{'date': ['The date is beyond fiscal range']}]}]}
        )

    # def test_tc012_supervisor_can_access_work_shift_page(self):
    #     """
    #     supervisor should be able to view list of available shifts with its timings.
    #     """
    #     pass

    # def test_tc013_can_see_shifts_for_fiscal_month(self):
    #     """
    #     should be able to select preferred months and dates to assign the shift.
    #     """
    #     pass

    # def test_tc014_can_see_timings_for_each_day_across_fiscal_month(self):
    #     """
    #     report should display all the days in the selected months with available assigned
    #     shift to each individual for each days of the month.
    #     """
    #     pass

    # def test_tc015_can_paginate_api(self):
    #     """
    #     should have option to paginated the list.
    #     """
    #     pass

    @property
    def random_date(self):
        return self.fiscal_month.start_at + timedelta(randint(1, 10))


class TestTimeSheetRosterUtil(BaseTestCase):

    def test_timesheet_is_created_according_to_roster_shift(self):
        user = UserFactory()
        setting = IndividualAttendanceSettingFactory(user=user)
        start_date = timezone.now()-timedelta(2)
        alt_shift = WorkShiftFactory()
        alt_shift_2 = WorkShiftFactory()
        WorkDay.objects.filter(
            shift__in=(alt_shift, alt_shift_2)
        ).update(
            applicable_from=start_date
        )
        setting.individual_setting_shift.create(
            shift=alt_shift,
            applicable_from=start_date
        )
        roster_date = timezone.now()-timedelta(1)
        TimeSheetRoster.objects.create(
            user=user,
            date=roster_date,
            shift=alt_shift_2
        )
        populate_timesheet_for_user(
            user, start_date, timezone.now().date(),
            notify='false', authority=1
        )
        self.assertEqual(
            user.timesheets.filter(
                timesheet_for=start_date
            ).values_list(
                'work_shift',
                flat=True
            ).first(),
            alt_shift.id
        )
        self.assertEqual(
            user.timesheets.filter(
                timesheet_for=roster_date
            ).values_list(
                'work_shift',
                flat=True
            ).first(),
            alt_shift_2.id
        )
        self.assertEqual(
            user.timesheets.filter(
                timesheet_for=timezone.now().date()
            ).values_list(
                'work_shift',
                flat=True
            ).first(),
            alt_shift.id
        )
