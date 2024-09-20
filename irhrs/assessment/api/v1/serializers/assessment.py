import datetime

from django.contrib.auth import get_user_model
from django.db import transaction
from irhrs.core.utils import email
from django.db.models import Sum, Count, Value
from django.db.models.functions import Coalesce
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField, ReadOnlyField
from rest_framework.relations import PrimaryKeyRelatedField, SlugRelatedField

from irhrs.assessment.models.assessment import (UserAssessment, AssessmentSet, AssessmentQuestions,
                                                AssessmentSection, QuestionResponse)
from irhrs.assessment.models.helpers import COMPLETED, CANCELLED, PENDING
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer, DummySerializer
from irhrs.core.utils import get_system_admin
from irhrs.core.utils.training import set_training_members
from irhrs.core.utils.email import send_notification_email
from irhrs.core.constants.organization import ASSESSMENT_ASSIGNED_UNASSIGNED_TO_USER_EMAIL
from irhrs.notification.utils import add_notification
from irhrs.questionnaire.api.v1.serializers.questionnaire import (QuestionSerializer)
from irhrs.questionnaire.models.helpers import ASSESSMENT, CHECKBOX, RADIO, LINEAR_SCALE
from irhrs.questionnaire.models.questionnaire import Question
from irhrs.training.models import Training, UserTraining
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer

USER = get_user_model()


class AssessmentQuestionsSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = AssessmentQuestions
        fields = (
            'id', 'is_mandatory', 'question', 'order'
        )
        read_only_fields = ['order']

    def create(self, validated_data):
        assessment_section = self.context['assessment_section']
        validated_data['assessment_section'] = assessment_section
        validated_data['order'] = assessment_section.section_questions.count() + 1
        return super().create(validated_data)

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method == 'GET':
            fields['question'] = QuestionSerializer(
                context=self.context
            )
        else:
            fields['question'] = serializers.PrimaryKeyRelatedField(
                queryset=Question.objects.filter(question_type=ASSESSMENT)
            )
        return fields

    # as per new implementation this section has been commented out
    # @staticmethod
    # def _validate_weightage(assessment_section, question):
    #     assessment_set = assessment_section.assessment_set
    #     total_weightage = assessment_set.total_weightage
    #
    #     total_weightage_of_questions = calculate_total_weight(assessment_set) + question.weightage
    #
    #     if total_weightage_of_questions > total_weightage:
    #         raise ValidationError({
    #             'non_field_errors': 'Sum weight of questions for assessment set exceeded total'
    #                                 ' weightage of assessment set.'
    #         })

    def validate(self, attrs):
        assessment_section = self.context['assessment_section']
        question = attrs.get('question')
        qs = AssessmentQuestions.objects.filter(
            assessment_section__assessment_set=assessment_section.assessment_set
        )

        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        if qs.filter(question=question).exists():
            raise ValidationError({
                'question': f'This question already exits within \'{qs.first().assessment_section}\''
                            f' section in this assessment.'
            })

        # self._validate_weightage(assessment_section, question)
        # order = attrs.get('order')
        # # validate order of questions
        # if qs.filter(assessment_section=assessment_section, order=order).exists():
        #     raise ValidationError({
        #         'order': f'Question with order {order} already exits in this section.'
        #     })
        #
        # if order < 1:
        #     raise ValidationError({
        #         'order': f'Question with order {order} not accepted.'
        #     })
        return super().validate(attrs)


class QuestionResponseSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = QuestionResponse
        fields = (
            'id',
            'question',
            'answers',
            'score',
            'response',
            'remarks',
            'is_mandatory',
            'order'
        )
        read_only_fields = ('question', 'order')
        extra_kwargs = {
            'answers': {
                'required': False,
                'allow_empty': True
            }
        }

    def get_fields(self):
        fields = super().get_fields()
        if self.request:
            method = self.request.method
            if method == 'GET':
                fields['question'] = QuestionSerializer()
                # fields.pop('answers', None)
        return fields


