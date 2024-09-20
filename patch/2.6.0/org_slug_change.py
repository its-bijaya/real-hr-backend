from django.db.models import Value
from django.db.models.functions import Replace

from irhrs.notification.models.notification import OrganizationNotification, Notification
from irhrs.organization.models import Organization

current_organization_slug = 'aayulogic-private-ltd'
new_organization_name = 'Aayulogic'
new_organization_slug = 'alpl'

# verify current slug exists.
current_org = Organization.objects.get(slug=current_organization_slug)


def change_slug(organization, name, slug):
    old_slug = organization.slug
    organization.name = name
    organization.slug = slug
    organization.save()
    org_changes = OrganizationNotification.objects.filter(
        url__icontains=old_slug
    ).update(
        url=Replace(
            'url',
            Value(old_slug),
            Value(slug)
        )
    )
    notification_changes = Notification.objects.filter(
        url__icontains=old_slug
    ).update(
        url=Replace(
            'url',
            Value(old_slug),
            Value(slug)
        )
    )
    print(
        org_changes,
        ' org notifications updated.'
    )
    print(
        notification_changes,
        ' notifications updated.'
    )


if not Organization.objects.filter(slug=new_organization_slug).exists():
    change_slug(current_org, new_organization_name, new_organization_slug)
