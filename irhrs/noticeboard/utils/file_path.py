"""@irhrs_docs"""
import os

from irhrs.core.utils.common import get_uuid_filename


def get_post_attachment_path(instance, filename):
    """
    return path for post attachment
    """
    return os.path.join('uploads/noticeboard/attachments',
                        get_uuid_filename(filename))


def get_comment_attachment_path(instance, filename):
    """
    return path for post attachment
    """
    return os.path.join('uploads/noticeboard/comments',
                        get_uuid_filename(filename))