class AssessmentSectionSerializer(DynamicFieldsModelSerializer):
    assessment_questions = AssessmentQuestionsSerializer(many=True, read_only=True)
    all_questions = SerializerMethodField(read_only=True)
    questions_count = ReadOnlyField()

    class Meta:
        model = AssessmentSection
        fields = (
            'title', 'description', 'assessment_set', 'total_weightage',
            'marginal_weightage', 'assessment_questions', 'id', 'questions_count',
            'all_questions'
        )

    def validate(self, attrs):
        assessment_set = attrs.get('assessment_set')
        if not assessment_set and self.instance:
            assessment_set = self.instance.assessment_set

        if assessment_set and assessment_set.assessments.exists():
            raise ValidationError({'non_field_errors': ['Assessment has already been added to user.']})
        return attrs

    def get_all_questions(self, obj):
        # Return Questions From User Response Table
        return QuestionResponseSerializer(
            instance=QuestionResponse.objects.filter(
                user_assessment=self.context.get('user_assessment'),
                section=obj
            ),
            # instance.question_responses.all(),
            context=self.context,
            many=True,
            read_only=True
        ).data
        # return AssessmentQuestionsSerializer(
        #     instance.section_questions.all(),
        #     many=True,
        #     context=self.context
        # ).data

    # def create(self, validated_data):
    #     questions = validated_data.pop('questions', [])
    #
    #     validated_data['organization'] = self.context['organization']
    #     instance = super().create(validated_data)
    #
    #     self.create_questions(questions, instance)
    #     return instance
    #
    # def update(self, instance, validated_data):
    #     self.create_questions(validated_data.pop('questions', []), instance, update=True)
    #     return super().update(instance, validated_data)
    #
    # @staticmethod
    # def create_questions(questions, instance, update=False):
    #     if update:
    #         no_longer_valid = set(
    #             instance.questions.values_list('pk', flat=True)
    #         ) - set(
    #             map(lambda x: x.get('question').id, questions)
    #         )
    #         AssessmentQuestions.objects.filter(
    #             question__in=no_longer_valid
    #         )
    #         for question in questions:
    #             AssessmentQuestions.objects.update_or_create(
    #                 assessment_set=instance,
    #                 question=question.get('question'),
    #                 defaults=dict(
    #                     is_mandatory=question.get('is_mandatory'),
    #                     order=question.get('order')
    #                 )
    #             )
    #     else:
    #         AssessmentQuestions.objects.bulk_create(
    #             [
    #                 AssessmentQuestions(
    #                     assessment_set=instance,
    #                     question=question.get('question'),
    #                     is_mandatory=question.get('is_mandatory'),
    #                     order=question.get('order')
    #                 ) for question in questions
    #             ]
    #         )


class AssessmentSetSerializer(DynamicFieldsModelSerializer):
    assigned_count = ReadOnlyField()
    sections = AssessmentSectionSerializer(
        fields=['title', 'id'],
        read_only=True,
        many=True
    )
    assigned_users = SerializerMethodField()
    expiry_date = SerializerMethodField()
    question = SerializerMethodField()

    class Meta:
        model = AssessmentSet
        fields = (
            'id', 'title', 'description', 'duration', 'expiry_date', 'sections', 'assigned_count',
            'assigned_users', 'question', 'marginal_percentage', 'marginal_weightage',
            'total_weightage'
        )
        read_only_fields = ['marginal_weightage', 'total_weightage']

    def get_expiry_date(self, obj):
        assessment = obj.assessments.filter(user=self.request.user).first()
        return assessment.expiry_date.astimezone() if assessment else None

    def validate_title(self, title):
        organization = self.context['organization']
        assessments = organization.assessments.all()
        if self.instance:
            assessments = assessments.exclude(id=self.instance.id)
        if assessments.filter(title__iexact=title).exists():
            raise ValidationError('Duplicate title for assessment set.')
        return title

    @staticmethod
    def validate_duration(duration):
        if duration < datetime.timedelta(minutes=5):
            raise ValidationError('Time durations not allowed.')
        return duration

    @staticmethod
    def get_assigned_users(obj):
        user_assessment = obj.assessments.all().select_related(
            'user', 'user__detail', 'user__detail__organization',
            'user__detail__job_title', 'user__detail__employment_level',
            'user__detail__division'
        )
        return AssessmentScoreSerializer(
            user_assessment,
            fields=('id', 'user', 'status', 'expiry_date'),
            many=True
        ).data

    @staticmethod
    def get_question(instance):
        return {
            'count': instance.total_questions,
            'total_weightage': instance.total_weightage
        }

    def create(self, validated_data):
        validated_data['organization'] = self.context['organization']
        return super().create(validated_data)


