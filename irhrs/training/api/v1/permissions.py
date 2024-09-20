from irhrs.permission.constants.permissions import TRAINING_CREATE_PERMISSION
from irhrs.permission.permission_classes import permission_factory

TrainingPermission = permission_factory.build_permission(
    'TrainingPermission',
    allowed_to=[TRAINING_CREATE_PERMISSION]
)
