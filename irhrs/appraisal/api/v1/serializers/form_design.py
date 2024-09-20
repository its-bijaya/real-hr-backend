from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Subquery, OuterRef, IntegerField, F, Value, ExpressionWrapper, \
    DurationField
from django.db.models.functions import Coalesce
from rest_framework import serializers

from irhrs.appraisal.api.v1.serializers.question_set import \
    PerformanceAppraisalQuestionSetSerializer
from irhrs.appraisal.constants import SELF_APPRAISAL, SUPERVISOR_APPRAISAL, PEER_TO_PEER_FEEDBACK, \
    SUBORDINATE_APPRAISAL, APPRAISAL_TYPE, SENT, REVIEWER_EVALUATION, RECEIVED, ACTIVE, GENERATED, \
    NOT_GENERATED
from irhrs.appraisal.models.appraiser_setting import Appraisal
from irhrs.appraisal.models.form_design import PerformanceAppraisalFormDesign, \
    PerformanceAppraisalAnswerType, KAARFormDesign, KAARAnswerType
from irhrs.appraisal.models.key_achievement_and_rating_pa import KeyAchievementAndRatingAppraisal, \
    KAARAppraiserConfig
from irhrs.appraisal.models.performance_appraisal_setting import DeadlineExtendCondition
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils.common import DummyObject
from irhrs.notification.utils import add_notification
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer

User = get_user_model()


class PerformanceAppraisalAnswerTypeSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = PerformanceAppraisalAnswerType
        fields = ('question_type', 'answer_type', 'description', 'is_mandatory')


class KAARAnswerTypeSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = KAARAnswerType
        fields = ('question_type', 'answer_type', 'description', 'is_mandatory')


class PerformanceAppraisalFormDesignSerializer(DynamicFieldsModelSerializer):
    answer_types = PerformanceAppraisalAnswerTypeSerializer(many=True)

    class Meta:
        model = PerformanceAppraisalFormDesign
        fields = (
            'appraisal_type', 'instruction_for_evaluator', 'include_kra', 'caption_for_kra',
            'include_ksa', 'caption_for_ksa', 'include_kpi', 'caption_for_kpi',
            'generic_question_set', 'add_feedback', 'answer_types'
        )

    def get_fields(self):
        fields = super().get_fields()
        if self.request.method.lower() == 'get':
            fields['generic_question_set'] = PerformanceAppraisalQuestionSetSerializer(
                fields=('id', 'name')
            )

        return fields

    def create(self, validated_data):
        answer_types = validated_data.pop('answer_types')
        validated_data['sub_performance_appraisal_slot'] = self.context.get(
            'sub_performance_appraisal_slot')
        instance = super().create(validated_data)

        answer_type_instances = []
        for answer_type in answer_types:
            answer_type_instances.append(
                PerformanceAppraisalAnswerType(
                    form_design=instance,
                    **answer_type
                )
            )
        if answer_type_instances:
            PerformanceAppraisalAnswerType.objects.bulk_create(answer_type_instances)
        return instance


class KAARFormDesignSerializer(DynamicFieldsModelSerializer):
    kaar_answer_types = KAARAnswerTypeSerializer(many=True)

    class Meta:
        model = KAARFormDesign
        fields = (
            'instruction_for_evaluator', 'include_kra', 'caption_for_kra',
            'include_ksa', 'caption_for_ksa', 'include_kpi', 'caption_for_kpi',
            'generic_question_set', 'add_feedback', 'kaar_answer_types'
        )

    def get_fields(self):
        fields = super().get_fields()
        if self.request.method.lower() == 'get':
            fields['generic_question_set'] = PerformanceAppraisalQuestionSetSerializer(
                fields=('id', 'name')
            )

        return fields

    def create(self, validated_data):
        answer_types = validated_data.pop('kaar_answer_types')
        sub_performance_appraisal_slot = self.context.get('sub_performance_appraisal_slot')
        if hasattr(sub_performance_appraisal_slot, 'kaar_form_design'):
            sub_performance_appraisal_slot.kaar_form_design.delete()
        validated_data['sub_performance_appraisal_slot'] = self.context.get(
            'sub_performance_appraisal_slot')
        instance = super().create(validated_data)

        answer_type_instances = []
        for answer_type in answer_types:
            answer_type_instances.append(
                KAARAnswerType(
                    form_design=instance,
                    **answer_type
                )
            )
        if answer_type_instances:
            KAARAnswerType.objects.bulk_create(answer_type_instances)
        return instance


