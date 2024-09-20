from django.core.validators import MinValueValidator
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField

from config import settings
from irhrs.appraisal.api.v1.serializers.KAAR_question import KRAQuestionSetSerializer, \
    KPIQuestionSetSerializer, KSAOQuestionSetSerializer
from irhrs.appraisal.api.v1.serializers.kaar_serializer_mixin import KAARBaseMixin, \
    KAARScoreSerializerMixin
from irhrs.appraisal.api.v1.serializers.key_achivements_and_rating_pa import \
    ReviewerEvaluationSerializer, \
    AnnualRatingOnCompetenciesSerializer
from irhrs.appraisal.api.v1.serializers.question_set import ValidateQuestionSerializer
from irhrs.appraisal.constants import SELF_APPRAISAL, SUPERVISOR_APPRAISAL, REVIEWER_EVALUATION, \
    SUBMITTED, RANGE, GRADE, KPI, KSA, COMPLETED
from irhrs.appraisal.models.KAAR_score import KPIQuestionScore, KRAQuestionScore, \
    PerformanceAppraisalQuestionScore, KSAOQuestionScore, ScoreAndScalingConfig, \
    KAARScaleAndScoreSetting, RangeScore, GradeAndDefaultScaling, AnnualRatingOnCompetencies, \
    DefaultScoreSetting
from irhrs.appraisal.models.key_achievement_and_rating_pa import ReviewerEvaluation
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils import nested_getattr
from irhrs.core.utils.common import DummyObject
from irhrs.questionnaire.models.helpers import RATING_SCALE


class RangeScoreSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = RangeScore
        fields = ('id', 'score_config', 'start_range', 'end_range')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs.get('start_range') >= attrs.get('end_range'):
            raise ValidationError({"error": "start range must be less than end range."})
        return attrs


class GradeAndDefaultScalingSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = GradeAndDefaultScaling
        fields = ['id', 'score_config', 'name', 'score']


class ScoreAndScalingConfigSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = ScoreAndScalingConfig
        fields = ('id', 'sub_performance_appraisal_slot', 'scale_type', 'title')

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.upper() == 'GET':
            fields['scores'] = SerializerMethodField()
        return fields

    def validate(self, attrs):
        attrs = super().validate(attrs)
        scale_type = attrs.get('scale_type')
        if self.instance and self.instance.scale_type != scale_type:
            raise ValidationError({'scale_type': f'Can not change scale type.'})
        elif not self.instance and ScoreAndScalingConfig.objects.filter(
                sub_performance_appraisal_slot=attrs.get('sub_performance_appraisal_slot'),
                scale_type=scale_type).exists():
            raise ValidationError({'scale_type': f'scale type {scale_type} already exists.'})
        return attrs

    @staticmethod
    def get_scores(instance):
        if instance.scale_type == RANGE:
            return RangeScoreSerializer(getattr(instance, 'range_score', None)).data
        return GradeAndDefaultScalingSerializer(
            instance.grade_and_default_scales.all(), many=True
        ).data


class KAARScaleAndScoreSettingSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = KAARScaleAndScoreSetting
        fields = ('id', 'sub_performance_appraisal_slot', 'kpi', 'ksao', 'question_set')

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.upper() == 'GET':
            fields['kpi'] = ScoreAndScalingConfigSerializer(context=self.context)
            fields['ksao'] = ScoreAndScalingConfigSerializer(context=self.context)
            fields['question_set'] = ScoreAndScalingConfigSerializer(context=self.context)
        return fields


class DefaultScoreSettingSerializer(KAARBaseMixin, DynamicFieldsModelSerializer):
    class Meta:
        model = DefaultScoreSetting
        fields = ['id', 'sub_performance_appraisal_slot', 'question_type', 'score', 'grade_score']

    def validate(self, attrs):
        attrs = super().validate(attrs)
        question_type = attrs.get('question_type')
        question_type_mapper = {
            'kpi': 'kpi',
            'ksa': 'ksao'
        }
        if question_type not in [KPI, KSA]:
            raise ValidationError({'error': f"Can't assign {question_type}."})

        self.question_type = question_type_mapper.get(question_type) or question_type
        sub_performance_appraisal_slot = attrs.get('sub_performance_appraisal_slot')

        if not (self.instance and self.instance.question_type == question_type) and \
                sub_performance_appraisal_slot.default_scores.filter(
                    question_type=question_type).exists():
            raise ValidationError({'question_type': f'{question_type} already exists.'})

        score = attrs.get('score')
        grade_score = attrs.get('grade_score')

        if all((score, grade_score)):
            raise ValidationError("Can't assign score and grade score.")
        if not any((score, grade_score)):
            raise ValidationError("Please assign score first.")

        scale_config = self.get_scale_config()

        if scale_config.scale_type == RANGE:
            if grade_score:
                raise ValidationError({'grade_score': "Can't assign score in grade."})
        elif scale_config.scale_type == GRADE:
            if score:
                raise ValidationError({'grade_score': "Can't assign score in grade."})
            self.validate_grade_score_(grade_score)
        else:
            if grade_score:
                raise ValidationError({'grade_score': "Can't assign score in grade."})
            self.validate_default_score(score)
        return attrs


