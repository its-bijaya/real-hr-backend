import os

import base64
import binascii
import logging
import time

from collections import OrderedDict
from datetime import datetime, timedelta
from urllib.parse import unquote_plus

import requests
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.timezone import make_aware
from django.utils.translation import gettext_lazy as _
from oauthlib.oauth2 import RequestValidator

from oauth2_provider.exceptions import FatalClientError
from oauth2_provider.models import (
    AbstractApplication, get_access_token_model,
    get_application_model, get_grant_model, get_refresh_token_model
)
from oauth2_provider.scopes import get_scopes_backend
from oauth2_provider.settings import oauth2_settings

from irhrs.openid.constants import (
    PROFILE,
    APPLICATION_GROUPS
)

from irhrs.openid.models import ApplicationUser


log = logging.getLogger("oauth2_provider")

GRANT_TYPE_MAPPING = {
    "authorization_code": (AbstractApplication.GRANT_AUTHORIZATION_CODE, ),
    "password": (AbstractApplication.GRANT_PASSWORD, ),
    "client_credentials": (AbstractApplication.GRANT_CLIENT_CREDENTIALS, ),
    "refresh_token": (
        AbstractApplication.GRANT_AUTHORIZATION_CODE,
        AbstractApplication.GRANT_PASSWORD,
        AbstractApplication.GRANT_CLIENT_CREDENTIALS,
    )
}

Application = get_application_model()
AccessToken = get_access_token_model()
Grant = get_grant_model()
RefreshToken = get_refresh_token_model()
UserModel = get_user_model()

# open toolkit settings
# analyse from every entry point
#     with core validator and server


def build_absolute_uri(request, path):
    host = request.get('HTTP_HOST')
    scheme_header = settings.SECURE_PROXY_SSL_HEADER
    scheme = 'http'
    if scheme_header:
        scheme = request.get(scheme_header[0])
    return f"{scheme}://{host}{path}"


