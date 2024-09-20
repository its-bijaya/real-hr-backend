from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.appraisal.models.question_set import (
    PerformanceAppraisalQuestion,
    PerformanceAppraisalQuestionSection,
    PerformanceAppraisalQuestionSet
)
from irhrs.questionnaire.api.v1.serializers.questionnaire import QuestionSerializer


class PerformanceAppraisalQuestionSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = PerformanceAppraisalQuestion
        fields = 'id', 'is_mandatory', 'question', 'order',
        read_only_fields = 'order',

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method == 'GET':
            fields['question'] = QuestionSerializer(context=self.context)
        return fields

    def create(self, validated_data):
        section = self.context.get('question_section')
        validated_data['question_section'] = section
        validated_data['order'] = section.pa_questions.count() + 1
        return super().create(validated_data)


class PerformanceAppraisalQuestionSectionSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = PerformanceAppraisalQuestionSection
        fields = 'id', 'title', 'description', 'questions'
        read_only_fields = 'questions',

    def get_fields(self):
        fields = super().get_fields()
        fields['questions'] = PerformanceAppraisalQuestionSerializer(
            source='pa_questions',
            many=True, read_only=True,
            context=self.context
        )
        return fields

    def create(self, validated_data):
        validated_data['question_set'] = self.context.get('question_set')
        return super().create(validated_data)


class PerformanceAppraisalQuestionSetSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = PerformanceAppraisalQuestionSet
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

        fields['sections'] = PerformanceAppraisalQuestionSectionSerializer(
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
            create_section.append(PerformanceAppraisalQuestionSection(
                question_set=instance, **section))

        PerformanceAppraisalQuestionSection.objects.bulk_create(create_section)
        return instance
