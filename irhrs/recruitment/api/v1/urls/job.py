from django.urls import path
from rest_framework.routers import DefaultRouter

from irhrs.recruitment.api.v1.views import job
from irhrs.recruitment.api.v1.views import job_apply

app_name = 'job'

router = DefaultRouter()

router.register(
    'search',
    job.JobSearchAPIView,
    basename="search"
    # all public
)

router.register(
    'question',
    job.JobQuestionViewSet,
    basename="question"
    # private
)

router.register(
    'attachment',
    job.JobAttachmentViewSet,
    basename="attachment"
    # private
)

router.register(
    r'',
    job.JobViewSet,
    basename='job'
    # private
)

# router.register(
#     r'applications',
#     job_apply.JobApplicationShortlistViewSet,
#     basename='applications'
# )

# urlpatterns = [
#     path(
#         '<slug:job_slug>/apply/',
#         job_apply.JobApplyCreateViewSet.as_view({'post': 'create'}),
#         name='apply'
#     )
# ]

urlpatterns = router.urls
