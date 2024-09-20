# from datetime import timedelta
#
# from django.test import TestCase
# from django.utils import timezone
#
# from irhrs.attendance.api.v1.tests.factory import IndividualAttendanceSettingFactory
# from irhrs.attendance.constants import APPROVED
# from irhrs.attendance.models import TimeSheet
# from irhrs.attendance.tasks.credit_hours import create_entry_from_approved_credit
# from irhrs.attendance.tests.factory import CreditSettingFactory, CreditRequestFactory
# from irhrs.users.api.v1.tests.factory import UserMinimalFactory
#
#
# class TestEarnedCreditHours(TestCase):
#
#     def test_earned_credit_hours(self):
#         pass
#
#
# class TestEntryForApprovedCreditHours(TestCase):
#
#     def test_no_entry_for_approved_credit_hours_and_no_reduction(self):
#         credit_setting = CreditSettingFactory()
#         user = UserMinimalFactory()
#         user.attendance_setting = IndividualAttendanceSettingFactory(
#             enable_credit_hour=True,
#             credit_hour_setting=credit_setting
#         )
#         user.save()
#         credit_request = CreditRequestFactory(sender=user)
#
#         created_entry = create_entry_from_approved_credit(credit_request)
#         self.assertIsNone(created_entry, 'No Credit for Requested state.')
#
#         user = UserMinimalFactory()
#         credit_request = CreditRequestFactory(
#             sender=user,
#             status=APPROVED,
#             credit_hour_duration=timedelta(minutes=30)
#         )
#         user.attendance_setting = IndividualAttendanceSettingFactory(
#             enable_credit_hour=True,
#             credit_hour_setting=credit_setting
#         )
#         user.save()
#         TimeSheet.objects.clock(
#             user,
#             timezone.now().astimezone().replace(hour=9, minute=0),
#             'Device'
#         )
#         TimeSheet.objects.clock(
#             user,
#             timezone.now().astimezone().replace(hour=18, minute=0),
#             'Device'
#         )
#         created_entry = create_entry_from_approved_credit(credit_request)
#         self.assertIsNotNone(created_entry)
#         self.assertEqual(created_entry.earned_credit_hours, timedelta(minutes=30))
#
#
# class TestLeaveBalanceUpdatedAfterEntryIsCreated(TestCase):
#
#     def test_leave_balance_updated_after_entry_created(self):
#         pass
