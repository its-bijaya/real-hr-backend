from .views import HRPolicyHeadingViewSet, HRPolicyBodyViewSet
from rest_framework.routers import DefaultRouter
app_name = 'hrstatement'

# router = DefaultRouter()
#
# # Organization Commons
# router.register(r'(?P<organization_slug>[\w\-]+)/policy/heading',
#                 HRPolicyHeadingViewSet,
#                 base_name='hr-policy-heading')
#
# router.register(r'(?P<organization_slug>[\w\-]+)/policy/'
#                 r'(?P<header_slug>[\w\-]+)/body',
#                 HRPolicyBodyViewSet,
#                 base_name='hr-policy-body')
# urlpatterns = router.urls

urlpatterns = []