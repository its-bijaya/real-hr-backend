from django.urls import path, re_path
from rest_framework.routers import DefaultRouter

from irhrs.task.api.v1.views.task import (
    TaskSummaryViewSet, TaskListViewSetV2, TaskOverview
)
from .views import (
    TaskViewSet, TaskChecklistViewSet, TaskReminderViewSet, TaskExport
)
from .views.attachment import TaskAttachmentViewSet
from .views.comments import TaskCommentViewSet
from .views.efficiency import EfficiencyView, UserProfileTaskDetailView
from .views.worklog import WorkLogAPIViewSet, WorkLogReportViewSet
from .views.settings import TaskSettingsView, ProjectApiViewSet, ActivityApiViewSet, \
    UserActivityViewSet

app_name = 'task'

router = DefaultRouter()
# router.register(
#     'projects',
#     TaskProjectViewSet,
#     basename='project'
# )
router.register(
    'projects',
    ProjectApiViewSet,
    basename='project'
)

router.register(
    'worklog',
    WorkLogAPIViewSet,
    basename='worklog'
)
router.register('worklog/report', WorkLogReportViewSet, basename='report')
router.register(
    r'projects/(?P<project_id>[0-9a-f-]+)/user-activity',
    UserActivityViewSet,
    basename='user-activity'
)
router.register(
    'activities',
    ActivityApiViewSet,
    basename='activity'
)
router.register(
    'summary',
    TaskSummaryViewSet,
    basename='task-summary'
)
router.register(
    r'(?P<task_id>[0-9a-f-]+)/checklists',
    TaskChecklistViewSet,
    basename=''
)
router.register(
    r'(?P<task_id>[0-9a-f-]+)/reminder',
    TaskReminderViewSet,
    basename=''
)
router.register(
    r'(?P<task_id>[0-9a-f-]+)/attachments',
    TaskAttachmentViewSet,
    basename='task-attachment'
)
router.register(
    r'(?P<task_id>[0-9a-f-]+)/comments',
    TaskCommentViewSet,
    basename='task-comments'
)
router.register(
    'info',
    TaskListViewSetV2,
    basename='task-overview-v2'
)
router.register(
    'overview',
    TaskOverview,
    basename='task-overview-hr'
)
router.register(
    '',
    TaskViewSet,
    basename='task'
)

urlpatterns = [
    path('export/', TaskExport.as_view(), name='task-export'),
    path('efficiency/', EfficiencyView.as_view(), name='task-efficiency'),
    re_path(
        r'(?P<organization_slug>[\w\-]+)/settings',
        TaskSettingsView.as_view({'get': 'retrieve', 'put': 'update'}),
        name='task-setting'
    ),
    re_path(r'^detail/user/(?P<user_id>\d+)/$', UserProfileTaskDetailView.as_view(),
            name='task-detail'),
]

urlpatterns += router.urls
