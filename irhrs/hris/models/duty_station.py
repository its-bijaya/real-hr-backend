from django.contrib.auth import get_user_model
from django.db import models

from irhrs.core.validators import MinMaxValueValidator
from irhrs.core.validators import \
    MinMaxValueValidator
from irhrs.common.models import BaseModel
from irhrs.common.models.duty_station import DutyStation
from irhrs.organization.models import Organization


class DutyStationAssignment(BaseModel):
    duty_station = models.ForeignKey(
        DutyStation,
        related_name="assignments",
        on_delete=models.PROTECT
    )
    user = models.ForeignKey(
        get_user_model(),
        related_name="assigned_duty_stations",
        on_delete=models.CASCADE
    )
    organization = models.ForeignKey(
        Organization,
        related_name="duty_station_assignments",
        on_delete=models.PROTECT
    )
    from_date = models.DateField()
    to_date = models.DateField(null=True, blank=True)
