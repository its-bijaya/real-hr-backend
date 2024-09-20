from rest_framework import serializers

from irhrs.recruitment.api.v1.serializers import ApplicantProcessSerializer, \
    ProcessAnswerSerializer
from irhrs.recruitment.api.v1.serializers.external_profile import (
    ExternalSerializer, ReferenceCheckerSerializer
)
from irhrs.recruitment.models import InterViewAnswer, Interview, ReferenceCheckAnswer, \
    ReferenceCheck, ReferenceChecker
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from rest_framework import serializers

from irhrs.recruitment.api.v1.serializers import ApplicantProcessSerializer, \
    ProcessAnswerSerializer
from irhrs.recruitment.api.v1.serializers.external_profile import (
    ExternalSerializer, ReferenceCheckerSerializer
)
from irhrs.recruitment.models import InterViewAnswer, Interview, ReferenceCheckAnswer, \
    ReferenceCheck, ReferenceChecker
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer


class InterViewAnswerSerializer(ProcessAnswerSerializer):
    location = serializers.ReadOnlyField(source='parent.location')
    score = serializers.SerializerMethodField()

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.upper() == 'GET':
            fields['internal_interviewer'] = UserThinSerializer()
            fields['external_interviewer'] = ExternalSerializer(
                fields=['id', 'user'])
        return fields

    class Meta:
        model = InterViewAnswer
        fields = '__all__'

    @staticmethod
    def get_score(instance):
        return instance.data.get('given_score')


class InterviewSerializer(ApplicantProcessSerializer):
    rostered = serializers.SerializerMethodField()

    class Meta:
        model = Interview
        exclude = ['created_at', 'modified_at', 'modified_by', 'created_by']

        child_model = InterViewAnswer
        internal_user_field = 'internal_interviewer'
        external_user_field = 'external_interviewer'
        child_related_name = 'interview_question_answers'
        parent_field_name = 'interview'

    @staticmethod
    def get_rostered(interview):
        return bool(interview.job_apply.data.get('rostered'))

    def get_fields(self):
        fields = super().get_fields()
        fields['interview_question_answers'] = InterViewAnswerSerializer(
            fields=[
                'internal_interviewer', 'external_interviewer',
                'id', 'link_expired', 'frontend_link', 'status'
            ],
            context=self.context,
            many=True
        )
        return fields


class ReferenceCheckAnswerSerializer(ProcessAnswerSerializer):
    score = serializers.SerializerMethodField()

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.upper() == 'GET':
            fields['internal_reference_checker'] = UserThinSerializer()
            fields['external_reference_checker'] = ReferenceCheckerSerializer(
                fields=['id', 'user', 'uuid'], read_only=True)
        return fields

    class Meta:
        model = ReferenceCheckAnswer
        fields = '__all__'

    @staticmethod
    def get_score(instance):
        return instance.data.get('given_score')


class ReferenceCheckSerializer(ApplicantProcessSerializer):
    job_title = serializers.ReadOnlyField(source='job_apply.job.title.title')
    applicant_id = serializers.ReadOnlyField(source='job_apply.applicant_id')
    references = serializers.SerializerMethodField()

    class Meta:
        model = ReferenceCheck
        exclude = ['created_at', 'modified_at', 'modified_by', 'created_by']

        child_model = ReferenceCheckAnswer
        internal_user_field = 'internal_reference_checker'
        external_user_field = 'external_reference_checker'
        child_related_name = 'reference_check_question_answers'
        parent_field_name = 'reference_check'

    def get_fields(self):
        fields = super().get_fields()
        fields['reference_check_question_answers'] = ReferenceCheckAnswerSerializer(
            fields=[
                'internal_reference_checker', 'external_reference_checker',
                'id', 'link_expired', 'frontend_link', 'status'
            ],
            context=self.context,
            many=True
        )
        return fields

    def get_references(self, instance):
        return ReferenceCheckerSerializer(
            ReferenceChecker.objects.filter(
                user__applicant=instance.job_apply.applicant_id
            ),
            many=True,
            context=self.context
        ).data
