from django.urls import path, include
from irhrs.recruitment.api.v1.urls.screening_assessment import (
    pre_screening_urls, post_screening_urls,
    pre_screening_interview_urls, assessment_urls,
    rostered_urls
)

urlpatterns = [
    path('job/', include('irhrs.recruitment.api.v1.urls.job')),
    path('apply/', include('irhrs.recruitment.api.v1.urls.job_apply')),
    path('applicant/', include('irhrs.recruitment.api.v1.urls.applicant')),
    path('external/', include('irhrs.recruitment.api.v1.urls.external')),

    path('pre-screening/', include(pre_screening_urls)),
    path('post-screening/', include(post_screening_urls)),
    path('pre-screening-interview/', include(pre_screening_interview_urls)),
    path('assessment/', include(assessment_urls)),
    path('rostered/', include(rostered_urls)),

    path('interview/', include('irhrs.recruitment.api.v1.urls.interview')),
    path('reference-check/', include('irhrs.recruitment.api.v1.urls.reference_check')),
    path('common/', include('irhrs.recruitment.api.v1.urls.common')),
    path('', include('irhrs.recruitment.api.v1.urls.question')),
    path('no-objection/', include('irhrs.recruitment.api.v1.urls.no_objection')),
    path('salary-declaration/', include('irhrs.recruitment.api.v1.urls.salary')),
    path('template/', include('irhrs.recruitment.api.v1.urls.template')),
]
