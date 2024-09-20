"""@irhrs_docs"""

import os

from irhrs.core.utils.common import get_uuid_filename


def get_meeting_document_path(_, filename):
    return os.path.join('uploads/meeting/documents',
                        get_uuid_filename(filename))


def get_event_featured_image(_, filename):
    return os.path.join('uploads/event/attachments',
                        get_uuid_filename(filename))


def get_event_frontend_url(event):
    return f"/user/events/{event.id}"
