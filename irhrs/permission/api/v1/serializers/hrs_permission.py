from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.permission.models import HRSPermission


class HRSPermissionSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = HRSPermission
        fields = (
            'id', 'name', 'code', 'description', 'organization_specific',
            'category',
        )
