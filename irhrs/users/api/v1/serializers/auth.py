from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError, TokenBackendError
from rest_framework_simplejwt.serializers import (TokenRefreshSerializer,
                                                  TokenObtainPairSerializer, PasswordField)
from rest_framework_simplejwt.utils import datetime_from_epoch
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.simple_jwt import SimpleJWTParser
from irhrs.notification.models import Notification
from irhrs.organization.models import UserOrganization
from irhrs.permission.constants.groups import ADMIN
from irhrs.permission.constants.permissions import NOTICE_BOARD_PERMISSION, AUTH_PERMISSION
from irhrs.users.api.v1.serializers.user_detail import MeSerializer
from irhrs.users.models import UserPhone as Phone, UserDetail, UserSupervisor
from irhrs.noticeboard.models.noticeboard_setting import NoticeBoardSetting

User = get_user_model()
LOGIN_FAILED = None if settings.DEBUG else "Unable to login with given credentials."


def d_raise(msg):
    """
    :param msg: Message to display
    :return: Raises proper message behind login failed in debug state.
    Just displays unable to login while debug is false.
    """
    raise ValidationError(LOGIN_FAILED or msg)


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    refreshed_on = None
    user = None

    @staticmethod
    def token_created(exp):
        created_on = datetime_from_epoch(exp)
        return created_on

    def set_last_refreshed(self, token):
        token_parser = SimpleJWTParser(token=token)
        self.user = token_parser.user
        if not self.user.is_active:
            raise ValidationError(
                "User is inactive"
            )
        elif self.user.is_blocked:
            raise ValidationError(
                "User is blocked"
            )
        created_on = token_parser.token_created
        token_refreshed_on = getattr(self.user, 'token_refresh_date', None)
        if token_refreshed_on:
            if (created_on - token_refreshed_on).total_seconds() < -1:
                raise ValidationError({
                    'detail': 'Token is invalid or expired'
                })
        expire_old_token = getattr(
            settings, 'INVALIDATE_TOKEN_ON_REFRESH', True
        )
        if expire_old_token:
            setattr(self.user, 'token_refresh_date', self.refreshed_on)
            self.user.save(update_fields=['token_refresh_date'])

    def validate(self, attrs):
        access_token = attrs.get('refresh')
        ret = super().validate(attrs)
        self.refreshed_on = timezone.now()
        self.set_last_refreshed(access_token)
        return ret


class TokenWithMeMixin:
    @staticmethod
    def me_response(user):
        queryset = UserDetail.objects.filter(
            user=user
        ).select_related(
            'user',
            'organization',
        )
        if not queryset:
            raise ValidationError(
                "You do not have permission"
            )
        user_detail = queryset.get()
        user = user_detail.user
        data = MeSerializer(user_detail).data
        user_supervisor = UserSupervisor.objects.filter(
            supervisor=user
        )
        is_supervisor = user_supervisor.exists()
        if is_supervisor:
            sub_ordinate_org = set(user_supervisor.exclude(
                user_organization__isnull=True
            ).values_list('user_organization', flat=True))
            supervisor_org = user.detail.organization.id
            _supervisor_data = TokenWithMeMixin.calculate_supervisor_action(
                sub_ordinate_org=sub_ordinate_org,
                supervisor_org=supervisor_org
            )
        else:
            _supervisor_data = None
        is_admin = validate_permissions(
            user.get_hrs_permissions(),
            AUTH_PERMISSION
        )
        noticeboard_setting = NoticeBoardSetting.objects.first()
        data.update({
            'is_admin': is_admin,
            'supervisor': _supervisor_data,
            'can_switch_organizations': UserOrganization.objects.filter(
                user=user,
                can_switch=True
            ).exists(),
            'unread_notifications': Notification.objects.filter(
                recipient=user,
                read=False
            ).count(),
            'noticeboard_permission': validate_permissions(
                user.get_hrs_permissions(),
                NOTICE_BOARD_PERMISSION
            ),
            'notice_board_settings': {
                'allow_to_post': noticeboard_setting.allow_to_post if noticeboard_setting else True,
                'need_approval': noticeboard_setting.need_approval if noticeboard_setting else False
            },
            'attendance_approval_required': user.attendance_setting.enable_approval
        })
        return data

    @staticmethod
    def calculate_supervisor_action(sub_ordinate_org, supervisor_org):
        """
        It determines whether supervisor can switch organization or not and also determines whether
        there are default organization or not i.e. subordinates from same organization

        :param sub_ordinate_org: takes set of subordinates organization id
        :param supervisor_org: takes supervisors organization id
        :return: tuple of bool value
        """
        can_switch, has_default = False, True
        if supervisor_org not in sub_ordinate_org:
            can_switch, has_default = has_default, can_switch
        if len(sub_ordinate_org) > 1:
            can_switch = True
        return dict(
            can_switch=can_switch,
            has_default=has_default
        )


