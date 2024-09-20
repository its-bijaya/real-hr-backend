from rest_framework.routers import DefaultRouter
from irhrs.recruitment.api.v1.views import common

app_name = 'common'

router = DefaultRouter()

router.register(
    r'location',
    common.LocationViewSet,
    basename='location'
    # public all
)

router.register(
    'country',
    common.CountryViewSet,
    basename='country'
    # read public
)

router.register(
    r'country/(?P<country_id>[\d]+)/provinces/(?P<province_id>[\d]+)/district',
    common.DistrictViewSet,
    basename='district'
)

router.register(
    'city',
    common.CityViewSet,
    basename='city'
    # read public
)

router.register(
    'skill',
    common.SkillViewSet,
    basename='skill'
    # read public
)

router.register(
    'job-category',
    common.JobCategoryViewSet,
    basename='job_category'
    # private all
)

router.register(
    'employment-status',
    common.EmploymentStatusViewSet,
    basename='employment_status'
    # public all
)

router.register(
    'employment-level',
    common.EmploymentLevelViewSet,
    basename='employment_level'
    # public all
)

# router.register(
#     'benefit',
#     common.JobBenefitViewSet,
#     basename='benefit'
# )

urlpatterns = router.urls
