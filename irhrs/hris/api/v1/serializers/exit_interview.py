from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.common.api.serializers.common import ExitInterviewAnswerPostSerializer
from irhrs.core.constants.interviewer import PENDING, PROGRESS
from irhrs.core.constants.interviewer import COMPLETED as _COMPLETED
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils import nested_get
from irhrs.core.utils.common import DummyObject
from irhrs.hris.api.v1.serializers.onboarding_offboarding import EmployeeSeparationTHinSerializer
from irhrs.hris.constants import STOPPED, COMPLETED
from irhrs.hris.models import EmployeeSeparation
from irhrs.hris.models.exit_interview import ExitInterview, ExitInterviewQuestionSet
from irhrs.questionnaire.api.v1.serializers.questionnaire import QuestionSerializer
from irhrs.questionnaire.models.helpers import EXIT_INTERVIEW
from irhrs.questionnaire.models.questionnaire import Question
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer

User = get_user_model()


class ExitInterViewQuestionSetSerializer(DynamicFieldsModelSerializer):
    questions = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.filter(question_type=EXIT_INTERVIEW),
        many=True
    )

    class Meta:
        model = ExitInterviewQuestionSet
        fields = ['id', 'name', 'description', 'questions']

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == 'get':
            fields['questions'] = QuestionSerializer(
                many=True
            )
        return fields


class ExitInterviewSerializer(DynamicFieldsModelSerializer):
    interviewer = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all().current()
    )
    separation = serializers.PrimaryKeyRelatedField(
        queryset=EmployeeSeparation.objects.exclude(status__in=[STOPPED, COMPLETED])
    )

    class Meta:
        model = ExitInterview
        fields = [
            'id', 'separation', 'scheduled_at', 'location', 'question_set',
            'interviewer', 'status', 'data'
        ]
        read_only_fields = ['status']

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == 'get':
            fields['interviewer'] = UserThinSerializer(
                fields=["id", "full_name", "profile_picture", "cover_picture", "job_title",
                        "is_online", 'is_current', 'organization',]
            )
            fields['question_set'] = ExitInterViewQuestionSetSerializer(
                fields=['id', 'name', 'description']
            )
            fields['separation'] = EmployeeSeparationTHinSerializer()
        return fields

    def validate(self, attrs):
        data = attrs.get('data')
        if data:
            questions = data.get('questions')
            if questions:
                serializer = ExitInterviewAnswerPostSerializer(
                    data=questions,
                    many=True
                )
                serializer.is_valid(raise_exception=True)

        return super().validate(attrs)

    def validate_separation(self, separation):
        if self.request and self.request.method == "POST":
            if hasattr(separation, 'exit_interview'):
                interview = getattr(separation, 'exit_interview')
                if interview.status != PENDING:
                    raise ValidationError({
                        'detail': 'Interview process is in action by interviewer.'
                    })
        return separation

    def create(self, validated_data):
        data = ExitInterViewQuestionSetSerializer(
            validated_data.get('question_set'),
            fields=['questions'],
            context={
                'request': DummyObject(method='GET')
            }
        ).data
        data['status'] = 'pending'
        validated_data['data'] = data
        separation = validated_data.pop('separation')
        instance, _temp = ExitInterview.objects.update_or_create(
            separation=separation,
            defaults=validated_data
        )
        return instance

    def update(self, instance, validated_data):
        data_status = nested_get(validated_data, 'data.status')
        updated_instance = super().update(instance, validated_data)
        if data_status == 'in_progress':
            updated_instance.status = PROGRESS
        elif data_status == 'completed':
            updated_instance.status = _COMPLETED

        updated_instance.save()
        return updated_instance
