from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.relations import PrimaryKeyRelatedField

from irhrs.appraisal.api.v1.serializers.KAAR_question import KAARQuestionSetSerializer
from irhrs.appraisal.api.v1.serializers.kaar_appraiser import KAARAppraiserSerializer
from irhrs.appraisal.api.v1.serializers.kaar_serializer_mixin import KAARBaseMixin
from irhrs.appraisal.constants import COMPLETED, GRADE, \
    RANGE, KPI, SUBMITTED, SELF_APPRAISAL
from irhrs.appraisal.models.KAAR_question import KAARQuestionSet
from irhrs.appraisal.models.KAAR_score import AnnualRatingOnCompetencies
from irhrs.appraisal.models.key_achievement_and_rating_pa import \
    KeyAchievementAndRatingAppraisal, KAARAppraiserConfig, ReviewerEvaluation, \
    SupervisorEvaluation
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.users.api.v1.serializers.thin_serializers import UserThickSerializer


class ValidateOverallRating(KAARBaseMixin):
    def validate_range_score(self, question_type, value):
        if not isinstance(value, (int, float)):
            raise ValidationError({
                f'{question_type}_score': f'{question_type} score should be Number.'}
            )
        if not 0 < value < 100:
            raise ValidationError({
                f'{question_type}_score': f'Score should be in between 0 and 100.'
            })

    def validate_scores(self, question_type, value):
        if value is None:
            return
        self.question_type = question_type
        scale_type = self.get_scale_config().scale_type
        if scale_type == GRADE:
            self.validate_grade_score_(value)
        elif scale_type == RANGE:
            self.validate_range_score(question_type, value)
        else:
            self.validate_default_score(value)

    def validate_kpi_score(self, value):
        self.validate_scores(KPI, value)

    def validate_ksao_score(self, value):
        self.validate_scores('ksao', value)


class EvaluationBaseSerializer(DynamicFieldsModelSerializer):
    # appraiser is oneToOne field in model
    # so to bypass unique validator in appraiser field we have added PrimaryKeyRelatedField only
    appraiser = PrimaryKeyRelatedField(queryset=KAARAppraiserConfig.objects.all())


def validate_question_status_and_kaar_appraisal_status(appraiser_config: KAARAppraiserConfig):
    if appraiser_config.kaar_appraisal.status == COMPLETED:
        raise ValidationError({'error': "Can't submit, Appraisal cycle is completed."})
    if appraiser_config.question_status == SUBMITTED:
        raise ValidationError({'error': "Can't submit submitted question set."})


class ReviewerEvaluationSerializer(EvaluationBaseSerializer):
    class Meta:
        model = ReviewerEvaluation
        fields = ('id', 'appraiser', 'agree_with_appraiser', 'remarks')

    @transaction.atomic
    def create(self, validated_data):
        instance = super().create(validated_data)
        self.forward_or_resend_appraisal_question(instance)
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        self.forward_or_resend_appraisal_question(instance)
        return instance

    def validate(self, attrs):
        attrs = super().validate(attrs)
        remarks = attrs.get('remarks')
        if not remarks:
            raise ValidationError("Reviewer's remarks field is required.")
        appraiser = getattr(self.instance, 'appraiser', None) or attrs.get('appraiser')
        validate_question_status_and_kaar_appraisal_status(appraiser)
        return attrs

    def forward_or_resend_appraisal_question(self, instance):
        from irhrs.appraisal.utils.kaar_appraisal import ForwardAppraisalQuestions, ResendToAppraiser
        appraiser_config = instance.appraiser
        appraiser_config.question_status = SUBMITTED
        appraiser_config.save()
        if instance.agree_with_appraiser:
            forward = ForwardAppraisalQuestions(
                instance.appraiser,
                self.context.get('sub_performance_appraisal_slot'),
                self.request.user
            )
            forward.send_question_to_next_appraiser()
            forward.send_notification_to_appraiser()
            forward.complete_kaar_appraisal()
        else:
            resend = ResendToAppraiser(instance.appraiser.kaar_appraisal, self.request.user)
            resend.resend_to_supervisor()


