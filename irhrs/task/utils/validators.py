from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext as _


def validate_score(score):
    if not (1 <= score <= 10):
        raise ValidationError(_("Must be from 1-10"))
    return score


def validate_efficiency(efficiency):
    if not (0 <= efficiency <= 100):
        raise ValidationError(_("Must be from 0-100"))
    return efficiency
