from django.conf.urls import url

from oauth2_provider import views as oauth2_provider_views

from irhrs.openid import views as openid_views
from irhrs.openid.api.v1.views import (
    OICDDiscoveryAPIView,
    OICDDiscoveryJWKSAPIView
)


app_name = "oauth2_provider"


base_urlpatterns = [
    url(r"^authorize/$", openid_views.AuthorizationView.as_view(), name="authorize"),
    url(r"^token/$", oauth2_provider_views.TokenView.as_view(), name="token"),
    url(r"^revoke_token/$", oauth2_provider_views.RevokeTokenView.as_view(), name="revoke-token"),
    url(r"^introspect/$", oauth2_provider_views.IntrospectTokenView.as_view(), name="introspect"),
    url(r'.well-known/openid-configuration', OICDDiscoveryAPIView.as_view(), name='ocid-discovery'),
    url(r'jwks', OICDDiscoveryJWKSAPIView.as_view(), name='ocid-jwks'),
    url(r'check-session-iframe', openid_views.CheckSessionIframeView.as_view(), name='check-session-iframe'),
    url(r'end-session', openid_views.EndSessionView.as_view(), name='end-session')
]


management_urlpatterns = [
    # # Application management views
    # url(r"^applications/$", oauth2_provider_views.ApplicationList.as_view(), name="list"),
    # url(r"^applications/register/$", oauth2_provider_views.ApplicationRegistration.as_view(), name="register"),
    # url(r"^applications/(?P<pk>[\w-]+)/$", oauth2_provider_views.ApplicationDetail.as_view(), name="detail"),
    # url(r"^applications/(?P<pk>[\w-]+)/delete/$", oauth2_provider_views.ApplicationDelete.as_view(), name="delete"),
    # url(r"^applications/(?P<pk>[\w-]+)/update/$", oauth2_provider_views.ApplicationUpdate.as_view(), name="update"),
    # # Token management views
    # url(r"^authorized_tokens/$", oauth2_provider_views.AuthorizedTokensListView.as_view(), name="authorized-token-list"),
    # url(r"^authorized_tokens/(?P<pk>[\w-]+)/delete/$", oauth2_provider_views.AuthorizedTokenDeleteView.as_view(),
    #     name="authorized-token-delete"),
]


urlpatterns = base_urlpatterns + management_urlpatterns
