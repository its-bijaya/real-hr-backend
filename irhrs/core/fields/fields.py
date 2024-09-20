from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import TextField, CharField
from json import loads, dumps, JSONDecodeError

from django.utils.translation import gettext_lazy as _

from rest_framework.serializers import CharField as SerializerCharField


class JSONTextField(TextField):
    description = _('A JSON object')
    default_error_messages = {
        'invalid': _("Value must be valid JSON.")
    }

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            value = loads(value)
            if not isinstance(value, dict):
                raise IntegrityError("Invalid JSON in database.")
            return value
        except JSONDecodeError:
            raise IntegrityError("Invalid JSON in database.")

    def to_python(self, value):
        if isinstance(value, dict):
            return value

        if value is None:
            return value

        try:
            value = loads(value)
            if not isinstance(value, dict):
                raise ValidationError(_("Value must be valid JSON."),
                                      code="invalid",
                                      params={'value': value}, )
            return value
        except JSONDecodeError:
            raise ValidationError(_("Value must be valid JSON."),
                                  code="invalid",
                                  params={'value': value}, )

    def get_prep_value(self, value):
        if value is None:
            return value
        return dumps(self.to_python(value))


class MaskedCharField(SerializerCharField):

    @staticmethod
    def get_mask():
        return '********'

    def to_representation(self, _):
        # return self.get_mask()
        return super().to_representation(_)
