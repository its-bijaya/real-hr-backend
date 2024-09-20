from jsonschema import validate as validate_schema
from jsonschema.exceptions import ValidationError as SchemaValidationError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.relations import PrimaryKeyRelatedField, SlugRelatedField

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.questionnaire.models.helpers import (CHECKBOX, RADIO, RATING_SCALE)
from irhrs.questionnaire.models.questionnaire import (
    Question, QuestionCategory, Answer
)
from irhrs.training.models.helpers import ASSESSMENT
from irhrs.questionnaire.models.helpers import PERFORMANCE_APPRAISAL

class AnswerSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Answer
        fields = (
            'id',
            'title',
            'order',
            # 'description',
            'is_correct',
            'remarks',
        )

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method == 'POST':
            # Will not use this serializer for
            if 'question' in fields:
                fields['question'] = PrimaryKeyRelatedField(
                    queryset=Question.objects.filter(
                        organization=self.context.get('organization')
                    )
                )
        return fields


class QuestionSerializer(DynamicFieldsModelSerializer):
    answers = AnswerSerializer(
        many=True,
        required=False,
        exclude_fields=['is_correct']
    )

    class Meta:
        model = Question
        fields = (
            'id', 'title', 'description', 'answer_choices', 'question_type',
            'category', 'order', 'weightage', 'is_open_ended',  # 'image',
            'rating_scale', 'answers', 'display_type', 'extra_data',
        )
        read_only_fields = 'id', 'question_type', 'order'

    def create(self, validated_data):
        validated_data['organization'] = self.context['organization']
        answers = validated_data.pop('answers', [])
        category = validated_data['category']
        validated_data['question_type'] = category.category
        validated_data['order'] = Question.objects.filter(category=category).count() + 1
        if validated_data['category'].category == PERFORMANCE_APPRAISAL:
            validated_data.pop('is_open_ended', None)
            validated_data.pop('weightage', None)
            validated_data.pop('rating_scale', None)
        question = super().create(validated_data)
        self.create_answers(answers, question)
        return question

    @staticmethod
    def create_answers(answers, question):
        old_answers = set(question.answers.values_list('id', flat=True))
        valid_answers_in_db = list()
        for index, answer in enumerate(answers):
            obj, _ = Answer.objects.update_or_create(
                title=answer.get('title'),
                question=question,
                defaults={
                    'order': answer.get('order', index),
                    # 'description': answer.get('description'),
                    'is_correct': answer.get('is_correct'),
                    # 'remarks': answer.get('remarks'),
                }
            )
            valid_answers_in_db.append(obj)
        Answer.objects.filter(
            id__in=old_answers - set(map(lambda obj_: obj_.id, valid_answers_in_db))
        ).delete()

    def validate(self, attrs):
        # validate ordering for organization question
        category = attrs.get('category')
        is_open_ended = attrs.get('is_open_ended')
        choice_type = attrs.get('answer_choices')
        weightage = attrs.get('weightage')
        rating_scale = attrs.get('rating_scale')

        # if category.category != ASSESSMENT and choice_type in [CHECKBOX, RADIO]:
        #     # for other category except Assessment
        #     raise ValidationError({
        #         'choice_type': [f'Multiple Choice Question is not '
        #                         f'acceptable for {category.get_category_display()}.']
        #     })

        if self.instance:
            answer_choices = self.instance.answer_choices
            if answer_choices in [CHECKBOX, RADIO] and choice_type not in [CHECKBOX, RADIO]:
                attrs['answers'] = []
            if answer_choices == RATING_SCALE and choice_type != RATING_SCALE:
                attrs['rating_scale'] = None

        if not is_open_ended and weightage and weightage < 1:
            raise ValidationError({
                'weightage': ['Value of weightage must be at least 1.']
            })

        if category == ASSESSMENT:
            self.validation_for_assessment(choice_type, is_open_ended, weightage)

        if is_open_ended and choice_type not in [CHECKBOX, RADIO] and weightage > 0:
            # update weightage to zero if answer is Short, long or linear scale
            attrs.update({
                'weightage': 0
            })

        # following line checks whether provided rating scale is accepted or not
        accepted_rating_scale = rating_scale and 1 <= rating_scale <= 10
        if choice_type == RATING_SCALE and not accepted_rating_scale and category.category!=PERFORMANCE_APPRAISAL:
            raise ValidationError({
                'rating_scale': ['Rating Scale Value must be in between 1 to 10.']
            })

        # Validate Answers are present for MCQs.
        self.validate_number_of_correct_answer(attrs, category)

        return super().validate(attrs)

    def validate_extra_data(self, extra_data):
        question_schema = {
            "type": "object",
            "properties": {
                "rows": {
                    "type": "array",
                    "uniqueItems": True,
                    "items": {
                        "type": "string",
                        "maxLength": 255
                    },
                },
                "columns": {
                    "type": "array",
                    "uniqueItems": True,
                    "items": {
                        "type": "string",
                        "maxLength": 255
                    },
                },
                "all_rows_mandatory": {
                    "type": "boolean",
                },
            },
            "required": ["rows", "columns", "all_rows_mandatory"],
        }
        try:
            validate_schema(extra_data, question_schema)
        except SchemaValidationError as schema_error:
            raise ValidationError({
                "error": schema_error.message
            })
        return extra_data


    def validation_for_assessment(self, choice_type, is_open_ended, weightage):
        if is_open_ended and choice_type in [CHECKBOX, RADIO]:
            # for multiple choice answer
            raise ValidationError({
                'choice_type': ['Multiple Choice Questions can\'t be open ended question.']
            })
        if choice_type in [CHECKBOX, RADIO] and weightage and weightage < 1:
            # for multiple choice question where weightage is less then 1
            raise ValidationError({
                'weightage': ['Value of weightage must be at least 1.']
            })

    @staticmethod
    def validate_number_of_correct_answer(attrs, category):
        answers = attrs.get('answers')
        answer_choices = attrs.get('answer_choices')
        if category.category == ASSESSMENT and answer_choices in (CHECKBOX, RADIO):
            if not answers:
                raise ValidationError({
                    'answers': 'Answers is required for Multiple Choice Questions.'
                })

            answer_title = list(map(lambda x: x.get('title'), answers))
            if len(answer_title) != len(set(answer_title)):
                raise ValidationError({
                    'answers': 'Repeated answer provided for Multiple Choice Questions.'
                })

            correct_answer = list(
                filter(
                    lambda x: x.get('is_correct'),
                    answers
                )
            )

            if not correct_answer:
                raise ValidationError({
                    'answers': 'At least one correct answer must be selected'
                               'for Multiple Choice Questions.'
                })

            if len(correct_answer) == len(answers):
                raise ValidationError({
                    'answers': 'At least two options must be added.'
                })

    def get_fields(self):
        """
        {
  "title": "Ravi?",
  "description": "as",
  "answer_choices": "single-mcq",
  "question_type": "assessment",
  "category": "rb",
  "order": 1,
  "weightage": 80,
  "is_open_ended": false,
  "answers": [

  ]
}
        :return:
        """
        fields = super().get_fields()

        if self.request and self.request.method == 'GET':
            exclude_fields = []
            if self.context.get('hide_answer'):
                exclude_fields.append('is_correct')
            fields['answers'] = AnswerSerializer(
                many=True,
                context=self.context,
                exclude_fields=exclude_fields
            )
            fields['category'] = QuestionCategorySerializer(
                fields=('title', 'slug'),
                context=self.context
            )
        else:
            fields['category'] = SlugRelatedField(
                queryset=QuestionCategory.objects.all(),
                slug_field='slug'
            )
            fields['answers'] = AnswerSerializer(
                many=True,
                required=False,
            )
        return fields

    def update(self, instance, validated_data):
        self.create_answers(validated_data.pop('answers', []), instance)
        return super().update(instance, validated_data)


class QuestionCategorySerializer(DynamicFieldsModelSerializer):
    total_questions = serializers.IntegerField(read_only=True)
    total_weightage = serializers.IntegerField(read_only=True)

    class Meta:
        model = QuestionCategory
        fields = (
            'title', 'slug', 'description', 'category', 'total_questions', 'total_weightage'
        )
        read_only_fields = 'slug',

    def create(self, validated_data):
        validated_data['organization'] = self.context.get('organization')
        return super().create(validated_data)

    def validate(self, attrs):
        qs = QuestionCategory.objects.filter(
            organization=self.context.get('organization'),
            title__iexact=attrs.get('title'),
            category=attrs.get('category')
        )
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if qs.exists():
            raise ValidationError({
                'title': 'The title already exists'
            })
        return super().validate(attrs)
