import itertools
import logging

import requests
from dateutil.parser import parse
from django.conf import settings
from django.db import transaction
from django_q.models import Schedule
from requests import Request
from rest_framework import status

from irhrs.attendance.constants import ADMS, DEVICE
from irhrs.attendance.handlers.adms_from_mysql_database import AdmsHandler
from irhrs.attendance.models import AttendanceSource, TimeSheet, AttendanceUserMap

ADMS_SERVER = getattr(settings, 'ADMS_SERVER', None)
logger = logging.getLogger(__name__)

# def pull_adm_server_attendance():
#     """
#     Pulls Attendance from database server mentioned as "ADMS_SERVER" in DATABASES.
#
#     :return:
#     """
#     from irhrs.attendance.models import AttendanceEntryCache, AttendanceSource
#     last_id_per_device = dict(AttendanceSource.objects.filter(
#         sync_method=ADMS
#     ).values_list(
#         'serial_number', 'extra_data'
#     ))
#     new_entries = AttendanceLog.objects.using(
#         ADMS_SERVER
#     ).select_related(
#         'device'
#     ).filter(
#         device__serial_number__in=last_id_per_device.keys()
#     )
#     raw_entries = list()
#     for serial_number, extra_data in last_id_per_device.items():
#         extra_data = extra_data or {}
#         fil = {
#             'id__gt': extra_data.get('last_id')
#         } if extra_data.get('last_id') else {}
#         qs = new_entries.filter(device__serial_number=serial_number).filter(**fil)
#         if not qs:
#             continue
#         raw_entries.append(qs)
#         last_id = json.dumps({
#             'last_id': qs.order_by('-id').first().id
#         })
#         AttendanceSource.objects.filter(serial_number=serial_number).update(
#             extra_data=last_id
#         )
#     serial_number_to_fk = dict(AttendanceSource.objects.filter(
#         serial_number__in=list(
#             new_entries.values_list(
#                 'device__serial_number', flat=True
#             )
#         )
#     ).values_list(
#         'serial_number', 'id'
#     ))
#     entry_cache_objs = list()
#     for entry in itertools.chain.from_iterable(raw_entries):
#         entry_cache_objs.append(
#             AttendanceEntryCache(
#                 source_id=serial_number_to_fk.get(entry.device.serial_number),
#                 bio_id=entry.bio_user_id,
#                 timestamp=entry.punch_time
#             )
#         )
#     entry_caches = AttendanceEntryCache.objects.bulk_create(
#         entry_cache_objs
#     )
#     grouped = dict(itertools.groupby(
#         entry_caches,
#         key=lambda x: x.source
#     ))
#     from irhrs.attendance.handlers.adms import AdmsHandler
#     result = dict()
#     for device, unsynced in grouped.items():
#         sync_count = AdmsHandler(device).sync(pull=False)
#         result.update({
#             device.name: sync_count
#         })
#     return result


@transaction.atomic()
def pull_attendance_data_from_server():
    attendance_devices = AttendanceSource.objects.filter(
        sync_method=ADMS
    )
    if attendance_devices.count() == 0:
        logger.warning(
            'Auto removing Attendance Pull From ADMS Server as no more devices left to pull.'
        )
        Schedule.objects.filter(
            func='irhrs.attendance.utils.attendance_pull_mechanisms.pull_attendance_data_from_server'
        ).delete()
    new_entries = list()
    for adms_device in attendance_devices:
        extra_data = adms_device.extra_data or {}
        fails = extra_data.get('failed_count') or 0
        if fails >= 100:
            continue
        last_id = extra_data.get('last_id') or 0
        payload = {
            'last_id': last_id,
            'sn': adms_device.serial_number,
            'access_key_1': settings.ADMS_ACCESS_KEY1,
            'access_key_2': settings.ADMS_ACCESS_KEY2,
        }
        url = "{}://{}:{}/api/logs".format(
            'https' if adms_device.port == '443' else 'http',
            adms_device.ip,
            adms_device.port
        )
        uri = Request(
            method='GET',
            url=url,
            data=payload
        )
        entries = list()
        next_url = uri.prepare().url
        while next_url:
            response = requests.post(next_url)
            if response.status_code == status.HTTP_200_OK:
                response_json = response.json()
                entries += response_json.get('results')
                next_url = response_json.get('next')
            else:
                fails += 1
                extra_data.update({
                    'failed_count': fails
                })
                break
        if entries:
            extra_data.update({
                'last_id': max([x.get('id') for x in entries])
            })
        adms_device.extra_data = extra_data
        adms_device.save()
        new_entries.append(
            (adms_device, entries),
        )
    return clock_raw_entries(new_entries)


def update_attendance_device(adms_device):
    response = {}
    url = r"{}://{}:{}/device/{}".format(
        'https' if adms_device.port == '443' else 'http',
        adms_device.ip,
        adms_device.port,
        adms_device.serial_number
    )
    payload = {
        'name': adms_device.name,
        'timezone': adms_device.timezone,
        'is_disabled': adms_device.sync_method != ADMS,
        'access_key_1': settings.ADMS_ACCESS_KEY1,
        'access_key_2': settings.ADMS_ACCESS_KEY2,
    }
    uri = Request(
        method='PUT',
        url=url,
        data=payload
    )
    next_url = uri.prepare().url
    requests.post(next_url)
    return response


def clock_raw_entries(entries):
    _FAILED = _SUCCESS = 0
    for device, entries_device in entries:
        grouped_iterator = itertools.groupby(
            entries_device,
            key=lambda e: e.get('bio_user_id')
        )
        for bio_user_id, entries_user in grouped_iterator:
            user_map = AttendanceUserMap.objects.filter(
                source=device,
                bio_user_id=bio_user_id
            ).select_related('setting').first()
            if not user_map:
                _FAILED += 1
                continue
            for entry in entries_user:
                TimeSheet.objects.clock(
                    user_map.setting.user,
                    parse(entry.get('punch_time')),
                    entry_method=DEVICE,
                )
                _SUCCESS += 1
    return {
        'FAILED': _FAILED,
        'SUCCESS': _SUCCESS,
    }


def sync_adms_devices():
    attendance_devices = AttendanceSource.objects.filter(
        sync_method=ADMS
    )
    if attendance_devices.count() == 0:
        logger.warning(
            'Auto removing Attendance Pull From ADMS Server as no more devices left '
            'to pull.'
        )
        Schedule.objects.filter(
            func='irhrs.attendance.utils.attendance_pull_mechanisms.sync_adms_devices'
        ).delete()
    for device in attendance_devices:
        handler = AdmsHandler(device=device)
        handler.sync(pull=True)
