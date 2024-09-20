from rest_framework.routers import DefaultRouter

from irhrs.notification.api.v1.views.notification import (
    NotificationViewSet, OrganizationNotificationViewSet
)

app_name = "notification"

router = DefaultRouter()

router.register('', NotificationViewSet, basename='notifications')
router.register(
    r'(?P<organization_slug>[a-z\-]+)',
    OrganizationNotificationViewSet,
    basename='organization-notifications'
)

urlpatterns = router.urls
