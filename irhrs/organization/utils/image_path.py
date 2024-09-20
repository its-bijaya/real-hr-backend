import os

from irhrs.core.utils.common import get_uuid_filename, get_today


def get_image_file_path(instance, filename):
    """
    return path for logo
    """
    return os.path.join('uploads/branch/logo', get_uuid_filename(filename))
