from rest_framework.routers import DefaultRouter

from irhrs.recruitment.api.v1.views import interview

app_name = 'interview'

router = DefaultRouter()


router.register(
    r'(?P<job_slug>[\w-]+)',
    interview.InterviewViewSet,
    basename='interview'
    # private all
)

router.register(
    r'interviewer/(?P<user_id>[\w-]+)/answer',
    interview.InterViewAnswerViewSet,
    basename='interview_answer'
    # put and retrieve public
)

urlpatterns = router.urls
