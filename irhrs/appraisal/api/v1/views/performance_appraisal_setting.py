from django.contrib.auth import get_user_model

from irhrs.appraisal.api.v1.permissions import PerformanceAppraisalSettingPermission
from irhrs.appraisal.api.v1.serializers.performance_appraisal_setting import (
    AppraisalSettingSerializer, ScoreAndScalingSettingSerializer,
    DeadlineExtendConditionSerializer, DeadlineExceedScoreDeductionConditionSerializer,
    StepUpDownRecommendationSerializer, FormReviewSettingSerializer, StepUpDownCriteriaSerializer,
    DeductionCriteriaSerializer, ExceptionalAppraiseeFilterSettingSerializer
)
from irhrs.appraisal.api.v1.views.performance_appraisal import SubPerformanceAppraisalMixin
from irhrs.appraisal.constants import PERCENTAGE
from irhrs.appraisal.models.performance_appraisal_setting import (
    AppraisalSetting, ScoreAndScalingSetting, DeadlineExtendCondition,
    DeadlineExceedScoreDeductionCondition, StepUpDownRecommendation, FormReviewSetting
)
from irhrs.appraisal.utils.common import _validate_repeated_data, _validate_overlapped_data
from irhrs.core.mixins.viewset_mixins import (
    OrganizationMixin, CreateListModelMixin,
    ListCreateViewSetMixin, CreateViewSetMixin
)

User = get_user_model()


class AppraisalSettingViewSet(OrganizationMixin, SubPerformanceAppraisalMixin,
                              ListCreateViewSetMixin):
    queryset = AppraisalSetting.objects.all()
    serializer_class = AppraisalSettingSerializer
    permission_classes = [PerformanceAppraisalSettingPermission]


class ExceptionalAppraiseeFilterSettingViewSet(
    OrganizationMixin, SubPerformanceAppraisalMixin,
    CreateViewSetMixin
):
    serializer_class = ExceptionalAppraiseeFilterSettingSerializer
    permission_classes = [PerformanceAppraisalSettingPermission]


class ScoreAndScalingSettingViewSet(OrganizationMixin, CreateListModelMixin,
                                    SubPerformanceAppraisalMixin, ListCreateViewSetMixin):
    queryset = ScoreAndScalingSetting.objects.all()
    serializer_class = ScoreAndScalingSettingSerializer
    permission_classes = [PerformanceAppraisalSettingPermission]

    def perform_create(self, serializer):
        _validate_repeated_data(
            data=serializer.data,
            key='name',
            message='Duplicate name supplied.'
        )
        _validate_repeated_data(
            data=serializer.data,
            key='score',
            message='Duplicate score supplied.'
        )
        sub_performance_appraisal_slot = self.get_performance_appraisal_slot()
        sub_performance_appraisal_slot.score_and_scaling_setting.all().delete()
        super().perform_create(serializer)


class DeadlineExtendConditionViewSet(OrganizationMixin, CreateListModelMixin,
                                     SubPerformanceAppraisalMixin, ListCreateViewSetMixin):
    queryset = DeadlineExtendCondition.objects.all()
    serializer_class = DeadlineExtendConditionSerializer
    permission_classes = [PerformanceAppraisalSettingPermission]

    def perform_create(self, serializer):
        sub_performance_appraisal_slot = self.get_performance_appraisal_slot()
        _validate_overlapped_data(
            serializer.data,
            from_key='total_appraise_count_ranges_from',
            to_key='total_appraise_count_ranges_to',
            message='Appraise count ranges should not overlap.'
        )
        sub_performance_appraisal_slot.deadline_extend_condition.all().delete()
        super().perform_create(serializer)


class DeadlineExceedScoreDeductionConditionViewSet(
    OrganizationMixin, SubPerformanceAppraisalMixin,
    ListCreateViewSetMixin
):
    queryset = DeadlineExceedScoreDeductionCondition.objects.all()
    serializer_class = DeadlineExceedScoreDeductionConditionSerializer
    permission_classes = [PerformanceAppraisalSettingPermission]

    def get_serializer_class(self):
        if self.request.method.lower() == 'get':
            return DeductionCriteriaSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        self.get_queryset().filter(
            sub_performance_appraisal_slot=self.performance_appraisal_slot
        ).delete()
        super().perform_create(serializer)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        instance = self.get_queryset().first()
        response.data['deduction_type'] = getattr(instance, 'deduction_type', PERCENTAGE)
        return response


class StepUpDownRecommendationViewSet(
    OrganizationMixin, SubPerformanceAppraisalMixin,
    ListCreateViewSetMixin
):
    queryset = StepUpDownRecommendation.objects.all()
    serializer_class = StepUpDownRecommendationSerializer
    permission_classes = [PerformanceAppraisalSettingPermission]

    def get_serializer_class(self):
        if self.request.method.lower() == 'get':
            return StepUpDownCriteriaSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        # _validate_overlapped_data(
        #     serializer.data,
        #     from_key='score_acquired_from',
        #     to_key='score_acquired_to',
        #     message='Acquired score ranges should not overlap.'
        # )
        self.get_queryset().filter(
            sub_performance_appraisal_slot=self.performance_appraisal_slot
        ).delete()
        super().perform_create(serializer)


class FormReviewSettingViewSet(
    OrganizationMixin, SubPerformanceAppraisalMixin,
    ListCreateViewSetMixin
):
    queryset = FormReviewSetting.objects.all()
    serializer_class = FormReviewSettingSerializer
    permission_classes = [PerformanceAppraisalSettingPermission]

'''
[
{
    "appraisal_type": "Self Appraisal",
                    "start_date": "2020-07-16T10:40:00+05:45",
                    "deadline": "2021-01-15T10:40:00+05:45"
},
{
    "appraisal_type": "Supervisor Appraisal",
                    "start_date": "2020-07-16T10:40:00+05:45",
                    "deadline": "2021-01-15T10:40:00+05:45"
},
{
    "appraisal_type": "Subordinate Appraisal",
                    "start_date": "2020-07-16T10:40:00+05:45",
                    "deadline": "2021-01-15T10:40:00+05:45"
},
{
    "appraisal_type": "Peer To Peer Feedback",
                    "start_date": "2020-07-16T10:40:00+05:45",
                    "deadline": "2021-01-15T10:40:00+05:45"
}
]
'''
