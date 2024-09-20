from rest_framework import routers

from irhrs.builder.api.v1.generalized_reports.views.attendance_and_leave_report import AttendanceAndLeaveViewSet
from irhrs.builder.api.v1.views.builder import BuilderViewSet
from irhrs.builder.api.v1.views.report import ReportViewSet

router = routers.DefaultRouter()
router.register('report', ReportViewSet, basename='dj-report')
router.register('', BuilderViewSet, basename='dj-report-builder')
router.register(r'(?P<organization_slug>[\w\-]+)/attendance-and-leave',
                AttendanceAndLeaveViewSet,
                basename='attendance-and-leave-report')
urlpatterns = router.urls
