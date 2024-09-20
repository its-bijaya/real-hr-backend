from datetime import timedelta

import factory
from factory.django import DjangoModelFactory

from irhrs.attendance.constants import DAILY, REQUESTED, P_MONTH, DURATION, GENERATED
from irhrs.attendance.models import CreditHourSetting, CreditHourRequest, PenaltyRule, \
    TimeSheetUserPenalty
from irhrs.attendance.models.breakout_penalty import TimeSheetPenaltyToPayroll, \
    BreakOutPenaltySetting
from irhrs.core.utils.common import get_today, get_tomorrow
from irhrs.attendance.constants import DAILY, REQUESTED
from irhrs.attendance.models import CreditHourSetting, CreditHourRequest
from irhrs.core.utils.common import get_today
from irhrs.organization.api.v1.tests.factory import OrganizationFactory
from django.template.defaultfilters import slugify

from irhrs.users.api.v1.tests.factory import UserFactory


class CreditSettingFactory(DjangoModelFactory):
    class Meta:
        model = CreditHourSetting

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.Faker('first_name')
    slug = slugify(factory.Faker('last_name'))
    minimum_credit_request = timedelta(hours=1)
    credit_hour_calculation = DAILY
    require_prior_approval = True
    reduce_credit_if_actual_credit_lt_approved_credit = True
    allow_edit_of_pre_approved_credit_hour = True


class CreditRequestFactory(DjangoModelFactory):
    class Meta:
        model = CreditHourRequest

    status = REQUESTED
    credit_hour_duration = timedelta(hours=1)
    credit_hour_date = get_today()
    sender = factory.SubFactory(UserFactory)
    recipient = factory.SubFactory(UserFactory)
    request_remarks = 'Test'
    action_remarks = 'Test'


class BreakOutPenaltySettingFactory(DjangoModelFactory):
    organization = factory.SubFactory(OrganizationFactory)

    class Meta:
        model = BreakOutPenaltySetting


class PenaltyRuleFactory(DjangoModelFactory):
    penalty_setting = factory.SubFactory(BreakOutPenaltySettingFactory)

    penalty_duration_in_days = 1
    penalty_counter_value = 1
    penalty_counter_unit = P_MONTH
    calculation_type = DURATION
    tolerated_duration_in_minutes = 60
    tolerated_occurrences = 1
    consider_late_in = True
    consider_early_out = False
    consider_in_between_breaks = False
    penalty_accumulates = True

    class Meta:
        model = PenaltyRule


class TimeSheetUserPenaltyFactory(DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    rule = factory.SubFactory(PenaltyRuleFactory)
    start_date = factory.LazyFunction(get_today)
    end_date = factory.LazyFunction(get_tomorrow)
    # fiscal_month = factory.SubFactory(FiscalYearMonthFactory)
    loss_accumulated = timedelta(0)
    lost_days_count = 0
    penalty_accumulated = 0
    status = GENERATED
    remarks = 'remarks'

    class Meta:
        model = TimeSheetUserPenalty


class TimeSheetPenaltyToPayrollFactory(DjangoModelFactory):
    user_penalty = factory.SubFactory(TimeSheetUserPenaltyFactory)
    days = 1

    class Meta:
        model = TimeSheetPenaltyToPayroll
