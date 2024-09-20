from rest_framework.routers import DefaultRouter

from irhrs.event.api.v1.views.event import EventViewSet
from irhrs.event.api.v1.views.meeting import MeetingDocumentViewSet, \
    MeetingAgendaViewSet, AgendaCommentViewSet, MeetingAttendanceViewSet, \
    MeetingViewSet, MeetingAgendaTaskViewSet

app_name = 'event'

router = DefaultRouter()

router.register(
    r'event',
    MeetingViewSet,
    basename='meeting'
)

router.register(
    '',
    EventViewSet,
    basename=''
)

router.register(
    r'(?P<event_id>\d+)/meeting/document',
    MeetingDocumentViewSet,
    basename='meeting-document'
)

router.register(
    r'(?P<event_id>\d+)/meeting/agenda',
    MeetingAgendaViewSet,
    basename='meeting-agenda'
)

router.register(
    r'(?P<event_id>\d+)/meeting/agenda/(?P<agenda_id>\d+)/task',
    MeetingAgendaTaskViewSet,
    basename='meeting-agenda-task'
)

router.register(
    r'(?P<event_id>\d+)/meeting/attendance',
    MeetingAttendanceViewSet,
    basename='meeting-attendance'
)

router.register(
    r'meeting/agenda/(?P<agenda_id>\d+)/comment',
    AgendaCommentViewSet,
    basename='agenda-comment'
)

urlpatterns = router.urls
