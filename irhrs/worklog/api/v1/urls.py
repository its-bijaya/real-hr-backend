from rest_framework.routers import DefaultRouter

from irhrs.worklog.api.v1.views.worklog import WorkLogViewSet
from irhrs.worklog.api.v1.views.dashboard import WorkLogOverview

app_name = "worklog"

router = DefaultRouter()
router.register('overview', WorkLogOverview, basename='overview')
router.register('', WorkLogViewSet, basename='')

urlpatterns = router.urls
