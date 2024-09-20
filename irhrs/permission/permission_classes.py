from irhrs.permission.utils.factory import PermissionFactory
from .constants.permissions import AUTH_PERMISSION, HAS_PERMISSION_FROM_METHOD

permission_factory = PermissionFactory()

GroupPermission = permission_factory.build_permission(
    "GroupPermission",
    allowed_to=[AUTH_PERMISSION],
    limit_read_to=[
        AUTH_PERMISSION,
        HAS_PERMISSION_FROM_METHOD
    ]
)

FullyDynamicPermission = permission_factory.build_permission(
    "DynamicPermission",
    allowed_to=[HAS_PERMISSION_FROM_METHOD]
)
