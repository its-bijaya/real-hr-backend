import logging

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from irhrs.core.constants.common import INFO
from irhrs.core.utils.email import send_notification_email
from irhrs.core.constants.organization import CONTRACT_EXPIRY_ALERT_EMAIL
from irhrs.core.utils import get_system_admin
from irhrs.core.utils.common import get_today
from irhrs.core.utils import email
from irhrs.core.utils.common_utils import get_users_list_from_permissions, nested_getattr
from irhrs.notification.utils import add_notification, notify_organization
from irhrs.permission.constants.groups import ADMIN, HR_ADMIN
from irhrs.permission.models.hrs_permisssion import OrganizationGroup, HRSPermission
from irhrs.permission.constants.permissions import (
    HRIS_PERMISSION,
    HRIS_REPORTS_PERMISSION,
    HRIS_CONTRACT_SETTINGS_PERMISSION,
    HRIS_EMPLOYMENT_REVIEW_PERMISSION,
    HRIS_EMPLOYMENT_REVIEW_PROCESS_PERMISSION,
    HRIS_SEPARATION_TYPE_PERMISSION,
    EXIT_INTERVIEW_PERMISSION
)

User = get_user_model()


def deactivate_no_current_experience_users():
    """
    Task for deactivating the users whose employment experience has ended.
    Makes user `is_active=False`.
    """

    today = get_today()

    updated_count = User.objects.filter(
        user_experiences__is_current=False,
        # user with inactive experience
        user_experiences__end_date__lt=today,
        # user with no running experience
    ).exclude(
        groups__name=ADMIN  # except admin users
    ).update(
        is_active=False
    )
    if updated_count > 0:
        action_message = f"Deactivated {updated_count} users on {today}"
        logging.info(
            action_message
        )
        recipient_list = User.objects.filter(
            groups__name=HR_ADMIN
        )
        add_notification(
            action=None,
            label=INFO,
            actor=get_system_admin(),
            sticky=False,
            can_be_reminded=False,
            recipient=recipient_list,
            text=action_message
        )
    logging.debug(
        f"User Deactivation Task run successfully on {timezone.now()}"
    )


def notify_contract_expiring():
    """
    Notifies an organization regarding the expiry date of contract settings.
    Two notifications are sent:
        * <Someone>'s contract is expiring in <x> days.
        * <Someone>'s contract is expiring in 1 days.
    :return:
    {
        "affected_users": <count>,
        "users": [ FullName1, FullName2]
    }
    """
    from irhrs.organization.models import Organization
    from irhrs.users.models import UserExperience
    contract_experiences = UserExperience.objects.filter(
        is_current=True,
        employment_status__is_contract=True
    )

    user_list = []

    email_receiving_permissions = [
        HRIS_PERMISSION,
        HRIS_CONTRACT_SETTINGS_PERMISSION,
        HRIS_EMPLOYMENT_REVIEW_PERMISSION,
        HRIS_EMPLOYMENT_REVIEW_PROCESS_PERMISSION,
        EXIT_INTERVIEW_PERMISSION
    ]
    # for each organization,
    # for each defined days or 1 day,
    # for each user, --> Notify.
    for organization in Organization.objects.all():

        # expires in defined days
        critical_days = organization.contract_settings.critical_days
        when = {
            critical_days: f'in {critical_days} days',
            0: 'today',
            1: 'tomorrow',
            # 0 and 1 is placed at bottom to ensure proper message when
            # critical days is 1 or 0.
        }

        # Setup for sending email to users
        email_intro_message = f"The following contracts are in a critical state:<br>"
        recipients = set()
        mail_to_users = get_users_list_from_permissions(
            email_receiving_permissions,
            organization
        )
        expiring_users_list_for_email = []
        user_count = 1

        for day in (0, 1, critical_days):
            contract_expiring_date = get_today() + relativedelta(days=day)

            fil = dict(
                end_date=contract_expiring_date,
                organization=organization
            )

            if day == critical_days:
                fil = dict(
                end_date__lte=contract_expiring_date,
                end_date__gte=get_today()+ relativedelta(days=2),
                organization=organization
            )

            expiring_contracts_in_org = contract_experiences.filter(**fil)

            for user_experience in expiring_contracts_in_org:
                if nested_getattr(user_experience, 'user.detail.last_working_date'):
                    continue
                user_separataion = user_experience.user.employeeseparation_set.first()
                if user_separataion and user_separataion.release_date:
                    continue
                user_list.append(user_experience.user)
                slug = organization.slug

                notification_text = (
                    f"{user_experience.user.full_name}'s contract expires "
                    f"{when.get(day)}."
                )

                # format for email body: `1. John Doe(Expires tomorrow)`
                email_person_days = (
                    f"{user_count}. {user_experience.user.full_name}"
                    f"(Expires {when.get(day)})."
                )
                day_difference = user_experience.end_date - get_today()
                expiring_in_days = day_difference.days
                if day == critical_days and expiring_in_days>= 2:
                    notification_text = (
                        f"{user_experience.user.full_name}'s contract expires "
                        f"in {expiring_in_days} days."
                    )
                    email_person_days = (
                        f"{user_count}. {user_experience.user.full_name}"
                        f"(Expires in {expiring_in_days} days)."
                    )

                # format for email body: `1. John Doe(Expires tomorrow)`
                expiring_users_list_for_email.append(email_person_days)
                user_count += 1

                notify_organization(
                    text=notification_text,
                    action=user_experience,
                    organization=organization,
                    permissions=[
                        HRIS_PERMISSION,
                        HRIS_REPORTS_PERMISSION,
                    ],
                    url=f'/admin/{slug}/hris/reports/basic/contract-status',
                )

                add_notification(
                    text=notification_text,
                    action=user_experience,
                    recipient=[user_experience.user.first_level_supervisor],
                    url='/user/supervisor/my-team/reports/contract-status'
                )

                for user in mail_to_users:
                    can_send_email =  email.can_send_email(user, CONTRACT_EXPIRY_ALERT_EMAIL, organization)
                    if can_send_email and expiring_contracts_in_org:
                        recipients.add(user)

        email_message_content = email_intro_message + "<br>".join(expiring_users_list_for_email)

        final_recipients = []
        for user in recipients:
            if not email.has_sent_email(user, email_message_content):
                final_recipients.append(user.email)

        if recipients:
            send_notification_email(
                recipients=list(final_recipients),
                notification_text=email_message_content,
                subject=f"Contract Expiry for some users is in critical state."
            )

    return {
        "notified_contracts": len(user_list),
        "notified_users": list(
            map(lambda x: x.full_name, user_list)
        )
    }
