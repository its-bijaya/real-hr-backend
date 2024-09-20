"""@irhrs_docs"""
import requests
from django.conf import settings
from django.db import connections, OperationalError
from rest_framework.status import HTTP_200_OK

ADMS_DIRECT = getattr(settings, 'ADMS_DIRECT', 'adms_direct')


def adms_connection_test():
    try:
        connection = connections[ADMS_DIRECT]
        connection.cursor()
    except OperationalError:
        success = False
    else:
        connection.close()
        success = True
    return success


def dirsync_connection_test(ip, port=4370, password=0):
    from zk import ZK
    from zk.exception import ZKError
    from django.core.exceptions import ImproperlyConfigured
    device = ZK(ip=ip, port=port, password=password, timeout=10)
    try:
        device.connect()
    except (ImproperlyConfigured, ZKError):
        success = False
    else:
        success = True
        device.disconnect()
    return success
