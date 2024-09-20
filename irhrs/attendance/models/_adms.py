from datetime import timedelta
from django.db import models
from ..constants import (
    DEVICE, PASSWORD, RFID_CARD, METHOD_OTHER,
    PUNCH_IN, PUNCH_OUT, BREAK_IN, BREAK_OUT)

ATTSTATES = (
    ("0", "Check in"),
    ("1", "Check out"),
    ("2", "Break out"),
    ("3", "Break in"),
    ("4", "Overtime in"),
    ("5", "Overtime out"),
    ("8", "Meal start"),
    ("9", "Meal end"),
)

VERIFYS_STATES = {
    '0': PUNCH_IN,
    '1': PUNCH_OUT,
    '2': BREAK_OUT,
    '3': BREAK_IN,
}

VERIFYS = (
    (0, "Password"),
    (1, "Fingerprint"),
    (2, "Card"),
    (9, "Other"),
)

VERIFYS_MAP = {
    0: PASSWORD,
    1: DEVICE,
    2: RFID_CARD,
    9: METHOD_OTHER
}


class DeviceEmployee(models.Model):
    id = models.AutoField(db_column="userid", primary_key=True)
    # original name: PIN
    # user's ID in device aka biouser id
    id_on_device = models.CharField(db_column="badgenumber", max_length=20, db_index=True)

    class Meta:
        managed = False
        db_table = 'userinfo'


class DeviceTimesheet(models.Model):
    # original name: UserID
    employee = models.ForeignKey('DeviceEmployee', db_column='userid', on_delete=models.CASCADE)

    # original name: TTime
    check_time = models.DateTimeField(db_column='checktime')

    # original name: State
    # e.g. check in, check out, break out, break in etc.
    check_type = models.CharField(
        max_length=11, db_column='checktype', choices=ATTSTATES, db_index=True)

    # original name: Verify
    # attendance method i.e. card, finger etc
    check_method = models.IntegerField(db_column='verifycode', choices=VERIFYS)

    # device serial number original name: SN
    device_sn = models.CharField(db_column='SN', max_length=20)

    @property
    def bio_id(self):
        return int(self.employee.id_on_device)

    @property
    def checktype(self):
        return VERIFYS_STATES.get(self.check_type, 'N/A')

    @property
    def checktime(self):
        # Convert the time to UTC and apply formula according to device TimeZone
        # currently assuming for Asia/Kathmandu
        # TODO: Shrawan
        utc_offset = timedelta(seconds=20700)
        return self.check_time - utc_offset

    @property
    def checkmethod(self):
        return VERIFYS_MAP[self.check_method]

    def __str__(self):
        return "{0} -> {1}: <{2}>, <{3}>".format(
            self.employee.id_on_device,
            self.check_time,
            self.get_check_type_display(),
            self.get_check_method_display()
        )

    class Meta:
        managed = False
        db_table = 'checkinout'
        ordering = ('id',)
