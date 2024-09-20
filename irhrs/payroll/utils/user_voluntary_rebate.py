from django.db.models import Q
from rest_framework.exceptions import ValidationError

from irhrs.core.constants.organization import GLOBAL
from irhrs.core.utils import get_system_admin
from irhrs.core.validators import validate_fiscal_year_months_amount
from irhrs.notification.utils import add_notification
from irhrs.organization.models import Organization, FiscalYear, FiscalYearMonth
from irhrs.payroll.constants import MONTHLY
from irhrs.payroll.models import UserVoluntaryRebate, PackageHeading, CREATED, Heading, Package, \
    UserVoluntaryRebateAction, DELETED
from irhrs.payroll.utils.helpers import get_last_payroll_generated_date
from irhrs.users.models import User


def get_total_rebate_amount_from_fiscal_months(fiscal_months_amount: dict) -> float:
    """Returns total rebate amount from fiscal months"""
    return sum(map(float, fiscal_months_amount.values()))

def get_default_fiscal_months_amount(organization: Organization, fiscal_year: str = None) -> dict:
    """Returns fiscal_months_amount 0 for all the months

    :param organization: Organization instance
    :param fiscal_year: FiscalYear id
    :returns : either fiscal_months default amount i.e, 0 or empty dictionary
    """
    current_fiscal_year = FiscalYear.objects.current(
        organization
    )
    if fiscal_year:
        current_fiscal_year = FiscalYear.objects.filter(
            id=fiscal_year
        ).first()
    if not current_fiscal_year:
        return {}

    fiscal_year_months = current_fiscal_year.fiscal_months.all().values_list('display_name')
    return {key[0]: 0 for key in fiscal_year_months}


def get_ordered_fiscal_months_amount(
    organization: Organization, fiscal_months_amount: dict, fiscal_year: FiscalYear = None
) -> dict:
    """Order fiscal_months_amount stored in JSON field(in unordered way)

    :param organization: Organization instance
    :param fiscal_months_amount: unordered fiscal_months_amount stored in JSONField
    :param fiscal_year: FiscalYear id
    :returns : either ordered fiscal_months_amount or empty dictionary
    """
    if not fiscal_months_amount:
        return {}
    ordered_fiscal_months = get_default_fiscal_months_amount(organization, fiscal_year=fiscal_year)
    return {key: fiscal_months_amount[key] for key, _ in ordered_fiscal_months.items()}


def get_fiscal_months_amount(data) -> dict:
    """Clean fiscal_months amount before saving to database

    Frontend sends payload in following format: fiscal_months_amount.Baishak
    we only store Baisakh with amount in JSONField

    :param data: Frontend payload in above format
    :returns : Cleaned fiscal_months_amount
    """
    fiscal_months_amount = {}
    for full_month, amount in data.items():
        if full_month.startswith("fiscal_months_amount"):
            month = full_month.split(".")[1]
            fiscal_months_amount[month] = round(float(amount), 2)
    return fiscal_months_amount


def validated_fiscal_months_amount(
    organization: Organization, amount, data, fiscal_year_id
) -> dict:
    """Validate fiscal_months_amount

    :param organization: Organization instance
    :param amount: total rebate amount from RebateSetting
    :param data: frontend payload
    :param fiscal_year_id: FiscalYear id
    :returns : Either raise Validation error or return fiscal_months_amount
    """
    fiscal_year = FiscalYear.objects.filter(
            id=fiscal_year_id
        ).first()
    if not fiscal_year:
        raise ValidationError("No current fiscal year found.")
    fiscal_months = fiscal_year.fiscal_months.all().values_list('display_name')

    fiscal_months_amount = get_fiscal_months_amount(data)
    if not fiscal_months_amount:
        fiscal_months_amount = get_default_fiscal_months_amount(organization)
    validate_fiscal_year_months_amount(fiscal_months, fiscal_months_amount)
    if amount and amount != 0 and amount < get_total_rebate_amount_from_fiscal_months(fiscal_months_amount):
        raise ValidationError("Rebate amount limit exceeded.")
    return fiscal_months_amount


