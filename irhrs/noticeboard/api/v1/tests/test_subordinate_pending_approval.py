from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from faker import Factory
from rest_framework import status
from rest_framework.test import APIClient

from irhrs.attendance.api.v1.tests.factory import (WorkShiftFactory2,
                                                   AttendanceAdjustmentFactory)
from irhrs.attendance.constants import (APPROVED, REQUESTED, FORWARDED, PUNCH_IN,
                                        PUNCH_OUT, DAILY)
from irhrs.attendance.models import (IndividualUserShift, TimeSheet, OvertimeClaim,
                                     AttendanceAdjustment, IndividualAttendanceSetting)
from irhrs.attendance.tasks.overtime import generate_overtime
from irhrs.common.api.tests.common import TestCaseValidateData
from irhrs.core.utils.common import get_today, get_yesterday
from irhrs.leave.api.v1.tests.factory import (LeaveTypeFactory, LeaveRuleFactory,
                                              LeaveAccountFactory, MasterSettingFactory)
from irhrs.leave.constants.model_constants import FULL_DAY, LEAVE_TYPE_CATEGORIES
from irhrs.leave.models import LeaveRequest
from irhrs.users.api.v1.tests.factory import UserFactory
from irhrs.users.models import UserSupervisor


class PendingApprovalTestCase(TestCaseValidateData):
    client = APIClient()
    fake = Factory.create()
    experience_url = 'api_v1:commons:all-request-summary-list'

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        super().setUp()
        self.users = [UserFactory()]
        self.user = get_user_model()
        self.client.force_login(self.users[0])
        self.user_check = self.users[0]
        self.organization = self.user_check.detail.organization
        self.user_hello = UserFactory(
            email=f'{self.fake.first_name()}.{self.fake.last_name()}{self.fake.word()}'
                  f'@gmail.com'
        )

        self.user_hello.detail.organization = self.organization
        self.user_hello.detail.save()

        UserSupervisor(
            user=self.user_hello,
            supervisor=self.user_check,
            approve=True,
            deny=True,
            forward=False
        )

    def test_leave_request(self):
        """
            test covers the pending approval of subordinates that includes attendance adjustments,
            leave requests and overtime claim requests
        """
        master_setting = MasterSettingFactory(organization=self.organization,
                                              half_shift_leave=True,
                                              compensatory=True
                                              )
        # create four different leave type on the basis of category and send leave request
        data = []
        for index, leave_type_constant in enumerate(LEAVE_TYPE_CATEGORIES):
            leave_type = LeaveTypeFactory(master_setting=master_setting,
                                          category=leave_type_constant[0],
                                          )
            leave_rule = LeaveRuleFactory(leave_type=leave_type,
                                          employee_can_apply=True,
                                          can_apply_half_shift=True,
                                          )
            leave_account = LeaveAccountFactory(user=self.user_check,
                                                rule=leave_rule,
                                                )
            data.append({
                'user': self.user_hello,
                'recipient': self.user_check,
                'balance': 1,
                'start': timezone.now() - relativedelta(days=index),
                'end': timezone.now() - relativedelta(days=index),
                'part_of_day': FULL_DAY,
                'leave_account': leave_account,
                'leave_rule': leave_rule,
                'status': APPROVED if index == 0 else FORWARDED if index == 1 else REQUESTED,
                'details': self.fake.text(max_nb_chars=500),
            })
        LeaveRequest.objects.bulk_create(
            [
                LeaveRequest(**leave) for leave in data
            ]
        )

        # create user's work shift, generate ot(over time) , late in and send adjustments
        self.create_individual_user_shift()
        self.generate_ot()
        late_time_sheet = self.generate_late_in()
        AttendanceAdjustmentFactory(timesheet=late_time_sheet,
                                    sender=self.user_hello,
                                    receiver=self.user_check,
                                    new_punch_in=get_yesterday(with_time=True).replace(
                                        hour=9, minute=0
                                    ),
                                    new_punch_out=get_yesterday(with_time=True).replace(
                                        hour=18,
                                        minute=0
                                    )
                                    )

        # leave request count from db
        leave_db = LeaveRequest.objects.filter(
            status__in=[REQUESTED, FORWARDED],
            recipient=self.user_check
        ).count()

        # overtime count from db
        overtime_claim_db = OvertimeClaim.objects.filter(
                status__in=[REQUESTED, FORWARDED],
                recipient=self.user_check
            ).count()

        # attendance adjustment count from db
        attendance_adjustment_db = AttendanceAdjustment.objects.filter(
                status__in=[REQUESTED, FORWARDED],
                receiver=self.user_check
            ).count()

        # get all request summary list from url
        response = self.client.get(reverse(self.experience_url))

        # test response from url is equal to database value
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('attendance_adjustments'), attendance_adjustment_db)
        self.assertEqual(response.json().get('leave_requests'), leave_db)
        self.assertEqual(response.json().get('overtime_claims'), overtime_claim_db)
        self.assertFalse(response.json().get('payroll_requests'))

    def generate_ot(self):
        """
        here we generate the overtime of user. Overtime entry and overtime claim implicitly sets
        user detail from logged in user, se we login as a user who has to send overtime request
        """
        self.client.force_login(self.user_hello)
        _ = self.make_attendance(
            punch_in=get_today(with_time=True).replace(
                hour=7,
                minute=0
            ) - timezone.timedelta(days=1),
            punch_out=get_today(with_time=True).replace(
                hour=20,
                minute=0
            ) - timezone.timedelta(days=1),
        )
        generate_overtime(
            timezone.now().date() - timezone.timedelta(days=4),
            timezone.now().date(),
            DAILY
        )
        # overtime claim recipient is implicitly set to logged in user, so we change the recipient
        overtime_claim = OvertimeClaim.objects.filter(recipient=self.user_hello).first()
        if overtime_claim:
            overtime_claim.status = REQUESTED
            overtime_claim.recipient = self.user_check
            overtime_claim.save()
        # now we change our login to supervisor to check all requests
        self.client.force_login(self.user_check)

    def create_individual_user_shift(self):
        """
        for creating attendance we need to set attendance setting and work shift
        """
        IndividualAttendanceSetting.objects.create(user=self.user_hello)
        IndividualUserShift.objects.create(
            individual_setting=self.user_hello.attendance_setting,
            shift=WorkShiftFactory2(work_days=6, organization=self.organization),
            applicable_from=timezone.now() - timezone.timedelta(days=6)
        )

    def generate_late_in(self):
        """
        user is late in so that we can send the attendance adjustment request
        """
        late_in_time_sheet = self.make_attendance(
            punch_in=get_yesterday(with_time=True).replace(
                hour=13,
                minute=0
            ),
            punch_out=get_yesterday(with_time=True).replace(
                hour=18,
                minute=0
            ),
        )
        return late_in_time_sheet

    def make_attendance(self, punch_in, punch_out):
        """
        :param punch_in: punch in time of user
        :param punch_out: punch out time of user
        :return: punch out time sheet, punch in and punch out are on the same time sheet so we
        return only one
        """
        # for punch in
        TimeSheet.objects.clock(
            user=self.user_hello,
            date_time=punch_in,
            entry_method='Web App',
            entry_type=PUNCH_IN
        )

        # for punch out
        punch_out = TimeSheet.objects.clock(
            user=self.user_hello,
            date_time=punch_out,
            entry_method='Web App',
            entry_type=PUNCH_OUT
        )
        return punch_out
