from rest_framework.permissions import BasePermission

from irhrs.permission.constants.groups import ADMIN


class AdminPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.groups.filter(name=ADMIN).exists()


def admin_permission(view_class):
    class DecoratedView(view_class):
        permission_classes = [AdminPermission]

    return DecoratedView
