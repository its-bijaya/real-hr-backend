from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from irhrs.core.utils.common import get_today
from irhrs.organization.models import Organization, EmploymentJobTitle, OrganizationDivision, \
    EmploymentLevel
from irhrs.users.models import UserSupervisor, UserExperience, UserDetail
from irhrs.users.utils.cache_utils import set_user_autocomplete_cache, \
    recalibrate_supervisor_subordinate_relation

USER = get_user_model()


@receiver(post_save, sender=UserSupervisor)
def create_activity_on_noticeboard(*args, **kwargs):
    recalibrate_supervisor_subordinate_relation()


def create_history(experience):
    experience.step_histories.create(
        step=experience.current_step,
        start_date=experience.start_date
    )


@receiver(post_save, sender=UserExperience)
def set_step_history(sender, instance, *args, **kwargs):
    """
    maintain Step History automatically when UserExperience updates.
    This updates are either:
    at creation:
        i.e. Creating a new User Experience
    at updating:
        i.e. Through Serializer.
    at scheduled tasks:
        i.e. through django_q objects.
    """
    immediate_history = instance.step_histories.order_by(
        '-start_date'
    ).first()
    if immediate_history:
        if immediate_history.step == instance.current_step:
            # The step was not updated. So, do not maintain this history.
            return
        # expire past
        immediate_history.end_date = get_today()
        immediate_history.save(update_fields=['end_date'])
    create_history(instance)


@receiver(post_save, sender=USER)
@receiver(post_save, sender=UserDetail)
@receiver(post_save, sender=Organization)
def update_cache_on_user_update(*args, **kwargs):
    set_user_autocomplete_cache()


@receiver(post_save, sender=USER)
def create_email_setting(sender, instance, created, **kwargs):
    if created:
        from irhrs.hris.models.email_setting import EmailSetting
        EmailSetting.objects.create(user=instance)


@receiver(post_save, sender=EmploymentJobTitle)
@receiver(post_save, sender=OrganizationDivision)
@receiver(post_save, sender=EmploymentLevel)
def update_cache_on_user_organization_update(sender, instance, created, **kwargs):
    if not created:
        # update user autocomplete on updates of organization details
        set_user_autocomplete_cache()