class AppraiseeQuestionSetCountBySerializer(UserThinSerializer):
    question_set_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'full_name',
            'profile_picture',
            'cover_picture',
            'job_title',
            'is_current',
            'organization',
            'question_set_count'
        ]

    @staticmethod
    def get_question_set_count(obj):
        return {
            SELF_APPRAISAL: {
                'saved': obj.saved_self_appraisal,
                'received': obj.received_self_appraisal,
                'sent': obj.sent_self_appraisal,
                'approved': obj.approved_self_appraisal,
            },
            SUPERVISOR_APPRAISAL: {
                'saved': obj.saved_supervisor_appraisal,
                'received': obj.received_supervisor_appraisal,
                'sent': obj.sent_supervisor_appraisal,
                'approved': obj.approved_supervisor_appraisal,
            },
            SUBORDINATE_APPRAISAL: {
                'saved': obj.saved_subordinate_appraisal,
                'received': obj.received_subordinate_appraisal,
                'sent': obj.sent_subordinate_appraisal,
                'approved': obj.approved_subordinate_appraisal,
            },
            PEER_TO_PEER_FEEDBACK: {
                'saved': obj.saved_peer_to_peer_feedback,
                'received': obj.received_peer_to_peer_feedback,
                'sent': obj.sent_peer_to_peer_feedback,
                'approved': obj.approved_peer_to_peer_feedback,
            }
        }


class AppraiseeAppraiserQuestionSetCountSerializer(UserThinSerializer):
    question_set_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'full_name',
            'profile_picture',
            'cover_picture',
            'job_title',
            'is_current',
            'organization',
            'question_set_count'
        ]

    @staticmethod
    def get_question_set_count(obj):
        return {
            SELF_APPRAISAL: obj.sent_self_appraisal,
            SUPERVISOR_APPRAISAL: obj.sent_supervisor_appraisal,
            SUBORDINATE_APPRAISAL: obj.sent_subordinate_appraisal,
            PEER_TO_PEER_FEEDBACK: obj.sent_peer_to_peer_feedback
        }


class KAARAppraiserQuestionSetCountBySerializer(DynamicFieldsModelSerializer):
    question_set_count = serializers.SerializerMethodField()
    appraisee = UserThinSerializer()

    class Meta:
        model = KeyAchievementAndRatingAppraisal
        fields = [
            'appraisee',
            'question_set_count'
        ]

    @staticmethod
    def get_question_set_count(obj):
        return {
            SELF_APPRAISAL: {
                'generated': obj.generated_self_appraisal,
                'received': obj.received_self_appraisal,
                'submitted': obj.submitted_self_appraisal,
            },
            SUPERVISOR_APPRAISAL: {
                'generated': obj.generated_supervisor_appraisal,
                'received': obj.received_supervisor_appraisal,
                'submitted': obj.submitted_supervisor_appraisal,
            },
            REVIEWER_EVALUATION: {
                'generated': obj.generated_reviewer_appraisal,
                'received': obj.received_reviewer_appraisal,
                'submitted': obj.submitted_reviewer_appraisal
            },
        }


def get_appraiser_config_id(obj, appraiser_type):
    appraiser_configs = obj.appraiser_configs.filter(appraiser_type=appraiser_type)
    return appraiser_configs.first().id if appraiser_configs else ""


class KeyAchievementAndRatingAppraisalQuestionSetCount(DynamicFieldsModelSerializer):
    question_set_count = serializers.SerializerMethodField()
    appraisee = UserThinSerializer()

    class Meta:
        model = KeyAchievementAndRatingAppraisal
        fields = [
            'appraisee',
            'question_set_count'
        ]

    @staticmethod
    def get_question_set_count(obj):
        return {
            SELF_APPRAISAL: {
                'count': obj.self_appraiser_question_count,
                'appraiser_config_id': get_appraiser_config_id(obj, SELF_APPRAISAL)
            },
            SUPERVISOR_APPRAISAL: {
                'count': obj.supervisor_appraiser_question_count,
                'appraiser_config_id': get_appraiser_config_id(obj, SUPERVISOR_APPRAISAL)
            },
            REVIEWER_EVALUATION: {
                'count': obj.reviewer_appraiser_question_count,
                'appraiser_config_id': get_appraiser_config_id(obj, REVIEWER_EVALUATION)
            },
        }


