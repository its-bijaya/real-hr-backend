from django.conf import settings
from django.core.validators import MinValueValidator
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import JSONField

from irhrs.appraisal.models.appraiser_setting import Appraisal
from irhrs.appraisal.models.question_set import PerformanceAppraisalQuestionSet, \
    QuestionSetUserType, PerformanceAppraisalQuestion
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils.common import DummyObject
from irhrs.core.utils.questions import validate_mandatory_questions
from irhrs.organization.api.v1.serializers.branch import OrganizationBranchSerializer
from irhrs.organization.api.v1.serializers.division import OrganizationDivisionSerializer
from irhrs.organization.api.v1.serializers.employment import EmploymentJobTitleSerializer, \
    EmploymentLevelSerializer
from irhrs.organization.models import OrganizationBranch, OrganizationDivision, EmploymentJobTitle, \
    EmploymentLevel
from irhrs.questionnaire.api.v1.serializers.questionnaire import QuestionSerializer, \
    AnswerSerializer
from irhrs.questionnaire.models.helpers import PERFORMANCE_APPRAISAL, ANSWER_TYPES
from irhrs.questionnaire.models.questionnaire import Question


class PerformanceAppraisalQuestionSetSerializer(DynamicFieldsModelSerializer):
    questions = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.filter(
            question_type=PERFORMANCE_APPRAISAL
        ),
        many=True
    )

    class Meta:
        model = PerformanceAppraisalQuestionSet
        fields = ['id', 'name', 'description', 'questions']

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == 'get':
            fields['questions'] = serializers.SerializerMethodField()
        return fields

    def get_questions(self, performance_appraisal_question_set):
        return QuestionSerializer(
            [qs_set.question for qs_set in
             performance_appraisal_question_set.appraisal_user_type.order_by('order')],
            many=True,
            context=self.context,
        ).data

    def create(self, validated_data):
        validated_data['organization'] = self.context.get('organization')
        questions = validated_data.pop('questions', [])
        instance = super().create(validated_data)
        batch_objects = []
        for order, question in enumerate(questions):
            batch_objects.append(
                QuestionSetUserType(
                    question_set=instance, question=question, order=order
                )
            )
        QuestionSetUserType.objects.bulk_create(batch_objects)
        return instance

    def update(self, instance, validated_data):
        instance.questions.clear()
        questions = validated_data.pop('questions', [])
        obj = super().update(instance, validated_data)
        batch_objects = []
        for order, question in enumerate(questions):
            batch_objects.append(
                QuestionSetUserType(
                    question_set=obj, question=question, order=order)
            )
        QuestionSetUserType.objects.bulk_create(batch_objects)
        return obj


class QuestionSetUserTypeSerializer(DynamicFieldsModelSerializer):
    branches = OrganizationBranchSerializer(
        fields=('name', 'slug'),
        many=True
    )
    divisions = OrganizationDivisionSerializer(
        fields=('name', 'slug'),
        many=True
    )
    job_titles = EmploymentJobTitleSerializer(
        fields=('slug', 'title'),
        many=True
    )
    employment_levels = EmploymentLevelSerializer(
        fields=('slug', 'title'),
        many=True
    )

    class Meta:
        model = QuestionSetUserType
        fields = (
            'question', 'question_set', 'branches', 'divisions',
            'job_titles', 'employment_levels'
        )
        read_only_fields = ('question', 'question_set')

    def get_fields(self):
        fields = super().get_fields()
        if self.request.method.lower() == 'post':
            fields['branches'] = serializers.SlugRelatedField(
                queryset=OrganizationBranch.objects.filter(
                    organization=self.context.get('organization')
                ),
                many=True,
                slug_field='slug'
            )
            fields['divisions'] = serializers.SlugRelatedField(
                queryset=OrganizationDivision.objects.filter(
                    organization=self.context.get('organization')
                ),
                many=True,
                slug_field='slug'

            )
            fields['job_titles'] = serializers.SlugRelatedField(
                queryset=EmploymentJobTitle.objects.filter(
                    organization=self.context.get('organization')
                ),
                many=True,
                slug_field='slug'
            )
            fields['employment_levels'] = serializers.SlugRelatedField(
                queryset=EmploymentLevel.objects.filter(
                    organization=self.context.get('organization')
                ),
                many=True,
                slug_field='slug'
            )
        return fields


class AppraisalQuestionsListSerializer(DynamicFieldsModelSerializer):
    question = serializers.SerializerMethodField()

    class Meta:
        model = PerformanceAppraisalQuestion
        fields = (
            'order', 'question', 'is_mandatory'
        )

    @staticmethod
    def get_question(obj):
        question = obj.question
        return {
            'id': question.id,
            'title': question.title,
            'answer_choices': question.answer_choices,
            'answers': AnswerSerializer(
                question.all_answer_choices.all(),
                many=True
            ).data,
            'description': question.description,
            'rating_scale': question.rating_scale or 5,
            'remarks': '',
            'remarks_required': False,
            'score': 0,
            'weightage': question.weightage,
            'is_open_ended': question.is_open_ended
        }


