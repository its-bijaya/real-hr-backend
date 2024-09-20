import uuid

from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models import F, Value
from django.db.models.functions import Concat
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django_q.tasks import async_task

from irhrs.core.constants.payroll import CONFIRMED
from irhrs.notification.models.notification import OrganizationNotification
from irhrs.notification.utils import notify_organization, add_notification
from irhrs.payroll.do_not_compile import sync_create_package_rows, sync_update_backdated_payroll
from irhrs.payroll.models import UserExperiencePackageSlot, PackageHeading, Payroll, \
    UnitOfWorkRequestHistory, APPROVED
from irhrs.permission.constants.permissions import ALL_PAYROLL_PERMISSIONS, \
    UNIT_OF_WORK_REQUEST_PERMISSION
from irhrs.recruitment.constants import DENIED


def async_create_package_rows(instance):
    key = uuid.uuid4()
    cache_key = f"__packagewisesalary__instance__{instance.id}"
    cache.set(cache_key, key)

    async_task(sync_create_package_rows, instance.id, cache_key, key)


def async_update_or_create_backdated_payroll(instance):
    if instance.backdated_calculation_generated:
        # quick hack to disable signal and infinite recursion
        # set backdated calculation generated to False to show in progress status
        UserExperiencePackageSlot.objects.filter(id=instance.id).update(
            backdated_calculation_generated=False)
    async_task(sync_update_backdated_payroll, instance.id)


@receiver(post_save, sender=UserExperiencePackageSlot)
def create_update_report_row_user_experience_package(sender, instance, created, **kwargs):
    async_create_package_rows(instance)
    async_update_or_create_backdated_payroll(instance)


@receiver(post_delete, sender=PackageHeading)
@receiver(post_save, sender=PackageHeading)
def update_package_heading_rows(sender, instance, *args, **kwargs):
    for employee_slot in instance.package.employee_payroll_packages.all():
        async_create_package_rows(employee_slot)

    # TODO whenever PackageHeading of unused Package of UserExperiencePackageSlot with backdate is
    # added, deleted, or updated, backdated calculations should be updated as well.


@receiver(pre_delete, sender=Payroll)
def send_delete_notification(sender, instance, *args, **kwargs):
    if hasattr(instance, 'generation'):
        payroll_history = instance.generation
        ctype = ContentType.objects.get_for_model(payroll_history)
        OrganizationNotification.objects.filter(
            action_content_type=ctype,
            action_object_id=payroll_history.id
        ).update(
            url='',
            text=Concat(F('text'), Value(' (DELETED)'))
        )


@receiver(post_save, sender=UnitOfWorkRequestHistory)
def send_unit_of_work_request_notification(sender, instance, *args, **kwargs):
    if instance.action_performed == APPROVED:
        notify_organization(
            text=str(instance),
            action=instance,
            actor=instance.action_performed_by,
            organization=instance.request.user.detail.organization,
            permissions=[ALL_PAYROLL_PERMISSIONS, UNIT_OF_WORK_REQUEST_PERMISSION],
            url=f'/admin/{instance.request.user.detail.organization.slug}/payroll/unit-of-work'
        )
    if instance.action_performed in [CONFIRMED, DENIED, APPROVED]:
        add_notification(
            text=f"{instance.action_performed_by} "
                 f"{instance.action_performed.lower()} your unit of work request.",
            action=instance,
            actor=instance.action_performed_by,
            recipient=instance.request.user,
            url='/user/payroll/unit-of-work'
        )
    else:
        add_notification(
            text=str(instance),
            action=instance,
            actor=instance.action_performed_by,
            recipient=instance.action_performed_to,
            url='/user/supervisor/payroll/unit-of-work'
        )
