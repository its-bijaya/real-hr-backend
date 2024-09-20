# import logging
#
# from django.db import connections
# from django.db.utils import OperationalError, ConnectionDoesNotExist
# from django.utils import timezone
#
# from irhrs.adms.utils import DeviceTimesheet
# from ..models import AttendanceEntryCache
# from .base import BaseHandler
#
# from ..constants import ADMS
#
# logger = logging.getLogger(__name__)
#
#
# class AdmsHandler(BaseHandler):
#
#     def __init__(self, device):
#         assert device.sync_method == ADMS
#         self.device = device
#
#     def get_device(self):
#         return self.device
#
#     def _has_connection(self):
#         try:
#             connections['adms_database']
#         except (OperationalError, ConnectionDoesNotExist):
#             logger.error('Could not connect to ADMS Database server!')
#             return False
#         else:
#             return True
#
#     def _get_base_queryset(self):
#
#         if not self._has_connection():
#             logger.error('Cannot establish connection with {}'.format(self.device))
#             return
#
#         return DeviceTimesheet.objects.select_related('employee') \
#             .using('adms_database').filter(device_sn=self.device.serial_number)
#
#     def _get_queryset_for_devices(self):
#         base_qs = self._get_base_queryset()
#         _pointer = self._get_pointer()
#         if base_qs and _pointer:
#             base_qs = base_qs.filter(check_time__gt=timezone.make_naive(_pointer.timestamp))
#         return base_qs
#
#     def pull_attendance(self, clear=None):
#         total_pulled = 0
#         sync_caches = []
#         queryset = self._get_queryset_for_devices()
#         if queryset is None or not queryset.exists():
#             logger.info("No new attendance data was found on ADMS server!")
#             return total_pulled
#         last_attendance = queryset.last()
#         queryset = queryset.filter(
#             id__lte=last_attendance.id).order_by('employee__id_on_device')
#         for attendance in queryset:
#             total_pulled += 1
#             _sync_cache = AttendanceEntryCache(
#                 source=self.get_device(), bio_id=attendance.bio_id,
#                 timestamp=attendance.checktime, entry_category=attendance.checktype)
#             sync_caches.append(_sync_cache)
#         if sync_caches:
#             AttendanceEntryCache.objects.bulk_create(sync_caches)
#         else:
#             logger.warning('No new attendance data found on {}.'.format(self.get_device()))
#         data = {
#             'last_pulled_data_id': last_attendance.id,
#             'last_pulled_data_timestamp': str(last_attendance.checktime)
#         }
#         self.get_device().last_activity = timezone.now()
#         self.get_device().extra_data = data
#         self.get_device().save(update_fields=['last_activity', 'extra_data'])
#         logger.debug('Finished pulling for {}-{}'.format(self.get_device(), self.get_device().ip))
#         return total_pulled
