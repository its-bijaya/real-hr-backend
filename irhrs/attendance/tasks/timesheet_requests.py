import itertools
from logging import getLogger

from django.contrib.auth import get_user_model
from django.db.models import DateField, Exists, OuterRef, Case, When

from irhrs.attendance.models import TimeSheetRegistrationReportSettings, TimeSheetReportRequest, \
    TimeSheet
from irhrs.attendance.utils.timesheet_report import generate_timesheet_report_of_user, \
    save_timesheet_report
from irhrs.core.utils.common import get_today
from irhrs.organization.models import Organization, FiscalYearMonth

USER = get_user_model()

logger = getLogger(__name__)


def generate_timesheet_requests():
    settings = TimeSheetRegistrationReportSettings.objects.filter(
        approval_required=True
    )

    organization_settings_map = {
        setting.organization.id: setting
        for setting in settings
    }
    today = get_today()
    organization_fiscal_month_map = dict()
    for org in Organization.objects.filter(id__in=organization_settings_map.keys()):
        s = organization_settings_map.get(org.id, None)
        if s:
            last_month = FiscalYearMonth.objects.filter(
                fiscal_year__organization=org,
                fiscal_year__category=s.fiscal_year_category,
                end_at__lt=today
            ).order_by('-end_at').first()
            logger.info(f"last_month {last_month}")

            if last_month:
                organization_fiscal_month_map[org.id] = last_month

    organization_settings_map = {
        o: sett for o, sett in organization_settings_map.items()
        if o in organization_fiscal_month_map
    }

    users = USER.objects.filter(
        detail__organization_id__in=organization_settings_map.keys(),
        detail__joined_date__lte=get_today()
    ).current()

    month_start_case = Case(
        output_field=DateField(null=True),
        default=None,
        *[
            When(
                detail__organization_id=org_id,
                then=getattr(month, 'start_at', None)
            )
            for org_id, month in organization_fiscal_month_map.items()
        ]
    )
    month_end_case = Case(
        output_field=DateField(null=True),
        default=None,
        *[
            When(
                detail__organization_id=org_id,
                then=getattr(month, 'end_at', None)
            )
            for org_id, month in organization_fiscal_month_map.items()
        ]
    )

    past_users = USER.objects.filter(
        detail__organization_id__in=organization_settings_map.keys()
    ).past().annotate(
        fiscal_month_start=month_start_case,
        fiscal_month_end=month_end_case
    ).exclude(fiscal_month_start__isnull=True).annotate(
        timesheet_exists=Exists(
            TimeSheet.objects.filter(
                timesheet_user_id=OuterRef('id'),
                timesheet_for__gte=OuterRef('fiscal_month_start'),
                timesheet_for__lte=OuterRef('fiscal_month_end')
            )
        )
    ).exclude(timesheet_exists=False)

    for user in itertools.chain(users, past_users):
        organization = user.detail.organization
        org_setting = organization_settings_map.get(organization.id)
        fiscal_month = organization_fiscal_month_map.get(organization.id)

        if org_setting and fiscal_month and not TimeSheetReportRequest.objects.filter(
            fiscal_month=fiscal_month,
            user=user
        ).exists():
            logger.info(f"Timesheet Report generated for {user} for month {fiscal_month}")
            report = generate_timesheet_report_of_user(
                user=user, fiscal_month=fiscal_month, report_settings=org_setting)
            save_timesheet_report(
                report_data=report,
                user=user,
                fiscal_month=fiscal_month,
                report_settings=org_setting
            )
