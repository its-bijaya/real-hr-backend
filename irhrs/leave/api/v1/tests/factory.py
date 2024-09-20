import random

import factory
from factory.django import DjangoModelFactory
from django.utils import timezone

from irhrs.core.utils.common import get_today
from irhrs.leave.constants.model_constants import GENERAL, LEAVE_DURATION_CHOICES, FULL_DAY, \
    MONTHS, YEARLY, YEARS
from irhrs.leave.models import MasterSetting, LeaveType, LeaveRule, LeaveAccount, LeaveRequest
from irhrs.leave.models.account import LeaveEncashment, AdjacentTimeSheetOffdayHolidayPenalty

from irhrs.leave.models.rule import TimeOffRule, CompensatoryLeave, YearsOfServiceRule, \
    DeductionRule, RenewalRule, CompensatoryLeaveCollapsibleRule,\
    AccumulationRule, LeaveIrregularitiesRule, CreditHourRule
from irhrs.organization.api.v1.tests.factory import OrganizationFactory
from irhrs.users.api.v1.tests.factory import UserFactory


class MasterSettingFactory(DjangoModelFactory):
    class Meta:
        model = MasterSetting

    name = factory.Sequence(lambda n: f'Future MasterSetting-{n}')
    organization = factory.SubFactory(OrganizationFactory)

    effective_from = factory.LazyFunction(lambda: get_today() + timezone.timedelta(days=2))
    effective_till = None

    accumulation = False
    renewal = False
    deductible = False

    paid = False
    unpaid = False
    half_shift_leave = False

    occurrences = False
    beyond_balance = False
    proportionate_leave = False
    depletion_required = False

    require_experience = False
    require_time_period = False
    require_prior_approval = False
    require_document = False
    leave_limitations = False
    leave_irregularities = False

    employees_can_apply = False
    admin_can_assign = False

    continuous = False
    holiday_inclusive = False

    encashment = False
    carry_forward = False
    collapsible = False

    years_of_service = False
    time_off = False
    compensatory = False


class LeaveTypeFactory(DjangoModelFactory):
    class Meta:
        model = LeaveType

    master_setting = factory.SubFactory(MasterSettingFactory)
    name = factory.Faker('name')
    category = GENERAL


class LeaveRuleFactory(DjangoModelFactory):
    class Meta:
        model = LeaveRule

    leave_type = factory.SubFactory(LeaveTypeFactory)
    is_paid = False
    employee_can_apply = False
    admin_can_assign = False
    require_prior_approval = False

    @factory.post_generation
    def depletion_leave_types(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            # if extracted is not list, convert it to list
            extracted = [extracted] if not isinstance(extracted, list) else extracted
            for lt in extracted:
                self.depletion_leave_types.add(lt)


class TimeOffRuleFactory(DjangoModelFactory):
    total_late_minutes = 20
    leave_type = factory.SubFactory(LeaveTypeFactory, master_setting=factory.Iterator(MasterSetting.objects.all()))
    reduce_leave_by = 5

    class Meta:
        model = TimeOffRule


class CompensatoryLeaveRuleFactory(DjangoModelFactory):

    balance_to_grant = 5
    hours_in_off_day = 4

    class Meta:
        model = CompensatoryLeave

class CompensatoryLeaveCollapsibleRuleFactory(DjangoModelFactory):

    collapse_after = 5
    collapse_after_unit = "Days"

    class Meta:
        model = CompensatoryLeaveCollapsibleRule


class YearsOfServiceRuleFactory(DjangoModelFactory):
    years_of_service = 2
    balance_added = 12

    class Meta:
        model = YearsOfServiceRule


class CreditHourRuleFactory(DjangoModelFactory):
    minimum_request_duration_applicable = False
    maximum_request_duration_applicable = False

    class Meta:
        model = CreditHourRule


class DeductionRuleFactory(DjangoModelFactory):
    duration = 12
    duration_type = factory.LazyFunction(lambda: random.choice(LEAVE_DURATION_CHOICES)[0])
    balance_deducted = factory.LazyFunction(lambda: random.choice([1, 2, 3, 4]))

    class Meta:
        model = DeductionRule


class RenewalRuleFactory(DjangoModelFactory):

    duration = 12
    duration_type = YEARS
    initial_balance = factory.LazyFunction(lambda: random.choice([1, 2, 3, 4]))

    class Meta:
        model = RenewalRule


class AccumulationRuleFactory(DjangoModelFactory):

    duration = 12
    duration_type = factory.LazyFunction(lambda: random.choice(LEAVE_DURATION_CHOICES)[0])
    balance_added = factory.LazyFunction(lambda: random.choice([1, 2, 3, 4]))

    class Meta:
        model = AccumulationRule


class LeaveIrregularitiesRuleFactory(DjangoModelFactory):

    weekly_limit = factory.LazyFunction(lambda: random.choice([1, 2, 3, 4]))
    fortnightly_limit = factory.LazyAttribute(lambda o: o.weekly_limit + 1)
    monthly_limit = factory.LazyAttribute(lambda o: o.fortnightly_limit + 1)
    quarterly_limit = factory.LazyAttribute(lambda o: o.monthly_limit + 1)
    semi_annually_limit = factory.LazyAttribute(lambda o: o.quarterly_limit + 1)
    annually_limit = factory.LazyAttribute(lambda o: o.semi_annually_limit + 1)

    class Meta:
        model = LeaveIrregularitiesRule


class LeaveAccountFactory(DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    rule = factory.SubFactory(LeaveRuleFactory)
    balance = 10
    usable_balance = 10
    is_archived = False

    last_accrued = factory.LazyFunction(timezone.now)
    next_accrue = factory.LazyFunction(timezone.now)

    last_renewed = factory.LazyFunction(timezone.now)
    next_renew = factory.LazyFunction(timezone.now)

    last_deduction = factory.LazyFunction(timezone.now)
    next_deduction = factory.LazyFunction(timezone.now)

    class Meta:
        model = LeaveAccount

    @factory.lazy_attribute
    def rule(self):
        return LeaveRuleFactory(
            leave_type=LeaveTypeFactory(
                master_setting=MasterSettingFactory(
                    organization=self.user.detail.organization
                )
            )
        )


class LeaveRequestFactory(DjangoModelFactory):
    part_of_day = FULL_DAY
    start = factory.lazy_attribute(lambda s: timezone.now())
    end = factory.lazy_attribute(lambda s: timezone.now() + timezone.timedelta(days=1))
    leave_account = factory.SubFactory(LeaveAccountFactory)
    leave_rule = factory.SubFactory(LeaveRuleFactory)
    balance = 1

    class Meta:
        model = LeaveRequest


class LeaveEncashmentFactory(DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    account = factory.lazy_attribute(lambda s: LeaveAccountFactory(user=s.user))
    balance = 0
    status = "Generated"

    class Meta:
        model = LeaveEncashment


class AdjacentTimeSheetOffdayHolidayPenaltyFactory(DjangoModelFactory):
    class Meta:
        model = AdjacentTimeSheetOffdayHolidayPenalty

    penalty_for = factory.lazy_attribute(lambda s: timezone.now().date())
    penalty = 1.0
    leave_account = factory.SubFactory(LeaveAccountFactory)
