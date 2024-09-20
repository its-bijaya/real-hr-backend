"""@irhrs_docs"""
import logging
from functools import reduce
from types import FunctionType

from django.conf import settings
from rest_framework.permissions import SAFE_METHODS
from irhrs.permission.constants.permissions import HAS_OBJECT_PERMISSION
from irhrs.permission.models import HRSPermission
from irhrs.permission.utils.base import HRSPermissionBase
from irhrs.permission.utils.dynamic_permission import DynamicHRSPermission
from irhrs.permission.utils.functions import get_permission


class PermissionFactory:
    description = {}
    object_permission_fields = ['create', 'retrieve', 'update', 'delete']

    def __init__(self,
                 allowed_to=None,
                 limit_read_to=None,
                 limit_write_to=None,
                 limit_edit_to=None,
                 methods=None,
                 actions=None,
                 allowed_user_fields=None,
                 filter_function=None):
        """
        Initialize permission_factory with default permissions.

        These permissions will be used if not passed in build_permission

        :param allowed_to: list of permissions for all methods
        :type allowed_to: list

        :param limit_read_to: list of permissions for safe methods
            [get, options, head]
        :type limit_read_to: list

        :param limit_write_to: list of permissions for create and update
            i.e other methods than safe methods
        :type limit_write_to: list

        :param limit_edit_to: list of permissions fot update methods
        :type limit_edit_to: list

        :param methods: method level permissions
            eg.
            {
                "get": [permission1, permission2, ...],
                "post": [permission1, permission2, ...]
                ...
            }
        :type methods: dict

        :param actions: action level permissions, handy for custom actions
            eg.
            {
                "list": [permission1, permission2, ...],
                "create": [permission1, permission2, ...],
                "update": [permission1, permission2, ...]
            }
        :type actions: dict

        :param allowed_user_fields: field names that determines allowed users
         of object,
            Must be a user.
            eg. For a post, ["poster.user"]
            For comment, ["post.poster.user", "commenter.user"]
        :type allowed_user_fields: list

        :param filter_function: filter function to be applied in get_queryset
        :type filter_function: FunctionType
        """

        self.allowed_to = self.parse_permissions(allowed_to)
        self.limit_read_to = self.parse_permissions(limit_read_to)
        self.limit_write_to = self.parse_permissions(limit_write_to)
        self.limit_edit_to = self.parse_permissions(limit_edit_to)

        if methods:
            assert isinstance(methods, dict)
            methods = {key: self.parse_permissions(value)
                       for key, value in methods.items()}
        self.methods = methods

        if actions:
            assert isinstance(actions, dict)
            actions = {key: self.parse_permissions(value)
                       for key, value in actions.items()}
        self.actions = actions
        self.allowed_user_fields = allowed_user_fields

        if filter_function:
            assert isinstance(filter_function, FunctionType)
        self.filter_function = filter_function

    def build_permission(self, name,
                         allowed_to=None,
                         limit_read_to=None,
                         limit_write_to=None,
                         limit_edit_to=None,
                         methods=None,
                         actions=None,
                         allowed_user_fields=None,
                         filter_function=None):
        """
        # TODO @Ravi: Update documentation as per new implementation.

        Create and return permission class with given configurations
        If nothing passed, default settings passed while creating constructor
        will be used

        :param name: Name of the class
        :type name: str

        :param allowed_to: list of permissions for all methods
        :type allowed_to: list

        :param limit_read_to: list of permissions for safe methods
            [get, options, head]
        :type limit_read_to: list

        :param limit_write_to: list of permissions for create and update
            i.e other methods than safe methods
        :type limit_write_to: list

        :param limit_edit_to: list of permissions fot update methods
        :type limit_edit_to: list

        :param methods: method level permissions
            eg.
            {
                "get": [permission1, permission2, ...],
                "post": [permission1, permission2, ...]
                ...
            }
        :type methods: dict

        :param actions: action level permissions, handy for custom actions
            eg.
            {
                "list": [permission1, permission2, ...],
                "create": [permission1, permission2, ...],
                "update": [permission1, permission2, ...]
            }
        :type actions: dict

        :param allowed_user_fields: field name that determines owner of object,
            ** Not yet tested **
            Must be a user.
            eg. For a post, ["poster.user"]
            For comment, ["post.poster.user", "commenter.user"]
        :type allowed_user_fields: list

        :param filter_function: filter function to be applied in get_queryset
        :type filter_function: FunctionType
        """
        # parse arguments and get valid permission instances take argument from
        # permission_factory instance if not passed as argument

        """
            This will add a description field in every
            `view.permission_classes`. Using,
            `view.permission_classes[0]description` will generate something
            like this:

            OrganizationViewSet:
                PermissionClass1:
                    r: [ Can view edit/organization settings],  // read
                    w: [ Can view edit/organization settings],  // write
                    w+: [ Can view edit/organization settings], // edit
                    rw: [ Can view edit/organization settings], // all
                PermissionClass2:
                    r: [ Can view edit/organization settings],  // read
                    w: [ Can view edit/organization settings],  // write
                    w+: [ Can view edit/organization settings], // edit
                    rw: [ Can view edit/organization settings], // all

        """
        self.description = {
            'r': {},
            'w': {},
            'rw': {},
            'e': {},
        }
        if allowed_to:
            self.description['rw'] = allowed_to
        if limit_read_to:
            self.description['r'] = limit_read_to
        if limit_write_to:
            self.description['w'] = limit_write_to
        if limit_edit_to:
            self.description['e'] = limit_edit_to

        allowed_to = self.parse_permissions(allowed_to) or self.allowed_to
        limit_read_to = self.parse_permissions(limit_read_to) or \
                        self.limit_read_to
        limit_write_to = self.parse_permissions(limit_write_to) or \
                         self.limit_write_to
        limit_edit_to = self.parse_permissions(limit_edit_to) or \
                        self.limit_edit_to

        if methods:
            assert isinstance(methods, dict)
            methods = {key: self.parse_permissions(value)
                       for key, value in methods.items()}
        methods = methods or self.methods

        if actions:
            assert isinstance(actions, dict)
            actions = {key: self.parse_permissions(value)
                       for key, value in actions.items()}
        actions = actions or self.actions

        allowed_user_fields = allowed_user_fields or self.allowed_user_fields

        methods = self.get_methods(
            allowed_to, limit_read_to, limit_write_to, limit_edit_to, methods)

        if filter_function:
            assert isinstance(filter_function, FunctionType)
        filter_function = filter_function or self.filter_function

        attrs = {
            "has_permission": self.get_has_permission(),
            "check_method_permission": self.get_check_method_permission(
                methods),
            "has_object_permission": self.get_has_object_permission(
                methods,
                action_permissions=actions,
                allowed_user_fields=allowed_user_fields),
            "check_action_permission": self.get_check_action_permission(actions)
        }

        if filter_function:
            attrs.update({
                'filter_queryset': filter_function
            })
        attrs.update({
            'description': self.description
        })
        return type(str(name), (HRSPermissionBase,), attrs)

    @staticmethod
    def get_methods(allowed_to, limit_read_to,
                    limit_write_to, limit_edit_to, methods):
        """
        Parse other parameters and return method level permissions
        if methods is set, it will replace others.
        """
        http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head',
                             'options', 'trace']
        safe_methods = {method.lower() for method in SAFE_METHODS}
        writable_methods = set(http_method_names) - safe_methods
        permission_methods = {}

        if allowed_to:
            for method in http_method_names:
                permission_methods.update({method: allowed_to})

        if limit_read_to:
            for method in safe_methods:
                permission_methods.update({method: limit_read_to})

        if limit_write_to:
            for method in writable_methods:
                permission_methods.update({method: limit_write_to})

        if limit_edit_to:
            edit_methods = writable_methods - {'post'}
            for method in edit_methods:
                permission_methods.update({method: limit_edit_to})

        if methods:
            permission_methods.update(methods)

        return permission_methods

    @staticmethod
    def parse_permissions(permissions):
        """
        Parse permissions (string or objects) and return permission objects
        """
        valid_permissions = []
        if not permissions:
            return None
        if permissions and not isinstance(permissions, list):
            permissions = [permissions]

        for permission in permissions:
            if isinstance(permission, HRSPermission):
                valid_permissions.append(permission)
            else:
                valid_permissions.append(get_permission(permission))
        return valid_permissions

    @staticmethod
    def get_has_permission():
        """Build and return has_permission method for permission"""

        def has_permission(self, request, view):
            if hasattr(view, 'action'):
                return request.user and request.user.is_authenticated and \
                       (self.check_audit_user_permission(request, view) or \
                       (self.check_method_permission(request, view) and \
                       self.check_action_permission(request, view) and \
                       self.check_application_permission(request, view)))
            return request.user and request.user.is_authenticated and \
                   (self.check_audit_user_permission(request, view) or \
                   (self.check_method_permission(request, view) and \
                   self.check_application_permission(request, view)))



        return has_permission

    @staticmethod
    def get_check_method_permission(methods):
        """build and return check_method_permission method
         which will be called from has_permission"""

        def check_method_permission(self, request, view):
            permissions = methods.get(request.method.lower(), None)
            if permissions:
                hrs_permissions_code = {permission.code for permission in
                                        permissions
                                        if
                                        isinstance(permission, HRSPermission)}
                dynamic_permissions = {
                    permission for permission in permissions
                    if isinstance(permission, DynamicHRSPermission)}

                has_hrs_permission = self.check_hrs_permission(
                    request, view,
                    hrs_permissions_code
                )

                if has_hrs_permission:
                    return has_hrs_permission

                if dynamic_permissions:
                    return self.handle_dynamic_permissions(view,
                                                           dynamic_permissions)
                return has_hrs_permission
            return True

        return check_method_permission

    @staticmethod
    def get_check_action_permission(actions):
        """
        Build check_action_permission method that checks permissions for
        action.
        If action is None it will return True for all actions
        """
        if actions:
            def check_action_permission(self, request, view):
                permissions = actions.get(view.action, None)
                if permissions:
                    hrs_permissions_code = {permission.code for permission in
                                            permissions
                                            if isinstance(permission,
                                                          HRSPermission)}
                    dynamic_permissions = {
                        permission for permission in permissions
                        if isinstance(permission, DynamicHRSPermission)}

                    has_hrs_permission = self.check_hrs_permission(
                        request, view, hrs_permissions_code
                    )

                    if has_hrs_permission:
                        return True

                    if dynamic_permissions:
                        return self.handle_dynamic_permissions(
                            view, dynamic_permissions)

                    return has_hrs_permission
                return True

            return check_action_permission
        else:
            # return method that returns True if there is no action
            return lambda x, y, z: True

    @staticmethod
    def get_has_object_permission(
            method_permissions,
            allowed_user_fields,
            action_permissions,
    ):
        """
        Build has_object permission method for permission class and return it
        """

        def has_object_permission(self, request, view, obj):
            permissions = method_permissions.get(request.method.lower())
            if action_permissions:
                # override permissions by action permission of has one
                permissions = action_permissions.get(view.action)
            if permissions:
                hrs_permissions_codes = {permission.code for permission in
                                         permissions
                                         if
                                         isinstance(permission, HRSPermission)}
                dynamic_permissions = {
                    permission for permission in permissions
                    if isinstance(permission, DynamicHRSPermission)}

                if (get_permission(HAS_OBJECT_PERMISSION) in
                    dynamic_permissions) and \
                        allowed_user_fields:
                    # Check OBJECT PERMISSION field so ...
                    # check for fields, if user matched allow
                    for field_name in allowed_user_fields:
                        try:
                            attribute = reduce(
                                lambda ob, attr: getattr(ob, attr),
                                [obj] + str(field_name).split('.'))
                            if request.user and request.user.is_authenticated \
                              and \
                                    attribute == request.user:
                                return True

                        except AttributeError:
                            logging.getLogger('permission')
                            logging.debug("Attribute not found", exc_info=True)

                if hrs_permissions_codes:
                    has_hrs_permission = self.check_hrs_permission(
                        request, view, hrs_permissions_codes
                    )
                    if has_hrs_permission:
                        return True

                # if dynamic permissions is set but yet not returned true then
                # return false
                if dynamic_permissions:
                    return self.handle_dynamic_permissions(
                        view, dynamic_permissions, from_object=False)
            return True

        return has_object_permission
