from django.urls import path, include
from rest_framework.routers import DefaultRouter

from irhrs.training.api.v1.views import (TrainingTypeViewSet, TrainingViewSet,
                                         UserTrainingRequestViewSet, TrainersViewSet,
                                         TrainingFeedbackViewSet, TrainingAttendanceViewSet)
from irhrs.training.api.v1.views.training import TrainingStatsViewSet

app_name = 'training'

router = DefaultRouter()

router.register(
    r'training-type',
    TrainingTypeViewSet,
    basename='training-type'
)

router.register(
    r'training/(?P<training_slug>[\w\-]+)/feedbacks',
    TrainingFeedbackViewSet,
    basename='training'
)

router.register(
    r'training',
    TrainingViewSet,
    basename='training'
)

router.register(
    r'training-request',
    UserTrainingRequestViewSet,
    basename='training-request'
)

router.register(
    r'trainers',
    TrainersViewSet,
    basename='trainers'
)


router.register(
    r'training/(?P<training_slug>[\w\-]+)/attendance',
    TrainingAttendanceViewSet,
    basename='training'
)


router.register(
    r'detail',
    TrainingStatsViewSet,
    basename='training-stats'
)

urlpatterns = [
    path('<slug:organization_slug>/', include(router.urls))
]
