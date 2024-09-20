from django.db.models import F, Q, ExpressionWrapper, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.contrib.auth import get_user_model
from django.core import exceptions
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.filters import SearchFilter

from irhrs.core.utils.filters import FilterMapBackend
from irhrs.core.mixins.viewset_mixins import (
    ListViewSetMixin
)
from irhrs.appraisal.models.appraiser_setting import Appraisal
from irhrs.appraisal.models.performance_appraisal import SubPerformanceAppraisalSlotWeight
from irhrs.appraisal.models.performance_appraisal_setting import StepUpDownRecommendation
from irhrs.appraisal.utils.util import AppraisalSettingFilterMixin
from irhrs.core.mixins.viewset_mixins import  OrganizationMixin
from irhrs.appraisal.api.v1.views.performance_appraisal import SubPerformanceAppraisalMixin
from irhrs.appraisal.api.v1.serializers.recommendation_report import (
    RecommendationReportSerializer, AppraisalEmploymentReviewSerializer, AppraisalEmploymentReviewListSerializer)
from irhrs.core.utils.filters import FilterMapBackend, NullsAlwaysLastOrderingFilter, OrderingFilterMap
from irhrs.core.mixins.serializers import DummySerializer
from irhrs.hris.constants import EXPIRED, POST_TASK_COMPLETED
from irhrs.users.utils.common_utils import increment_experience
from irhrs.hris.models import ChangeType

User = get_user_model()


class RecommendationReportViewSet(SubPerformanceAppraisalMixin,ListViewSetMixin, OrganizationMixin):
    queryset = SubPerformanceAppraisalSlotWeight.objects.all()
    serializer_class = RecommendationReportSerializer
    filter_backends = [FilterMapBackend, SearchFilter,NullsAlwaysLastOrderingFilter]
    filter_map = {
        'year': 'sub_performance_appraisal_slot__performance_appraisal_year',
        'slot': 'sub_performance_appraisal_slot',
    }
    search_fields = (
        'appraiser__first_name', 'appraiser__middle_name', 'appraiser__last_name'
    )
    ordering_fields_map = {
        'full_name': (
            'appraiser__first_name', 'appraiser__middle_name', 'appraiser__last_name'
        ),
        'percentage': 'percentage'
    }

    def get_queryset(self):
        return super().get_queryset().annotate(
            step_up_down=Coalesce(
                Subquery(
                    StepUpDownRecommendation.objects.filter(
                        score_acquired_from__lte=OuterRef('percentage'),
                        score_acquired_to__gte=OuterRef('percentage'),
                        sub_performance_appraisal_slot=OuterRef('sub_performance_appraisal_slot'),
                    ).values('change_step_by')[:1]),
                0
            )
        )


    @action(detail=False,
            methods=['POST'],
            url_path='start-review',
            serializer_class=AppraisalEmploymentReviewListSerializer
            )
    def start_employment_review(self, request, organization_slug, sub_performance_appraisal_slot_id):
        employment_review_list_serializer = AppraisalEmploymentReviewListSerializer(data=request.data, context=self.get_serializer_context())
        employment_review_list_serializer.is_valid(raise_exception=True)
        emplpoyment_review_serializer = AppraisalEmploymentReviewSerializer(data=employment_review_list_serializer.data.get("employee_review_list"),
                                                                            many=True,
                                                                            context=self.get_serializer_context())
        emplpoyment_review_serializer.is_valid(raise_exception=True)
        emplpoyment_review_serializer.save()
        return Response(
            {'detail': 'Successfully started employment reviews for given employees.'},
            status=status.HTTP_201_CREATED
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx.update({
          "queryset": self.get_queryset()
        })
        return ctx
