from collections import defaultdict

from django.db import transaction
from django.db.models import Q
from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer, DummySerializer
from irhrs.core.utils.common import DummyObject
from irhrs.core.validators import validate_future_datetime
from irhrs.recruitment.api.v1.serializers.external_profile import ExternalUserSerializer
from irhrs.recruitment.api.v1.serializers.question import (
    QuestionSetSerializer
)
from irhrs.recruitment.constants import COMPLETED
from irhrs.recruitment.models import Template


class ApplicantProcessSerializer(DynamicFieldsModelSerializer):
    scheduled_at = serializers.DateTimeField(
        validators=[validate_future_datetime])
    email_template_external = serializers.SlugRelatedField(
        queryset=Template.objects.all(),
        slug_field='slug'
    )
    candidate = serializers.SerializerMethodField()
    completed_ratio = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()

    class Meta:
        model = None
        exclude = ['created_at', 'modified_at', 'modified_by', 'created_by']

        child_model = None
        internal_user_field = None
        external_user_field = None
        child_related_name = None
        parent_field_name = None

    @staticmethod
    def get_score(instance):
        return '{:0.2f}'.format(instance.score or 0)

    @staticmethod
    def get_candidate(instance):
        return ExternalUserSerializer(
            fields=['full_name', 'profile_picture', 'phone_number', 'email', 'gender'],
            instance=instance.job_apply.applicant.user
        ).data

    @staticmethod
    def get_completed_ratio(instance):
        return f'{instance.completed_answers.count()}/{instance.question_answers.count()}'

    def remove_user(self, instance, question_answers):
        internal_user = self.Meta.internal_user_field
        external_user = self.Meta.external_user_field

        _new_internal_user = set(
            map(
                lambda x: x.get(internal_user),
                filter(
                    lambda x: x.get(internal_user, None),
                    question_answers
                )
            )
        )
        _new_external_user = set(
            map(
                lambda x: x.get(external_user),
                filter(
                    lambda x: x.get(external_user, None),
                    question_answers
                )
            )
        )

        instance.question_answers.exclude(
            Q(
                **{f"{internal_user}__in": _new_internal_user}
            ) | Q(
                **{f"{external_user}__in": _new_external_user}
            )
        ).delete()

        _existing_users = defaultdict(set)

        _existing_users_list = instance.question_answers.filter(
            Q(
                **{f"{internal_user}__in": _new_internal_user}
            ) | Q(
                **{f"{external_user}__in": _new_external_user}
            )
        ).values(internal_user, external_user)

        for user in _existing_users_list:
            for key, value in user.items():
                if value:
                    _existing_users[key].add(value)

        def filter_new_user(_user):
            external = _user.get(external_user)
            internal = _user.get(internal_user)

            old_external_user = _existing_users.get(external_user)
            old_internal__user = _existing_users.get(internal_user)

            if external and old_external_user and external.id in old_external_user:
                return False

            if internal and old_internal__user and internal.id in old_internal__user:
                return False
            return True

        new_user = list(filter(filter_new_user, question_answers))
        return new_user, _existing_users

    def update(self, instance, validated_data):
        with transaction.atomic():
            internal_user = self.Meta.internal_user_field
            external_user = self.Meta.external_user_field
            interviewer_weightage = ''
            if 'interviewer_weightage' in self.Meta.__dict__.keys():
                interviewer_weightage = self.Meta.interviewer_weightage

            question_answers = validated_data.pop(self.Meta.child_related_name, [])
            # filter out empty values
            question_answers = list(filter(lambda x: bool(x), question_answers))

            question_set = validated_data.get('question_set')
            instance = super().update(instance, validated_data)

            new_user, old_user = self.remove_user(
                instance=instance,
                question_answers=question_answers
            )

            question_set_data = QuestionSetSerializer(
                instance=question_set,
                context={'request': DummyObject(method='GET')}
            ).data

            if old_user:
                self.Meta.child_model.objects.filter(
                    Q(**{self.Meta.parent_field_name: instance}),
                    Q(
                        **{f"{internal_user}__in": old_user.get(internal_user, [])}
                    ) |
                    Q(
                        **{f"{external_user}__in": old_user.get(external_user, [])}
                    )
                ).update(data=question_set_data)
            if getattr(instance, 'has_weightage', False):
                question_answer_list = [
                    self.Meta.child_model(
                        **{self.Meta.parent_field_name: instance},
                        **{
                            f"{internal_user}": data.get(internal_user),
                            f"{external_user}": data.get(external_user),
                            f"{interviewer_weightage}": data.get(interviewer_weightage)
                        },
                        data=question_set_data,
                    ) for data in new_user
                ]
            else:
                question_answer_list = [
                    self.Meta.child_model(
                        **{self.Meta.parent_field_name: instance},
                        **{
                            f"{internal_user}": data.get(internal_user),
                            f"{external_user}": data.get(external_user)
                        },
                        data=question_set_data,
                    ) for data in new_user
                ]
            new_objects = self.Meta.child_model.objects.bulk_create(
                question_answer_list)

            for obj in new_objects:
                transaction.on_commit(lambda: self.send_email_and_notifications(obj=obj))
        return instance

    @staticmethod
    def send_email_and_notifications(obj):
        if hasattr(obj, 'send_mail') and callable(obj.send_mail):
            obj.send_mail()
        if hasattr(obj, 'send_notification') and callable(obj.send_notification):
            obj.send_notification()


