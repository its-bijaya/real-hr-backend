from irhrs.permission.constants.permissions import NOTICE_BOARD_PERMISSION, \
    HAS_OBJECT_PERMISSION, HAS_PERMISSION_FROM_METHOD
from irhrs.permission.permission_classes import permission_factory

PostPermission = permission_factory.build_permission(
    "PostPermission",
    methods={
        'get': [HAS_PERMISSION_FROM_METHOD],
        'put': [HAS_OBJECT_PERMISSION],
        'patch': [HAS_PERMISSION_FROM_METHOD],
        'delete': [NOTICE_BOARD_PERMISSION, HAS_OBJECT_PERMISSION,
                   HAS_PERMISSION_FROM_METHOD],
        'post':[HAS_PERMISSION_FROM_METHOD]
    },
    actions={
        'status_change':[NOTICE_BOARD_PERMISSION]
    },
    allowed_user_fields=["posted_by"]
)

CommentPermission = permission_factory.build_permission(
    "CommentPermission",
    methods={
        'get': [HAS_PERMISSION_FROM_METHOD],
        'put': [HAS_OBJECT_PERMISSION],
        'patch': [HAS_OBJECT_PERMISSION],
        'delete': [NOTICE_BOARD_PERMISSION, HAS_PERMISSION_FROM_METHOD]
    },
    allowed_user_fields=["commented_by"]
)

LikePermission = permission_factory.build_permission(
    "LikePermission",
    methods={
        'get': [HAS_PERMISSION_FROM_METHOD],
    }
)

CommentReplyPermission = permission_factory.build_permission(
    "CommentReplyPermission",
    methods={
        'get': [HAS_PERMISSION_FROM_METHOD],
        'put': [HAS_OBJECT_PERMISSION],
        'patch': [HAS_OBJECT_PERMISSION],
        'delete': [NOTICE_BOARD_PERMISSION, HAS_OBJECT_PERMISSION,
                   HAS_PERMISSION_FROM_METHOD]
    },
    allowed_user_fields=["reply_by"]
)

CommentLikePermission = permission_factory.build_permission(
    "CommentLikePermission",
    methods={
        'get': [HAS_PERMISSION_FROM_METHOD],
    }
)
