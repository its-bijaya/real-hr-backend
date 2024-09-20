from datetime import timedelta

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils import timezone

from irhrs.core.utils import get_system_admin
from irhrs.notification.models import Notification
from irhrs.notification.models.notification import OrganizationNotification
from irhrs.notification.utils import add_notification, notify_organization
from irhrs.permission.constants.permissions import HRIS_CONTRACT_SETTINGS_PERMISSION, \
    HRIS_CHANGE_REQUEST_PERMISSION, HRIS_PERMISSION
from irhrs.users.models import UserInsurance, UserExperience


def notify_expiring_insurance():
    insurance_going_to_expire = UserInsurance.objects.filter(
        user__is_active=True, user__is_blocked=False,
        user__user_experiences__is_current=True,
        end_date__gte=timezone.now().date(),
        end_date__lte=timezone.now().date() + timedelta(days=settings.DAYS_BEFORE_NOTIFICATION)
    )

    for insurance in insurance_going_to_expire:
        policy_type = insurance.get_policy_type_display()
        add_notification(
            text=f'Your insurance \'{insurance.policy_name}\' of type'
                 f' \'{policy_type}\' is going to be expired on {insurance.end_date}.',
            url=f'/user/profile/{insurance.user_id}/?tab=insurance',
            recipient=insurance.user,
            action=insurance
        )

        notify_organization(
            text=f'\'{insurance.policy_name}\' for {insurance.user.full_name} of type '
                 f'\'{policy_type}\' is going to be expired on {insurance.end_date}.',
            organization=insurance.user.detail.organization,
            action=insurance,
            permissions=[
                HRIS_CONTRACT_SETTINGS_PERMISSION,
                HRIS_CHANGE_REQUEST_PERMISSION
            ],
            url=f'/admin/{insurance.user.detail.organization.slug}/hris/users/'
                f'{insurance.user_id}/?tab=insurance'
        )


def validate_sent_notification(instance, text, organization):
    notification_sent_to_user = Notification.objects.filter(
        text__icontains=text,
        action_content_type=ContentType.objects.get_for_model(instance._meta.model),
        action_object_id=instance.id,
    )
    notification_sent_to_organization = OrganizationNotification.objects.filter(
        text__icontains=text,
        action_content_type=ContentType.objects.get_for_model(instance._meta.model),
        action_object_id=instance.id,
        recipient=organization
    )
    return notification_sent_to_user.count(), notification_sent_to_organization.count()


def probation_completion_notification():
    first_level_notification_experiences = UserExperience.objects.filter(
        Q(in_probation=True),
        Q(probation_end_date__gte=timezone.now().date()),
        Q(
            probation_end_date__gte=timezone.now().date() + timedelta(days=30),
            probation_end_date__lte=timezone.now().date() + timedelta(days=45)
        )
    ).distinct()

    for experience in first_level_notification_experiences:
        text = f'Experience for \'{experience.job_title.title}\' ' \
               f'is going to be expired on {experience.probation_end_date} ' \
               f'for {experience.user.full_name}.'

        user_notification_count, org_notification_count = validate_sent_notification(
            instance=experience,
            text=text,
            organization=experience.organization
        )

        if user_notification_count == 0:
            send_probation_completion_pre_notification(experience, text)

    second_level_notification_experiences = UserExperience.objects.filter(
        in_probation=True,
        probation_end_date__gte=timezone.now().date(),
        probation_end_date__lte=timezone.now().date() + timedelta(days=30)
    ).distinct()

    for experience in second_level_notification_experiences:
        text = f'Experience for \'{experience.job_title.title}\' ' \
               f'is going to be expired on {experience.probation_end_date} ' \
               f'for {experience.user.full_name}.'
        notification_count = validate_sent_notification(
            instance=experience,
            text=text,
            organization=experience.organization
        )[-1]

        if notification_count == 1:
            send_probation_completion_pre_notification(experience, text)


def send_probation_completion_pre_notification(experience, text):
    supervisor = experience.user.first_level_supervisor
    if supervisor and supervisor != get_system_admin():
        add_notification(
            text=text,
            url=f'/user/supervisor/my-team/employee-detail/{experience.user_id}',
            recipient=experience.user.first_level_supervisor,
            action=experience
        )

    notify_organization(
        text=text,
        organization=experience.organization,
        action=experience,
        permissions=[
            HRIS_CONTRACT_SETTINGS_PERMISSION,
            HRIS_CHANGE_REQUEST_PERMISSION
        ],
        url=f'/admin/{experience.organization.slug}/hris/users/{experience.user_id}'
    )


def send_change_notification_to_user(self, instance, user, actor, action):
    view = self
    if hasattr(self, 'context'):
        view = self.context.get('view')
    detail_path = view.__module__
    view_path = detail_path.split('.')[-1]
    profile_detail = view_path.replace('_', ' ')
    if 'detail' not in profile_detail:
        profile_detail = profile_detail + ' detail'
    if self.__class__.__name__ != 'UserExperienceSerializer':
        add_notification(
            text=f'Your {profile_detail} has been {action} by HR.',
            recipient=user,
            action=instance,
            url=f'/user/profile/{user.id}/?tab={view_path}'
        )
    organization = user.detail.organization
    notify_organization(
        text=f'{profile_detail.title()} for {user.full_name} has been {action} by  {actor.full_name}',
        action=organization,
        organization=organization,
        url=f'/admin/{organization.slug}/hris/users/{user.id}/?tab={view_path}',
        permissions=[
            HRIS_PERMISSION,
            HRIS_CHANGE_REQUEST_PERMISSION
        ]
    )
