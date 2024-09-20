from irhrs.notification.utils import notify_organization, add_notification
from irhrs.permission.constants.permissions import ORGANIZATION_DOCUMENTS_PERMISSION, \
    ORGANIZATION_PERMISSION


def send_notification_for_acknowledge_document(ack_document, users_to_notify):
    add_notification(
        text="%s has been published. Please acknowledge the document." % ack_document.title,
        recipient=users_to_notify,
        action=ack_document,
        url='/user/organization/document'
    )


def send_notification_when_user_acknowledges_document(user, ack_document):
    notify_organization(
        text="%s has acknowledged the document %s." % (
            user.full_name, ack_document.title
        ),
        organization=ack_document.organization,
        action=ack_document,
        permissions=[ORGANIZATION_DOCUMENTS_PERMISSION, ORGANIZATION_PERMISSION],
        url='/admin/%s/organization/document' % ack_document.organization.slug
    )
