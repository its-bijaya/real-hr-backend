"""@irhrs_docs"""
import logging

from django.utils.functional import SimpleLazyObject
from rest_framework.permissions import BasePermission, SAFE_METHODS

from irhrs.core.constants.organization import APPLICATION_CHOICES
from irhrs.core.utils.common import is_request_read_only
from irhrs.organization.models.settings import ApplicationSettings
from irhrs.permission.constants.permissions import HAS_PERMISSION_FROM_METHOD
from irhrs.permission.models import HRSPermission
from irhrs.permission.utils.functions import get_permission

# Map permission code and organization specific
PERMISSION_CODES_MAP = SimpleLazyObject(
    func=lambda: dict(HRSPermission.objects.all().values_list('code', 'organization_specific'))
)


class ApplicationSettingsPermissionMixin:

    def check_application_permission(self, request, view):
        if request.user.is_authenticated:
            app_name = (view.__module__.split('.')[1])

            if (app_name, app_name) not in APPLICATION_CHOICES:
                return True
            try:
                organization = view.get_organization()
            except:
                organization = None
            if not organization:
                if not hasattr(request.user, 'detail'):
                    return False
                else:
                    organization = request.user.detail.organization

            queryset = ApplicationSettings.objects.filter(
                organization=organization,
                application=app_name,
            )

            if request.query_params.get('as') == 'hr' and queryset.exists():
                # this condition satisfies whether application is available for HR or not
                # if queryset exists and enabled is true hr has permission else he doesn't
                return queryset.first().enabled

            # if requested user is not hr permission is determined by existence of queryset
            # if queryset exists user doesn't has permission else he has permission
            return not queryset.exists()
        return False


class ApplicationSettingsPermission(ApplicationSettingsPermissionMixin, BasePermission):

    def has_permission(self, request, view):
        return self.check_application_permission(request, view)


class AudituserPermissionMixin:

    def check_audit_user_permission(self, request, view):
        if request.user.is_authenticated:
            try:
                organization = view.get_organization()
            except:
                organization = None
            if not organization:
                return False

            allowed_organizations = request.user.switchable_organizations_pks
            # if request.user.is_audit_user:
            #     return (organization.pk in allowed_organizations and \
            #             request.method in SAFE_METHODS)
        return False


class AuditUserPermission(AudituserPermissionMixin, BasePermission):

    def has_permission(self, request, view):
        return self.check_audit_user_permission(request, view)


class HRSPermissionBase(AudituserPermissionMixin, ApplicationSettingsPermissionMixin,
                        BasePermission):

    def check_method_permission(self, request):
        raise NotImplementedError

    def check_action_permission(self, request, view):
        raise NotImplementedError

    def check_hrs_permission(self, request, view, hrs_permissions_codes: set):
        """ check permissions"""

        # The `get_hrs_permission` for None organization refers to
        # `Common Permission Set` by default.
        if not (request.user and request.user.is_authenticated):
            return False
        hrs_permissions_codes = {
            f"{code.split('.')[0]}.00" for code in hrs_permissions_codes
        }.union(
            hrs_permissions_codes
        )
        request_is_read_only = is_request_read_only()
        if request_is_read_only:
            hrs_permissions_codes = {
                f"{code.split('.')[0]}.99" for code in hrs_permissions_codes
            }.union(
                hrs_permissions_codes
            )
        organization_specific_permissions = {
            perm for perm in hrs_permissions_codes
            if self.is_organization_specific(perm)
        }
        common_permissions = {
            perm for perm in hrs_permissions_codes
            if not self.is_organization_specific(perm)
        }
        matched_organization_permission_codes = set(request.user.get_hrs_permissions(
            getattr(view, "get_organization", lambda: None)()
        )).intersection(
            organization_specific_permissions
        )
        matched_common_permission_codes = set(request.user.get_hrs_permissions(
            None
        )).intersection(
            common_permissions
        )
        matched_permission_codes = matched_common_permission_codes.union(
            matched_organization_permission_codes
        )

        # matching permission codes will be done for org-specific and
        # org-non specific separately

        if not matched_permission_codes:
            # If no matching permissions return False
            return False

        # view can return None to ignore organization checks
        organization = getattr(view, "get_organization", lambda: ...)()
        for permission_code in matched_permission_codes:
            if self.is_organization_specific(permission_code):
                # The permission is organization specific
                # check if organization from view matches switchable
                # organizations
                if organization is not ...:
                    if organization is None or (
                        organization.id in
                        request.user.switchable_organizations_pks):
                        # if organization is None then view is saying allow this
                        # or organization matches
                        return True
                elif organization is ...:
                    logger = logging.getLogger('permission')
                    logger.info(
                        f"method `get_organization` not defined at {view}")
                    return False
                # if not matched check for other permissions
                # by default returns False
            else:
                # If user matches permission which is not permission specific
                # return True
                return True

        return False

    @staticmethod
    def handle_dynamic_permissions(view, dynamic_permissions, from_object=True):
        # While checking method permission from has_object_permission
        # if user does not have object permission `from_object` is `False`
        # so we return `False` as default. While from other sources we return
        # `True` as default.
        permission_from_method = get_permission(HAS_PERMISSION_FROM_METHOD)
        method = getattr(view, "has_user_permission", None)
        if permission_from_method in dynamic_permissions:

            if not method:
                logger = logging.getLogger('permission')
                logger.info(
                    f"method `has_user_permission` not defined at {view}")
                return True

            return method()
        return from_object

    @staticmethod
    def is_organization_specific(code):
        """Check whether permission of given code is organization specific"""
        return PERMISSION_CODES_MAP.get(code, False)
