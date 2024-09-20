"""@irhrs_docs"""
from irhrs.permission.constants.permissions import HAS_OBJECT_PERMISSION, \
    HAS_PERMISSION_FROM_METHOD
from irhrs.permission.models import HRSPermission
from irhrs.permission.utils.dynamic_permission import DynamicHRSPermission


def get_permission(data):
    """convert permission name to permission objects"""
    permission_code = data.get("code")
    permission_name = data.get("name")

    if data not in [HAS_OBJECT_PERMISSION, HAS_PERMISSION_FROM_METHOD]:
        try:
            # if permission_code is passed given use code
            if permission_code:
                return HRSPermission.objects.get(code=permission_code)
            else:
                return HRSPermission.objects.get(name=permission_name)
        except:
            # During initial migration, when tables are not created then an
            # error will be raised so, to handle that return DynamicPermission
            # for this time
            return HRSPermission(name=permission_name, code=permission_code)
    else:
        return DynamicHRSPermission(permission_name, permission_code)
