from django.db import transaction
from django.db.models import F, Prefetch, Count, Sum, Value
from django.db.models.functions import Coalesce
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from irhrs.assessment.api.v1.serializers.assessment import (AssessmentScoreSerializer,
                                                            AssignTrainingFromAssessmentSerializer)
from irhrs.assessment.models.assessment import UserAssessment, AssessmentSet
from irhrs.assessment.models.helpers import COMPLETED, CANCELLED
from irhrs.core.mixins.viewset_mixins import (OrganizationMixin, ListViewSetMixin,
                                              IStartsWithIContainsSearchFilter)
from irhrs.permission.constants.permissions import ASSESSMENT_SCORE_PERMISSION
from irhrs.permission.permission_classes import permission_factory


class AssessmentScoreView(OrganizationMixin, ListViewSetMixin):
    """
    # Marginal Filter
    * ?margin=above
    * ?margin=below
    """
    queryset = UserAssessment.objects.all()
    serializer_class = AssessmentScoreSerializer
    filter_backends = (
        DjangoFilterBackend,
        IStartsWithIContainsSearchFilter,
        OrderingFilter
    )
    permission_classes = [
        permission_factory.build_permission(
            'AssessmentScorePermission',
            allowed_to=[ASSESSMENT_SCORE_PERMISSION]
        )
    ]
    filter_fields = (
        'assessment_set',
    )
    search_fields = ('user__first_name', 'user__last_name', 'user__last_name')
    ordering_fields = ('modified_at',)

    def get_queryset(self):
        return super().get_queryset().filter(
            assessment_set__organization=self.organization,
            status__in=[COMPLETED, CANCELLED]
        )

    def filter_queryset(self, queryset):
        margin = self.request.query_params.get('margin')
        # filter_assigned = self.request.query_params.get('training_assigned') == 'true'
        base_qs = super().filter_queryset(queryset)
        if margin == 'above':
            base_qs = base_qs.filter(
                score__gte=F('assessment_set__marginal_weightage')
            )
        elif margin == 'below':
            base_qs = base_qs.filter(
                score__lt=F('assessment_set__marginal_weightage')
            )
        # if filter_assigned:
        #     base_qs = base_qs.filter(associated_training__isnull=True)
        # else:
        #     base_qs = base_qs.exclude(associated_training__isnull=True)
        return base_qs

    def get_serializer_context(self):
        return {
            **super().get_serializer_context(),
            'organization': self.organization
        }

    @transaction.atomic()
    @action(
        methods=['POST'],
        detail=False,
        serializer_class=AssignTrainingFromAssessmentSerializer,
        url_path='assign-training'
    )
    def assign_training(self, *args, **kwargs):
        ser = AssignTrainingFromAssessmentSerializer(
            data=self.request.data,
            context=self.get_serializer_context()
        )
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)
