from rest_framework_simplejwt.exceptions import TokenBackendError
from irhrs.permission.constants.groups import ADMIN
from irhrs.core.utils.simple_jwt import SimpleJWTParser
from django.contrib.auth import get_user_model
from django.utils.deprecation import MiddlewareMixin

User = get_user_model()


class CookieRefreshTokenAuthenticationMiddleware(MiddlewareMixin):
    # def get_user(self, user_id):
    #     return User.objects.get(id=user_id)

    def process_request(self, request):
        auth_token = request.COOKIES.get('auth._token.local')
        # if refresh_token:
        #     valid_refresh_token = False
        #     try:
        #         RefreshToken(refresh_token)
        #         valid_refresh_token = True
        #     except:
        #         pass

        #     if valid_refresh_token:
        #         payload = jwt.decode(refresh_token, verify=False)
        try:
            user = self.get_user(auth_token)
            if user:
                request.user = user
        except TokenBackendError:
            pass

    @staticmethod
    def get_user(raw_token):
        token_parser = SimpleJWTParser(raw_token)
        token_created = token_parser.token_created
        user = token_parser.user

        # Invalidate if the user has no experience or is not an admin
        is_active = user.current_experience or user.groups.filter(name=ADMIN).exists()
        is_enabled = user.is_active and not user.is_blocked
        if not (is_active and is_enabled):
            return None
        token_refreshed = getattr(user, 'token_refresh_date', None)
        if token_refreshed and (
                token_created
                - token_refreshed
        ).total_seconds() < -1:
            return None
        return user