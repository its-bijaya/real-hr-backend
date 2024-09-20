from django.utils.translation import gettext_lazy as _

from rest_framework.exceptions import APIException


class CustomValidationError(APIException):
    status_code = 400
    default_detail = _('Bad Request')
    default_code = 'invalid'

    def __init__(self, error_dict):
        self.error_dict = error_dict
        super().__init__(self.error_dict)


class AdvanceSalaryNotConfigured(APIException):
    status_code = 400
    default_detail = _('Advance salary not configured for this organization.')
    default_code = 'invalid'


class PackageNotAssigned(APIException):
    status_code = 400
    default_detail = _('No package assigned to employee for given dates.')
    default_code = 'invalid'


class ExperienceNotFound(APIException):
    status_code = 400
    default_detail = _('Experience of user does exist for given dates.')
    default_code = 'invalid'