class AssessmentSetWithSectionSerializer(serializers.Serializer):
    assessment_set = AssessmentSetSerializer(
        fields=['title', 'description', 'duration', 'marginal_percentage']
    )
    assessment_sections = AssessmentSectionSerializer(many=True, fields=['title', 'description'])

    def create(self, validated_data):
        organization = self.context['organization']
        _data_assessment_sections = validated_data.get('assessment_sections')
        _data_assessment_set = validated_data.get('assessment_set')

        assessment_set = AssessmentSet.objects.create(organization=organization,
                                                      **_data_assessment_set)

        if not _data_assessment_sections:
            _data_assessment_sections = [{
                'title': assessment_set.title,
                'description': assessment_set.description
            }]

        assessment_section = []
        for section in _data_assessment_sections:
            assessment_section.append(
                AssessmentSection(
                    assessment_set=assessment_set,
                    total_weightage=0,
                    marginal_weightage=0,
                    **section
                )
            )
        AssessmentSection.objects.bulk_create(assessment_section)
        return validated_data


class UserAssessmentSerializer(DynamicFieldsModelSerializer):
    user = UserThinSerializer(
        read_only=True
    )
    assessment_set = AssessmentSetSerializer(
        read_only=True,
        exclude_fields=('sections', 'assigned_users')
    )

    class Meta:
        model = UserAssessment
        fields = (
            'user', 'assessment_set', 'status', 'started_at', 'ended_at', 'score', 'remarks',
            'optional_remarks', 'id',
        )


class AssignAssessmentToUserSerializer(DummySerializer):
    def get_fields(self):
        return {
            'users': PrimaryKeyRelatedField(
                queryset=USER.objects.filter(
                    detail__organization=self.context['organization']
                ).current(),
                many=True
            ),
            'expiry_date': serializers.DateTimeField(required=True)
        }

    def validate(self, attrs):
        assessment_set = self.context['assessment']

        if assessment_set.assessments.filter(user__in=attrs['users']).exists():
            raise ValidationError({
                'non_field_errors': ['Some of users are already assigned to this assessment set.']
            })

        # total_weightset = assessment_set.total_weightage
        # if calculate_total_weight(assessment_set) != total_weightset:
        #     raise ValidationError({
        #         'non_field_errors': ['Sum weight of questions for assessment set is not equals to'
        #                              ' total weightage of assessment set.']
        #     })
        return super().validate(attrs)

    @transaction.atomic()
    def create(self, validated_data):
        expiry_date = validated_data.get('expiry_date')
        user_assessments = UserAssessment.objects.bulk_create([
            UserAssessment(
                assessment_set=self.context['assessment'],
                user=user,
                status=PENDING,
                expiry_date=expiry_date
            )
            for user in validated_data.get('users')
        ])
        request = self.context['request']
        for user_assessment in user_assessments:
            user = user_assessment.user
            subject = "New assessments were assigned."
            message = f"'{user_assessment.assessment_set.title}' has been assigned to you."
            can_send_email = email.can_send_email(user, ASSESSMENT_ASSIGNED_UNASSIGNED_TO_USER_EMAIL)
            email_already_sent = email.has_sent_email(
                    recipient=user,
                    notification_text=message,
                    subject=subject
            )
            if can_send_email and not email_already_sent:
                send_notification_email(
                    recipients=[user.email],
                    subject=subject,
                    notification_text=message
                )
            add_notification(
                text=message,
                actor=request.user if request else get_system_admin(),
                action=user_assessment,
                recipient=user_assessment.user,
                url=f"/user/assessment/new-assessment"
            )


        return super().create(validated_data)


