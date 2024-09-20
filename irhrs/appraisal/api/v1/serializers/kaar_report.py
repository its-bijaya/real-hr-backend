from rest_framework.fields import SerializerMethodField

from irhrs.appraisal.api.v1.serializers.form_design import get_appraiser_config_id
from irhrs.appraisal.api.v1.serializers.kaar_appraiser import KAARAppraiserSerializer
from irhrs.appraisal.constants import SELF_APPRAISAL
from irhrs.appraisal.models.key_achievement_and_rating_pa import KeyAchievementAndRatingAppraisal
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.users.api.v1.serializers.thin_serializers import UserThickSerializer


class KeyAchievementAndRatingAppraisalReportSerializer(DynamicFieldsModelSerializer):
    appraisee = UserThickSerializer()
    self_appraiser_config = SerializerMethodField()
    appraiser_configs = SerializerMethodField()

    class Meta:
        model = KeyAchievementAndRatingAppraisal
        fields = ('id', 'sub_performance_appraisal_slot', 'total_score', 'status',  'appraisee',
                  'overall_rating', 'is_appraisee_satisfied', 'self_appraiser_config', 'appraiser_configs'
                  )

    def get_fields(self):
        fields = super().get_fields()
        if self.context.get('action') == 'export':
            fields['is_appraisee_satisfied'] = SerializerMethodField()
        return fields

    @staticmethod
    def get_is_appraisee_satisfied(instance):
        if instance.is_appraisee_satisfied is None:
            return None
        return str(instance.is_appraisee_satisfied)

    @staticmethod
    def get_self_appraiser_config(obj):
        return get_appraiser_config_id(obj, SELF_APPRAISAL)

    def get_appraiser_configs(self, instance):
        return KAARAppraiserSerializer(instance=instance.appraiser_configs.exclude(
            appraiser_type=SELF_APPRAISAL).order_by('-appraiser_type'), many=True,
                                       fields=['appraiser', 'appraiser_type'], context=self.context
                                       ).data
