from rest_framework.fields import SerializerMethodField

from irhrs.appraisal.api.v1.serializers.kpi import ExtendedIndividualKPISerializer
from irhrs.appraisal.api.v1.serializers.questions import PerformanceAppraisalQuestionSerializer
from irhrs.appraisal.models.KAAR_question import KSAOQuestion, KPIQuestion, KRAQuestion, \
    KAARQuestionSet, GenericQuestionSet
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.hris.api.v1.serializers.core_task import UserResultAreaSerializer
from irhrs.users.api.v1.serializers.key_skill_ability import UserKSAOSerializer


class KSAOQuestionSetSerializer(DynamicFieldsModelSerializer):
    ksao = UserKSAOSerializer()
    scores = SerializerMethodField()

    class Meta:
        model = KSAOQuestion
        fields = ('id', 'ksao', 'description',
                  'is_mandatory', 'remarks_required', 'scores')

    def get_scores(self, instance):
        from irhrs.appraisal.api.v1.serializers.KAAR_score import KSAOQuestionScoreSerializer
        # score filter context is passed form KAARAppraiserSerializer
        return KSAOQuestionScoreSerializer(
            instance.ksao_scores.filter(**self.context.get('score_filter', {})),
            fields=['appraiser', 'appraiser_type', 'score', 'remarks', 'grade_score'],
            many=True
        ).data


class KPIQuestionSetSerializer(DynamicFieldsModelSerializer):
    extended_individual_kpi = SerializerMethodField()
    scores = SerializerMethodField()

    class Meta:
        model = KPIQuestion
        fields = ('id', 'extended_individual_kpi', 'description',
                  'scores', 'is_mandatory', 'remarks_required'
                  )

    def get_scores(self, instance):
        from irhrs.appraisal.api.v1.serializers.KAAR_score import KPIQuestionScoreSerializer
        # score filter context is passed form KAARAppraiserSerializer
        return KPIQuestionScoreSerializer(
            instance.kpi_scores.filter(**self.context.get('score_filter', {})).order_by(
                'appraiser__appraiser_type'),
            fields=['key_achievements', 'score', 'appraiser_type', 'appraiser', 'grade_score'],
            many=True
        ).data

    def get_extended_individual_kpi(self, instance):
        return ExtendedIndividualKPISerializer(
            instance.extended_individual_kpi,
            context=self.context
        ).data


class KRAQuestionSetSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = KRAQuestion
        fields = ('id', 'kra', 'description',
                  'is_mandatory', 'remarks_required')

    def get_fields(self):
        fields = super().get_fields()
        fields['kra'] = UserResultAreaSerializer(
            exclude_fields=['core_tasks', 'user_experience'],
            context=self.context)
        return fields


class KAARGenericQuestionSerializer(PerformanceAppraisalQuestionSerializer):
    def get_fields(self):
        fields = super().get_fields()
        fields['scores'] = SerializerMethodField()
        return fields

    def get_scores(self, instance):
        from irhrs.appraisal.api.v1.serializers.KAAR_score import \
            PerformanceAppraisalQuestionScoreSerializer
        return PerformanceAppraisalQuestionScoreSerializer(
            instance.question_scores.filter(
                appraiser__kaar_appraisal=self.context.get('kaar_appraisal')).first()
        ).data


class GenericQuestionSetSerializer(DynamicFieldsModelSerializer):
    generic_question = SerializerMethodField()

    class Meta:
        model = GenericQuestionSet
        fields = ('id', 'generic_question')

    def get_generic_question(self, instance):
        return KAARGenericQuestionSerializer(instance=instance.generic_question, context={**self.context, 'kaar_appraisal': instance.question_set.kaar_appraisal}).data


class KAARQuestionSetSerializer(DynamicFieldsModelSerializer):
    generic_questions = GenericQuestionSetSerializer(many=True)
    annual_rating = SerializerMethodField()

    class Meta:
        model = KAARQuestionSet
        fields = (
            'id', 'name', 'description', 'is_archived', 'question_type', 'annual_rating',
            'ksao_questions', 'kra_questions', 'generic_questions'
        )

    def get_fields(self):
        fields = super().get_fields()
        fields['ksao_questions'] = KSAOQuestionSetSerializer(many=True, context=self.context)
        fields['kpi_questions'] = KPIQuestionSetSerializer(many=True, context=self.context)
        fields['kra_questions'] = KRAQuestionSetSerializer(many=True, context=self.context)

        return fields

    @staticmethod
    def get_annual_rating(instance):
        from irhrs.appraisal.api.v1.serializers.key_achivements_and_rating_pa import \
            AnnualRatingOnCompetenciesSerializer
        return AnnualRatingOnCompetenciesSerializer(instance.annual_rating).data \
            if hasattr(instance, 'annual_rating') else {}
