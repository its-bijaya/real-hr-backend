from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.noticeboard.models.noticeboard_setting import NoticeBoardSetting

class NoticeBoardSettingSerializer(DynamicFieldsModelSerializer):
    """
    Serializer for NoticeBoardSetting.
    """

    class Meta:
        model = NoticeBoardSetting
        fields = ('created_at', 'modified_at',
                  'allow_to_post', 'need_approval')

    def create(self, validated_data):
        instance = NoticeBoardSetting.objects.first()
        if instance:
            instance.allow_to_post = validated_data.get('allow_to_post')
            instance.need_approval = validated_data.get('need_approval')
            instance.save()
        else:
            instance = NoticeBoardSetting.objects.create(**validated_data)
        return instance

