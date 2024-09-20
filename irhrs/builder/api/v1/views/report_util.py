import os
import uuid

from django.utils import timezone
from django.conf import settings
from django.core.cache import cache

from irhrs.export.utils.helpers import save_workbook

MEDIA_ROOT = settings.MEDIA_ROOT
BACKEND_URL = settings.BACKEND_URL


def export_report(report_object):
    cache.delete(f'report_export_{report_object.id}')
    file_name = report_object.name[:15].replace(' ',
                                                '') + '-' + uuid.uuid4().hex + '.xlsx'
    base_path = 'report-exports'
    if not os.path.exists(base_path):
        os.mkdir(base_path)
    file_path = os.path.join(base_path, file_name)
    try:
        wb = report_object.export_result_wb()
        file_path = save_workbook(wb, file_path)
        _prepare_cache = {  # key will be used in future
            'url': BACKEND_URL + '/media/' + file_path + '?key=' + uuid.uuid4().hex + '&public=' + uuid.uuid4().hex,
            'created_on': timezone.now().astimezone()
        }
        cache.set(f'report_export_{report_object.id}',
                  _prepare_cache,
                  timeout=None)
        cache.delete(f'report_export_on_progress_{report_object.id}')
    except Exception as e:
        print(e)
        cache.delete(f'report_export_on_progress_{report_object.id}')
