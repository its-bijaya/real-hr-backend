from django.urls import path
from rest_framework.routers import DefaultRouter

from irhrs.recruitment.api.v1.views import job_apply

app_name = 'apply'

router = DefaultRouter()

router.register(
    r'eligible/(?P<job_slug>[\w-]+)/applicants',
    job_apply.EligibleCandidateViewSet,
    basename='eligible-applicants'
    # private all
)

router.register(
    r'rejected/(?P<job_slug>[\w-]+)/applicants',
    job_apply.RejectedCandidateViewSet,
    basename='rejected-applicants'
    # private all
)

router.register(
    r'(?P<job_slug>[\w-]+)/applications',
    job_apply.JobApplicationShortlistViewSet,
    basename='applications'
    # all private
)

urlpatterns = [
    path(
        r'verify-application/',
        job_apply.ApplicationVerificationViewSet.as_view({'post': 'create'}),
        name='verify-application'
    ),
    path(
        r'applications/all/',
        job_apply.JobApplicationShortlistViewSet.as_view({'get': 'list'}),
        name='all-applications'
    ),
    path(
        r'applications/all/stat/',
        job_apply.JobApplicationShortlistViewSet.as_view({'get': 'get_stats'}),
        name='all-applications'
    ),
    path(
        'internal/<slug:job_slug>/',
        job_apply.JobApplyCreateViewSet.as_view({'post': 'create'}),
        name='job_apply'
        # all public
    ),
    path(
        '<slug:job_slug>/',
        job_apply.JobApplyCreateViewSet.as_view({'post': 'create'}),
        name='job_apply'
        # all public
    )
]

urlpatterns += router.urls
