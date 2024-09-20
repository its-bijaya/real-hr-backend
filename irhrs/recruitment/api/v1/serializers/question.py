from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.questionnaire.api.v1.serializers.questionnaire import QuestionSerializer
from irhrs.recruitment.models import QuestionSet
from irhrs.recruitment.models.question import RecruitmentQuestions, RecruitmentQuestionSection


class QuestionsSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = RecruitmentQuestions
        fields = 'id', 'is_mandatory', 'question', 'order'
        read_only_fields = 'order',

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method == 'GET':
            fields['question'] = QuestionSerializer(context=self.context)
        return fields

    def create(self, validated_data):
        section = self.context.get('question_section')
        validated_data['question_section'] = section
        validated_data['order'] = section.recruitment_questions.count() + 1
        return super().create(validated_data)


class QuestionSectionSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = RecruitmentQuestionSection
        fields = 'id', 'title', 'description', 'questions'
        read_only_fields = 'questions',

    def get_fields(self):
        fields = super().get_fields()
        fields['questions'] = QuestionsSerializer(
            source='recruitment_questions',
            many=True, read_only=True,
            context=self.context
        )
        return fields

    def create(self, validated_data):
        validated_data['question_set'] = self.context.get('question_set')
        return super().create(validated_data)


class QuestionSetSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = QuestionSet
        fields = ['id', 'name', 'description', 'sections']

    def get_fields(self):
        fields = super().get_fields()

        read_only = {}
        if self.request and self.request.method != 'POST':
            read_only = {'read_only': True}

        section_fields = ['id', 'title', 'description']
        if self.context.get('with_questions', True):
            section_fields.append('questions')

        fields['sections'] = QuestionSectionSerializer(
            many=True,
            context=self.context,
            fields=section_fields,
            **read_only
        )
        return fields

    def create(self, validated_data):
        sections = validated_data.pop('sections')
        validated_data.update({
            'form_type': self.context.get('form_type')
        })
        instance = super().create(validated_data)

        if not sections:
            sections = [{
                'title': instance.name,
                'description': instance.description
            }]

        create_section = []
        for section in sections:
            create_section.append(RecruitmentQuestionSection(question_set=instance, **section))

        RecruitmentQuestionSection.objects.bulk_create(create_section)
        return instance
