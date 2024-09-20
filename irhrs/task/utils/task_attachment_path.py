"""@irhrs_docs"""
import os

from irhrs.core.utils.common import get_uuid_filename


def get_task_attachment_path(_, filename):
    return os.path.join('uploads/tasks/attachments',
                        get_uuid_filename(filename))