def get_all_payroll_generated_months(user: User, organization: Organization, fiscal_year_id) -> list:
    """Get list of payroll generated months for given fiscal_year

    :param user: User instance
    :param organization: Organization instance
    :param fiscal_year_id: FiscalYear id
    :returns : list of payroll generated months
    """
    payroll_generated_upto = get_last_payroll_generated_date(user)

    fiscal_months = []
    if payroll_generated_upto:
        current_fy = FiscalYear.objects.current(organization)
        if fiscal_year_id:
            current_fy = FiscalYear.objects.get(id=fiscal_year_id)
        payroll_generated_fy = FiscalYear.objects.active_for_date(
            organization, payroll_generated_upto)

        if current_fy and payroll_generated_fy and current_fy == payroll_generated_fy:
            current_fiscal_month = payroll_generated_fy.fiscal_months.filter(
                start_at__lte=payroll_generated_upto, end_at__gte=payroll_generated_upto
            ).first()
            if not current_fiscal_month:
                return []
            fiscal_month_index = current_fiscal_month.month_index

            if fiscal_month_index:
                fiscal_months = payroll_generated_fy.fiscal_months.filter(
                    month_index__lte=fiscal_month_index
                ).values_list('display_name')
                # we get fiscal_months in tuple, so we only take fiscal_month i.e, first element
                fiscal_months = [fiscal_month[0] for fiscal_month in fiscal_months]

    return fiscal_months


def get_amount_from_rebate(
    employee: User, heading: Heading, package: Package, fiscal_year_id
):
    """Get amount from rebate

    :param employee: User instance
    :param heading: Heading instance
    :param package: Package instance
    :param fiscal_year_id: FiscalYear id
    :returns : fiscal_months_amount and whether the rebate is archived or not
    """
    rules = heading.packageheading_set.get(package=package).rules

    fiscal_year = FiscalYear.objects.get(id=fiscal_year_id)
    rebate = get_user_voluntary_rebate_from_heading(
        employee, heading, employee.detail.organization, fiscal_year=fiscal_year)

    if not rebate:
        return {}, False

    title = rebate.rebate.title
    if rules.rfind(title) != -1 and rebate.rebate.duration_type == MONTHLY:
        return rebate.fiscal_months_amount, rebate.statuses.first().action == "Archived"

    return {}, False


def get_archived_rebate_amount(
    employee: User, organization: Organization, fiscal_year_id, rebate_amount: dict
) -> dict:
    """Get rebate amount

    :param employee: User instance
    :param organization: Organization instance
    :param fiscal_year_id: FiscalYear instance
    :param rebate_amount: UserVoluntaryRebate fiscal_months_amount

    :returns : dictionary of remaining amount of rebate
    """
    payroll_generated_months = get_all_payroll_generated_months(
        employee, organization, fiscal_year_id)
    return {
        key: value for key, value in rebate_amount.items() if key in payroll_generated_months
    }


def get_annual_amount_from_rebate(
    employee: User, heading: Heading, package: Package, organization: Organization, fiscal_year_id
) -> float:
    """Get total rebate amount for given fiscal year

    :param employee: User instance
    :param heading: Heading instance
    :param package: Package instance
    :param organization: Organization instance
    :param fiscal_year_id: FiscalYear id
    :returns : total rebate amount in float
    """
    rebate_amount, is_archived = get_amount_from_rebate(employee, heading, package, fiscal_year_id)
    if is_archived:
        rebate_amount = get_archived_rebate_amount(
            employee, organization, fiscal_year_id, rebate_amount)
    return get_total_rebate_amount_from_fiscal_months(rebate_amount)


def get_remaining_amount_to_be_calculated_in_payroll(
    row, from_date, to_date, include_current_month=True, calculate_projected_months=False
):
    """Get remaining amount to be calculated in given date

    :param row: ReportRowRecord instance
    :param from_date: payroll generated from date
    :param to_date: payroll generated to date
    :param include_current_month: set this True if we want to include current month while
    calculating the remaining rebate amount
    :param calculate_projected_months: this boolean is set to true only when we calculate projected
    amount from __ags__
    :returns : total remaining amount in float
    """
    remaining_fiscal_months = get_remaining_fiscal_months_in_payroll(
        row, from_date, to_date, include_current_month=include_current_month,
        calculate_projected_months=calculate_projected_months
    )
    return get_total_rebate_amount_from_fiscal_months(remaining_fiscal_months)