class OAuth2Validator(RequestValidator):
    def _extract_basic_auth(self, request):
        """
        Return authentication string if request contains basic auth credentials,
        otherwise return None
        """
        auth = request.headers.get("HTTP_AUTHORIZATION", None)
        if not auth:
            return None

        splitted = auth.split(" ", 1)
        if len(splitted) != 2:
            return None
        auth_type, auth_string = splitted

        if auth_type != "Basic":
            return None

        return auth_string

    def _authenticate_basic_auth(self, request):
        """
        Authenticates with HTTP Basic Auth.

        Note: as stated in rfc:`2.3.1`, client_id and client_secret must be encoded with
        "application/x-www-form-urlencoded" encoding algorithm.
        """
        auth_string = self._extract_basic_auth(request)
        if not auth_string:
            return False

        try:
            encoding = request.encoding or settings.DEFAULT_CHARSET or "utf-8"
        except AttributeError:
            encoding = "utf-8"

        try:
            b64_decoded = base64.b64decode(auth_string)
        except (TypeError, binascii.Error):
            log.debug(
                "Failed basic auth: %r can't be decoded as base64", auth_string)
            return False

        try:
            auth_string_decoded = b64_decoded.decode(encoding)
        except UnicodeDecodeError:
            log.debug(
                "Failed basic auth: %r can't be decoded as unicode by %r",
                auth_string, encoding
            )
            return False

        try:
            client_id, client_secret = map(
                unquote_plus, auth_string_decoded.split(":", 1))
        except ValueError:
            log.debug("Failed basic auth, Invalid base64 encoding.")
            return False

        if self._load_application(client_id, request) is None:
            log.debug(
                "Failed basic auth: Application %s does not exist" % client_id)
            return False
        elif request.client.client_id != client_id:
            log.debug("Failed basic auth: wrong client id %s" % client_id)
            return False
        elif request.client.client_secret != client_secret:
            log.debug("Failed basic auth: wrong client secret %s" %
                      client_secret)
            return False
        else:
            return True

    def _authenticate_request_body(self, request):
        """
        Try to authenticate the client using client_id and client_secret
        parameters included in body.

        Remember that this method is NOT RECOMMENDED and SHOULD be limited to
        clients unable to directly utilize the HTTP Basic authentication scheme.
        See rfc:`2.3.1` for more details.
        """
        try:
            client_id = request.client_id
            client_secret = request.client_secret
        except AttributeError:
            return False

        if self._load_application(client_id, request) is None:
            log.debug(
                "Failed body auth: Application %s does not exists" % client_id)
            return False
        elif request.client.client_secret != client_secret:
            log.debug("Failed body auth: wrong client secret %s" %
                      client_secret)
            return False
        else:
            return True

    def _load_application(self, client_id, request):
        """
        If request.client was not set, load application instance for given
        client_id and store it in request.client
        """

        # we want to be sure that request has the client attribute!
        assert hasattr(
            request, "client"), '"request" instance has no "client" attribute'

        try:
            request.client = request.client or Application.objects.get(
                client_id=client_id)
            # Check that the application can be used (defaults to always True)
            if not request.client.is_usable(request):
                log.debug(
                    "Failed body authentication: Application %r is disabled" % (client_id))
                return None
            return request.client
        except Application.DoesNotExist:
            log.debug(
                "Failed body authentication: Application %r does not exist" % (client_id))
            return None

    def _set_oauth2_error_on_request(self, request, access_token, scopes):
        if access_token is None:
            error = OrderedDict([
                ("error", "invalid_token", ),
                ("error_description", _("The access token is invalid."), ),
            ])
        elif access_token.is_expired():
            error = OrderedDict([
                ("error", "invalid_token", ),
                ("error_description", _("The access token has expired."), ),
            ])
        elif not access_token.allow_scopes(scopes):
            error = OrderedDict([
                ("error", "insufficient_scope", ),
                ("error_description", _(
                    "The access token is valid but does not have enough scope."), ),
            ])
        else:
            log.warning(
                "OAuth2 access token is invalid for an unknown reason.")
            error = OrderedDict([
                ("error", "invalid_token", ),
            ])
        request.oauth2_error = error
        return request

    def client_authentication_required(self, request, *args, **kwargs):
        """
        Determine if the client has to be authenticated

        This method is called only for grant types that supports client authentication:
            * Authorization code grant
            * Resource owner password grant
            * Refresh token grant

        If the request contains authorization headers, always authenticate the client
        no matter the grant type.

        If the request does not contain authorization headers, proceed with authentication
        only if the client is of type `Confidential`.

        If something goes wrong, call oauthlib implementation of the method.
        """
        if self._extract_basic_auth(request):
            return True

        try:
            if request.client_id and request.client_secret:
                return True
        except AttributeError:
            log.debug("Client ID or client secret not provided...")
            pass

        self._load_application(request.client_id, request)
        if request.client:
            return request.client.client_type == AbstractApplication.CLIENT_CONFIDENTIAL

        return super().client_authentication_required(request, *args, **kwargs)

    def authenticate_client(self, request, *args, **kwargs):
        """
        Check if client exists and is authenticating itself as in rfc:`3.2.1`

        First we try to authenticate with HTTP Basic Auth, and that is the PREFERRED
        authentication method.
        Whether this fails we support including the client credentials in the request-body,
        but this method is NOT RECOMMENDED and SHOULD be limited to clients unable to
        directly utilize the HTTP Basic authentication scheme.
        See rfc:`2.3.1` for more details
        """
        authenticated = self._authenticate_basic_auth(request)

        if not authenticated:
            authenticated = self._authenticate_request_body(request)

        return authenticated

    def authenticate_client_id(self, client_id, request, *args, **kwargs):
        """
        If we are here, the client did not authenticate itself as in rfc:`3.2.1` and we can
        proceed only if the client exists and is not of type "Confidential".
        """
        if self._load_application(client_id, request) is not None:
            log.debug("Application %r has type %r" %
                      (client_id, request.client.client_type))
            return request.client.client_type != AbstractApplication.CLIENT_CONFIDENTIAL
        return False

    def confirm_redirect_uri(self, client_id, code, redirect_uri, client, *args, **kwargs):
        """
        Ensure the redirect_uri is listed in the Application instance redirect_uris field
        """
        grant = Grant.objects.get(code=code, application=client)
        return grant.redirect_uri_allowed(redirect_uri)

    def invalidate_authorization_code(self, client_id, code, request, *args, **kwargs):
        """
        Remove the temporary grant used to swap the authorization token
        """
        grant = Grant.objects.get(code=code, application=request.client)
        grant.delete()

    def validate_client_id(self, client_id, request, *args, **kwargs):
        """
        Ensure an Application exists with given client_id.
        If it exists, it's assigned to request.client.
        """
        return self._load_application(client_id, request) is not None

    def get_default_redirect_uri(self, client_id, request, *args, **kwargs):
        return request.client.default_redirect_uri

    def _get_token_from_authentication_server(
            self, token, introspection_url, introspection_token, introspection_credentials
    ):
        """Use external introspection endpoint to "crack open" the token.
        :param introspection_url: introspection endpoint URL
        :param introspection_token: Bearer token
        :param introspection_credentials: Basic Auth credentials (id,secret)
        :return: :class:`models.AccessToken`

        Some RFC 7662 implementations (including this one) use a Bearer token while others use Basic
        Auth. Depending on the external AS's implementation, provide either the introspection_token
        or the introspection_credentials.

        If the resulting access_token identifies a username (e.g. Authorization Code grant), add
        that user to the UserModel. Also cache the access_token up until its expiry time or a
        configured maximum time.

        """
        headers = None
        if introspection_token:
            headers = {"Authorization": "Bearer {}".format(
                introspection_token)}
        elif introspection_credentials:
            client_id = introspection_credentials[0].encode("utf-8")
            client_secret = introspection_credentials[1].encode("utf-8")
            basic_auth = base64.b64encode(client_id + b":" + client_secret)
            headers = {"Authorization": "Basic {}".format(
                basic_auth.decode("utf-8"))}

        try:
            response = requests.post(
                introspection_url,
                data={"token": token}, headers=headers
            )
        except requests.exceptions.RequestException:
            log.exception(
                "Introspection: Failed POST to %r in token lookup", introspection_url)
            return None

        try:
            content = response.json()
        except ValueError:
            log.exception("Introspection: Failed to parse response as json")
            return None

        if "active" in content and content["active"] is True:
            if "username" in content:
                user, _created = UserModel.objects.get_or_create(
                    **{UserModel.USERNAME_FIELD: content["username"]}
                )
            else:
                user = None

            max_caching_time = datetime.now() + timedelta(
                seconds=oauth2_settings.RESOURCE_SERVER_TOKEN_CACHING_SECONDS
            )

            if "exp" in content:
                expires = datetime.utcfromtimestamp(content["exp"])
                if expires > max_caching_time:
                    expires = max_caching_time
            else:
                expires = max_caching_time

            scope = content.get("scope", "")
            expires = make_aware(expires)

            try:
                access_token = AccessToken.objects.select_related(
                    "application", "user").get(token=token)
            except AccessToken.DoesNotExist:
                access_token = AccessToken.objects.create(
                    token=token,
                    user=user,
                    application=None,
                    scope=scope,
                    expires=expires
                )
            else:
                access_token.expires = expires
                access_token.scope = scope
                access_token.save()

            return access_token

    def validate_bearer_token(self, token, scopes, request):
        """
        When users try to access resources, check that provided token is valid
        """
        if not token:
            return False

        introspection_url = oauth2_settings.RESOURCE_SERVER_INTROSPECTION_URL
        introspection_token = oauth2_settings.RESOURCE_SERVER_AUTH_TOKEN
        introspection_credentials = oauth2_settings.RESOURCE_SERVER_INTROSPECTION_CREDENTIALS

        try:
            access_token = AccessToken.objects.select_related(
                "application", "user").get(token=token)
            # if there is a token but invalid then look up the token
            if introspection_url and (introspection_token or introspection_credentials):
                if not access_token.is_valid(scopes):
                    access_token = self._get_token_from_authentication_server(
                        token,
                        introspection_url,
                        introspection_token,
                        introspection_credentials
                    )
            if access_token and access_token.is_valid(scopes):
                request.client = access_token.application
                request.user = access_token.user
                request.scopes = scopes

                # this is needed by django rest framework
                request.access_token = access_token
                return True
            self._set_oauth2_error_on_request(request, access_token, scopes)
            return False
        except AccessToken.DoesNotExist:
            # there is no initial token, look up the token
            if introspection_url and (introspection_token or introspection_credentials):
                access_token = self._get_token_from_authentication_server(
                    token,
                    introspection_url,
                    introspection_token,
                    introspection_credentials
                )
                if access_token and access_token.is_valid(scopes):
                    request.client = access_token.application
                    request.user = access_token.user
                    request.scopes = scopes

                    # this is needed by django rest framework
                    request.access_token = access_token
                    return True
            self._set_oauth2_error_on_request(request, None, scopes)
            return False

    def validate_code(self, client_id, code, client, request, *args, **kwargs):
        try:
            grant = Grant.objects.get(code=code, application=client)
            if not grant.is_expired():
                request.scopes = grant.scope.split(" ")
                request.user = grant.user
                return True
            return False

        except Grant.DoesNotExist:
            return False

    def validate_grant_type(self, client_id, grant_type, client, request, *args, **kwargs):
        """
        Validate both grant_type is a valid string and grant_type is allowed for current workflow
        """
        assert(grant_type in GRANT_TYPE_MAPPING)  # mapping misconfiguration
        return request.client.allows_grant_type(*GRANT_TYPE_MAPPING[grant_type])

    def validate_response_type(self, client_id, response_type, client, request, *args, **kwargs):
        """
        We currently do not support the Authorization Endpoint Response Types registry as in
        rfc:`8.4`, so validate the response_type only if it matches "code" or "token"
        """

        # response_types = {
        #     'code': auth_grant_choice,
        #     'token': implicit_grant_choice,
        #     'id_token': openid_connect_implicit,
        #     'id_token token': openid_connect_implicit,
        #     'code token': openid_connect_hybrid,
        #     'code id_token': openid_connect_hybrid,
        #     'code id_token token': openid_connect_hybrid,
        #     'none': auth_grant
        # },

        if response_type in ["code", 'code token', 'code id_token', 'code id_token token']:
            return client.allows_grant_type(AbstractApplication.GRANT_AUTHORIZATION_CODE)
        elif response_type in ["token", 'id_token', 'id_token token']:
            return client.allows_grant_type(AbstractApplication.GRANT_IMPLICIT)
        else:
            return False

    def validate_scopes(self, client_id, scopes, client, request, *args, **kwargs):
        """
        Ensure required scopes are permitted (as specified in the settings file)
        """
        available_scopes = get_scopes_backend().get_available_scopes(
            application=client, request=request)
        return set(scopes).issubset(set(available_scopes))

    def get_default_scopes(self, client_id, request, *args, **kwargs):
        default_scopes = get_scopes_backend().get_default_scopes(
            application=request.client, request=request)
        return default_scopes

    def validate_redirect_uri(self, client_id, redirect_uri, request, *args, **kwargs):
        return request.client.redirect_uri_allowed(redirect_uri)

    def save_authorization_code(self, client_id, code, request, *args, **kwargs):
        expires = timezone.now() + timedelta(
            seconds=oauth2_settings.AUTHORIZATION_CODE_EXPIRE_SECONDS)
        g = Grant(application=request.client, user=request.user, code=code["code"],
                  expires=expires, redirect_uri=request.redirect_uri,
                  scope=" ".join(request.scopes))
        g.save()

    def rotate_refresh_token(self, request):
        """
        Checks if rotate refresh token is enabled
        """
        return oauth2_settings.ROTATE_REFRESH_TOKEN

    @transaction.atomic
    def save_bearer_token(self, token, request, *args, **kwargs):
        """
        Save access and refresh token, If refresh token is issued, remove or
        reuse old refresh token as in rfc:`6`

        @see: https://tools.ietf.org/html/draft-ietf-oauth-v2-31#page-43
        """
        if "scope" not in token:
            raise FatalClientError(
                "Failed to renew access token: missing scope")

        expires = timezone.now() + timedelta(seconds=oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS)

        if request.grant_type == "client_credentials":
            request.user = None

        # This comes from OAuthLib:
        # https://github.com/idan/oauthlib/blob/1.0.3/oauthlib/oauth2/rfc6749/tokens.py#L267
        # Its value is either a new random code; or if we are reusing
        # refresh tokens, then it is the same value that the request passed in
        # (stored in `request.refresh_token`)
        refresh_token_code = token.get("refresh_token", None)

        if refresh_token_code:
            # an instance of `RefreshToken` that matches the old refresh code.
            # Set on the request in `validate_refresh_token`
            refresh_token_instance = getattr(
                request, "refresh_token_instance", None)

            # If we are to reuse tokens, and we can: do so
            if not self.rotate_refresh_token(request) and \
                isinstance(refresh_token_instance, RefreshToken) and \
                    refresh_token_instance.access_token:

                access_token = AccessToken.objects.select_for_update().get(
                    pk=refresh_token_instance.access_token.pk
                )
                access_token.user = request.user
                access_token.scope = token["scope"]
                access_token.expires = expires
                access_token.token = token["access_token"]
                access_token.application = request.client
                access_token.save()

            # else create fresh with access & refresh tokens
            else:
                # revoke existing tokens if possible to allow reuse of grant
                if isinstance(refresh_token_instance, RefreshToken):
                    previous_access_token = AccessToken.objects.filter(
                        source_refresh_token=refresh_token_instance
                    ).first()
                    try:
                        refresh_token_instance.revoke()
                    except (AccessToken.DoesNotExist, RefreshToken.DoesNotExist):
                        pass
                    else:
                        setattr(request, "refresh_token_instance", None)
                else:
                    previous_access_token = None

                # If the refresh token has already been used to create an
                # access token (ie it's within the grace period), return that
                # access token
                if not previous_access_token:
                    access_token = self._create_access_token(
                        expires,
                        request,
                        token,
                        source_refresh_token=refresh_token_instance,
                    )

                    refresh_token = RefreshToken(
                        user=request.user,
                        token=refresh_token_code,
                        application=request.client,
                        access_token=access_token
                    )
                    refresh_token.save()
                else:
                    # make sure that the token data we're returning matches
                    # the existing token
                    token["access_token"] = previous_access_token.token
                    token["scope"] = previous_access_token.scope
        # No refresh token should be created, just access token
        else:
            self._create_access_token(expires, request, token)

    def _create_access_token(self, expires, request, token, source_refresh_token=None):
        access_token = AccessToken(
            user=request.user,
            scope=token["scope"],
            expires=expires,
            token=token["access_token"],
            application=request.client,
            source_refresh_token=source_refresh_token,
        )
        access_token.save()
        return access_token

    def revoke_token(self, token, token_type_hint, request, *args, **kwargs):
        """
        Revoke an access or refresh token.

        :param token: The token string.
        :param token_type_hint: access_token or refresh_token.
        :param request: The HTTP Request (oauthlib.common.Request)
        """
        if token_type_hint not in ["access_token", "refresh_token"]:
            token_type_hint = None

        token_types = {
            "access_token": AccessToken,
            "refresh_token": RefreshToken,
        }

        token_type = token_types.get(token_type_hint, AccessToken)
        try:
            token_type.objects.get(token=token).revoke()
        except ObjectDoesNotExist:
            for other_type in [_t for _t in token_types.values() if _t != token_type]:
                # slightly inefficient on Python2, but the queryset contains only one instance
                list(map(lambda t: t.revoke(), other_type.objects.filter(token=token)))

    def validate_user(self, username, password, client, request, *args, **kwargs):
        """
        Check username and password correspond to a valid and active User
        """
        u = authenticate(username=username, password=password)
        if u is not None and u.is_active:
            request.user = u
            return True
        return False

    def get_original_scopes(self, refresh_token, request, *args, **kwargs):
        # Avoid second query for RefreshToken since this method is invoked *after*
        # validate_refresh_token.
        rt = request.refresh_token_instance
        if not rt.access_token_id:
            return AccessToken.objects.get(source_refresh_token_id=rt.id).scope

        return rt.access_token.scope

    def validate_refresh_token(self, refresh_token, client, request, *args, **kwargs):
        """
        Check refresh_token exists and refers to the right client.
        Also attach User instance to the request object
        """

        null_or_recent = Q(revoked__isnull=True) | Q(
            revoked__gt=timezone.now() - timedelta(
                seconds=oauth2_settings.REFRESH_TOKEN_GRACE_PERIOD_SECONDS
            )
        )
        rt = RefreshToken.objects.filter(
            null_or_recent, token=refresh_token).first()

        if not rt:
            return False

        request.user = rt.user
        request.refresh_token = rt.token
        # Temporary store RefreshToken instance to be reused by
        # get_original_scopes and save_bearer_token.
        request.refresh_token_instance = rt
        return rt.application == client