class KPIQuestionScoreSerializer(KAARScoreSerializerMixin):
    appraiser_type = serializers.ReadOnlyField(source='appraiser.appraiser_type')
    question_type = 'kpi'

    class Meta:
        model = KPIQuestionScore
        fields = ('question', 'appraiser', 'appraiser_type',
                  'key_achievements', 'score', 'grade_score')

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.upper() == 'GET':
            fields['question'] = KPIQuestionSetSerializer()
        return fields

    def validate(self, attrs):
        attrs = super().validate(attrs)
        appraiser = attrs.get('appraiser')
        if appraiser.appraiser_type == SELF_APPRAISAL and not attrs.get('key_achievements'):
            raise ValidationError({'key_achievements': 'Key achievements are required.'})
        return attrs


class KRAQuestionScoreSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = KRAQuestionScore
        fields = ('question', 'appraiser', 'score', 'remarks')

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.upper() == 'GET':
            fields['question'] = KRAQuestionSetSerializer()
        return fields


class KSAOQuestionScoreSerializer(KAARScoreSerializerMixin):
    question_type = 'ksao'
    appraiser_type = serializers.ReadOnlyField(source='appraiser.appraiser_type')

    class Meta:
        model = KSAOQuestionScore
        fields = ['question', 'appraiser', 'score', 'grade_score', 'remarks', 'appraiser_type']

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.upper() == 'GET':
            fields['question'] = KSAOQuestionSetSerializer()
        return fields


class validateQuestionScoreSerializer(KAARBaseMixin, ValidateQuestionSerializer):
    question_type = "question_set"

    id = serializers.IntegerField(allow_null=True, required=False)
    order = serializers.IntegerField(allow_null=True, required=False)
    temp_score = serializers.IntegerField(validators=[MinValueValidator(0)], default=0)
    remarks = serializers.CharField(
        max_length=settings.TEXT_FIELD_MAX_LENGTH,
        allow_null=True, allow_blank=True,
        required=False
    )
    display_type = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    extra_data = serializers.JSONField(
        required=False,
        allow_null=True
    )
    rating_scale = serializers.IntegerField(required=False, allow_null=True)
    remarks_required = serializers.BooleanField(required=False)

    def get_fields(self):
        fields = super().get_fields()
        if self.get_scale_config().scale_type == GRADE:
            fields['temp_score'] = serializers.CharField(max_length=255,required=False)
            fields['score'] = serializers.CharField(max_length=255, required=False)
        elif self.get_scale_config().scale_type == RANGE:
            fields['temp_score'] = serializers.FloatField(validators=[MinValueValidator(0)], default=0)
            fields['score'] = serializers.FloatField(validators=[MinValueValidator(0)], default=0)

        return fields

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs.get('answer_choices') == RATING_SCALE:
            score = attrs.get('score')
            scale_config = self.get_scale_config()
            if scale_config.scale_type == RANGE:
                self.validate_range_score(score)
            elif scale_config.scale_type == GRADE:
                self.validate_grade_score_(score)
            else:
                self.validate_default_score(score)
        return attrs


class PerformanceAppraisalQuestionScoreSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = PerformanceAppraisalQuestionScore
        fields = ('question', 'appraiser', 'data')

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.upper() == "POST":
            fields['data'] = validateQuestionScoreSerializer(context=self.context)
        return fields


