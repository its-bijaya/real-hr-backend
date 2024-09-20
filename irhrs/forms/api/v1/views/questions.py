from rest_framework.generics import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.response import Response

from irhrs.forms.models import (
    FormQuestion,
    FormQuestionSet,
    FormQuestionSection
)
from irhrs.core.utils.common import validate_permissions
from irhrs.permission.permission_classes import permission_factory
from irhrs.forms.api.v1.permission import (
    FormCRUDPermission
)
from irhrs.forms.api.v1.serializers.questions import (
    FormQuestionSerializer,
    FormQuestionSectionSerializer,
    FormQuestionSetSerializer,
    FormQuestionBulkSerializer
)
from irhrs.core.mixins.viewset_mixins import (
    OrganizationMixin,
    OrganizationCommonsMixin
)
from irhrs.permission.constants.permissions import (
    FORM_QUESTION_AND_SETTING_VIEW_CREATE_UPDATE_DELETE_PERMISSION
)


class FormQuestionSetViewSet(
        OrganizationCommonsMixin,
        OrganizationMixin,
        ModelViewSet
):
    """For CRUD of survery form."""

    queryset = FormQuestionSet.objects.all()
    serializer_class = FormQuestionSetSerializer
    permission_classes = [FormCRUDPermission]

    @property
    def user_mode(self):
        _as = self.request.query_params.get('as')
        if _as == 'hr':
            is_hr = validate_permissions(
                self.request.user.get_hrs_permissions(self.get_organization()),
                FORM_QUESTION_AND_SETTING_VIEW_CREATE_UPDATE_DELETE_PERMISSION
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
        if question_set.forms.exists():
            raise ValidationError({
                "error": "This question set is in use in one of the forms."
            })
        return super().destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        question_set = self.get_object()
        if question_set.forms.exists():
            raise ValidationError({
                "error": "This question set is in use in one of the forms."
            })
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=['GET'])
    def questions(self, request, *args, **kwargs):
        question_set = self.get_object()
        sections = question_set.sections.all()
        questions = FormQuestionSectionSerializer(
            sections,
            context=self.get_serializer_context(),
            many=True
        ).data
        return Response({
            'count': sections.count(),
            'questions': questions
        })


class FormQuestionSectionViewSet(OrganizationMixin, ModelViewSet):
    queryset = FormQuestionSection.objects.all()
    serializer_class = FormQuestionSectionSerializer
    filter_fields = ['question_set', ]
    permission_classes = [FormCRUDPermission]
    question_set = None

    def initial(self, *args, **kwargs):
        super().initial(*args, **kwargs)
        self.question_set = get_object_or_404(
            FormQuestionSet.objects.all(),
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


class FormQuestionViewSet(OrganizationMixin, ModelViewSet):
    queryset = FormQuestion.objects.all()
    serializer_class = FormQuestionSerializer
    # filter_backends = (
    #     IStartsWithIContainsSearchFilter, DjangoFilterBackend
    # )
    permission_classes = [FormCRUDPermission]
    question_section = None

    @property
    def user_mode(self):
        _as = self.request.query_params.get('as')
        if _as == 'hr':
            is_hr = validate_permissions(
                self.request.user.get_hrs_permissions(self.get_organization()),
                FORM_QUESTION_AND_SETTING_VIEW_CREATE_UPDATE_DELETE_PERMISSION
            )
            if not is_hr:
                raise PermissionDenied
            return 'hr'
        return ''

    def initial(self, *args, **kwargs):
        super().initial(*args, **kwargs)
        self.question_section = get_object_or_404(
            FormQuestionSection.objects.all(),
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
        serializer = FormQuestionBulkSerializer(
            data=request.data,
            context=self.get_serializer_context()
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status":"ok"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
