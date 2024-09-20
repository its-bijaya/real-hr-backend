import hashlib, uuid
from oauthlib.openid.connect.core.grant_types.implicit import ImplicitGrant
from oauthlib.oauth2.rfc6749.grant_types.implicit import ImplicitGrant as OAuth2ImplicitGrant
class OICDImplicitGrant(ImplicitGrant):

    def __init__(self, request_validator=None, **kwargs):
        self.proxy_target = OAuth2ImplicitGrant(
            request_validator=request_validator, **kwargs)
        self.register_response_type('id_token')
        self.register_response_type('id_token token')
        self.custom_validators.post_auth.append(
            self.openid_authorization_validator)
        self.register_token_modifier(self.add_id_token)
        self.register_token_modifier(self.add_session_state)

    def add_session_state(self, token, token_handler, request):
        salt = uuid.uuid4().hex
        client_id = request.client_id
        origin = '/'.join(request.redirect_uri.split('/')[0:3])
        browser_state = request.cookie


        state = client_id + ' ' + origin + ' ' + browser_state + ' ' + salt

        hh = hashlib.sha256()
        hh.update(state.encode('utf-8'))

        session_state = hh.hexdigest() + '.' + salt

        token['session_state'] = session_state

        return token

    def validate_authorization_request(self, request):
        
        """Validates the OpenID Connect authorization request parameters.

        :returns: (list of scopes, dict of request info)
        """

        # If request.prompt is 'none' then no login/authorization form should
        # be presented to the user. Instead, a silent login/authorization
        # should be performed.
        
        return self.proxy_target.validate_authorization_request(request)