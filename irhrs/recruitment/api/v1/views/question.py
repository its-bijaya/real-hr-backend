from django.db.models import Q, ProtectedError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.viewset_mixins import HRSModelViewSet, IStartsWithIContainsSearchFilter, OrganizationMixin
from irhrs.permission.utils.base import ApplicationSettingsPermission
from irhrs.recruitment.api.v1.mixins import RecruitmentPermissionMixin
from irhrs.recruitment.api.v1.permissions import RecruitmentPermission
from irhrs.recruitment.api.v1.serializers.question import QuestionSetSerializer, \
    QuestionsSerializer, QuestionSectionSerializer
from irhrs.recruitment.models import QuestionSet, Job
from irhrs.recruitment.models.question import RecruitmentQuestionSection, RecruitmentQuestions


class QuestionSetPermissionMixin(RecruitmentPermissionMixin):
    permission_classes = [IsAuthenticated, ApplicationSettingsPermission]

    @property
    def is_supervisor(self):
        return bool(self.request.user.subordinates_pks)

    def get_permission_classes(self):
        if self.request.user.is_authenticated and (
                self.is_supervisor and self.request.method in SAFE_METHODS
        ):
            return self.permission_classes
        else:
            return [RecruitmentPermission, ]

    @property
    def get_form_type(self):
        form_type = self.kwargs.get('form_type')
        if form_type:
            return form_type.replace('-', '_')
        return form_type


class QuestionSetViewSet(OrganizationMixin, QuestionSetPermissionMixin, HRSModelViewSet):
    queryset = QuestionSet.objects.all()
    serializer_class = QuestionSetSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['organization'] = self.organization
        context['form_type'] = self.get_form_type
        context['with_questions'] = False
        return context

    # def get_serializer(self, *args, **kwargs):
    #     if self.action != 'retrieve':
    #         kwargs['exclude_fields'] = ('sections',)
    #     return super().get_serializer(*args, **kwargs)

    def get_queryset(self):
        return super(QuestionSetViewSet, self).get_queryset().filter(
            form_type=self.get_form_type
        )

    def destroy(self, request, *args, **kwargs):
        self.check_pre_conditions()
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            raise ValidationError('Unable to delete used question set.')

    def check_pre_conditions(self):
        pk = self.kwargs.get('pk')
        if Job.objects.filter(
            Q(hiring_info__pre_screening__id=pk) |
            Q(hiring_info__post_screening__id=pk) |
            Q(hiring_info__pre_screening_interview__id=pk) |
            Q(hiring_info__assessment__id=pk) |
            Q(hiring_info__interview__id=pk) |
            Q(hiring_info__reference_check__id=pk)
        ).exists():
            raise ValidationError('Unable to delete used question set.')

    @action(
        detail=True,
        methods=['GET']
    )
    def questions(self, request, *args, **kwargs):
        question_set = self.get_object()
        sections = question_set.sections.all()
        questions = QuestionSectionSerializer(
            sections,
            context=self.get_serializer_context(),
            many=True
        ).data
        return Response({
            'count': sections.count(),
            'questions': questions
        })


class RecruitmentQuestionSectionViewSet(ModelViewSet, QuestionSetPermissionMixin):
    queryset = RecruitmentQuestionSection.objects.all()
    serializer_class = QuestionSectionSerializer
    # filter_backends = (
    #     filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend
    # )
    filter_fields = ['question_set', ]
    question_set = None

    def initial(self, *args, **kwargs):
        super().initial(*args, **kwargs)
        self.question_set = get_object_or_404(
            QuestionSet.objects.filter(
                form_type=self.get_form_type
            ), pk=self.kwargs.get('question_set')
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


class RecruitmentQuestionsViewSet(ModelViewSet, QuestionSetPermissionMixin):
    queryset = RecruitmentQuestions.objects.all()
    serializer_class = QuestionsSerializer
    filter_backends = (
        IStartsWithIContainsSearchFilter, DjangoFilterBackend
    )
    question_section = None

    def initial(self, *args, **kwargs):
        super().initial(*args, **kwargs)
        self.question_section = get_object_or_404(
            RecruitmentQuestionSection.objects.all(),
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
        RecruitmentQuestions.objects.filter(
            question_section=self.question_section
        ).delete()
        return super().create(request, *args, **kwargs)
