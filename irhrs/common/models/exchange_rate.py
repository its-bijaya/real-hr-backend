from django.core.validators import MinValueValidator
from django.db import models

from irhrs.common.models import BaseModel

USD, NRS = "USD", "NRS"

CURRENCY_CHOICES = (
    (USD, "USD"),
    (NRS, "NRS")
)


class ExchangeRate(BaseModel):
    from_amount = models.FloatField(validators=[MinValueValidator(limit_value=0.0)])
    from_currency = models.CharField(choices=CURRENCY_CHOICES, max_length=15, db_index=True)
    to_currency = models.CharField(choices=CURRENCY_CHOICES, max_length=15, db_index=True)
    to_amount = models.FloatField(validators=[MinValueValidator(limit_value=0.0)])
    from_date = models.DateField()
    to_date = models.DateField()
    description = models.TextField(max_length=600, blank=True)

    def __str__(self):
        return f"{self.from_currency} {self.from_amount} = {self.to_currency} {self.to_amount} " \
               f"({self.from_date} - {self.to_date if self.to_date else 'Currently active'})"
