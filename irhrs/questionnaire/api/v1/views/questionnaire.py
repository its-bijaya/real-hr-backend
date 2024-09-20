from django.db.models import ProtectedError, Count, Value, Sum
from django.db.models.functions import Coalesce
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import ModelViewSet

from irhrs.assessment.models.assessment import AssessmentSet
from irhrs.core.mixins.viewset_mixins import OrganizationCommonsMixin, OrganizationMixin
from irhrs.permission.constants.permissions.assessment_questionnaire_training import \
    (FULL_QUESTIONNAIRE_PERMISSION, QUESTIONNAIRE_READ_PERMISSION)
from irhrs.permission.permission_classes import permission_factory
from irhrs.questionnaire.api.v1.serializers.questionnaire import (
    QuestionSerializer, QuestionCategorySerializer
)
from irhrs.questionnaire.models.questionnaire import (
    Question, QuestionCategory
)

FullQuestionnairePermission = permission_factory.build_permission(
    'FullQuestionnairePermission',
    allowed_to=[FULL_QUESTIONNAIRE_PERMISSION],
    limit_read_to=[
        QUESTIONNAIRE_READ_PERMISSION
    ]
)


class QuestionViewSet(OrganizationMixin, OrganizationCommonsMixin, ModelViewSet):
    queryset = Question.objects.all().order_by('order')
    serializer_class = QuestionSerializer
    permission_classes = [FullQuestionnairePermission]
    filter_backends = (
        filters.SearchFilter, DjangoFilterBackend
    )
    filter_fields = (
        'question_type', 'category__slug'
    )

    def destroy(self, request, *args, **kwargs):
        question = self.get_object()
        if AssessmentSet.objects.filter(
            sections__questions=question,
            assessments__user__isnull=False
        ).exists():
            raise ValidationError(
                {
                    "detail": ["Unable to delete this question."
                               "Some Assessment having this question "
                               "has been assigned to user."]
                }
            )
        response = super().destroy(request, *args, **kwargs)
        self._update_question_order(
            question.category.questions.all()
        )
        return response

    @staticmethod
    def _update_question_order(queryset):
        for index, instance in enumerate(queryset):
            instance.order = index + 1
            instance.save()


class QuestionCategoryViewSet(
    OrganizationCommonsMixin, OrganizationMixin, ModelViewSet
):
    lookup_field = 'slug'
    permission_classes = [FullQuestionnairePermission]
    queryset = QuestionCategory.objects.all()
    serializer_class = QuestionCategorySerializer

    def get_queryset(self):
        return super().get_queryset().annotate(
            total_questions=Count('questions__id'),
            total_weightage=Coalesce(
                Sum('questions__weightage'),
                Value(0)
            )
        )

    def filter_queryset(self, queryset):
        category = self.request.query_params.get('category')
        fil = dict()
        if category:
            category = category.replace('-', '_')
            fil = {'category': category}
        return super().filter_queryset(queryset).filter(**fil)

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            raise ValidationError({
                'error': "Can not delete used question categories"
            })