class AnswerSerializer(DummySerializer):

    def validate(self, attrs):
        if not self.initial_data.get('answers'):
            raise serializers.ValidationError(
                {'answers': _('Answer is required for mandatory question')}
            )
        return super().validate(attrs)


class QuestionAnswerSerializer(DummySerializer):
    is_mandatory = serializers.BooleanField(required=False)
    question = serializers.JSONField(required=False)

    def validate(self, attrs):
        if attrs.get('is_mandatory'):
            ser = AnswerSerializer(data=attrs.get('question'))
            ser.is_valid(raise_exception=True)
        return super().validate(attrs)


class QuestionAnswerSectionSerializer(DummySerializer):
    questions = QuestionAnswerSerializer(many=True)


class ProcessAnswerSerializer(DynamicFieldsModelSerializer):
    frontend_link = serializers.ReadOnlyField()
    questions = serializers.SerializerMethodField()
    candidate = serializers.SerializerMethodField()
    job_title = serializers.ReadOnlyField(source='parent.job_apply.job_title')
    job_slug = serializers.ReadOnlyField(source='parent.job_apply.job.slug')
    verified = serializers.ReadOnlyField(source='parent.verified')
    scheduled_at = serializers.ReadOnlyField(source='parent.scheduled_at')
    applicant_id = serializers.ReadOnlyField(source='parent.job_apply.applicant_id')

    class Meta:
        model = None
        fields = '__all__'

    def get_questions(self, instance):
        question_set = instance.parent.question_set
        return QuestionSetSerializer(instance=question_set, context=self.context).data

    @staticmethod
    def get_candidate(instance):
        return ExternalUserSerializer(
            fields=['full_name', 'profile_picture', 'phone_number', 'email', 'gender'],
            instance=instance.parent.job_apply.applicant.user
        ).data

    def validate(self, attrs):
        if self.instance:
            if self.instance.status == COMPLETED or (
                self.instance.parent.status == COMPLETED
            ):
                raise ValidationError({
                    'non_field_errors': ['This reference check has already been completed.']
                })
        status = attrs.get('status')

        if attrs.get('data'):
            if attrs.get('data').get('sections'):
                sections = attrs.get('data').get('sections')
                ser = QuestionAnswerSectionSerializer(many=True, data=sections)
                ser.is_valid(raise_exception=True)

            overall_remarks = attrs.get('data').get('overall_remarks')
            is_recommended = attrs.get('data').get('is_recommended')
            if status and not overall_remarks:
                raise ValidationError({
                    'overall_remarks': ['This field is required.']
                })

            if status and not is_recommended:
                raise ValidationError({
                    'is_recommended': ['This field is required.']
                })

        return super().validate(attrs)
