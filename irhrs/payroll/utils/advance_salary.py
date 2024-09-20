import typing

from datetime import date
from numbers import Number

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property
from rest_framework import serializers

from irhrs.core.utils.common import get_today
from irhrs.leave.constants.model_constants import DENIED
from irhrs.organization.models import Organization, FiscalYear
from irhrs.payroll.models import AdvanceSalarySetting, OverviewConfig
from irhrs.payroll.models.advance_salary_request import PENDING, AdvanceSalaryRequest, COMPLETED, \
    AdvanceSalarySurplusRequest
from irhrs.core.constants.payroll import EMPLOYEE, SUPERVISOR, FIRST, SECOND, THIRD, APPROVED, \
    CANCELED
from irhrs.payroll.utils.exceptions import AdvanceSalaryNotConfigured, ExperienceNotFound, \
    PackageNotAssigned

Employee = get_user_model()


class AdvanceSalaryRequestValidator:
    """
    Wrapper for Advance Salary Request

    Contains utils required to validate request
    and create AdvanceSalaryRequest instance

    :ivar employee: Employee who is requesting advance salary
    :ivar amount: Amount of advance salary request
    :ivar disbursement_count_for_repayment: Number of disbursements for repayment
    :ivar requested_for: Date advance payroll is requested for
    :ivar above_limit: request is above limit of organization or not
    :ivar repayment_plan: JSON containing repayment plan
    :ivar organization: Organization of employee (If not passed will be taken from employee.detail)
    :ivar surplus_request: Surplus Request to take limit amount from
    """

    def __init__(self, employee: Employee,
                 amount: float = None,
                 disbursement_count_for_repayment: int = None,
                 requested_for: date = None,
                 above_limit: bool = False,
                 repayment_plan: typing.List[Number] = None,
                 organization: Organization = None,
                 surplus_request: AdvanceSalarySurplusRequest = None) -> None:

        self.employee = employee
        self.amount = amount
        self.disbursement_count_for_repayment = disbursement_count_for_repayment
        self.requested_for = requested_for
        self.above_limit = above_limit
        self.repayment_plan = repayment_plan
        self.surplus_request = surplus_request

        if organization:
            self.organization = organization
        else:
            self.organization = employee.detail.organization

    @cached_property
    def settings(self):
        """Advance Salary Settings for organization"""
        settings = AdvanceSalarySetting.objects.filter(organization=self.organization).first()
        if not settings:
            raise AdvanceSalaryNotConfigured
        return settings

    @cached_property
    def fiscal_year_start_end(self):
        request_date = self.requested_for or get_today()
        fy = FiscalYear.objects.active_for_date(organization=self.organization, date_=request_date)
        if fy:
            return fy.start_at, fy.end_at
        else:
            return date(year=request_date.year, month=1, day=1), \
                   date(year=request_date.year, month=12, day=31)

    @cached_property
    def package_slot(self):
        request_date = self.requested_for or get_today()
        experience = self.employee.first_date_range_user_experiences(request_date, request_date)
        if not experience:
            raise ExperienceNotFound

        package_slot = experience.user_experience_packages.order_by(
            'active_from_date'
        ).filter(
            active_from_date__lte=request_date,
        ).last()

        if not package_slot:
            raise PackageNotAssigned

        return package_slot

    @cached_property
    def limit_amount(self):
        """Max amount employee can request"""
        if (
            self.surplus_request and
            self.above_limit and
            self.employee == self.surplus_request.employee and
            self.surplus_request.status == APPROVED and

            # approved surplus request is not used yet
            self.surplus_request.advance_salary_request is None
        ):
            return self.surplus_request.amount

        fixed_limit = self.settings.limit_upto
        heading_amounts = []
        package_slot = self.package_slot
        amount_settings_qs = self.settings.amount_setting.all()
        for amount_setting in amount_settings_qs:
            report_row = package_slot.package_rows.filter(
                package_heading__heading=amount_setting.payroll_heading
            ).last()

            heading_amounts.append(
                (getattr(report_row, 'package_amount', None) or 0.0) * amount_setting.multiple
            )

        # (max of heading ) or (fixed amount) whichever is lower
        if fixed_limit is not None and heading_amounts:
            return min(max(heading_amounts), fixed_limit)
        elif heading_amounts and fixed_limit is None:
            return max(heading_amounts)
        elif not heading_amounts and fixed_limit is not None:
            return fixed_limit
        else:
            raise AdvanceSalaryNotConfigured

    @cached_property
    def approvals(self):
        approvals = []
        approval_settings = self.settings.approval_setting.all().order_by('approval_level')
        for index, approval_setting in enumerate(approval_settings, start=1):
            if approval_setting.approve_by == EMPLOYEE:
                approvals.append({
                    "user": approval_setting.employee,
                    "status": PENDING,
                    "role": EMPLOYEE,
                    "level": index
                })
            elif approval_setting.approve_by == SUPERVISOR:
                supervisor_level = [0, FIRST, SECOND, THIRD].index(
                    approval_setting.supervisor_level)
                supervisor_authority = self.employee.supervisors.filter(
                    authority_order=supervisor_level).first()

                if not supervisor_authority:
                    continue  # skip to next authority order
                    # raise serializers.ValidationError({
                    #     "non_field_errors": _(f"{supervisor_level} Level supervisor not found.")
                    # })
                approvals.append({
                    "user": supervisor_authority.supervisor,
                    "status": PENDING,
                    "role": SUPERVISOR,
                    "level": index
                })

        if len(approvals) == 0:
            raise AdvanceSalaryNotConfigured(detail=_("Approval Levels not set."))
        return approvals

    @cached_property
    def recipient(self):
        return self.approvals[0]["user"]

    @cached_property
    def salary_payable(self):
        config = OverviewConfig.objects.filter(organization=self.organization).first()
        if not config:
            return 0.0

        report_row = self.package_slot.package_rows.filter(
            package_heading__heading=config.salary_payable
        ).last()
        return getattr(report_row, 'package_amount', 0.0)

    def validate_amount(self):
        if self.amount <= 0:
            raise serializers.ValidationError({
                "amount": _("Please make sure amount is more than zero.")
            })

        if self.above_limit and not self.surplus_request:
            raise serializers.ValidationError({
                "non_field_errors": _("Surplus Request reference not found for above"
                                      " limit requests.")
            })

        if self.amount > self.limit_amount:
            raise serializers.ValidationError(
                {"amount": _(f"This value is above limit. The limit is {self.limit_amount}")}
            )

    def has_pending_requests(self):
        if (self.settings.complete_previous_request and
            AdvanceSalaryRequest.objects.filter(
                employee=self.employee).exclude(
                status__in=[COMPLETED, DENIED, CANCELED]).exists()):
            raise serializers.ValidationError(
                {"non_field_errors": _("You have previous incomplete request.")}
            )

    def validate_employment_type(self):
        excluded_types = self.settings.excluded_employment_type.values_list('id', flat=True)
        if self.employee.detail.employment_status and \
           self.employee.detail.employment_status.id in excluded_types:
            raise serializers.ValidationError({
                "non_field_errors": _("Based on employment type you"
                                      " are not allowed to request advance salary.")})

    def validate_time_of_service_completion(self):
        days_to_complete = self.settings.time_of_service_completion
        if days_to_complete:
            days_of_service = (get_today() - self.employee.detail.joined_date).days
            if days_of_service < days_to_complete:
                raise serializers.ValidationError({
                    "non_field_errors": _("You are not yet eligible to request advance salary."
                                          " You can request once you've completed "
                                          f"{days_to_complete} days of work.")
                })

    def validate_request_limit(self):
        if self.settings.request_limit:
            no_of_requests = self.employee.advance_salary_requests.filter(
                requested_for__range=self.fiscal_year_start_end
            ).exclude(status__in=[DENIED, CANCELED]).count()

            if no_of_requests >= self.settings.request_limit:
                raise serializers.ValidationError({
                    "non_field_errors": _("You have reached limit for advance salary requests "
                                          "for this fiscal year.")
                })

    def validate_request_interval(self):
        if self.settings.request_interval and self.employee.advance_salary_requests.filter(
            requested_for__gte=get_today() - timezone.timedelta(
                days=self.settings.request_interval
            )
        ).exclude(status__in=[DENIED, CANCELED]).exists():
            raise serializers.ValidationError({
              "non_field_errors": _(f"You have a request in last {self.settings.request_interval}"
                                    f" days.")
            })

    def validate_has_approvers(self):
        # this will calculate approvals and raise validation error if does not exists
        _ = self.approvals

    def validate_disbursement_count(self):
        limit_value = self.settings.disbursement_limit_for_repayment
        if limit_value and self.disbursement_count_for_repayment > limit_value:
            raise serializers.ValidationError({
                'disbursement_count_for_repayment':
                    _(f"This value can not be greater then {limit_value}.")
            })

    def validate_plan(self):
        if not isinstance(self.repayment_plan, list):
            raise serializers.ValidationError({
                'repayment_plan': _('This value must be a list of amounts to be payed '
                                    'in each disbursement.')})

        if not all(map(lambda x: type(x) in (int, float), self.repayment_plan)):
            raise serializers.ValidationError({
                'repayment_plan': _('Expected this value to be list of integers or float.')
            })

        if any(map(lambda x: x > self.salary_payable, self.repayment_plan)):
            raise serializers.ValidationError({
                'repayment_plan': _(f'Please make sure none of the values are more than '
                                   f'{self.salary_payable}.')
            })

        if sum(self.repayment_plan) != self.amount:
            raise serializers.ValidationError({
                'repayment_plan': _(f'Please make sure all values sums up to advance amount.')
            })

        if len(self.repayment_plan) != self.disbursement_count_for_repayment:
            raise serializers.ValidationError({
                'repayment_plan': _(f'Number of repayments must be equal to disbursement count.')
            })

    def is_valid(self):
        self.validate_employment_type()
        self.validate_time_of_service_completion()
        self.validate_amount()
        self.validate_request_limit()
        self.validate_request_interval()
        self.has_pending_requests()
        self.validate_has_approvers()
        self.validate_disbursement_count()
        self.validate_plan()
        return True
