from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException


class AdvanceExpenseNotConfigured(APIException):
    status_code = 400
    default_detail = _('Advance expense not configured for this organization.')
    default_code = 'invalid'

