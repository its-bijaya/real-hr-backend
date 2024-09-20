from django.urls import path, include
from rest_framework.routers import DefaultRouter

from irhrs.questionnaire.api.v1.views.questionnaire import QuestionViewSet, QuestionCategoryViewSet

app_name = "questionnaire"
router = DefaultRouter()

router.register(
    'questions',
    QuestionViewSet,
    'questions-repo'
)

router.register(
    'question-categories',
    QuestionCategoryViewSet,
    'question-categories'
)

urlpatterns = [
    path('<slug:organization_slug>/', include(router.urls))
]
