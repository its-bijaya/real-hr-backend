from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins
from rest_framework.filters import SearchFilter
from rest_framework.viewsets import GenericViewSet

from irhrs.appraisal.api.v1.permissions import PerformanceAppraisalSettingPermission
from irhrs.appraisal.api.v1.serializers.kaar_report import \
    KeyAchievementAndRatingAppraisalReportSerializer
from irhrs.appraisal.api.v1.views.performance_appraisal import SubPerformanceAppraisalMixin
from irhrs.appraisal.constants import SUPERVISOR_APPRAISAL, REVIEWER_EVALUATION
from irhrs.appraisal.models.key_achievement_and_rating_pa import KeyAchievementAndRatingAppraisal
from irhrs.core.mixins.viewset_mixins import OrganizationMixin
from irhrs.core.utils import nested_getattr
from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.filters import OrderingFilterMap, FilterMapBackend
from irhrs.export.mixins.export import BackgroundExcelExportMixin
from irhrs.permission.constants.permissions import PERFORMANCE_APPRAISAL_SETTING_PERMISSION, \
    PERFORMANCE_APPRAISAL_PERMISSION


class KeyAchievementAndRatingAppraisalReportViewSet(
    OrganizationMixin,
    SubPerformanceAppraisalMixin,
    mixins.ListModelMixin,
    GenericViewSet,
    BackgroundExcelExportMixin
):
    queryset = KeyAchievementAndRatingAppraisal.objects.all()
    serializer_class = KeyAchievementAndRatingAppraisalReportSerializer
    filter_backends = [DjangoFilterBackend, FilterMapBackend, SearchFilter, OrderingFilterMap]
    permission_classes = [PerformanceAppraisalSettingPermission]
    filter_map = {
        'appraisee': 'appraisee',
        'username': 'appraisee__username',
        'status': 'status',
        'is_appraisee_satisfied': 'is_appraisee_satisfied',
        'branch': 'appraisee__detail__branch__slug',
        'division': 'appraisee__detail__division__slug',
        'job_title': 'appraisee__detail__job_title__slug',
        'employment_level': 'appraisee__detail__employment_level__slug',
        'employment_type': 'appraisee__detail__employment_status__slug',
    }
    search_fields = (
        'appraisee__first_name', 'appraisee__middle_name', 'appraisee__last_name',
        'appraisee__username'
    )
    ordering_fields_map = {
        'full_name': (
            'appraisee__first_name', 'appraisee__middle_name', 'appraisee__last_name',
        ),
        'status': 'status',
        'is_appraisee_satisfied': 'is_appraisee_satisfied',
        'kpi_score': 'overall_rating__kpi_score',
        'ksao_score': 'overall_rating__ksao_score'
    }

    export_type = "Key Achievement and Rating Appraisal Report"

    export_fields = {
        'Full Name': 'appraisee.full_name',
        'User Name': 'appraisee.username',
        'Supervisor': 'supervisor_name',
        'Reviewer': 'reviewer_name',
        'Satisfied': 'is_appraisee_satisfied',
        'KPI Score': 'kpi_scores',
        'Competencies Score': 'ksao_scores',
        'Status': 'status'
    }

    @property
    def user(self):
        return self.request.user

    @property
    def mode(self):
        mode = self.request.query_params.get('as', 'user')
        if mode == "hr" and validate_permissions(
            self.user.get_hrs_permissions(
                self.get_organization()
            ),
            PERFORMANCE_APPRAISAL_PERMISSION,
            PERFORMANCE_APPRAISAL_SETTING_PERMISSION
        ):
            return mode
        return 'user'

    def check_permissions(self, request):
        if self.mode == "user":
            return True
        super().check_permissions(request)

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'sub_performance_appraisal_slot',
            'appraisee',
            'appraisee__detail'
        )
        if self.mode == "user":
            return queryset.filter(appraisee=self.user)
        return queryset

    @staticmethod
    def prepare_export_object(obj, **kwargs):
        overall_rating = obj.overall_rating or {}
        obj.kpi_scores = overall_rating.get('kpi_score')
        obj.ksao_scores = overall_rating.get('ksao_score')
        def get_evaluator(appraiser_type):
            evaluators = obj.appraiser_configs.filter(appraiser_type=appraiser_type).first()
            return nested_getattr(evaluators, 'appraiser.full_name')

        obj.supervisor_name = get_evaluator(SUPERVISOR_APPRAISAL)
        obj.reviewer_name = get_evaluator(REVIEWER_EVALUATION)
        return obj

