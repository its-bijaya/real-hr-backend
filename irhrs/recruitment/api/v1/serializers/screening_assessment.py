from copy import deepcopy

from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.notification.utils import add_notification
from irhrs.recruitment.api.v1.serializers import (
    ApplicantProcessSerializer,
    ProcessAnswerSerializer, QuestionAnswerSectionSerializer
)
from irhrs.recruitment.api.v1.serializers.external_profile import (
    ExternalUserSerializer,
    ExternalSerializer
)
from irhrs.recruitment.api.v1.serializers.question import QuestionSetSerializer
from irhrs.recruitment.constants import PROGRESS, PENDING
from irhrs.recruitment.models import (
    PreScreening,
    PostScreening,
    PreScreeningInterview, PreScreeningInterviewAnswer, Assessment, AssessmentAnswer
)
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer

USER = get_user_model()


class ScreeningCreateSerializerMixin(DynamicFieldsModelSerializer):
    text = ''
    notification_url = None
    candidate = serializers.SerializerMethodField()
    job_title = serializers.SerializerMethodField()
    applicant_id = serializers.ReadOnlyField(source='job_apply.applicant.id')

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.upper() == 'GET':
            fields['responsible_person'] = UserThinSerializer()
            fields['questions'] = serializers.SerializerMethodField()
            fields['job_title'] = serializers.ReadOnlyField(
                source='job_apply.job.title.title'
            )
            fields['job_slug'] = serializers.ReadOnlyField(
                source='job_apply.job.slug'
            )
        return fields

    def create(self, validated_data):
        obj = super().create(validated_data)
        if self.request and self.request.user != obj.responsible_person:
            text = self.text
            recipient = obj.responsible_person
            action = obj
            add_notification(
                text,
                recipient,
                action,
                url=obj.notification_link
            )
        return obj

    @staticmethod
    def validate_status(status):
        if status not in [PENDING, PROGRESS]:
            raise serializers.ValidationError(_('Only Pending and Progress status is supported.'))
        return status

    @staticmethod
    def validate_data(data):
        sections = data.get('sections')
        ser = QuestionAnswerSectionSerializer(many=True, data=sections)
        ser.is_valid(raise_exception=True)
        return data

    def update(self, instance, validated_data):
        responsible_person = validated_data.pop('responsible_person', None)
        if responsible_person:
            responsible_person_changed = instance.responsible_person and (
                instance.responsible_person != responsible_person)
            if responsible_person_changed:
                instance = super().update(instance, validated_data)

                new_instance = deepcopy(instance)
                new_instance.pk = instance.pk
                new_instance.data = instance.job_apply.pre_screening.data if isinstance(
                    instance, PostScreening) else None
                new_instance.responsible_person = responsible_person
                instance.delete()
                new_instance.save()
            else:
                new_instance = super().update(instance, validated_data)
                new_instance.responsible_person = responsible_person
                new_instance.save()

            add_notification(
                self.text,
                new_instance.responsible_person,
                new_instance,
                url=instance.notification_link
            )

            return new_instance
        else:
            return super().update(instance, validated_data)

    @staticmethod
    def get_job_title(obj):
        return obj.job_apply.data.get('job_title') or obj.job_apply.job.title.title

    def get_questions(self, instance):
        question_set = instance.question_set
        return QuestionSetSerializer(instance=question_set, context=self.context).data

    @staticmethod
    def get_candidate(instance):
        return ExternalUserSerializer(
            fields=['full_name', 'profile_picture', 'phone_number', 'email', 'gender'],
            instance=instance.job_apply.applicant.user
        ).data


class PreScreeningSerializer(ScreeningCreateSerializerMixin):
    text = 'You have been assigned as Responsible person for Preliminary Shortlist of a candidate.'
    responsible_person = serializers.PrimaryKeyRelatedField(
        default=CurrentUserDefault(),
        queryset=USER.objects.all()
    )

    class Meta:
        model = PreScreening
        fields = '__all__'
        read_only_fields = ['verified', 'job_apply']


class PostScreeningSerializer(ScreeningCreateSerializerMixin):
    text = 'You have been assigned as Responsible person for Final Shortlist of a candidate.'

    class Meta:
        model = PostScreening
        fields = '__all__'
        read_only_fields = ['verified', 'job_apply']


class PreScreeningInterviewAnswerSerializer(ProcessAnswerSerializer):
    score = serializers.SerializerMethodField()

    class Meta:
        model = PreScreeningInterviewAnswer
        fields = '__all__'

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.upper() == 'GET':
            fields['internal_interviewer'] = UserThinSerializer()
            fields['external_interviewer'] = ExternalSerializer(
                fields=['id', 'user'])
        return fields

    @staticmethod
    def get_score(instance):
        return instance.data.get('percentage')

    def validate(self, attrs):
        interviewer_weightage = attrs.get('interviewer_weightage')
        if interviewer_weightage and interviewer_weightage <= 0:
            raise serializers.ValidationError(
                {"interviewer_weightage": "can not assign weightage less than 0."}
            )
        return super().validate(attrs)


class PreScreeningInterviewSerializer(ApplicantProcessSerializer):
    class Meta:
        model = PreScreeningInterview
        exclude = ['created_at', 'modified_at', 'modified_by', 'created_by']

        child_model = PreScreeningInterviewAnswer
        internal_user_field = 'internal_interviewer'
        external_user_field = 'external_interviewer'
        interviewer_weightage = 'interviewer_weightage'
        child_related_name = 'pre_screening_interview_question_answers'
        parent_field_name = 'pre_screening_interview'

    def get_fields(self):
        fields = super().get_fields()
        fields['pre_screening_interview_question_answers'] = PreScreeningInterviewAnswerSerializer(
            fields=[
                'internal_interviewer', 'external_interviewer',
                'id', 'link_expired', 'frontend_link', 'status', 'interviewer_weightage'
            ],
            many=True,
            context=self.context
        )
        return fields

    def validate(self, attrs):
        has_weightage = attrs.get('has_weightage')
        interviewer_and_weightage = attrs.get('pre_screening_interview_question_answers', [])
        total_weightage = 0
        for data in interviewer_and_weightage:
            weightage = data.get('interviewer_weightage', 0)
            total_weightage += weightage

        if has_weightage and total_weightage != 100:
            raise serializers.ValidationError(
                {'error': 'Total interviewer weightage must be 100%.'}
            )
        return super().validate(attrs)


class AssessmentAnswerSerializer(ProcessAnswerSerializer):
    score = serializers.SerializerMethodField()

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.upper() == 'GET':
            fields['internal_assessment_verifier'] = UserThinSerializer()
            fields['external_assessment_verifier'] = ExternalSerializer(
                fields=['id', 'user'])
        return fields

    class Meta:
        model = AssessmentAnswer
        fields = '__all__'

    @staticmethod
    def get_score(instance):
        return instance.data.get('percentage')


class AssessmentSerializer(ApplicantProcessSerializer):

    class Meta:
        model = Assessment
        exclude = ['created_at', 'modified_at', 'modified_by', 'created_by']

        child_model = AssessmentAnswer
        internal_user_field = 'internal_assessment_verifier'
        external_user_field = 'external_assessment_verifier'
        child_related_name = 'assessment_question_answers'
        parent_field_name = 'assessment'

    def get_fields(self):
        fields = super().get_fields()
        fields['assessment_question_answers'] = AssessmentAnswerSerializer(
            fields=[
                'internal_assessment_verifier', 'external_assessment_verifier',
                'id', 'link_expired', 'frontend_link', 'status'
            ],
            context=self.context,
            many=True
        )
        return fields
