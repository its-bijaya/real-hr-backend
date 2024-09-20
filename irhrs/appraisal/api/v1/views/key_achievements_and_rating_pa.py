from django.db import transaction
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import BasePermission
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from irhrs.appraisal.api.v1.permissions import PerformanceAppraisalSettingPermission
from irhrs.appraisal.api.v1.serializers.KAAR_score import KAARScoreSerializer
from irhrs.appraisal.api.v1.serializers.kaar_appraiser import KAARAppraiserSerializer
from irhrs.appraisal.api.v1.serializers.key_achivements_and_rating_pa import \
    KeyAchievementAndRatingAppraisalSerializer, \
    SupervisorEvaluationSerializer, ReviewerEvaluationSerializer
from irhrs.appraisal.api.v1.views.performance_appraisal import SubPerformanceAppraisalMixin
from irhrs.appraisal.constants import SUBMITTED, NOT_GENERATED, GENERATED, SAVED, \
    SUPERVISOR_APPRAISAL
from irhrs.appraisal.models.key_achievement_and_rating_pa import KeyAchievementAndRatingAppraisal, \
    KAARAppraiserConfig, SupervisorEvaluation, ReviewerEvaluation
from irhrs.appraisal.utils.kaar_appraisal import ForwardAppraisalQuestions, CalculateKaarScore
from irhrs.core.mixins.viewset_mixins import OrganizationMixin, GetStatisticsMixin
from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.filters import OrderingFilterMap, FilterMapBackend
from irhrs.permission.constants.permissions import PERFORMANCE_APPRAISAL_PERMISSION, \
    PERFORMANCE_APPRAISAL_SETTING_PERMISSION


class KeyAchievementAndRatingAppraisalViewSet(
    OrganizationMixin, SubPerformanceAppraisalMixin, ModelViewSet):
    queryset = KeyAchievementAndRatingAppraisal.objects.all()
    serializer_class = KeyAchievementAndRatingAppraisalSerializer
    permission_classes = [PerformanceAppraisalSettingPermission]


class KAARAppraiserViewSet(OrganizationMixin, SubPerformanceAppraisalMixin,
                           GetStatisticsMixin, ModelViewSet, BasePermission):
    queryset = KAARAppraiserConfig.objects.all()
    serializer_class = KAARAppraiserSerializer
    filter_backends = [DjangoFilterBackend, FilterMapBackend, SearchFilter, OrderingFilterMap]
    statistics_field = 'appraiser_type'
    filter_map = {
        'appraiser_type': 'appraiser_type',
        'appraisee': 'kaar_appraisal__appraisee',
        'username': 'kaar_appraisal__appraisee__username',
        'branch': 'kaar_appraisal__appraisee__detail__branch__slug',
        'division': 'kaar_appraisal__appraisee__detail__division__slug',
        'job_title': 'kaar_appraisal__appraisee__detail__job_title__slug',
        'employment_level': 'kaar_appraisal__appraisee__detail__employment_level__slug',
        'employment_type': 'kaar_appraisal__appraisee__detail__employment_status__slug',
    }

    search_fields = (
        'kaar_appraisal__appraisee__first_name', 'kaar_appraisal__appraisee__middle_name',
        'kaar_appraisal__appraisee__last_name', 'kaar_appraisal__appraisee__username'
    )

    @property
    def mode(self):
        mode = self.request.query_params.get('as')
        if mode in ['hr', 'supervisor']:
            return mode
        return 'user'

    def has_permission(self, request, view):
        if self.mode == 'hr':
            return validate_permissions(
                self.request.user.get_hrs_permissions(view.get_organization()),
                PERFORMANCE_APPRAISAL_PERMISSION,
                PERFORMANCE_APPRAISAL_SETTING_PERMISSION
            )
        return self.queryset.filter(
            Q(appraiser=self.request.user) | Q(kaar_appraisal__appraisee=self.request.user),
            kaar_appraisal__sub_performance_appraisal_slot=self.performance_appraisal_slot
        ).exists()

    def get_queryset(self):
        queryset = self.queryset.filter(
            kaar_appraisal__sub_performance_appraisal_slot=self.performance_appraisal_slot
        ).select_related(
            'appraiser',
            'kaar_appraisal',
            'kaar_appraisal__sub_performance_appraisal_slot',
            'kaar_appraisal__appraisee'
        ).prefetch_related(
            'kaar_appraisal__question_set',
            'kaar_appraisal__question_set__generic_questions',
            'kaar_appraisal__question_set__ksao_questions',
            'kaar_appraisal__question_set__kra_questions',
            'kaar_appraisal__question_set__kpi_questions',
        )
        if self.mode == 'user':
            queryset = queryset.exclude(
                question_status__in=[NOT_GENERATED, GENERATED]
            ).filter(appraiser=self.request.user)
        return queryset

    def list(self, request, *args, **kwargs):
        ret = super().list(request, *args, **kwargs)
        ret.data.update({
            'statistics': self.statistics
        })
        return ret

    @transaction.atomic
    @action(
        methods=['Post'],
        url_path='submit-answer',
        detail=True
    )
    def submit_answer(self, request, **kwargs):
        appraiser_config = self.get_object()
        question_status = SUBMITTED if request.data.get('answer_committed', False) else SAVED
        if appraiser_config.appraiser_type == SUPERVISOR_APPRAISAL:
            question_status = SAVED

        ser = KAARScoreSerializer(
            data=request.data, context={**self.get_serializer_context(), 'appraiser_config': appraiser_config}
        )
        ser.is_valid(raise_exception=True)
        ser.save()
        appraiser_config.question_status = question_status
        appraiser_config.save()
        if question_status == SUBMITTED:
            forward_question = ForwardAppraisalQuestions(
                appraiser_config, self.performance_appraisal_slot, self.request.user
            )
            forward_question.send_question_to_next_appraiser()
            forward_question.complete_kaar_appraisal()
            forward_question.send_notification_to_appraiser()
        cal = CalculateKaarScore(appraiser_config.kaar_appraisal)
        if appraiser_config.appraiser_type == SUPERVISOR_APPRAISAL and \
                not hasattr(appraiser_config, 'supervisor_evaluation'):
            cal.save_overall_rating()
        return Response(
            {'message': "Successfully updated.", 'data': cal.calculate_overall_rating()}
        )


