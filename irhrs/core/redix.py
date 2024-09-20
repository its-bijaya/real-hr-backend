from redis import ConnectionPool, StrictRedis
from django.conf import settings

# Lock mechanism has  been implemented in:
#                   1. Attendance Sync tasks (irhrs.attendance.tasks.timesheets)

REDIS_POOL = ConnectionPool(**getattr(settings, 'REDIS_DATABASE'))


def general():
    return StrictRedis(connection_pool=REDIS_POOL)


def get_a_lock(key, timeout=None):
    r = general()
    lock = r.lock(key, timeout)
    return lock