def get_remaining_fiscal_months_in_payroll(
    row, from_date, to_date, include_current_month=True, calculate_projected_months=False) -> dict:
    """Get remaining fiscal months with given dates with fiscal_months_amount

    Note: If rebate is archived, set all the remaining fiscal_months_amount to zero.
    :param row: RowReportRecord instance
    :param from_date: payroll generated from date
    :param to_date: payroll generated to date
    :param include_current_month: set this True if we want to include current month while
    calculating the remaining rebate amount
    :param calculate_projected_months: this boolean is set to true only when we calculate projected
    amount from __ags__
    :returns : remaining fiscal year months amounts
    """
    user = row.employee
    heading = row.heading
    package = row.package_heading.package
    organization = user.detail.organization
    payroll_generated_fy = FiscalYear.objects.active_for_date(
        organization, row.to_date)
    fiscal_year_month = FiscalYearMonth.objects.filter(
        end_at__gte=to_date,
        fiscal_year__organization=organization,
        fiscal_year__category=GLOBAL
    ).order_by('end_at').first()

    if not fiscal_year_month:
        return {}
    fiscal_year_month = fiscal_year_month.display_name

    payroll_generated_months = get_all_payroll_generated_months(
        user, organization, payroll_generated_fy.id)

    fiscal_months_amount, is_archived = get_amount_from_rebate(
        user, heading, package, payroll_generated_fy.id)
    if calculate_projected_months and fiscal_months_amount and UserVoluntaryRebate.objects.filter(
        user=user,
        fiscal_year=payroll_generated_fy,
        fiscal_months_amount__isnull=False
    ).exists():
        try:
            fiscal_months_amount.pop(fiscal_year_month)
        except KeyError:
            pass
    if not include_current_month and payroll_generated_months:
        try:
            payroll_generated_months.remove(fiscal_year_month)
        except ValueError:
            pass

    if is_archived:
        return {key: 0 for key, value in fiscal_months_amount.items() if
                key not in payroll_generated_months}

    return {key: value for key, value in fiscal_months_amount.items() if key not in payroll_generated_months}


def update_monthly_rebate_rows(
    rows, from_date, to_date, include_current_month=True, calculate_projected_months=False
):
    """Update monthly rebate rows

        Note: If rebate is archived, set all the remaining fiscal_months_amount to zero.
        :param rows: RowReportRecord instance list
        :param from_date: payroll generated from date
        :param to_date: payroll generated to date
        :param include_current_month: set this True if we want to include current month while
        calculating the remaining rebate amount
        :param calculate_projected_months: this boolean is set to true only when we calculate projected
        amount from __ags__
        :returns : remaining fiscal year months amounts
        """
    monthly_rebate_rows = list(filter(lambda x: x.heading.duration_unit == "Monthly", rows))
    for row in monthly_rebate_rows:
        if row.heading.rules.rfind("__USER_VOLUNTARY_REBATE__") != -1:
            amount = get_remaining_amount_to_be_calculated_in_payroll(
                row, from_date, to_date, include_current_month=include_current_month,
                calculate_projected_months=calculate_projected_months
            )
            row.amount = amount
    return rows


