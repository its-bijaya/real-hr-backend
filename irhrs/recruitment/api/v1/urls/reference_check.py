from rest_framework.routers import DefaultRouter

from irhrs.recruitment.api.v1.views import reference_check

app_name = 'reference_check'

router = DefaultRouter()

router.register(
    r'reference-checker/(?P<user_id>[\w-]+)/answer',
    reference_check.ReferenceCheckAnswerViewSet,
    basename='reference_check_answer'
    # put and retrieve public
)

# router.register(
#     r'applicant-reference/(?P<applicant_id>[\w-]+)/',
#     reference_check.ReferenceCheckerViewSet,
#     base_name='reference_checker'
# )


router.register(
    r'(?P<job_slug>[\w-]+)',
    reference_check.ReferenceCheckViewSet,
    basename='reference_check'
    # private all
)

urlpatterns = router.urls
