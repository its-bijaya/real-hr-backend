from django.views.decorators.clickjacking import xframe_options_exempt
from django.utils import timezone
from django.views.generic import (
    FormView,
    TemplateView,
    RedirectView
)

from django.contrib.auth import (
    REDIRECT_FIELD_NAME
)
from django.http import HttpResponseRedirect, QueryDict
from django.conf import settings as irhrs_settings

from urllib.parse import urlparse, urlunparse


from oauth2_provider.settings import oauth2_settings

from oauth2_provider.models import get_access_token_model, get_application_model
from oauth2_provider.scopes import get_scopes_backend
from oauth2_provider.views.base import BaseAuthorizationView
from oauth2_provider.exceptions import OAuthToolkitError

from irhrs.openid.forms import OCIDAllowForm

from django.core.exceptions import PermissionDenied


def redirect_to_login(next, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Redirect the user to the login page, passing the given 'next' page.
    """
    resolved_url = login_url

    login_url_parts = list(urlparse(resolved_url))
    if redirect_field_name:
        querystring = QueryDict(login_url_parts[4], mutable=True)
        querystring[redirect_field_name] = next
        login_url_parts[4] = querystring.urlencode(safe='/')

    return HttpResponseRedirect(urlunparse(login_url_parts))


class AuthorizationView(BaseAuthorizationView, FormView):
    """
    Implements an endpoint to handle *Authorization Requests* as in :rfc:`4.1.1` and prompting the
    user with a form to determine if she authorizes the client application to access her data.
    This endpoint is reached two times during the authorization process:
    * first receive a ``GET`` request from user asking authorization for a certain client
    application, a form is served possibly showing some useful info and prompting for
    *authorize/do not authorize*.

    * then receive a ``POST`` request possibly after user authorized the access

    Some information contained in the ``GET`` request and needed to create a Grant token during
    the ``POST`` request would be lost between the two steps above, so they are temporarily stored
    in hidden fields on the form.
    A possible alternative could be keeping such informations in the session.

    The endpoint is used in the following flows:
    * Authorization code
    * Implicit grant
    """
    template_name = "oauth2_provider/authorize.html"
    form_class = OCIDAllowForm

    server_class = oauth2_settings.OAUTH2_SERVER_CLASS
    validator_class = oauth2_settings.OAUTH2_VALIDATOR_CLASS
    oauthlib_backend_class = oauth2_settings.OAUTH2_BACKEND_CLASS

    skip_authorization_completely = False

    def get_login_url(self):
        return irhrs_settings.OPENID_LOGIN_URL

    def handle_no_permission(self):
        if self.raise_exception or self.request.user.is_authenticated:
            raise PermissionDenied(self.get_permission_denied_message())

        return redirect_to_login(self.request.get_full_path(), self.get_login_url(),
                                 self.get_redirect_field_name())

    @xframe_options_exempt
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            prompt = request.GET.get('prompt')
            if prompt == 'none':
                clinet_id = request.GET.get('client_id')
                redirect_uri = request.GET.get('redirect_uri')
                application = get_application_model().objects.get(client_id=clinet_id)

                if not application.redirect_uri_allowed(redirect_uri):
                    redirect_uri = application.default_redirect_uri

                redirect_uri = redirect_uri + '?error=No+session+present'

                return self.redirect(redirect_uri, application)

        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        scopes = self.oauth2_data.get(
            "scope", self.oauth2_data.get("scopes", []))
        initial_data = {
            "redirect_uri": self.oauth2_data.get("redirect_uri", None),
            "scope": " ".join(scopes),
            "client_id": self.oauth2_data.get("client_id", None),
            "state": self.oauth2_data.get("state", None),
            "response_type": self.oauth2_data.get("response_type", None),
            "nonce": self.oauth2_data.get("nonce", None),
        }
        return initial_data

    def form_valid(self, form):
        client_id = form.cleaned_data["client_id"]
        application = get_application_model().objects.get(client_id=client_id)
        credentials = {
            "client_id": form.cleaned_data.get("client_id"),
            "redirect_uri": form.cleaned_data.get("redirect_uri"),
            "response_type": form.cleaned_data.get("response_type", None),
            "state": form.cleaned_data.get("state", None),
            "nonce": form.cleaned_data.get("nonce", None),
            "cookie": self.request.COOKIES.get('auth._refresh_token.local')
        }
        scopes = form.cleaned_data.get("scope")
        allow = form.cleaned_data.get("allow")

        try:
            uri, headers, body, status = self.create_authorization_response(
                request=self.request, scopes=scopes, credentials=credentials, allow=allow
            )
        except OAuthToolkitError as error:
            return self.error_response(error, application)

        self.success_url = uri
        return self.redirect(self.success_url, application)

    def get(self, request, *args, **kwargs):
        try:
            scopes, credentials = self.validate_authorization_request(request)
        except OAuthToolkitError as error:
            # Application is not available at this time.
            return self.error_response(error, application=None)

        all_scopes = get_scopes_backend().get_all_scopes()
        kwargs["scopes_descriptions"] = [all_scopes[scope] for scope in scopes]
        kwargs["scopes"] = scopes
        # at this point we know an Application instance with such client_id exists in the database

        application = get_application_model().objects.get(
            client_id=credentials["client_id"])
        kwargs["application"] = application
        kwargs["client_id"] = credentials["client_id"]
        kwargs["redirect_uri"] = credentials["redirect_uri"]
        kwargs["response_type"] = credentials["response_type"]
        kwargs["state"] = credentials["state"]
        kwargs["nonce"] = credentials["nonce"]
        kwargs["iss"] = request.build_absolute_uri('/o')
        kwargs['cookie'] = self.request.COOKIES.get(
            'auth._refresh_token.local')

        self.oauth2_data = kwargs
        # following two loc are here only because of https://code.djangoproject.com/ticket/17795
        form = self.get_form(self.get_form_class())
        kwargs["form"] = form

        # Check to see if the user has already granted access and return
        # a successful response depending on "approval_prompt" url parameter
        require_approval = request.GET.get(
            "approval_prompt", oauth2_settings.REQUEST_APPROVAL_PROMPT)

        try:
            # If skip_authorization field is True, skip the authorization screen even
            # if this is the first use of the application and there was no previous authorization.
            # This is useful for in-house applications-> assume an in-house applications
            # are already approved.

            if application.skip_authorization or request.GET.get('prompt') == 'none':

                del kwargs['application']
                uri, headers, body, status = self.create_authorization_response(
                    request=self.request, scopes=" ".join(scopes),
                    credentials=kwargs, allow=True
                )

                return self.redirect(uri, application)

            elif require_approval == "auto":
                tokens = get_access_token_model().objects.filter(
                    user=request.user,
                    application=kwargs["application"],
                    expires__gt=timezone.now()
                ).all()

                # check past authorizations regarded the same scopes as the current one
                for token in tokens:
                    if token.allow_scopes(scopes):
                        uri, headers, body, status = self.create_authorization_response(
                            request=self.request, scopes=" ".join(scopes),
                            credentials=credentials, allow=True
                        )

                        return self.redirect(uri, application)

        except OAuthToolkitError as error:
            return self.error_response(error, application)
        # Below folling one line code is commented wrt no consent form
        # return self.render_to_response(self.get_context_data(**kwargs))

        # Start no consent form
        del kwargs['application']
        scopes = kwargs.get("scope")

        try:
            uri, headers, body, status = self.create_authorization_response(
                request=self.request, scopes=scopes, credentials=kwargs, allow=True
            )
        except OAuthToolkitError as error:
            return self.error_response(error, application)

        self.success_url = uri
        return self.redirect(self.success_url, application)

        # End no consent form


class CheckSessionIframeView(TemplateView):
    template_name = "check_session_iframe.html"

    @xframe_options_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class EndSessionView(RedirectView):

    permanent = False
    query_string = True
    url = '/rp-logout-handler'
