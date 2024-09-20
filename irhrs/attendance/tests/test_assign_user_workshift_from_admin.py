from datetime import timedelta, time
from django.core.exceptions import ValidationError

from irhrs.attendance.api.v1.tests.factory import WorkShiftFactory, \
    IndividualAttendanceSettingFactory, IndividualUserShiftFactory, WorkDayFactory, \
    WorkTimingFactory
from irhrs.attendance.models import IndividualAttendanceSetting, IndividualUserShift, TimeSheet
from irhrs.attendance.tasks.timesheets import populate_timesheet_for_user
from irhrs.attendance.views import AssignShiftToUserFromDate
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.utils.common import get_today


class TestAssignUserWorkShiftFromAdmin(RHRSAPITestCase):
    users = [
        ('normal@email.com', 'password', 'Male'),
        ('normaltwo@email.com', 'password', 'Male'),
        ('normalthree@email.com', 'password', 'Male'),
    ]
    organization_name = "Google"

    def setUp(self):
        super().setUp()
        self.workshift = WorkShiftFactory(work_days=7)
        self.from_date = get_today() - timedelta(days=10)
        self.setting1 = IndividualAttendanceSettingFactory(user=self.created_users[0])
        self.setting2 = IndividualAttendanceSettingFactory(user=self.created_users[1])
        self.setting3 = IndividualAttendanceSettingFactory(user=self.created_users[2])

    def test_assign_user_workshift_from_admin(self):
        normal = self.created_users[0]
        normal.detail.joined_date = get_today() - timedelta(days=11)
        normal.save()
        normal1 = self.created_users[1]
        normal1.detail.joined_date = get_today() - timedelta(days=12)
        normal1.save()
        normal2 = self.created_users[2]
        normal2.detail.joined_date = get_today() - timedelta(days=13)
        normal2.save()
        AssignShiftToUserFromDate.assign_shift(
            self.created_users, self.from_date, work_shift=self.workshift
        )
        ias = IndividualAttendanceSetting.objects.all()
        ius = IndividualUserShift.objects.all()
        self.assertEqual(ias.count(), len(self.created_users))
        self.assertEqual(ius.count(), len(self.created_users))
        for shift in ius:
            self.assertEqual(shift.shift, self.workshift)
            self.assertEqual(shift.applicable_from, self.from_date)

        for user in self.created_users:
            populate_timesheet_for_user(user, self.from_date, get_today())
            self.assertEqual(
                TimeSheet.objects.filter(timesheet_user=user).count(),
                11
            )

    def test_assign_user_workshift_before_joined_date(self):
        normal = self.created_users[0]
        normal.detail.joined_date = get_today() - timedelta(days=9)
        normal.save()
        try:
            AssignShiftToUserFromDate.assign_shift(
                self.created_users, self.from_date, work_shift=self.workshift
            )
        except ValidationError as e:
            self.assertEqual(
                e.args[0],
                f"Cannot assign work shift before joined date for {normal}"
            )

    def test_assign_user_workshift_from_date_smaller_than_applicable_date(self):
        for day in range(1, 8):
            WorkDayFactory(shift=self.workshift, day=day, applicable_from=get_today())
        AssignShiftToUserFromDate.assign_shift(
            self.created_users, self.from_date, work_shift=self.workshift
        )
        self.assertEqual(
            IndividualUserShift.objects.get(
                individual_setting=self.setting1, shift=self.workshift
            ).applicable_from,
            get_today()
        )
        self.assertEqual(
            IndividualUserShift.objects.get(
                individual_setting=self.setting2, shift=self.workshift
            ).applicable_from,
            get_today()
        )
        self.assertEqual(
            IndividualUserShift.objects.get(
                individual_setting=self.setting3, shift=self.workshift
            ).applicable_from,
            get_today()
        )

    def test_from_date_greater_than_today(self):
        self.from_date = get_today() + timedelta(days=1)
        try:
            AssignShiftToUserFromDate.assign_shift(
                self.created_users, self.from_date, work_shift=self.workshift
            )
        except ValidationError as e:
            self.assertEqual(
                e.args[0],
                "From date must be past date."
            )


class TestAssignUserWorkShiftFromAdminV2(RHRSAPITestCase):
    users = [
        ('normal@email.com', 'password', 'Male'),
        ('normaltwo@email.com', 'password', 'Male'),
        ('normalthree@email.com', 'password', 'Male'),
    ]
    organization_name = "Google"

    def setUp(self):
        super().setUp()
        self.workshift = WorkShiftFactory(work_days=7)
        self.from_date = get_today() - timedelta(days=10)
        self.ias = IndividualAttendanceSettingFactory(user=self.created_users[0])
        IndividualUserShiftFactory(
            individual_setting=self.ias,
            shift=self.workshift,
            applicable_from=self.from_date
        )

    def test_assign_user_workshift_from_admin_v2(self):
        # when one or many user is already assigned with shift, shift is assigned to no one.
        normal = self.created_users[0]
        normal.detail.joined_date = get_today() - timedelta(days=11)
        normal.save()
        try:
            AssignShiftToUserFromDate.assign_shift(
                self.created_users, self.from_date, work_shift=self.workshift
            )
        except ValidationError as e:
            ias = IndividualAttendanceSetting.objects.all()
            ius = IndividualUserShift.objects.all()
            self.assertEqual(ias.count(), 1)
            self.assertEqual(ius.count(), 1)
            self.assertEqual(
                e.args[0],
                "Cannot assign work shift to user! User already has timesheet or work shift."
            )


class TestAssignUserWorkShiftFromAdminForNightShift(RHRSAPITestCase):
    users = [
        ('normal@email.com', 'password', 'Male'),
        ('normaltwo@email.com', 'password', 'Male'),
        ('normalthree@email.com', 'password', 'Male'),
    ]
    organization_name = "Google"

    def setUp(self):
        super().setUp()
        self.from_date = get_today() - timedelta(days=10)
        self.shift = WorkShiftFactory(
            name="Night Shift",
            work_days=7,
            organization=self.organization,
            start_time_grace=time(hour=0, minute=0, second=0),
            end_time_grace=time(hour=0, minute=0, second=0)
        )
        for day in range(1, 8):
            self.work_day = WorkDayFactory(shift=self.shift, day=day, applicable_from=self.from_date)
            self.work_day.timings.all().delete()
            self.work_timing = WorkTimingFactory(
                work_day=self.work_day,
                start_time=time(hour=21, minute=0),
                end_time=time(hour=6, minute=0),
                extends=True
            )
        self.ias = IndividualAttendanceSettingFactory(
            user=self.created_users[0]
        )

    def test_assign_night_workshift_from_admin(self):
        normal = self.created_users[0]
        normal.detail.joined_date = get_today() - timedelta(days=11)
        normal.save()
        AssignShiftToUserFromDate.assign_shift(
            self.created_users[0], self.from_date, work_shift=self.shift
        )
        for timesheet in TimeSheet.objects.all():
            self.assertEqual(
                timesheet.leave_coefficient,
                'No Leave'
            )
