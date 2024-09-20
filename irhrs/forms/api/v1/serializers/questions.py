from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils.common import DummyObject
from irhrs.forms.models import (
    FormQuestion,
    FormQuestionSection,
    FormQuestionSet
)
from irhrs.questionnaire.api.v1.serializers.questionnaire import QuestionSerializer


class FormQuestionExplicitIDSerializer(DynamicFieldsModelSerializer):
    id = serializers.IntegerField(read_only=False)
    # question = serializers.IntegerField(read_only=False)

    class Meta:
        model = FormQuestion
        fields = ('id', 'is_mandatory', 'question',
                  'order', 'answer_visible_to_all_users')
        read_only_fields = ('order',)


class FormQuestionSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = FormQuestion
        fields = ('id', 'is_mandatory', 'question',
                  'order', 'answer_visible_to_all_users')
        read_only_fields = 'order',

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method == 'GET':
            fields['question'] = QuestionSerializer(context=self.context)
        return fields

    def create(self, validated_data):
        section = self.context.get('question_section')
        validated_data['question_section'] = section
        validated_data['order'] = section.form_questions.count() + 1
        return super().create(validated_data)


class FormQuestionBulkSerializer(serializers.Serializer):
    questions_edited = FormQuestionExplicitIDSerializer(many=True)
    questions_added = FormQuestionSerializer(many=True)

    def get_fields(self):
        fields = super().get_fields()
        question_section = self.context.get('question_section')
        fields['questions_deleted'] = serializers.PrimaryKeyRelatedField(
            queryset=FormQuestion.objects.filter(
                question_section=question_section
            ),
            many=True
        )
        return fields

    def create(self, validated_data):
        added_serializer = validated_data.get('added_serializer')
        edited_serializers = validated_data.get('edited_serializers')
        deleted_question_ids = [
            question.id for question in
            validated_data.get('questions_deleted', [])
        ]

        if added_serializer:
            added_serializer.save()

        for edited_ser in edited_serializers:
            edited_ser.save()

        FormQuestion.objects.filter(
            id__in=deleted_question_ids
        ).delete()

        return DummyObject(**validated_data)

    def validate(self, attrs):
        errors = {
            "questions_added": [],
            "questions_edited": []
        }
        question_section = self.context.get('question_section')
        edited_questions = attrs.get('questions_edited')
        added_questions = attrs.get('questions_added')
        for question_dict in added_questions:
            question_dict["question"] = question_dict["question"].id
        added_ser = FormQuestionSerializer(
            data=added_questions,
            many=True,
            context=self.context
        )
        if not added_ser.is_valid():
            errors["questions_added"].append(added_ser.errors)
        else:
            attrs["added_serializer"] = added_ser

        edited_serializers = []
        for question_dict in edited_questions:
            question_dict["question"] = question_dict["question"].id
            edited_question = get_object_or_404(
                FormQuestion.objects.filter(
                    question_section=question_section,
                ),
                id=question_dict.get('id')
            )
            edited_ser = FormQuestionSerializer(
                edited_question,
                data=question_dict,
                context=self.context
            )
            if not edited_ser.is_valid():
                errors["questions_edited"].append(edited_ser.errors)
            else:
                edited_serializers.append(edited_ser)

        if errors.get("questions_added") or errors.get("questions_edited"):
            raise ValidationError(errors)

        attrs["edited_serializers"] = edited_serializers

        super().validate(attrs)

        return attrs

class FormQuestionSectionSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = FormQuestionSection
        fields = 'id', 'title', 'description', 'questions'
        read_only_fields = 'questions',

    def get_fields(self):
        fields = super().get_fields()
        fields['questions'] = FormQuestionSerializer(
            source='form_questions',
            many=True, read_only=True,
            context=self.context
        )
        return fields

    def create(self, validated_data):
        validated_data['question_set'] = self.context.get('question_set')
        return super().create(validated_data)


class FormQuestionSetSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = FormQuestionSet
        fields = ['id', 'name', 'description', 'sections', 'organization']
        extra_kwargs = {
            'organization': {
                'required': False
            }
        }

    def get_fields(self):
        fields = super().get_fields()

        read_only = {}
        if self.request and self.request.method != 'POST':
            read_only = {'read_only': True}

        section_fields = ['id', 'title', 'description']
        if self.context.get('with_questions', True):
            section_fields.append('questions')

        fields['sections'] = FormQuestionSectionSerializer(
            many=True,
            context=self.context,
            fields=section_fields,
            **read_only
        )
        return fields

    def create(self, validated_data):
        sections = validated_data.pop('sections')
        validated_data["organization"] = self.context["organization"]
        instance = super().create(validated_data)

        if not sections:
            sections = [{
                'title': instance.name,
                'description': instance.description
            }]

        create_section = []
        for section in sections:
            create_section.append(FormQuestionSection(
                question_set=instance, **section))

        FormQuestionSection.objects.bulk_create(create_section)
        return instance
