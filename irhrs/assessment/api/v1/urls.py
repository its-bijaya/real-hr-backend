from django.urls import path, include
from rest_framework.routers import DefaultRouter

from irhrs.assessment.api.v1.views.assessment import (
    AssessmentSetViewSet, AssessmentSectionViewSet, AssessmentSectionQuestionsView,
    TakeAssessmentView, PastAssessmentView)
from irhrs.assessment.api.v1.views.assessment_results import AssessmentScoreView

router = DefaultRouter()

router.register(
    'assessments',
    AssessmentSetViewSet,
    basename='assessment'
)
router.register(
    'assessment-sections',
    AssessmentSectionViewSet,
    basename='assessment-section'
)

router.register(
    r'assessment-sections/(?P<assessment_section_id>\d+)/questions',
    AssessmentSectionQuestionsView,
    basename='assessment-section'
)

router.register(
    r'assessments/(?P<assessment_id>\d+)/take',
    TakeAssessmentView,
    basename='take-assessment'
)

router.register(
    r'past-assessments',
    PastAssessmentView,
    basename='pass-assessments'
)

router.register(
    r'assessment-reports',
    AssessmentScoreView,
    basename='assessment-report'
)

urlpatterns = [
    path('<slug:organization_slug>/', include(router.urls)),
]