class UserInvolvementDataMixin:

    @staticmethod
    def involvement_data(user):
        return {
            'involvement_data': {
                'interview': UserInvolvementDataMixin.get_interview_data(user),
                'reference_check': UserInvolvementDataMixin.get_reference_check_data(user),
            }
        }

    @staticmethod
    def get_interview_data(user):
        from irhrs.recruitment.models.job_apply import InterViewAnswer
        return InterViewAnswer.objects.filter(internal_interviewer=user).exists()

    @staticmethod
    def get_reference_check_data(user):
        from irhrs.recruitment.models.job_apply import ReferenceCheckAnswer
        return ReferenceCheckAnswer.objects.filter(
            internal_reference_checker=user).exists()


class CustomTokenRefreshView(
    UserInvolvementDataMixin,
    TokenWithMeMixin,
    TokenRefreshView
):
    def post(self, request, *args, **kwargs):
        ser = CustomTokenRefreshSerializer(
            data=request.data
        )
        try:
            ser.is_valid(raise_exception=True)
        except (TokenError, TokenBackendError):
            return Response({
                'refresh': 'Token is Invalid or Expired'
            }, status=400)
        return Response({
            'token': ser.validated_data,
            **self.me_response(ser.user),
            # **self.involvement_data(ser.user)
        })


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'] = serializers.CharField(required=False)
        self.fields['email'] = serializers.CharField(required=False)
        self.fields['password'] = PasswordField(trim_whitespace=False)

    username_field = 'email'
    auth_fields = ['email', 'username']
    user = None

    def validate(self, attrs):
        email = attrs.get('email')
        username = attrs.get('username') or email
        password = attrs.get('password')
        for auth_field in self.auth_fields:
            try:
                self.user = User.objects.get(
                    **{auth_field + '__iexact': username})
                if self.user:
                    is_active = self.user.is_active
                    is_blocked = self.user.is_blocked
                    if not is_active:
                        d_raise("User is inactive.")
                    if is_blocked:
                        d_raise("User has been blocked.")
                    if not (
                            self.user.current_experience
                            or self.user.groups.filter(name=ADMIN).exists()
                    ):
                        d_raise("User has no current experience.")
            except User.DoesNotExist:
                pass
        if self.user and self.user.check_password(password):
            refresh = self.get_token(self.user)
            data = dict(
                refresh=str(refresh),
                access=str(refresh.access_token)
            )
            return data
        d_raise("Either user does not exist or username password was incorrect.")


class CustomTokenObtainView(
    UserInvolvementDataMixin,
    TokenWithMeMixin,
    TokenObtainPairView
):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        ser = CustomTokenObtainPairSerializer(
            data=request.data
        )
        ser.is_valid(raise_exception=True)
        return Response({
            'token': ser.validated_data,
            **self.me_response(ser.user),
            # **self.involvement_data(ser.user)
        })
