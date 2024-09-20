from collections import deque

from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from irhrs.appraisal.api.v1.permissions import PerformanceAppraisalSettingPermission
from irhrs.appraisal.api.v1.serializers.KAAR_score import KAARScaleAndScoreSettingSerializer, \
    ScoreAndScalingConfigSerializer, DefaultScoreSettingSerializer
from irhrs.appraisal.api.v1.views.performance_appraisal import SubPerformanceAppraisalMixin
from irhrs.appraisal.models.KAAR_score import KAARScaleAndScoreSetting, ScoreAndScalingConfig, DefaultScoreSetting
from irhrs.appraisal.utils.kaar_appraisal import CreateKAARScore, UpdateKAARScores
from irhrs.core.mixins.viewset_mixins import OrganizationMixin


class ScoreAndScalingConfigViewSet(OrganizationMixin, SubPerformanceAppraisalMixin, ModelViewSet):
    queryset = ScoreAndScalingConfig.objects.all()
    serializer_class = ScoreAndScalingConfigSerializer
    permission_classes = [PerformanceAppraisalSettingPermission]

    @action(
        methods=['POST'],
        detail=True,
        url_path='create-scores'
    )
    def create_scores(self, request, *args, **kwargs):
        instance = self.get_object()
        create = CreateKAARScore(
            instance, request.data, self.get_serializer_context()
        )
        create.create_scores()
        return Response("Successfully created.")

    @action(
        methods=['POST'],
        detail=True,
        url_path='update-scores'
    )
    def update_scores(self, request, *args, **kwargs):
        instance = self.get_object()
        update = UpdateKAARScores(
            instance, request.data, self.get_serializer_context()
        )
        update.update_scores()
        return Response("Successfully created.")


class KAARScaleAndScoreSettingViewSet(
        OrganizationMixin, SubPerformanceAppraisalMixin, ModelViewSet):
    queryset = KAARScaleAndScoreSetting.objects.all()
    serializer_class = KAARScaleAndScoreSettingSerializer
    permission_classes = [PerformanceAppraisalSettingPermission]


class DefaultScoreSettingViewSet(OrganizationMixin, SubPerformanceAppraisalMixin, ModelViewSet):
    queryset = DefaultScoreSetting.objects.all().order_by('created_at')
    serializer_class = DefaultScoreSettingSerializer
    permission_classes = [PerformanceAppraisalSettingPermission]

    @action(
        methods=['POST'],
        url_path='bulk-create',
        detail=False
    )
    def bulk_create(self, request, *args, **kwargs):
        ser = self.get_serializer_class()(data=request.data, context=self.get_serializer_context(), many=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response("Successfully created")

    @action(
        methods=['POST'],
        url_path='bulk-update',
        detail=False
    )
    def bulk_update(self, request, *args, **kwargs):
        valid_ser = deque()
        for data in request.data:
            instance = get_object_or_404(DefaultScoreSetting, id=data.pop('id'))
            ser = self.get_serializer_class()(
                instance=instance, data=data, context=self.get_serializer_context(), partial=True
            )
            ser.is_valid(raise_exception=True)
            valid_ser.append(ser)

        for ser in valid_ser:
            ser.save()

        return Response("Successfully Updated")
