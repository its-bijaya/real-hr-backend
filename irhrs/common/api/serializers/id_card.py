from irhrs.common.models.id_card import IdCardSample
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer


class IdCardSampleSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = IdCardSample
        fields = ("id", "name", "content", "created_at", "modified_at")
