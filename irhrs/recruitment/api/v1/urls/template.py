from rest_framework.routers import DefaultRouter

from irhrs.recruitment.api.v1.views import template

app_name = 'template'

router = DefaultRouter()


router.register(
    r'',
    template.TemplateAPIViewSet,
    basename='template'
)


urlpatterns = [

]

urlpatterns += router.urls