class SupervisorEvaluationViewSet(
    OrganizationMixin,
    SubPerformanceAppraisalMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
    BasePermission
):
    queryset = SupervisorEvaluation.objects.all()
    serializer_class = SupervisorEvaluationSerializer

    def get_queryset(self):
        return self.queryset.filter(
            appraiser__kaar_appraisal__sub_performance_appraisal_slot=self.performance_appraisal_slot
        )

    @property
    def mode(self):
        mode = self.request.query_params.get('as')
        if mode in ['hr', 'supervisor']:
            return mode
        return 'user'

    def has_permission(self, request, view):
        if self.mode == 'hr':
            return validate_permissions(
                self.request.user.get_hrs_permissions(view.get_organization()),
                PERFORMANCE_APPRAISAL_PERMISSION,
                PERFORMANCE_APPRAISAL_SETTING_PERMISSION
            )
        return self.queryset.filter(
            Q(appraiser__appraiser=self.request.user) | Q(appraiser__appraiser_type=SUPERVISOR_APPRAISAL),
            appraiser__sub_performance_appraisal_slot=self.performance_appraisal_slot
        ).exists()


class ReviewerEvaluationViewSet(
    OrganizationMixin,
    SubPerformanceAppraisalMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
    BasePermission
):
    queryset = ReviewerEvaluation.objects.all()
    serializer_class = ReviewerEvaluationSerializer

    def get_queryset(self):
        queryset = self.queryset.filter(
            appraiser__kaar_appraisal__sub_performance_appraisal_slot=self.performance_appraisal_slot
        )
        if self.mode != 'hr':
            return queryset.filter(appraiser__appraiser=self.request.user)
        return queryset

    @property
    def mode(self):
        mode = self.request.query_params.get('as')
        if mode in ['hr', 'supervisor']:
            return mode
        return 'user'

    def has_permission(self, request, view):
        if self.mode == 'hr':
            return validate_permissions(
                self.request.user.get_hrs_permissions(view.get_organization()),
                PERFORMANCE_APPRAISAL_PERMISSION,
                PERFORMANCE_APPRAISAL_SETTING_PERMISSION
            )
        return True
