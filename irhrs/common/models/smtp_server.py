from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models

from irhrs.common.constants import SECURED_LAYER_TYPE
from irhrs.core.utils.common import get_upload_path
from irhrs.core.validators import MinMaxValueValidator


class SMTPServer(models.Model):
    username = models.CharField(max_length=128)
    password = models.CharField(max_length=128)
    host = models.CharField(max_length=122)
    port = models.PositiveIntegerField(validators=[MinMaxValueValidator(0, 65535)])
    use_tls = models.BooleanField(default=False)
    use_ssl = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.host}-{self.port}'
