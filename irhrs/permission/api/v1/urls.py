from rest_framework.routers import DefaultRouter

from irhrs.permission.api.v1.views.groups import UserGroupViewSet
from irhrs.permission.api.v1.views.hrs_permission import HRSPermissionViewSet
from irhrs.permission.api.v1.views.organization import OrganizationCreateViewSet

app_name = 'permissions'

router = DefaultRouter()
router.register('', HRSPermissionViewSet, basename='permissions')
router.register('groups', UserGroupViewSet, basename='user-group')
router.register('organization', OrganizationCreateViewSet, basename='organization')

urlpatterns = router.urls
