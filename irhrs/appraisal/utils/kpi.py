from irhrs.appraisal.constants import ARCHIVED, CONFIRMED
from irhrs.appraisal.models.kpi import IndividualKPI, IndividualKPIHistory
from irhrs.notification.utils import add_notification, notify_organization
from irhrs.organization.models import Organization
from irhrs.permission.constants.permissions import KPI_PERMISSION, INDIVIDUAL_KPI_PERMISSION
from irhrs.users.models import User


def send_notification_and_create_history(individual_kpi: IndividualKPI, url, remarks, user=None):
    if not user:
        user = individual_kpi.created_by
    create_individual_kpi_history(individual_kpi, remarks)
    add_notification(
        text=remarks,
        recipient=individual_kpi.user,
        action=individual_kpi,
        actor=user,
        url=url
    )


def create_individual_kpi_history(individual_kpi: IndividualKPI, remarks: str):
    IndividualKPIHistory.objects.create(
        individual_kpi=individual_kpi,
        status=individual_kpi.status,
        remarks=remarks
    )


def archive_previous_individual_kpi(user: User, fiscal_year: int, authenticated_user: User,
                                    status: str, individual_kpi_id=None):
    exclude_fields = {}
    if status != CONFIRMED:
        exclude_fields['status'] = CONFIRMED
    if individual_kpi_id:
        exclude_fields['id'] = individual_kpi_id
    previous_individual_kpis_qs = user.individual_kpis.filter(
        fiscal_year=fiscal_year,
        is_archived=False
    ).exclude(**exclude_fields)

    if not previous_individual_kpis_qs:
        return
    for individual_kpi in previous_individual_kpis_qs:
        remarks = f"{authenticated_user} updated the status from {individual_kpi.status}" \
                  f" to {ARCHIVED}."
        send_notification_and_create_history(
            individual_kpi, '/user/pa/kpi',
            remarks,
            authenticated_user
        )
    previous_individual_kpis_qs.update(status=ARCHIVED, is_archived=True)


def send_notification_to_hr_and_supervisor(instance: IndividualKPI, organization: Organization,
                                           authenticated_user: User, status: str) -> None:
    user = instance.user
    recipients = [
        supervisor.supervisor for supervisor in user.user_supervisors
    ]
    text = f"{authenticated_user} has {status} {instance.title} kpi."
    if authenticated_user != user:
        recipients.append(user)
    add_notification(
        text=text,
        recipient=recipients,
        action=instance,
        actor=authenticated_user,
        url='/user/supervisor/kpi/assign-kpi'
    )
    notify_organization(
        text=text,
        organization=organization,
        action=instance,
        actor=authenticated_user,
        permissions=[KPI_PERMISSION, INDIVIDUAL_KPI_PERMISSION],
        url=f"/admin/{organization.slug}/pa/settings/assign-kpi"
    )