class OpenIDRequestValidator(OAuth2Validator):
    def get_authorization_code_scopes(self, client_id, code, redirect_uri, request):

        # import ipdb
        # ipdb.set_trace()
        """ Extracts scopes from saved authorization code.

        The scopes returned by this method is used to route token requests
        based on scopes passed to Authorization Code requests.

        With that the token endpoint knows when to include OpenIDConnect
        id_token in token response only based on authorization code scopes.

        Only code param should be sufficient to retrieve grant code from
        any storage you are using, `client_id` and `redirect_uri` can have a
        blank value `""` don't forget to check it before using those values
        in a select query if a database is used.

        :param client_id: Unicode client identifier
        :param code: Unicode authorization code grant
        :param redirect_uri: Unicode absolute URI
        :return: A list of scope

        Method is used by:
            - Authorization Token Grant Dispatcher
        """
        # raise NotImplementedError('Subclasses must implement this method.')
        return ['openid']

    def get_authorization_code_nonce(self, client_id, code, redirect_uri, request):
        """ Extracts nonce from saved authorization code.

        If present in the Authentication Request, Authorization
        Servers MUST include a nonce Claim in the ID Token with the
        Claim Value being the nonce value sent in the Authentication
        Request. Authorization Servers SHOULD perform no other
        processing on nonce values used. The nonce value is a
        case-sensitive string.

        Only code param should be sufficient to retrieve grant code from
        any storage you are using. However, `client_id` and `redirect_uri`
        have been validated and can be used also.

        :param client_id: Unicode client identifier
        :param code: Unicode authorization code grant
        :param redirect_uri: Unicode absolute URI
        :return: Unicode nonce

        Method is used by:
            - Authorization Token Grant Dispatcher
        """
        raise NotImplementedError('Subclasses must implement this method.')

    def get_jwt_bearer_token(self, token, token_handler, request):
        """Get JWT Bearer token or OpenID Connect ID token

        If using OpenID Connect this SHOULD call `oauthlib.oauth2.RequestValidator.get_id_token`

        :param token: A Bearer token dict
        :param token_handler: the token handler (BearerToken class)
        :param request: OAuthlib request.
        :type request: oauthlib.common.Request
        :return: The JWT Bearer token or OpenID Connect ID token (a JWS signed JWT)

        Method is used by JWT Bearer and OpenID Connect tokens:
            - JWTToken.create_token
        """
        with open(os.path.join(settings.ROOT_DIR, "key-files/private_key.pem"), "rb") as fd:
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import serialization
            self.private_pem = serialization.load_pem_private_key(
                fd.read(),
                password=None,
                backend=default_backend()
            )

        import jwt
        jwt_claims = dict()
        jwt_claims["iss"] = build_absolute_uri(request.headers, '/o')
        jwt_claims["sub"] = request.client_id
        jwt_claims["iat"] = int(time.time())
        jwt_claims["exp"] = jwt_claims["iat"] + request.expires_in

        token = {
            'access_token': jwt.encode(jwt_claims, self.private_pem, 'RS256').decode('UTF-8'),
            'expires_in': request.expires_in,
            'token_type': 'Bearer JWT',
        }

        from oauthlib.oauth2.rfc6749.tokens import OAuth2Token
        # If provided, include - this is optional in some cases
        # https://tools.ietf.org/html/rfc6749#section-3.3 but
        # there is currently no mechanism to coordinate issuing a token
        # for only a subset of the requested scopes so
        # all tokens issued are for the entire set of requested scopes.
        if request.scopes is not None:
            token['scope'] = ' '.join(request.scopes)

        token.update(request.extra_credentials or {})
        return OAuth2Token(token)

    def get_id_token(self, token, token_handler, request):
        """Get OpenID Connect ID token

        This method is OPTIONAL and is NOT RECOMMENDED.
        `finalize_id_token` SHOULD be implemented instead. However, if you
        want a full control over the minting of the `id_token`, you
        MAY want to override `get_id_token` instead of using
        `finalize_id_token`.

        In the OpenID Connect workflows when an ID Token is requested this method is called.
        Subclasses should implement the construction, signing and optional encryption of the
        ID Token as described in the OpenID Connect spec.

        In addition to the standard OAuth2 request properties, the request may also contain
        these OIDC specific properties which are useful to this method:

            - nonce, if workflow is implicit or hybrid and it was provided
            - claims, if provided to the original Authorization Code request

        The token parameter is a dict which may contain an ``access_token`` entry, in which
        case the resulting ID Token *should* include a calculated ``at_hash`` claim.

        Similarly, when the request parameter has a ``code`` property defined, the ID Token
        *should* include a calculated ``c_hash`` claim.

        http://openid.net/specs/openid-connect-core-1_0.html
        (sections `3.1.3.6`_, `3.2.2.10`_, `3.3.2.11`_)

        .. _`3.1.3.6`: http://openid.net/specs/openid-connect-core-1_0.html#CodeIDToken
        .. _`3.2.2.10`: http://openid.net/specs/openid-connect-core-1_0.html#ImplicitIDToken
        .. _`3.3.2.11`: http://openid.net/specs/openid-connect-core-1_0.html#HybridIDToken

        :param token: A Bearer token dict
        :param token_handler: the token handler (BearerToken class)
        :param request: OAuthlib request.
        :type request: oauthlib.common.Request
        :return: The ID Token (a JWS signed JWT)
        """
        return None

    def finalize_id_token(self, id_token, token, token_handler, request):
        """Finalize OpenID Connect ID token & Sign or Encrypt.

        In the OpenID Connect workflows when an ID Token is requested
        this method is called.  Subclasses should implement the
        construction, signing and optional encryption of the ID Token
        as described in the OpenID Connect spec.

        The `id_token` parameter is a dict containing a couple of OIDC
        technical fields related to the specification. Prepopulated
        attributes are:

        - `aud`, equals to `request.client_id`.
        - `iat`, equals to current time.
        - `nonce`, if present, is equals to the `nonce` from the
          authorization request.
        - `at_hash`, hash of `access_token`, if relevant.
        - `c_hash`, hash of `code`, if relevant.

        This method MUST provide required fields as below:

        - `iss`, REQUIRED. Issuer Identifier for the Issuer of the response.
        - `sub`, REQUIRED. Subject Identifier
        - `exp`, REQUIRED. Expiration time on or after which the ID
          Token MUST NOT be accepted by the RP when performing
          authentication with the OP.

        Additionals claims must be added, note that `request.scope`
        should be used to determine the list of claims.

        More information can be found at `OpenID Connect Core#Claims`_

        # Claims`: https://openid.net/specs/openid-connect-core-1_0.html#Claims
        .. _`OpenID Connect Core

        :param id_token: A dict containing technical fields of id_token
        :param token: A Bearer token dict
        :param token_handler: the token handler (BearerToken class)
        :param request: OAuthlib request.
        :type request: oauthlib.common.Request
        :return: The ID Token (a JWS signed JWT or JWE encrypted JWT)
        """

        with open(os.path.join(settings.ROOT_DIR, "key-files/private_key.pem"), "rb") as fd:
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import serialization
            self.private_pem = serialization.load_pem_private_key(
                fd.read(),
                password=None,
                backend=default_backend()
            )

        import jwt
        id_token["iss"] = request.iss
        id_token["sub"] = request.user.id
        id_token["exp"] = id_token["iat"] + \
            3600 * 24  # keep it valid for 24hours

        id_token['aud'] = list(
            Application.objects.values_list('client_id', flat=True))

        id_token['azp'] = request.client_id

        real_hr_soft_claims = dict()

        if PROFILE in request.scopes:
            id_token["email"] = request.user.email
            id_token["name"] = request.user.full_name
            id_token["given_name"] = request.user.first_name
            id_token["middle_name"] = request.user.middle_name
            id_token["family_name"] = request.user.last_name
            id_token["picture"] = request.user.profile_picture_thumb
            id_token["gender"] = request.user.detail.gender
            id_token["is_admin"] = request.user == request.client.user

            real_hr_soft_claims['organization_name'] = request.user.detail.organization.name
            real_hr_soft_claims['organization_slug'] = request.user.detail.organization.slug

        if APPLICATION_GROUPS in request.scopes:

            application_groups = dict()
            application_users = ApplicationUser.objects.filter(
                user=request.user
            )

            for application_user in application_users:

                application_groups[application_users.application.client_id] = [
                    str(item) for item in application_user.groups.all()
                ]

            real_hr_soft_claims[APPLICATION_GROUPS] = application_groups

        id_token['real_hr_soft'] = real_hr_soft_claims

        return jwt.encode(id_token, self.private_pem, 'RS256')

    def validate_jwt_bearer_token(self, token, scopes, request):
        """
        Ensure the JWT Bearer token or OpenID Connect ID token are valids and authorized access
         to scopes.

        If using OpenID Connect this SHOULD call `oauthlib.oauth2.RequestValidator.get_id_token`

        If not using OpenID Connect this can `return None` to avoid 5xx rather 401/3 response.

        OpenID connect core 1.0 describe how to validate an id_token:
            - http://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation
            - http://openid.net/specs/openid-connect-core-1_0.html#ImplicitIDTValidation
            - http://openid.net/specs/openid-connect-core-1_0.html#HybridIDTValidation
            - http://openid.net/specs/openid-connect-core-1_0.html#HybridIDTValidation2

        :param token: Unicode Bearer token
        :param scopes: List of scopes (defined by you)
        :param request: OAuthlib request.
        :type request: oauthlib.common.Request
        :rtype: True or False

        Method is indirectly used by all core OpenID connect JWT token issuing grant types:
            - Authorization Code Grant
            - Implicit Grant
            - Hybrid Grant
        """
        raise NotImplementedError('Subclasses must implement this method.')

    def validate_id_token(self, token, scopes, request):
        """Ensure the id token is valid and authorized access to scopes.

        OpenID connect core 1.0 describe how to validate an id_token:
            - http://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation
            - http://openid.net/specs/openid-connect-core-1_0.html#ImplicitIDTValidation
            - http://openid.net/specs/openid-connect-core-1_0.html#HybridIDTValidation
            - http://openid.net/specs/openid-connect-core-1_0.html#HybridIDTValidation2

        :param token: Unicode Bearer token
        :param scopes: List of scopes (defined by you)
        :param request: OAuthlib request.
        :type request: oauthlib.common.Request
        :rtype: True or False

        Method is indirectly used by all core OpenID connect JWT token issuing grant types:
            - Authorization Code Grant
            - Implicit Grant
            - Hybrid Grant
        """
        raise NotImplementedError('Subclasses must implement this method.')

    def validate_silent_authorization(self, request):
        """Ensure the logged in user has authorized silent OpenID authorization.

        Silent OpenID authorization allows access tokens and id tokens to be
        granted to clients without any user prompt or interaction.

        :param request: OAuthlib request.
        :type request: oauthlib.common.Request
        :rtype: True or False

        Method is used by:
            - OpenIDConnectAuthCode
            - OpenIDConnectImplicit
            - OpenIDConnectHybrid
        """
        # raise NotImplementedError('Subclasses must implement this method.')
        return True

    def validate_silent_login(self, request):
        """Ensure session user has authorized silent OpenID login.

        If no user is logged in or has not authorized silent login, this
        method should return False.

        If the user is logged in but associated with multiple accounts and
        not selected which one to link to the token then this method should
        raise an oauthlib.oauth2.AccountSelectionRequired error.

        :param request: OAuthlib request.
        :type request: oauthlib.common.Request
        :rtype: True or False

        Method is used by:
            - OpenIDConnectAuthCode
            - OpenIDConnectImplicit
            - OpenIDConnectHybrid
        """
        # raise NotImplementedError('Subclasses must implement this method.')
        return True

    def validate_user_match(self, id_token_hint, scopes, claims, request):
        """Ensure client supplied user id hint matches session user.

        If the sub claim or id_token_hint is supplied then the session
        user must match the given ID.

        :param id_token_hint: User identifier string.
        :param scopes: List of OAuth 2 scopes and OpenID claims (strings).
        :param claims: OpenID Connect claims dict.
        :param request: OAuthlib request.
        :type request: oauthlib.common.Request
        :rtype: True or False

        Method is used by:
            - OpenIDConnectAuthCode
            - OpenIDConnectImplicit
            - OpenIDConnectHybrid
        """

        if not id_token_hint:
            return True
        else:
            raise NotImplementedError('Subclasses must implement this method.')

    def get_userinfo_claims(self, request):
        """Return the UserInfo claims in JSON or Signed or Encrypted.

        The UserInfo Claims MUST be returned as the members of a JSON object
         unless a signed or encrypted response was requested during Client
         Registration. The Claims defined in Section 5.1 can be returned, as can
         additional Claims not specified there.

        For privacy reasons, OpenID Providers MAY elect to not return values for
        some requested Claims.

        If a Claim is not returned, that Claim Name SHOULD be omitted from the
        JSON object representing the Claims; it SHOULD NOT be present with a
        null or empty string value.

        The sub (subject) Claim MUST always be returned in the UserInfo
        Response.

        Upon receipt of the UserInfo Request, the UserInfo Endpoint MUST return
        the JSON Serialization of the UserInfo Response as in Section 13.3 in
        the HTTP response body unless a different format was specified during
        Registration [OpenID.Registration].

        If the UserInfo Response is signed and/or encrypted, then the Claims are
        returned in a JWT and the content-type MUST be application/jwt. The
        response MAY be encrypted without also being signed. If both signing and
        encryption are requested, the response MUST be signed then encrypted,
        with the result being a Nested JWT, as defined in [JWT].

        If signed, the UserInfo Response SHOULD contain the Claims iss (issuer)
        and aud (audience) as members. The iss value SHOULD be the OP's Issuer
        Identifier URL. The aud value SHOULD be or include the RP's Client ID
        value.

        :param request: OAuthlib request.
        :type request: oauthlib.common.Request
        :rtype: Claims as a dict OR JWT/JWS/JWE as a string

        Method is used by:
            UserInfoEndpoint
        """
