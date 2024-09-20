from rest_framework.routers import DefaultRouter

from irhrs.recruitment.api.v1.views import external

app_name = 'external'

router = DefaultRouter()

router.register(
    r'(?P<organization_slug>[\w-]+)',
    external.ExternalViewSet,
    basename='external'
    # private all
)

urlpatterns = router.urls
