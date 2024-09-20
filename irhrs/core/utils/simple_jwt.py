"""@irhrs_docs"""
from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework_simplejwt.backends import TokenBackend
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.utils import datetime_from_epoch

jwt_config = settings.SIMPLE_JWT

# The below settings are defined in settings.
simple_jwt_backend = TokenBackend(
    jwt_config.get('ALGORITHM'),
    jwt_config.get('SIGNING_KEY'),
    jwt_config.get('VERIFYING_KEY')
)
USER = get_user_model()


class SimpleJWTParser:
    token = ''

    def __init__(self, token):
        self.token = token

    @property
    def parsed(self):
        if hasattr(self, 'parsed_token'):
            return self.parsed_token
        try:
            self.parsed_token = simple_jwt_backend.decode(token=self.token)
            return self.parsed_token
        except TokenError:
            return None

    @property
    def token_created(self):
        parsed = self.parsed
        exp = parsed.get('exp')
        token_lifetime = {
            'access': 'ACCESS_TOKEN_LIFETIME',
            'refresh': 'REFRESH_TOKEN_LIFETIME'
        }
        return datetime_from_epoch(exp) - jwt_config.get(
            token_lifetime.get(parsed.get('token_type'))
        )

    @property
    def user(self):
        token = self.parsed
        return USER.objects.get(id=token.get('user_id'))
