from rest_framework.routers import DefaultRouter

from irhrs.recruitment.api.v1.views import screening_assessment

app_name = 'screening'

# ********************** Pre Screening Urls ***********************

pre_screening_router = DefaultRouter()
pre_screening_router.register(
    r'(?P<job_slug>[\w-]+)',
    screening_assessment.PreScreeningViewSet,
    basename='pre_screening'
    # private all
)

pre_screening_urls = pre_screening_router.urls

# ********************** Post Screening Urls End ********************


# ********************** Post Screening Urls ***********************

post_screening_router = DefaultRouter()
post_screening_router.register(
    r'(?P<job_slug>[\w-]+)',
    screening_assessment.PostScreeningViewSet,
    basename='post_screening'
    # private all
)

post_screening_urls = post_screening_router.urls

# ********************** Post Screening Urls End ***********************


# ********************** Pre Screening Interview ***********************

pre_screening_interview_router = DefaultRouter()
pre_screening_interview_router.register(
    r'(?P<job_slug>[\w-]+)',
    screening_assessment.PreScreeningInterviewViewSet,
    basename='pre_screening_interview'
    # private all
)

pre_screening_interview_router.register(
    r'interviewer/(?P<user_id>[\w-]+)/answer',
    screening_assessment.PreScreeningInterviewViewAnswerViewSet,
    basename='pre_screening_interview_answer'
    # put and retrieve public
)

pre_screening_interview_urls = pre_screening_interview_router.urls

# ********************** Pres Screening Interview End ***********************


# ********************** Assessment ***********************

assessment_router = DefaultRouter()
assessment_router.register(
    r'(?P<job_slug>[\w-]+)',
    screening_assessment.AssessmentViewSet,
    basename='assessment'
    # private all
)

assessment_router.register(
    r'assessment-verifier/(?P<user_id>[\w-]+)/answer',
    screening_assessment.AssessmentAnswerViewSet,
    basename='assessment_answer'
    # put and retrieve public
)

assessment_urls = assessment_router.urls

# ********************** Assessment End ***********************


# ********************** Rostered ***********************

rostered_router = DefaultRouter()
rostered_router.register(
    r'(?P<job_slug>[\w-]+)',
    screening_assessment.RosteredViewSet,
    basename='rostered'
    # private all
)

rostered_urls = rostered_router.urls

# ********************** Rostered End ***********************
