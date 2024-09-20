import os

from irhrs.core.utils.common import get_uuid_filename


def get_work_log_attachment_path(_, filename):
    return os.path.join('uploads/work_log/attachments',
                        get_uuid_filename(filename))
