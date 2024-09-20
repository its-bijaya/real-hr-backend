from django.urls import reverse
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.questionnaire.models.helpers import (
    CHECKBOX,
    RADIO,
    SHORT,
    LONG,
    RATING_SCALE,
    DATE,
    TIME,
    DURATION,
    DATE_TIME,
    DATE_WITHOUT_YEAR,
    DATE_TIME_WITHOUT_YEAR,
    FILE_UPLOAD,
)

from irhrs.questionnaire.models.questionnaire import Question, Answer
from irhrs.forms.utils.reports import (
    get_aggregate_for_type,
    get_prepoulated_offset
)
from irhrs.forms.models import (
    Form,
    UserForm,
    FormQuestion,
    FormQuestionSection,
    UserFormAnswerSheet,
    UserFormIndividualQuestionAnswer,
    AnonymousFormIndividualQuestionAnswer,
    AnonymousFormAnswerSheet,
)

class AnonymousFormSummaryQuestionAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormQuestion
        fields = (
            'question_text', 'question', 'question_type', 'answers',
            'question_section', 'is_mandatory'
        )

    question_text = serializers.SerializerMethodField()
    question_section = serializers.ReadOnlyField(source='question_section.title')
    question_type = serializers.SerializerMethodField()
    answers = serializers.SerializerMethodField()

    def get_question_text(self, form_question):
        return form_question.question.title

    def get_question_type(self, form_question):
        return form_question.question.answer_choices

    def get_answers(self, form_question):
        form = self.context.get('form')
        context = {
            "request": self.context.get('request'),
            "organization": self.context.get('organization')
        }
        question_answers = AnonymousFormIndividualQuestionAnswer.objects.filter(
            answer_sheet__form=form,
            question=form_question
        )
        request = self.context.get('request')
        form_fill_date = request.query_params.get("form_fill_date")
        if form_fill_date:
            question_answers = question_answers.filter(
                created_at__date=form_fill_date
            )
        result = get_aggregate_for_type(
            form_question,
            question_answers,
            context
        )
        return result


class IndividualFormSummaryQuestionAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormQuestion
        fields = (
            'question_text', 'question', 'question_type', 'answers',
            'next', 'question_section', 'is_mandatory','description'
        )

    question_text = serializers.SerializerMethodField()
    question_type = serializers.SerializerMethodField()
    question_section = serializers.ReadOnlyField(source='question_section.title')
    question = serializers.SerializerMethodField()
    next = serializers.SerializerMethodField()
    answers = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    def get_question(self, form_question):
        return form_question.id

    def get_question_text(self, form_question):
        return form_question.question.title

    def get_question_type(self, form_question):
        return form_question.question.answer_choices
    
    def get_description(self, form_quesetion):
        return form_quesetion.question.description

    def fetch_question_answers(self, form_question):
        form = self.context.get('form')
        request = self.context.get('request')
        queryset = self.context.get('queryset')
        is_anonymous_form = form.is_anonymously_fillable
        individual_qa_model = (
            AnonymousFormIndividualQuestionAnswer if is_anonymous_form else
            UserFormIndividualQuestionAnswer
        )
        filters = dict(
            answer_sheet__form=form,
            question=form_question
        )
        if not is_anonymous_form:
            filters.update({
                'answer_sheet__is_approved': True,
                'answer_sheet__user__in': queryset
            })

        question_answers = individual_qa_model.objects.filter(
            **filters
        )

        form_fill_date = request.query_params.get("form_fill_date")
        if form_fill_date:
            question_answers = question_answers.filter(
                created_at__date=form_fill_date
            )
        return question_answers

    def get_answers(self, form_question):
        question_answers = self.fetch_question_answers(form_question)
        request = self.context.get('request')
        context = {
            "request": self.context.get('request'),
            "organization": self.context.get('organization')
        }

        result = get_aggregate_for_type(
            form_question,
            question_answers,
            context
        )
        return result

    def get_next(self, form_question):
        request = self.context.get('request')
        organization = self.context.get('organization')
        question_answers = self.fetch_question_answers(form_question)
        offset = get_prepoulated_offset(
            form_question,
            question_answers
        )
        limit = 10
        form = self.context.get('form')
        if offset:
            reverse_url = ''
            date_types = [
                DATE,
                TIME,
                DURATION,
                DATE_TIME,
                DATE_WITHOUT_YEAR,
                DATE_TIME_WITHOUT_YEAR,
            ]
            if form_question.question.answer_choices in date_types:
                reverse_url = "api_v1:forms:forms-report-list-aggregated-response"
            elif form_question.question.answer_choices in [SHORT, LONG, FILE_UPLOAD]:
                reverse_url = "api_v1:forms:forms-report-list-response"
            else:
                return None

            url = reverse(
                reverse_url,
                kwargs={
                    "organization_slug": organization.slug,
                    "form_id": form.id,
                    "question_id": form_question.id
                },
            ) + f'?limit={limit}&offset={offset}'
        else:
            return None
        return request.build_absolute_uri(url)


class UserFormIndividualQuestionAnswerPaginatedSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFormIndividualQuestionAnswer
        fields = ('answers',)

class UserFormIndividualQuestionAnswerAggregatedSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFormIndividualQuestionAnswer
        fields = ('answers',)


class AnonymousFormIndividualQuestionAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnonymousFormIndividualQuestionAnswer
        fields = ('answers', 'question')

    question = serializers.SerializerMethodField()

    def get_question(self, form_question):
        return form_question.id