def get_user_voluntary_rebate_from_heading(
    employee: User, heading: Heading, organization: Organization, fiscal_year=None, to_date=None
) -> UserVoluntaryRebate:
    """Get user voluntary rebate if present in the heading

    :param employee: User instance
    :param heading: Heading instance
    :param organization: Organization instance
    :param fiscal_year: FiscalYear instance
    :param to_date: payroll generation to_date

    :returns : UserVoluntaryRebate rebate if exists
    """
    if not isinstance(employee, User):
        return

    if not (fiscal_year or to_date):
        return
    rules = heading.rules
    if not isinstance(rules, str):
        rules = str(rules)

    try:
        if not (heading and rules.rfind('__USER_VOLUNTARY_REBATE__') != -1):
            return
    except AttributeError:
        return

    split_data = rules.split('__USER_VOLUNTARY_REBATE__')[1]
    import re
    matched_pattern = re.sub(r'[^A-Za-z ]+', '$', split_data)

    rebate_title = matched_pattern.split("$")[1]

    if not fiscal_year:
        fiscal_year = FiscalYear.objects.active_for_date(organization, to_date)

    return UserVoluntaryRebate.objects.filter(
        user=employee, rebate__title=rebate_title,
        fiscal_year=fiscal_year, statuses__action=CREATED
    ).first()


def update_rebate_settings_from_payroll_edit(
    employee: User, data: dict, from_date, to_date, organization: Organization, package: Package
) -> None:
    """update rebate settings from payroll update(i.e, from excel update and from collection)

    :param employee: User instance
    :param data: changed heading data with initialValue and currentValue
    :param from_date: payroll generated from_date
    :param to_date: payroll generated to date
    :param organization: Organization instance
    :param package: Package instance

    :returns : None
    """
    if not data:
        return

    payroll_generated_fy = FiscalYear.objects.active_for_date(organization, to_date)

    if not payroll_generated_fy:
        return

    fiscal_year_month = payroll_generated_fy.fiscal_months.filter(
        start_at__gte=from_date,
        end_at__lte=to_date,
        fiscal_year__organization=organization,
        fiscal_year__category=GLOBAL
    ).order_by('end_at').first()

    if not fiscal_year_month:
        return

    for heading_id in data.keys():
        try:
            heading = PackageHeading.objects.filter(
                heading_id=heading_id,
                package=package
            ).first()

            if not heading:
                return

            user_rebate = get_user_voluntary_rebate_from_heading(
                employee, heading, organization, fiscal_year=payroll_generated_fy)

            if not user_rebate:
                continue

            fiscal_months_amount = user_rebate.fiscal_months_amount
            if not fiscal_months_amount:
                continue

            display_name = fiscal_year_month.display_name
            fiscal_months_amount[display_name] = data.get(heading_id, {}).get('currentValue', 0)
            user_rebate.amount = get_total_rebate_amount_from_fiscal_months(fiscal_months_amount)
            user_rebate.save()

            add_notification(
                text=f"Your {user_rebate.title} for {display_name}'s rebate have been changed.",
                recipient=employee,
                action=user_rebate,
                actor=get_system_admin(),
                url='/user/payroll/rebate/'
            )

        except ValueError:
            pass


def revert_fiscal_months_amount_to_zero_when_rebate_is_archived(instance):
    organization = instance.user.detail.organization
    fy_id = instance.fiscal_year_id
    payroll_generated_months = get_all_payroll_generated_months(
        instance.user, organization, fy_id)
    fiscal_months_amount = instance.fiscal_months_amount

    if not fiscal_months_amount:
        fiscal_months_amount = get_default_fiscal_months_amount(organization, fy_id)

    for key, value in fiscal_months_amount.items():
        if key not in payroll_generated_months:
            fiscal_months_amount[key] = 0

    instance.fiscal_months_amount = fiscal_months_amount
    instance.amount = sum(fiscal_months_amount.values())

    instance.save()


def archive_old_rebate_entry(instance):
    entries_to_be_archived = UserVoluntaryRebate.objects.filter(
        user=instance.user,
        fiscal_year=instance.fiscal_year,
        rebate=instance.rebate
    ).exclude(id=instance.id)

    if entries_to_be_archived:
        UserVoluntaryRebateAction.objects.bulk_create(
            [
                UserVoluntaryRebateAction(
                    user_voluntary_rebate=entry,
                    action=DELETED,
                    remarks=(
                        'Archived because same type '
                        'entry of same duration unit '
                        'in same fiscal year was added'
                    )
                ) for entry in entries_to_be_archived
            ]
        )
