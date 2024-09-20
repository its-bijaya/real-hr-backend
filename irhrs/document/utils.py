import os

from irhrs.core.utils.common import get_uuid_filename


def get_document_file_path(instance, filename):
    """
    return path for media document
    """
    return os.path.join('uploads/documents/', get_uuid_filename(filename))
