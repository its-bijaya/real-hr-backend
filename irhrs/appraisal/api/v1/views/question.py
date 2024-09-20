from django.http import Http404
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, PermissionDenied

from irhrs.appraisal.models.question_set import (
    PerformanceAppraisalQuestion,
    PerformanceAppraisalQuestionSet,
    PerformanceAppraisalQuestionSection,
    QuestionSetUserType
)
from irhrs.appraisal.api.v1.serializers.question_set import \
    PerformanceAppraisalQuestionSetSerializer, QuestionSetUserTypeSerializer, \
    CopyQuestionSetSerializer, EditQuestionSetSerializer
from irhrs.core.utils.common import validate_permissions
from irhrs.appraisal.api.v1.permissions import (
    PerformanceAppraisalQuestionSetPermission
)
from irhrs.appraisal.api.v1.serializers.questions import (
    PerformanceAppraisalQuestionSerializer,
    PerformanceAppraisalQuestionSectionSerializer,
    PerformanceAppraisalQuestionSetSerializer
)
from irhrs.core.mixins.viewset_mixins import (
    OrganizationMixin,
    OrganizationCommonsMixin
)
from irhrs.permission.constants.permissions import (
    PERFORMANCE_APPRAISAL_QUESTION_SET_PERMISSION
)


class PerformanceAppraisalQuestionSetViewSet(
        OrganizationCommonsMixin,
        OrganizationMixin,
        ModelViewSet
):
    queryset = PerformanceAppraisalQuestionSet.objects.all()
    serializer_class = PerformanceAppraisalQuestionSetSerializer
    permission_classes = [PerformanceAppraisalQuestionSetPermission]

    @property
    def user_mode(self):
        _as = self.request.query_params.get('as')
        if _as == 'hr':
            is_hr = validate_permissions(
                self.request.user.get_hrs_permissions(self.get_organization()),
                PERFORMANCE_APPRAISAL_QUESTION_SET_PERMISSION
            )
            if not is_hr:
                raise PermissionDenied
            return 'hr'
        return ''

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(
            organization=self.organization
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['organization'] = self.organization
        context['with_questions'] = False
        return context

    def destroy(self, request, *args, **kwargs):
        question_set = self.get_object()
        # if question_set.forms.exists():
        #     raise ValidationError({
        #         "error": "This question set is in use in one of the forms."
        #     })
        return super().destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        question_set = self.get_object()
        # if question_set.forms.exists():
        #     raise ValidationError({
        #         "error": "This question set is in use in one of the forms."
        #     })
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=['GET'])
    def questions(self, request, *args, **kwargs):
        question_set = self.get_object()
        sections = question_set.sections.all()
        questions = PerformanceAppraisalQuestionSectionSerializer(
            sections,
            context=self.get_serializer_context(),
            many=True
        ).data
        return Response({
            'count': sections.count(),
            'questions': questions
        })

    @action(
        detail=True,
        methods=['get'],
        url_path=r'question/(?P<question_id>\d+)/user-type',
        serializer_class=QuestionSetUserTypeSerializer
    )
    def user_type(self, request, *args, **kwargs):
        instance = QuestionSetUserType.objects.filter(
            question=kwargs.get('question_id')

        ).first()
        if not instance:
            return Response({
                "branches": [],
                "divisions": [],
                "job_titles": [],
                "employment_levels": [],
            })
        serializer = self.get_serializer(
            instance,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    @user_type.mapping.post
    def post_user_type(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        question = get_object_or_404(
            PerformanceAppraisalQuestion.objects.filter(
                question_section__question_set=self.get_object()
            ),
            id=self.kwargs.get('question_id')
        )
        instance = QuestionSetUserType.objects.filter(
            question=question
        ).first()

        if not instance:
            instance = QuestionSetUserType.objects.create(
                question=question,
                question_set=self.get_object()
            )

        for user_type in ['branches', 'divisions', 'job_titles', 'employment_levels']:
            user_type_instance = getattr(instance, user_type)
            user_type_instance.clear()
            user_type_instance.add(*validated_data.get(user_type))
        instance.save()
        return Response(serializer.data)

class PerformanceAppraisalQuestionSectionViewSet(OrganizationMixin, ModelViewSet):
    queryset = PerformanceAppraisalQuestionSection.objects.all()
    serializer_class = PerformanceAppraisalQuestionSectionSerializer
    filter_fields = ['question_set', ]
    permission_classes = [PerformanceAppraisalQuestionSetPermission]
    question_set = None

    def initial(self, *args, **kwargs):
        super().initial(*args, **kwargs)
        self.question_set = get_object_or_404(
            PerformanceAppraisalQuestionSet.objects.all(),
            pk=self.kwargs.get('question_set')
        )

    def get_serializer(self, *args, **kwargs):
        if self.action != 'retrieve':
            kwargs['exclude_fields'] = ('questions',)
        return super().get_serializer(*args, **kwargs)

    def get_queryset(self):
        question_set_id = self.kwargs.get('question_set')
        return super().get_queryset().filter(
            question_set=question_set_id
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['question_set'] = self.question_set
        return context


class PerformanceAppraisalQuestionViewSet(OrganizationMixin, ModelViewSet):
    queryset = PerformanceAppraisalQuestion.objects.all()
    serializer_class = PerformanceAppraisalQuestionSerializer
    # filter_backends = (
    #     IStartsWithIContainsSearchFilter, DjangoFilterBackend
    # )
    permission_classes = [PerformanceAppraisalQuestionSetPermission]
    question_section = None

    @property
    def user_mode(self):
        _as = self.request.query_params.get('as')
        if _as == 'hr':
            is_hr = validate_permissions(
                self.request.user.get_hrs_permissions(self.get_organization()),
                PERFORMANCE_APPRAISAL_QUESTION_SET_PERMISSION
            )
            if not is_hr:
                raise PermissionDenied
            return 'hr'
        return ''

    def initial(self, *args, **kwargs):
        super().initial(*args, **kwargs)
        self.question_section = get_object_or_404(
            PerformanceAppraisalQuestionSection.objects.all(),
            pk=self.kwargs.get('question_section')
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['question_section'] = self.question_section
        return ctx

    def get_serializer(self, *args, **kwargs):
        if isinstance(kwargs.get('data', {}), list):
            kwargs['many'] = True
        return super().get_serializer(*args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(
            question_section=self.question_section
        ).order_by('order')

    def filter_queryset(self, queryset):
        return super().filter_queryset(queryset).order_by('order')

    def create(self, request, *args, **kwargs):
        PerformanceAppraisalQuestion.objects.filter(
            question_section=self.question_section
        ).delete()
        return super().create(request, *args, **kwargs)
