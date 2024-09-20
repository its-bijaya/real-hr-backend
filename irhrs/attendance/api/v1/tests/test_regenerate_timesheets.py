"""
Assumptions:
    User Exists
    Attendance Setting Exists
    Shift Exists
    Shift has been assigned
"""
from irhrs.attendance.api.v1.tests.factory import IndividualAttendanceSettingFactory
from irhrs.common.api.tests.common import RHRSAPITestCase


class TestAttendanceCalendarRegeneration(RHRSAPITestCase):
    organization_name = 'Attendance'

    users = [
        ('emailX@email.com', 'password', 'gender'),
        # ('emailY@email.com', 'password', 'gender')
    ]

    def setUp(self):
        super().setUp()
        user = self.created_users[0]
        attendance_setting = IndividualAttendanceSettingFactory(user=user)
