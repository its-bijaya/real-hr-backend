import os

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.urls import reverse

from irhrs.forms.models import (
    UserFormAnswerSheet,
    UserFormIndividualQuestionAnswer,
    AnonymousFormIndividualQuestionAnswer,
    AnonymousFormAnswerSheet,
    AnswerSheetStatus,
    FormQuestion,
    FormQuestionSet,
    FormQuestionSection,
)
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
from irhrs.questionnaire.models.questionnaire import (
    Question,
    Answer,
    QuestionCategory
)
from irhrs.core.constants.payroll import SUPERVISOR
from irhrs.users.models import UserSupervisor
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.forms.constants import APPROVED
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer


class ListUserFormAnswerSheetSerializer(DynamicFieldsModelSerializer):
    form_name = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    deadline = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()


    class Meta:
        model = UserFormAnswerSheet
        fields = ('id', 'form', 'form_name', 'user', 'status', 'deadline')

    def get_deadline(self, answer_sheet):
        return answer_sheet.form.deadline

    def get_status(self, answer_sheet):
        return answer_sheet.final_status

    def get_form_name(self, answer_sheet):
        return answer_sheet.form.name

    def get_user(self, answer_sheet):
        return UserThinSerializer(answer_sheet.user).data


class AnswerSheetStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerSheetStatus
        fields = ('id', 'action', 'approver', 'answer_sheet', 'approval_level', 'remarks')

    def validate_actions(self, attrs):
        approver = self.context["request"].user
        action = attrs.get("action")
        answer_sheet = attrs.get("answer_sheet")
        approval_level = attrs.get("approval_level")
        answer_user = answer_sheet.user
        if approval_level.approve_by == SUPERVISOR:
            supervisor_obj = UserSupervisor.objects.filter(
                user=answer_user,
                supervisor=approver
            ).first()
            if not supervisor_obj:
                raise ValidationError({"error": "Supervisor does not exist."})
            if action == APPROVED and not supervisor_obj.approve:
                raise ValidationError({"error": "Supervisor does not have approve authority."})
            if action == APPROVED and not supervisor_obj.deny:
                raise ValidationError({"error": "Supervisor does not have deny authority."})


class AnswerSheetHistorySerializer(serializers.ModelSerializer):
    approver = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    def get_user(self, sheet_status):
        return UserThinSerializer(sheet_status.answer_sheet.user).data

    def get_approver(self, sheet_status):
        return UserThinSerializer(sheet_status.approver).data

    class Meta:
        model = AnswerSheetStatus
        fields = ('id', 'action', 'user',
                  'remarks', 'approver',
                  'created_at')



class ListAnonymousFormAnswerSheetSerializer(serializers.ModelSerializer):
    form_name = serializers.SerializerMethodField()
    deadline = serializers.SerializerMethodField()

    class Meta:
        model = AnonymousFormAnswerSheet
        fields = ('id', 'form', 'form_name', 'deadline')

    def get_deadline(self, answer_sheet):
        return answer_sheet.form.deadline

    def get_form_name(self, answer_sheet):
        return answer_sheet.form.name

class DisplayChoiceAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ('id', 'order', 'title', 'remarks', 'is_correct')


# class SaveFormAnswerChoiceSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Answer
#         fields = (
#             'id',
#             'title',
#             'order',
#             'is_correct',
#             'remarks',
#         )

#     def get_fields(self):
#         fields = super().get_fields()
#         fields['question'] = serializers.PrimaryKeyRelatedField(
#             queryset=Question.objects.filter(
#                 organization=self.context.get('organization')
#             )
#         )
#         return fields


class DisplayQuestionCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionCategory
        fields = ('title', 'slug')

class FormDisplayQuestionSerializer(serializers.ModelSerializer):
    answers = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ('id', 'order', 'title', 'answers', 'category',
                  'weightage', 'description', 'rating_scale',
                  'is_open_ended', 'question_type', 'answer_choices', 'display_type',
                  'extra_data')

    def get_category(self, question):
        return DisplayQuestionCategorySerializer(question.category).data

    def get_answers(self, question):
        answer_sheet = self.context.get('answer_sheet')
        request = self.context.get('request')
        individual_answer_model = (
            AnonymousFormIndividualQuestionAnswer if answer_sheet.form.is_anonymously_fillable
            else UserFormIndividualQuestionAnswer
        )
        answer_choices = question.answer_choices
        answers = individual_answer_model.objects.filter(
            question__question=question,
            answer_sheet=answer_sheet
        )
        if answer_choices in [FILE_UPLOAD]:
            default_answer = [{
                "file_name": "",
                "file_url": "",
                "saved_file_name_only": ""
            }]
            if answers:
                json_answer = answers.first().answers
                if json_answer and isinstance(json_answer, list):
                    file_url = json_answer[0].get('file_url')
                    if not file_url:
                        return default_answer
                    else:
                        original_nice_file_name = json_answer[0].get("file_name")
                        filename = os.path.basename(file_url)
                        file_download_link = reverse(
                            'api_v1:forms:forms-answer-sheets-download-form-attachment',
                            kwargs={
                                'organization_slug': answer_sheet.form.organization.slug,
                            }
                        ) + f"?file_name={original_nice_file_name}&file_uuid={filename}"
                        json_answer[0]['file_url'] = request.build_absolute_uri(
                            file_download_link
                        )
                        return json_answer
                return default_answer
        else:
            indvidiual_answer_obj = answers.first()
            return indvidiual_answer_obj.answers if indvidiual_answer_obj else []
        return []

