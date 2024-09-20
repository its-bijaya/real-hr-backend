from rest_framework.fields import SerializerMethodField

from irhrs.appraisal.constants import SELF_APPRAISAL, KSA, NOT_GENERATED, GENERATED, COMPLETED, \
    PA_QUESTION_SET
from irhrs.appraisal.models.key_achievement_and_rating_pa import KAARAppraiserConfig
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils import nested_getattr
from irhrs.users.api.v1.serializers.thin_serializers import UserThickSerializer


class KAARAppraiserSerializer(DynamicFieldsModelSerializer):
    appraiser = UserThickSerializer()
    kaar_appraisal = SerializerMethodField()

    class Meta:
        model = KAARAppraiserConfig
        fields = ('id', 'appraiser', 'appraiser_type', 'question_status', 'kaar_appraisal',
                        'start_date', 'deadline')

    def get_kaar_appraisal(self, instance):
        context_data = {}
        exclude_fields = []
        exclude_question_types = []
        if not nested_getattr(
            instance, 'kaar_appraisal.display_to_appraisee', default=False
        ):
            exclude_fields = ['is_appraisee_satisfied']
            if instance.appraiser_type == SELF_APPRAISAL:
                exclude_fields += ['reviewer_evaluation', 'supervisor_evaluation', 'overall_rating']
                exclude_question_types.append(KSA)
                context_data['score_filter'] = {'appraiser': instance.id}
            elif instance.question_status in [NOT_GENERATED, GENERATED]:
                exclude_question_types.append(KSA)

        if nested_getattr(instance, 'kaar_appraisal.status') != COMPLETED:
            if instance.appraiser_type != SELF_APPRAISAL:
                exclude_question_types.append(PA_QUESTION_SET)
        if exclude_question_types:
            context_data['exclude_filter'] = {'question_type__in': exclude_question_types}
        self.context.update(context_data)
        from irhrs.appraisal.api.v1.serializers.key_achivements_and_rating_pa import \
            KeyAchievementAndRatingAppraisalSerializer
        return KeyAchievementAndRatingAppraisalSerializer(
            instance.kaar_appraisal, context=self.context, exclude_fields=exclude_fields
        ).data