class AssessmentQuestionsPerCategories(DynamicFieldsModelSerializer):
    class Meta:
        model = AssessmentSection
        fields = (
            'id',
            'question',
            'answers',
            'score',
            'response',
            'remarks',
        )
        read_only_fields = 'question',


class AssessmentScoreSerializer(DynamicFieldsModelSerializer):
    assessment_set = AssessmentSetSerializer(
        exclude_fields=('assigned_users',)
    )
    user = UserThinSerializer()

    class Meta:
        model = UserAssessment
        fields = (
            'user', 'assessment_set', 'status', 'started_at', 'ended_at', 'score', 'remarks',
            'optional_remarks', 'id', 'associated_training', 'expiry_date'
        )
        read_only_fields = ['associated_training', 'expiry_date']

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if request and request.method.lower() == 'get':
            fields['associated_training'] = serializers.SlugRelatedField(
                slug_field='slug',
                queryset=Training.objects.all()
            )
        return fields


class AssignTrainingFromAssessmentSerializer(DummySerializer):
    def get_fields(self):
        organization = self.context.get('organization')
        return {
            'training': SlugRelatedField(
                queryset=Training.objects.filter(
                    training_type__organization=organization
                ),
                slug_field='slug'
            ),
            'user_assessments': PrimaryKeyRelatedField(
                queryset=UserAssessment.objects.filter(
                    assessment_set__organization=organization,
                    status=COMPLETED,
                    associated_training__isnull=True
                ),
                many=True
            )
        }

    def create(self, validated_data):
        user_training = []
        user_assessments = validated_data.get('user_assessments')
        training = validated_data.get('training')

        assigned_user_assessment = []
        for user_assessment in user_assessments:
            user = user_assessment.user
            if not UserTraining.objects.filter(
                    user=user,
                    training=training
            ).exists():
                request = self.context.get('request')
                if user not in assigned_user_assessment:
                    user_training.append(
                        UserTraining(
                            training_need=ASSESSMENT,
                            user=user,
                            training=training,
                            start=training.start,
                            end=training.end
                        )
                    )
                    assigned_user_assessment.append(user)
                add_notification(
                    text=f"You have been assigned to training \'{training.name}\'.",
                    recipient=user,
                    action=user_assessment,
                    url=f"/user/training?training={training.id}",
                    actor=request.user if request and request.user != user else None,
                )

        UserTraining.objects.bulk_create(user_training)
        UserAssessment.objects.filter(
            id__in=list(map(lambda x: getattr(x, 'id'), user_assessments))
        ).update(associated_training=training)

        set_training_members()
        return super().create(validated_data)

    def validate(self, attrs):
        training = attrs['training']

        if training.status in [COMPLETED, CANCELLED]:
            raise ValidationError('This training has be completed or cancelled.')

        # if UserTraining.objects.filter(
        #     user=self.context['user'],
        #     training=training
        # ).exists():
        #     raise ValidationError(
        #         "Already Assigned this training."
        #     )
        return attrs


class UserAssessmentRateSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = QuestionResponse
        fields = (
            'score', 'remarks'
        )

    def validate(self, attrs):
        if not self.instance:
            raise ValidationError(
                'Not supported for create!'
            )
        if self.instance.question.answer_type in [RADIO, CHECKBOX, LINEAR_SCALE]:
            raise ValidationError(
                'Only Subjective answers can be graded.'
            )
        return super().validate(attrs)
