from rest_framework import viewsets, filters
from rest_framework.mixins import RetrieveModelMixin

from irhrs.help.models import (HelpModule, HelpCategory, HelpQuestion
                            #    HelpQuestionImage
                               , HelpQuestionFeedback)
from .serializers import (
    HelpModuleSerializer, HelpCategorySerializer,
    HelpQuestionSerializer, HelpQuestionFeedbackSerializer,
    # HelpQuestionImageSerializer
)

# TODO @Shital: Check if the Mixin is used, or API is still in use.


class HelpViewsIncrementMixin(RetrieveModelMixin):
    def retrieve(self, request, *args, **kwargs):
        self.get_object().increase_view_count()
        return super(HelpViewsIncrementMixin, self).retrieve(request)


class HelpModuleViewSet(HelpViewsIncrementMixin, viewsets.ReadOnlyModelViewSet):
    queryset = HelpModule.objects.all().order_by('-views')
    serializer_class = HelpModuleSerializer


class HelpCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HelpCategory.objects.all()
    serializer_class = HelpCategorySerializer

    def get_queryset(self):
        module = self.request.query_params.get('module')
        queryset = super().get_queryset()
        if module:
            try:
                queryset = queryset.filter(help_module=module)
            except ValueError:
                queryset = queryset.none()
        return queryset


class HelpQuestionViewSet(HelpViewsIncrementMixin, viewsets.ReadOnlyModelViewSet):
    queryset = HelpQuestion.objects.filter(parent__isnull=True).order_by('-views')
    serializer_class = HelpQuestionSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('title', 'answer')

    def get_queryset(self):
        category = self.request.query_params.get('category')
        queryset = super().get_queryset()
        if category:
            try:
                queryset = queryset.filter(help_category=category)
            except ValueError:
                queryset = queryset.none()

        return queryset


# class HelpQuestionImageViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = HelpQuestionImage.objects.all()
#     serializer_class = HelpQuestionImageSerializer


class HelpQuestionFeedbackViewSet(viewsets.ModelViewSet):
    queryset = HelpQuestionFeedback.objects.all()
    serializer_class = HelpQuestionFeedbackSerializer
