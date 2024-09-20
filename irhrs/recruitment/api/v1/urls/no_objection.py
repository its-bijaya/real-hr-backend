from rest_framework.routers import DefaultRouter

from irhrs.recruitment.api.v1.views import no_objection

app_name = 'no_objection'

router = DefaultRouter()

router.register(
    r'(?P<job_slug>[\w-]+)',
    no_objection.NoObjectionViewSet,
    basename='no_objection'
    # private all
)

urlpatterns = [

]

urlpatterns += router.urls