class KAARScoreSerializer(serializers.Serializer):
    pa_question_score = PerformanceAppraisalQuestionScoreSerializer(many=True, required=False)
    reviewer_evaluation = ReviewerEvaluationSerializer(required=False)
    kpi_question_score = KPIQuestionScoreSerializer(required=False, many=True)
    ksao_question_score = KSAOQuestionScoreSerializer(required=False, many=True)
    annual_rating = AnnualRatingOnCompetenciesSerializer(required=False, many=True)
    is_appraisee_satisfied = serializers.BooleanField(required=False)

    def create(self, validated_data):
        function_mapper = {
            'kpi_question_score': KPIQuestionScore,
            'ksao_question_score': KSAOQuestionScore,
            'pa_question_score': PerformanceAppraisalQuestionScore,
        }
        extra_function_mapper = {
            'annual_rating': self.assign_annual_rating,
            'is_appraisee_satisfied': self.set_appraisee_satisfied_or_not

        }
        for key, val in validated_data.items():
            if not isinstance(val, bool) and not val:
                continue
            if key == 'reviewer_evaluation':
                ReviewerEvaluation.objects.update_or_create(
                    appraiser=val.pop('appraiser'),
                    defaults=val
                )
                continue
            elif key in extra_function_mapper:
                extra_function_mapper.get(key)(val)
                continue
            self.create_scores(function_mapper.get(key), val)
        return DummyObject(**validated_data)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        appraiser_type = self.appraiser_config.appraiser_type
        if self.appraiser_config.kaar_appraisal.status == COMPLETED:
            raise ValidationError({'error': "Can't submit, Appraisal cycle is completed."})
        if self.appraiser_config.question_status == SUBMITTED and appraiser_type != SELF_APPRAISAL:
            raise ValidationError({'error': "Can't submit submitted question set."})

        validate_function_mapper = {
            SELF_APPRAISAL: self.validation_for_self_appraiser,
            SUPERVISOR_APPRAISAL: self.validation_for_supervisor,
            REVIEWER_EVALUATION: self.validation_for_reviewer
        }

        validate_function_mapper.get(appraiser_type)(attrs)
        return attrs

    @staticmethod
    def create_scores(klass, scores):
        for score in scores:
            klass.objects.update_or_create(
                question=score.pop('question'),
                appraiser=score.pop('appraiser'),
                defaults=score
            )

    @staticmethod
    def assign_annual_rating(val):
        for rating in val:
            AnnualRatingOnCompetencies.objects.update_or_create(
                question_set=rating.pop('question_set'),
                kaar_appraisal=rating.pop('kaar_appraisal'),
                defaults=rating
            )

    def set_appraisee_satisfied_or_not(self, val: bool):
        kaar_appraisal = self.appraiser_config.kaar_appraisal
        kaar_appraisal.is_appraisee_satisfied = val
        kaar_appraisal.save()

    def validate_kpi_question_score(self, value):
        if self.appraiser_config.question_status == SUBMITTED:
            raise ValidationError({'error': "Can't assign kpi score."})
        return value

    def validate_is_appraisee_satisfied(self, value):
        if self.appraiser_config.appraiser_type != SELF_APPRAISAL:
            raise ValidationError("Only appraisee can send this form.")
        if not self.appraiser_config.kaar_appraisal.display_to_appraisee:
            raise ValidationError("You can't submit your review.")
        return value

    def validation_for_self_appraiser(self, attrs):
        if self.appraiser_config.kaar_appraisal.display_to_appraisee:
            if not attrs.get('pa_question_score'):
                raise ValidationError({'PA Question set Score are Required.'})
            if attrs.get('is_appraisee_satisfied') is None:
                raise ValidationError('Are you satisfied with review.')
        else:
            if self.appraiser_config.question_status == SUBMITTED:
                raise ValidationError("Can't submit submitted question set.")
            if not attrs.get('kpi_question_score'):
                raise ValidationError('KPI Question Score are Required.')

    def validation_for_supervisor(self, attrs):
        error_msg = {}
        kpi_question_score = attrs.get('kpi_question_score')
        ksao_question_score = attrs.get('ksao_question_score')

        if not any((kpi_question_score, ksao_question_score)):
            error_msg['error'] = 'KPI/KSA scores are required.'
        scale_setting = getattr(self.sub_performance_appraisal_slot, 'kaar_score_setting', None)

        kpi_scale_type = nested_getattr(scale_setting, f'{KPI}.scale_type')
        ksao_scale_type = nested_getattr(scale_setting, 'ksao.scale_type')

        annual_rating = attrs.get('annual_rating')
        if kpi_question_score and kpi_scale_type == GRADE and not annual_rating:
            error_msg['annual_rating'] = 'Annual rating for kpi is required.'

        if ksao_question_score and ksao_scale_type == GRADE and not annual_rating:
            error_msg['annual_rating'] = 'Annual rating for kaso is required.'

        if error_msg:
            raise ValidationError(error_msg)

    @staticmethod
    def validation_for_reviewer(attrs):
        if not attrs.get('reviewer_evaluation'):
            raise ValidationError({'error': 'Reviewer is required.'})

    @property
    def appraiser_config(self):
        return self.context['appraiser_config']

    @property
    def sub_performance_appraisal_slot(self):
        return self.context['sub_performance_appraisal_slot']