class UserFormDisplayFormQuestionSerializer(serializers.ModelSerializer):
    question = FormDisplayQuestionSerializer()

    class Meta:
        model = FormQuestion
        fields = ('id', 'order', 'is_mandatory', 'question')


class UserFormDisplayQuestionSectionSerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()

    class Meta:
        model = FormQuestionSection
        fields = ('id', 'title', 'description', 'questions')

    def get_questions(self, form_question_section):
        return UserFormDisplayFormQuestionSerializer(
            form_question_section.form_questions.all(),
            many=True,
            context=self.context
        ).data


class UserFormDisplayAnswerSheetSerializer(serializers.ModelSerializer):
    sections = UserFormDisplayQuestionSectionSerializer(many=True)
    count = serializers.SerializerMethodField()

    class Meta:
        model = FormQuestionSet
        fields = ('id', 'name', 'sections', 'count')

    def get_count(self, question_set):
        return question_set.sections.count()


class AnonymousFormDisplayFormQuestionSerializer(serializers.ModelSerializer):
    question = FormDisplayQuestionSerializer()

    class Meta:
        model = FormQuestion
        fields = ('id', 'order', 'is_mandatory', 'question')


class AnonymousFormDisplayQuestionSectionSerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()

    class Meta:
        model = FormQuestionSection
        fields = ('id', 'title', 'description', 'questions')

    def get_questions(self, form_question_section):
        return AnonymousFormDisplayFormQuestionSerializer(
            form_question_section.form_questions.all(),
            many=True,
            context=self.context
        ).data


class AnonymousFormDisplayAnswerSheetSerializer(serializers.ModelSerializer):
    sections = AnonymousFormDisplayQuestionSectionSerializer(many=True)
    count = serializers.SerializerMethodField()

    class Meta:
        model = FormQuestionSet
        fields = ('id', 'name', 'sections', 'count')

    def get_count(self, question_set):
        return question_set.sections.count()


class RetrieveUserFormAnswerSheetSerializer(serializers.ModelSerializer):
    history = serializers.SerializerMethodField()
    disclaimer_text = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    question_answer = serializers.SerializerMethodField()
    deadline = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = UserFormAnswerSheet
        fields = (
            'id', 'question_answer', 'form',
            'history', 'deadline', 'status',
            'description', 'disclaimer_text'
        )

    def get_status(self, answer_sheet):
        return answer_sheet.final_status

    def get_question_answer(self, answer_sheet):
        context = self.context
        context.update({
            "answer_sheet": answer_sheet
        })
        return UserFormDisplayAnswerSheetSerializer(
            answer_sheet.form.question_set,
            context=context
        ).data

    def get_disclaimer_text(self, answer_sheet):
        return answer_sheet.form.disclaimer_text

    def get_description(self, answer_sheet):
        return answer_sheet.form.description

    def get_deadline(self, answer_sheet):
        return answer_sheet.form.deadline

    def get_history(self, answer_sheet):
        sheet_activites = answer_sheet.status.all()
        return AnswerSheetHistorySerializer(
            sheet_activites,
            many=True
        ).data


class RetrieveAnonymousFormAnswerSheetSerializer(serializers.ModelSerializer):
    description = serializers.ReadOnlyField(source='form.description')
    deadline = serializers.ReadOnlyField(source='form.deadline')
    question_answer = serializers.SerializerMethodField()

    class Meta:
        model = AnonymousFormAnswerSheet
        fields = (
            'id', 'question_answer', 'form',
            'deadline', 'description'
        )

    def get_question_answer(self, answer_sheet):
        context = self.context
        context.update({
            "answer_sheet": answer_sheet
        })
        return AnonymousFormDisplayAnswerSheetSerializer(
            answer_sheet.form.question_set,
            context=context
        ).data