class SupervisorEvaluationSerializer(ValidateOverallRating, DynamicFieldsModelSerializer):

    class Meta:
        model = SupervisorEvaluation
        fields = ('id', 'appraiser', 'set_default_rating', 'remarks')

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.upper() in ['PATCH', 'POST']:
            fields['overall_rating'] = serializers.JSONField(required=False)
            fields['answer_committed'] = serializers.BooleanField(write_only=True)
        return fields

    @transaction.atomic
    def create(self, validated_data):
        overall_rating = validated_data.pop('overall_rating', None)
        answer_committed = validated_data.pop('answer_committed', False)
        instance = super().create(validated_data)
        if overall_rating:
            self.set_overall_rating(instance.appraiser, overall_rating)
        if answer_committed:
            self.forward_question_set(instance.appraiser)
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        overall_rating = validated_data.pop('overall_rating', None)
        answer_committed = validated_data.pop('answer_committed', False)
        updated_instance = super().update(instance, validated_data)
        if overall_rating:
            self.set_overall_rating(updated_instance.appraiser, overall_rating)
        if answer_committed:
            self.forward_question_set(instance.appraiser)

        return updated_instance

    def validate(self, attrs):
        attrs = super().validate(attrs)
        overall_rating = attrs.get('overall_rating')
        appraiser_config = attrs.get('appraiser') or getattr(self.instance, 'appraiser', None)
        validate_question_status_and_kaar_appraisal_status(appraiser_config)
        if overall_rating:
            kpi_score = overall_rating.get('kpi_score')
            ksao_score = overall_rating.get('ksao_score')
            if not all(value in overall_rating for value in ['kpi_score', 'ksao_score']):
                raise ValidationError({'error': 'KPI/KSA score are required.'})
            self.validate_kpi_score(kpi_score)
            self.validate_ksao_score(ksao_score)
        return attrs

    @staticmethod
    def set_overall_rating(appraiser_config: KAARAppraiserConfig, overall_rating):
        kaar_appraisal = appraiser_config.kaar_appraisal
        kaar_appraisal.overall_rating = overall_rating
        kaar_appraisal.save()

    def forward_question_set(self, appraiser_config):
        from irhrs.appraisal.utils.kaar_appraisal import ForwardAppraisalQuestions
        appraiser_config.question_status = SUBMITTED
        appraiser_config.save()
        forward_question = ForwardAppraisalQuestions(
            appraiser_config, self.sub_performance_appraisal_slot, self.request.user
        )
        forward_question.send_question_to_next_appraiser()
        forward_question.send_notification_to_appraiser()
        forward_question.complete_kaar_appraisal()

    def set_kaar_default_score(self, instance):
        from irhrs.appraisal.utils.kaar_appraisal import setDefaultScoreForAppraisal
        if instance.set_default_rating:
            obj = setDefaultScoreForAppraisal(instance.appraiser, self.sub_performance_appraisal_slot)
            obj.set_default_score()


class AnnualRatingOnCompetenciesSerializer(DynamicFieldsModelSerializer):
    question_set = PrimaryKeyRelatedField(queryset=KAARQuestionSet.objects.all())

    class Meta:
        model = AnnualRatingOnCompetencies
        fields = ('id', 'kaar_appraisal', 'question_set', 'final_score')


class KeyAchievementAndRatingAppraisalSerializer(DynamicFieldsModelSerializer):
    appraisee = UserThickSerializer()
    question_set = SerializerMethodField()
    reviewer_evaluation = SerializerMethodField()
    supervisor_evaluation = SerializerMethodField()
    instruction_for_evaluator = serializers.ReadOnlyField(
        source='sub_performance_appraisal_slot.kaar_form_design.instruction_for_evaluator'
    )
    appraiser_configs = serializers.SerializerMethodField()

    class Meta:
        model = KeyAchievementAndRatingAppraisal
        fields = ('id', 'sub_performance_appraisal_slot', 'total_score', 'status',
                  'reviewer_evaluation', 'supervisor_evaluation',  'appraisee', 'overall_rating',
                  'question_set', 'instruction_for_evaluator', 'display_to_appraisee',
                  'is_appraisee_satisfied', 'appraiser_configs'
                  )

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.upper() == 'GET':
            fields['overall_rating'] = SerializerMethodField()
            fields['self_appraiser_score'] = SerializerMethodField()
        return fields

    def get_question_set(self, instance):
        exclude_filter = self.context.get('exclude_filter', {})
        if instance.status == COMPLETED:
            exclude_filter = {}
        return KAARQuestionSetSerializer(
            instance.question_set.exclude(**exclude_filter),
            many=True, context=self.context
        ).data

    def get_appraiser_configs(self, instance):
        return KAARAppraiserSerializer(instance=instance.appraiser_configs.exclude(
            appraiser_type=SELF_APPRAISAL).order_by('-appraiser_type'), many=True,
            fields=['appraiser', 'appraiser_type'], context=self.context
        ).data

    def get_self_appraiser_score(self, instance):
        from irhrs.appraisal.utils.kaar_appraisal import CalculateKpiScore
        self_appraiser = instance.appraiser_configs.filter(appraiser=instance.appraisee).first()
        if not self_appraiser:
            return 0
        calc_score = CalculateKpiScore(instance)
        return calc_score.calculate_self_appraiser_score(self_appraiser)

    @staticmethod
    def get_reviewer_evaluation(instance):
        appraiser_ids = instance.appraiser_configs.values_list('reviewer_evaluation', flat=True)
        return ReviewerEvaluationSerializer(
            ReviewerEvaluation.objects.filter(id__in=appraiser_ids).first()
        ).data

    @staticmethod
    def get_supervisor_evaluation(instance):
        appraiser_ids = instance.appraiser_configs.values_list('supervisor_evaluation', flat=True)
        return SupervisorEvaluationSerializer(
            SupervisorEvaluation.objects.filter(id__in=appraiser_ids).first()
        ).data

    @staticmethod
    def get_overall_rating(instance):
        if not instance.overall_rating:
            return {'kpi_score': None, 'ksao_score': None}
        return instance.overall_rating




