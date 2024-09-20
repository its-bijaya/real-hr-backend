import os

from django.conf import settings
from jwkest import long_to_base64
from cryptography.hazmat.primitives import serialization
from django.urls import reverse
from rest_framework.views import APIView
from rest_framework.response import Response


class OCIDDiscoveryConf(object):

    def __init__(self, request):
        self.request = request

    def get_issuer(self):
        return self.request.build_absolute_uri('/o')

    def get_authorization_endpoint(self):
        return self.request.build_absolute_uri(
            reverse('oauth2_provider:authorize')
        )

    def get_response_types_supported(self):
        return ['id_token']

    def get_scopes_supported(self):
        return ['openid']

    def get_token_endpoint(self):
        return self.request.build_absolute_uri(
            reverse('oauth2_provider:token')
        )

    def get_jwks_uri(self):
        return self.request.build_absolute_uri(
            reverse('oauth2_provider:ocid-jwks')
        )

    def get_check_session_iframe(self):
        return self.request.build_absolute_uri(
            reverse('oauth2_provider:check-session-iframe')
        )

    def get_end_session_endpoint(self):
        return self.request.build_absolute_uri(
            '/rp-logout-handler/'
        )


class OICDDiscoveryAPIView(APIView):
    """
    OpenID Connect discovery endpoint
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None):

        conf = OCIDDiscoveryConf(request)

        data = dict(
            issuer=conf.get_issuer(),
            authorization_endpoint=conf.get_authorization_endpoint(),
            token_endpoint=conf.get_token_endpoint(),
            response_types_supported=conf.get_response_types_supported(),
            scopes_supported=conf.get_scopes_supported(),
            jwks_uri=conf.get_jwks_uri(),
            check_session_iframe=conf.get_check_session_iframe(),
            end_session_endpoint=conf.get_end_session_endpoint()
        )

        return Response(data)


class OICDDiscoveryJWKSAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None):

        from cryptography.hazmat.backends import default_backend
        with open(os.path.join(settings.ROOT_DIR, "key-files/public_key.pem"), "rb") as key_file:
            public_key = serialization.load_pem_public_key(
                key_file.read(),
                backend=default_backend()
            )

        n_parameter = public_key.public_numbers().n

        e_parameter = public_key.public_numbers().e

        data = dict(
            keys=[
                dict(
                    use='sig',
                    alg='RS256',
                    kty='RSA',
                    n=long_to_base64(n_parameter),
                    e=long_to_base64(e_parameter)
                )
            ]
        )

        return Response(data)
