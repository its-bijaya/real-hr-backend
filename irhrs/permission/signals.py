import logging

from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from irhrs.organization.models import Organization
from irhrs.permission.constants.groups import ADMIN
from irhrs.permission.models.hrs_permisssion import OrganizationGroup, HRSPermission

logger = logging.getLogger(__name__)


def seed_organization_vs_group(org_list, group_list):
    bulks = list()
    for org in org_list:
        for group in group_list:
            bulks.append(
                OrganizationGroup(
                    organization=org,
                    group=group
                )
            )
            logger.info(
                f"Added group {group} for {org}"
            )
    groups = OrganizationGroup.objects.bulk_create(bulks)
    admin_group, _ = Group.objects.get_or_create(name=ADMIN)
    for admin_grp in filter(
        lambda x: x.group == admin_group,
        groups
    ):
        if admin_grp.organization:
            for perm in HRSPermission.objects.filter(
                organization_specific=True
            ):
                admin_grp.permissions.add(perm)
        else:
            for perm in HRSPermission.objects.filter(
                organization_specific=False
            ):
                admin_grp.permissions.add(perm)


@receiver(post_save, sender=Organization)
@receiver(post_save, sender=Group)
def add_organization_group(sender, instance, created, **kwargs):
    if not created:
        return
    if sender == Organization:
        seed_organization_vs_group(
            [instance],
            Group.objects.all()
        )

    elif sender == Group:
        seed_organization_vs_group(
            [None, *Organization.objects.all()],
            [instance]
        )