class ValidateQuestionSerializer(serializers.Serializer):
    score = serializers.IntegerField(validators=[MinValueValidator(0)], default=0)
    title = serializers.CharField()
    remarks = serializers.CharField(
        max_length=settings.TEXT_FIELD_MAX_LENGTH,
        allow_null=True, allow_blank=True
    )
    description = serializers.CharField(
        max_length=settings.TEXT_FIELD_MAX_LENGTH,
        allow_blank=True, allow_null=True
    )
    rating_scale = serializers.IntegerField(validators=[MinValueValidator(0)], default=0)
    answer_choices = serializers.ChoiceField(
        choices=list(dict(ANSWER_TYPES).keys())
    )
    weightage = serializers.IntegerField(required=False, allow_null=True)
    is_open_ended = serializers.BooleanField()
    remarks_required = serializers.BooleanField()
    answers = serializers.JSONField(
        required=False,
        allow_null=True
    )

    def validate(self, attrs):
        score = attrs.get('score')
        weightage = attrs.get('weightage')

        if weightage and score > weightage:
            raise ValidationError({
                'score': ['Score must be less than or equal to weightage.']
            })

        return super().validate(attrs)


class ValidateQuestionsSerializer(serializers.Serializer):
    order = serializers.IntegerField(validators=[MinValueValidator(0)])
    question = ValidateQuestionSerializer()
    is_mandatory = serializers.BooleanField()

    def validate(self, attrs):
        question_answer = attrs.get('question')
        is_mandatory = attrs.get('is_mandatory', False)
        validate_mandatory_questions(
            question_answer,
            is_mandatory=is_mandatory,
        )
        return super().validate(attrs)

class ValidateSectionsSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(
        max_length=settings.TEXT_FIELD_MAX_LENGTH,
        required=False,
        allow_null=True,
        allow_blank=True
    )
    questions = ValidateQuestionsSerializer(
        many=True
    )


class ValidateQuestionSetSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(
        max_length=10000,
        required=False,
        allow_null=True,
        allow_blank=True
    )
    sections = ValidateSectionsSerializer(many=True)


class EditQuestionSetSerializer(serializers.Serializer):
    question_set = JSONField()
    new_questions = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.filter(
            question_type=PERFORMANCE_APPRAISAL
        ),
        many=True
    )

    def get_fields(self):
        fields = super().get_fields()
        fields['appraisal'] = serializers.PrimaryKeyRelatedField(
            queryset=Appraisal.objects.filter(
                sub_performance_appraisal_slot=self.context.get('sub_performance_appraisal_slot')
            )
        )
        return fields

    @staticmethod
    def generate_questions(questions):
        return AppraisalQuestionsListSerializer(
            questions,
            many=True
        ).data

    @staticmethod
    def validate_question_set(question_set):
        serializer = ValidateQuestionSetSerializer(data=question_set)
        serializer.is_valid(raise_exception=True)
        return question_set

    def create(self, validated_data):
        question_set = validated_data.get('question_set')
        generic_question_section = list(
            filter(
                lambda x: x.get('title') == "Generic Question Set",
                question_set.get('sections')
            )
        )

        new_questions = self.generate_questions(questions=validated_data.get('new_questions'))

        if generic_question_section:
            generic_question_section[0]['questions'] += new_questions
        elif not generic_question_section and new_questions:
            question_set['sections'].append({
                'title': 'Generic Question Set',
                'description': '',
                'questions': new_questions
            })

        appraisal = validated_data.get('appraisal')
        appraisal.question_set = question_set
        appraisal.save()

        return DummyObject(**validated_data)


class CopyQuestionSetSerializer(serializers.Serializer):
    def get_fields(self):
        fields = super().get_fields()
        fields['copy_from'] = serializers.PrimaryKeyRelatedField(
            queryset=Appraisal.objects.filter(
                sub_performance_appraisal_slot=self.context.get('sub_performance_appraisal_slot')
            )
        )
        fields['copy_to'] = serializers.PrimaryKeyRelatedField(
            queryset=Appraisal.objects.filter(
                sub_performance_appraisal_slot=self.context.get('sub_performance_appraisal_slot')
            ),
            many=True
        )
        return fields

    def create(self, validated_data):
        copy_from = validated_data.get('copy_from')
        _ = Appraisal.objects.filter(
            id__in=map(
                lambda x: x.id,
                validated_data.get('copy_to')
            )
        ).update(
            question_set=copy_from.question_set
        )
        return DummyObject(**validated_data)
