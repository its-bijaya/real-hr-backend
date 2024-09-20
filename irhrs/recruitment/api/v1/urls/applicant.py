from rest_framework.routers import DefaultRouter
from irhrs.recruitment.api.v1.views import applicant

app_name = 'applicant'

router = DefaultRouter()


router.register(
    r'cv',
    applicant.ApplicantCVViewSet,
    basename='cv'
)

router.register(
    'on-board',
    applicant.ApplicantOnBoardViewSet,
    basename='on_board'
)

# router.register(
#     r'',
#     applicant.ApplicantViewSet,
#     basename='applicant'
# )

# router.register(
#     r'(?P<applicant_id>(\w+))/reference',
#     applicant.ApplicantReferenceViewSet,
#     basename='reference'
# )

# router.register(
#     r'(?P<applicant_id>(\w+))/work-experience',
#     applicant.ApplicantWorkExperienceViewSet,
#     basename='document'
# )

urlpatterns = router.urls
