import logging
from itertools import groupby

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.utils import timezone

from irhrs.notification.utils import notify_organization
from irhrs.organization.models import Organization
from irhrs.permission.constants.permissions import ATTENDANCE_PERMISSION, ATTENDANCE_DEVICE_SETTINGS_PERMISSION, \
    ATTENDANCE_INDIVIDUAL_ATTENDANCE_SETTINGS_PERMISSION
from ..models import AttendanceEntryCache, AttendanceUserMap, TimeSheet
from ..constants import SYNC_PENDING, SYNC_FAILED, SYNC_SUCCESS, DEVICE

logger = logging.getLogger(__name__)


class BaseHandler:
    def pull_attendance(self, clear=None):
        raise NotImplementedError

    def get_device(self):
        raise NotImplementedError

    def _get_pointer(self):
        try:
            last_entry = AttendanceEntryCache.objects.filter(
                source=self.get_device(),
                timestamp__lte=timezone.now()).order_by('-timestamp')[0]
        except IndexError:
            return None
        else:
            return last_entry

    def sync(self, pull=True, **kwargs):
        total_synced = 0

        if pull:
            self.pull_attendance(**kwargs)

        # UPDATE @raw-V
        # Because this takes a lot of time, this will be refactored under the following logic:
        # Attendance Entry Caches will be processed for registered Bio User Ids Only.
        # We will ignore them from the list forever.
        # When the bio user id is added, it is synced backed into the system.
        # This potentially gives us an issue of valid entries if BIO_USER_ID is duplicated
        # for a past user and a new user. But that's clearly, GIGO!

        registered_bio_maps = set(
            AttendanceUserMap.objects.filter(
                source=self.get_device()
            ).order_by().values_list(
                'bio_user_id', flat=True
            ).distinct()
        )

        unsynced = AttendanceEntryCache.objects.filter(
            source=self.get_device(),
            reason=SYNC_PENDING,
            bio_id__in=registered_bio_maps
        ).order_by('bio_id')

        logger.debug(
            "Beginning sync for {} attendance records for {}".format(
                unsynced.count(),
                self.get_device()
            )
        )

        grouped = groupby(unsynced.iterator(), lambda u: u.bio_id)

        for bio_id, unsync_list in grouped:
            sync_description = ''
            unsync_list = list(unsync_list)
            length = len(unsync_list)

            try:
                usermap = AttendanceUserMap.objects.select_related('setting__user') \
                    .get(bio_user_id=bio_id, source=self.get_device())

            except ObjectDoesNotExist:
                sync_description = 'Could not find map for device {} with bio_id as {}'.format(self.get_device(),
                                                                                               bio_id)
                logger.debug(sync_description, exc_info=True)
                reason = SYNC_FAILED
                for org in Organization.objects.all():
                    notify_organization(
                        text=f"An entry for {bio_id} was received from "
                             f"{self.get_device()}. However, it was not recognized.",
                        url='/',
                        action=unsync_list[0],
                        permissions=[
                            ATTENDANCE_PERMISSION,
                            ATTENDANCE_DEVICE_SETTINGS_PERMISSION,
                            ATTENDANCE_INDIVIDUAL_ATTENDANCE_SETTINGS_PERMISSION,
                        ],
                        organization=org,
                    )
            except MultipleObjectsReturned:
                sync_description = 'Could not find map for device {} with bio_id as {} because of DB MOR issue'.format(
                    self.get_device(), bio_id)
                logger.debug(sync_description, exc_info=True)
                reason = SYNC_FAILED
            else:
                logger.debug(
                    "Syncing {} records for user {} with bio_id as {}"
                        .format(length, usermap.setting.user, bio_id))

                timestamps = [u.timestamp for u in unsync_list]

                obj = TimeSheet.objects.sync_attendance(
                    usermap.setting.user, timestamps, DEVICE)
                reason = SYNC_SUCCESS if obj else SYNC_FAILED
                sync_description = 'Sync success' if obj else \
                    'Sync failed because of internal issue on TimeSheet generation'
                total_synced += length

            for unsynq in unsync_list:
                unsynq.sync_tries += 1
                unsynq.reason = reason
                unsynq.sync_description = sync_description
                unsynq.save()
        logger.debug("Finished syncing {} records for {}".format(total_synced, self.get_device()))
        return total_synced