class SendQuestionSetSerializer(serializers.Serializer):
    appraisal_type = serializers.ChoiceField(
        choices=list(dict(APPRAISAL_TYPE).values())
    )
    start_date = serializers.DateTimeField()
    deadline = serializers.DateTimeField()

    def create(self, validated_data):
        appraisal_type = validated_data.get('appraisal_type')
        start_date = validated_data.get('start_date')
        deadline = validated_data.get('deadline')

        sub_performance_appraisal_slot = self.context['sub_performance_appraisal_slot']

        def convert_to_timedelta(actual_deadline, deadline_factor):
            return actual_deadline + ExpressionWrapper(
                timedelta(days=1) * deadline_factor,
                output_field=DurationField()
            )

        _ = Appraisal.objects.filter(
            sub_performance_appraisal_slot=sub_performance_appraisal_slot,
            appraisal_type=appraisal_type
        ).annotate(
            appraisee_count=Subquery(
                Appraisal.objects.filter(
                    sub_performance_appraisal_slot=sub_performance_appraisal_slot,
                    appraiser=OuterRef('appraiser')
                ).values(
                    'appraiser'
                ).order_by().annotate(
                    count=Count('id')
                ).values('count')[:1],
                output_field=IntegerField()
            )
        ).annotate(
            deadline_update_factor=Subquery(
                DeadlineExtendCondition.objects.filter(
                    sub_performance_appraisal_slot=sub_performance_appraisal_slot,
                    total_appraise_count_ranges_from__lte=OuterRef('appraisee_count'),
                    total_appraise_count_ranges_to__gte=OuterRef('appraisee_count'),
                ).values_list('extended_days')[:1]
            )
        ).annotate(
            updated_deadline=convert_to_timedelta(
                actual_deadline=Value(deadline),
                deadline_factor=Coalesce(
                    F('deadline_update_factor'),
                    Value(0)
                )
            )
        ).update(
            start_date=start_date,
            deadline=F('updated_deadline')
        )
        sub_performance_appraisal_slot.question_set_status = SENT
        sub_performance_appraisal_slot.save()
        return DummyObject(**validated_data)


class SendKAARQuestionSetSerializer(serializers.Serializer):
    # these fields are added here for future purpose, if we want to add deadline to appraiser
    appraisal_type = serializers.ChoiceField(
        choices=list(dict(APPRAISAL_TYPE).values()),
        required=False
    )
    start_date = serializers.DateTimeField(required=False)
    deadline = serializers.DateTimeField(required=False)

    @property
    def request(self):
        return self.context['request']

    def create(self, validated_data):
        sub_performance_appraisal_slot = self.context['sub_performance_appraisal_slot']
        update_dict = {
            'start_date': validated_data.get('start_date'),
            'deadline': validated_data.get('deadline')
        }
        appraiser_type = validated_data.get('appraisal_type')
        appraiser_configs = KAARAppraiserConfig.objects.filter(
            kaar_appraisal__sub_performance_appraisal_slot=sub_performance_appraisal_slot,
            appraiser_type=appraiser_type,
            question_status=GENERATED
        )
        if appraiser_type == SELF_APPRAISAL:
            update_dict['question_status'] = RECEIVED
            for appraiser_config in appraiser_configs:
                add_notification(
                    text=f"Performance Appraisal Review Forms has been assigned to you.",
                    action=appraiser_config,
                    recipient=appraiser_config.appraiser,
                    actor=self.request.user,
                    url=f'/user/pa/appraisal/{sub_performance_appraisal_slot.id}/kaarForms'
                )

        appraiser_configs.update(
            **update_dict
        )
        sub_performance_appraisal_slot.question_set_status = SENT
        sub_performance_appraisal_slot.save()
        return DummyObject(**validated_data)
