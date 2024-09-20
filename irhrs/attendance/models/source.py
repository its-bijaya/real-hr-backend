import pytz
from django.db import models
from django.utils.functional import cached_property
from django.utils.module_loading import import_string

from irhrs.common.models import BaseModel
from irhrs.core.fields import JSONTextField
from irhrs.core.mixins.model_diff import ModelDiffMixin
from ..constants import SYNC_METHODS, DONT_SYNC, ADMS, SYNC_HANDLERS


class AttendanceSource(BaseModel, ModelDiffMixin):
    serial_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(
        max_length=50, help_text='Set name to identify the device uniquely.',
        unique=True
    )
    last_activity = models.DateTimeField(null=True, blank=True)
    sync_method = models.PositiveSmallIntegerField(choices=SYNC_METHODS, default=DONT_SYNC)
    # Removed Username, Password and DB-name as no more required for ADMS
    ip = models.GenericIPAddressField(protocol='ipv4', null=True, blank=True)
    port = models.IntegerField(null=True, blank=True)
    disable_device = models.BooleanField(
        "disable device to pull attendance data",
        default=True,
        help_text="This disables the device before pulling new data and enables "
                  "the device after completion. "
                  "WARNING: Turning this off may cause data-loss if 'Clear Device' "
                  "option has been enabled. "
                  "Only applicable for direct sync devices."
    )
    clear_device = models.BooleanField(
        "clear device after pulling data",
        default=False,
        help_text="WARNING: This can cause data-loss if 'Disable to Pull' "
                  "option has been turned off. "
                  "Only applicable for direct sync devices."
    )
    extra_data = JSONTextField(null=True, blank=True)
    timezone = models.CharField(
        max_length=100,
        choices=(
            (i, i) for i in pytz.common_timezones
        ),
        blank=True,
        help_text='In which timezone, is the device located. '
                  'The device sends an unaware timestamp. '
                  'So, this timezone will be used to aware the timestamp.'
    )

    @cached_property
    def handler(self):
        handler_str = SYNC_HANDLERS.get(self.sync_method)
        if handler_str is not None:
            return import_string(handler_str)(device=self)

    @property
    def adms_last_pulled_id(self):
        # Returns last id of fetch data
        assert self.sync_method == ADMS
        return (self.extra_data or {}).get('last_pulled_data_id', None)

    def __str__(self):
        return self.name
