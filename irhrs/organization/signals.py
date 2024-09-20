from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from irhrs.common.management.commands.seed_org_data import seed_default_data_for
from irhrs.organization.models import (Organization, ContractSettings, ApplicationSettings,
                                       EmailNotificationSetting)
from irhrs.organization.utils.cache import build_application_settings_cache
from irhrs.users.models import UserEmailUnsubscribe


@receiver(post_save, sender=Organization)
def create_organization_settings(sender, instance, created, **kwargs):
    if created:
        ContractSettings.objects.create(organization=instance)
        seed_default_data_for(instance)


@receiver(post_save, sender=ApplicationSettings)
@receiver(post_delete, sender=ApplicationSettings)
def reset_application_settings_cache(sender, instance, *args, **kwargs):
    """
    Resets Application Settings Cache.
    """
    build_application_settings_cache(instance.organization)


@receiver(post_save, sender=EmailNotificationSetting)
def update_users_email_settings(sender, instance, created, **kwargs):
    """
    When hr disables allow_unsubscribe for any email settings, then all those
    UserEmailUnsubscribe instances matching that particular email type should
    be deleted.
    """
    if not instance.allow_unsubscribe:
        UserEmailUnsubscribe.objects.filter(email_type=instance.email_type).delete()
