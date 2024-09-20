"""@irhrs_docs"""
from cuser.middleware import CuserMiddleware
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTTokenUserAuthentication

from irhrs.core.utils.simple_jwt import SimpleJWTParser
from irhrs.permission.constants.groups import ADMIN

LOGIN_FAILED = None if settings.DEBUG else "Unable to login with given credentials."


def d_raise(msg):
    """
    :param msg: Message to display
    :return: Raises proper message behind login failed in debug state.
    Just displays unable to login while debug is false.
    """
    raise AuthenticationFailed(_(LOGIN_FAILED or msg))


class CustomSimpleJWTAuthentication(JWTTokenUserAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if result:
            header = super().get_header(request)
            raw_token = super().get_raw_token(header)
            token_parser = SimpleJWTParser(raw_token)
            token_created = token_parser.token_created
            user = token_parser.user

            # Invalidate if the user has no experience or is not an admin
            if not (user.current_experience or user.groups.filter(name=ADMIN).exists()):
                d_raise("User has no current experience")
            if not user.is_active:
                d_raise("User is inactive")
            elif user.is_blocked:
                raise d_raise("User is blocked")
            token_refreshed = getattr(user, 'token_refresh_date', None)
            if token_refreshed and (
                    token_created
                    - token_refreshed
            ).total_seconds() < -1:
                raise d_raise('Signature has expired.')
            self.process_user(user)
            return user, result[1]
        return result

    @staticmethod
    def process_user(user):
        CuserMiddleware.set_user(user)
