import factory
from factory.django import DjangoModelFactory
from django.utils import timezone

from datetime import time, timedelta

from irhrs.attendance.constants import DAILY_OVERTIME_LIMIT_IN_HOURS, \
    DAILY, BOTH, NEITHER, GENERATE_BOTH, DAYS
from irhrs.attendance.models import IndividualAttendanceSetting, \
    IndividualUserShift, WorkDay, WorkShift, WorkTiming, \
    OvertimeSetting, TimeSheet, TimeSheetEntry, AttendanceAdjustment, \
    CreditHourSetting, PreApprovalOvertime
from irhrs.core.utils.common import get_today
from irhrs.organization.api.v1.tests.factory import OrganizationFactory
from irhrs.users.api.v1.tests.factory import UserFactory


class WorkTimingFactory(DjangoModelFactory):
    class Meta:
        model = WorkTiming

    start_time = time(hour=9, minute=0)
    end_time = time(hour=18, minute=0)
    working_minutes = 540


class WorkDayFactory(DjangoModelFactory):
    class Meta:
        model = WorkDay

    day = factory.sequence(lambda n: n % 7 + 1)
    applicable_from = factory.LazyFunction(lambda: get_today() - timezone.timedelta(days=100))

    @factory.post_generation
    def timings(self, create, extracted, **kwargs):
        if not create:
            return

        if not extracted:
            # if no passed then only create timing
            WorkTimingFactory(work_day=self)


class WorkShiftFactory(DjangoModelFactory):
    class Meta:
        model = WorkShift

    name = factory.Faker('name')
    start_time_grace = timezone.timedelta(0)
    end_time_grace = timezone.timedelta(0)
    organization = factory.SubFactory(OrganizationFactory)

    @factory.post_generation
    def work_days(self, create, extracted, **kwargs):
        if not create:
            return

        if isinstance(extracted, int):
            for w in range(extracted):
                if w not in [0, 6]:
                    WorkDayFactory(
                        shift=self,
                        day=w
                    )

            if extracted != 0 and not extracted:
                WorkDayFactory.create_batch(5, shift=self)


class WorkShiftFactory2(WorkShiftFactory):
    class Meta:
        model = WorkShift

    @factory.post_generation
    def work_days(self, create, extracted, **kwargs):
        if not create:
            return

        if isinstance(extracted, int):
            for day in range(2, extracted + 2):
                WorkDayFactory(shift=self, day=day % 7 + 1)

        if extracted != 0 and not extracted:
            WorkDayFactory.create_batch(5, shift=self)


class IndividualAttendanceSettingFactory(DjangoModelFactory):
    class Meta:
        model = IndividualAttendanceSetting

    user = factory.SubFactory(UserFactory)


class IndividualUserShiftFactory(DjangoModelFactory):
    class Meta:
        model = IndividualUserShift

    individual_setting = factory.SubFactory(IndividualAttendanceSettingFactory)
    shift = factory.SubFactory(WorkShiftFactory)


class OvertimeSettingFactory(DjangoModelFactory):
    class Meta:
        model = OvertimeSetting

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.Faker('name')
    daily_overtime_limit = DAILY_OVERTIME_LIMIT_IN_HOURS * 60
    off_day_overtime = True
    off_day_overtime_limit = DAILY_OVERTIME_LIMIT_IN_HOURS * 60
    applicable_before = 0
    applicable_after = 0
    overtime_calculation = DAILY
    paid_holiday_affect_overtime = True
    holiday_overtime_limit = DAILY_OVERTIME_LIMIT_IN_HOURS * 60
    leave_affect_overtime = True
    leave_overtime_limit = DAILY_OVERTIME_LIMIT_IN_HOURS * 60
    is_archived = False
    overtime_applicable_only_after = BOTH
    deduct_overtime_after_for = NEITHER
    overtime_after_offday = GENERATE_BOTH
    require_dedicated_work_time = False
    flat_reject_value = 0
    claim_expires = True
    expires_after = 1
    expires_after_unit = DAYS


class TimeSheetFactory(DjangoModelFactory):
    class Meta:
        model = TimeSheet

    timesheet_user = factory.SubFactory(UserFactory)
    work_shift = factory.SubFactory(WorkShiftFactory)
    work_time = factory.LazyAttribute(
        lambda s: WorkTiming.objects.filter(
            work_day__shift=s.work_shift
        ).first()
    )

    timesheet_for = get_today()


class TimeSheetEntryFactory(DjangoModelFactory):
    class Meta:
        model = TimeSheetEntry


class AttendanceAdjustmentFactory(DjangoModelFactory):
    class Meta:
        model = AttendanceAdjustment

    description = factory.Faker('text', max_nb_chars=225)


class CreditHourSettingFactory(DjangoModelFactory):
    class Meta:
        model = CreditHourSetting

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.Faker('name')
    minimum_credit_request = timedelta(hours=2)
    credit_hour_calculation = DAILY

    daily_credit_hour_limit_applicable = True
    daily_credit_hour_limit = 4 * 60
    weekly_credit_hour_limit_applicable = True
    weekly_credit_hour_limit = 20 * 60
    monthly_credit_hour_limit_applicable = True
    monthly_credit_hour_limit = 60 * 60
    off_day_credit_hour = True
    off_day_credit_hour_limit = 5 * 60
    holiday_credit_hour = False
    holiday_credit_hour_limit = None
    is_archived = False
    require_prior_approval = True
    grant_overtime_for_exceeded_minutes = False
    overtime_setting = None
    reduce_credit_if_actual_credit_lt_approved_credit = True
    allow_edit_of_pre_approved_credit_hour = False


class PreApprovalOvertimeFactory(DjangoModelFactory):
    class Meta:
        model = PreApprovalOvertime

    sender = factory.SubFactory(UserFactory)
    recipient = factory.SubFactory(UserFactory)
    request_remarks = 'request'
    action_remarks = 'action'
    overtime_duration = timedelta(hours=2)
    overtime_date = factory.LazyFunction(lambda: get_today() - timezone.timedelta(days=1))
