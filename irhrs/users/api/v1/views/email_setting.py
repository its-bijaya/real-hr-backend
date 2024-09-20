from django.db.models import Case, When, F
from rest_framework.response import Response

from irhrs.core.mixins.viewset_mixins import ListCreateViewSetMixin, UserCommonsMixin
from irhrs.users.api.v1.serializers.email_setting import UserEmailSettingSerializer, \
    UserEmailSettingBulkUpdateSerializer, UserEmailGroupSettingSerializer


class UserEmailNotificationSettingViewSet(
    UserCommonsMixin,
    ListCreateViewSetMixin
):
    serializer_class = UserEmailSettingSerializer

    def has_user_permission(self):
        return self.is_current_user()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserEmailSettingBulkUpdateSerializer
        return super().get_serializer_class()

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['user'] = self.user
        ctx['organization'] = self.get_organization()
        return ctx

    def get_queryset(self):
        unsubscribed_emails = self.user.unsubscribed_emails.values_list('email_type', flat=True)
        organization = self.get_organization()
        queryset = organization.email_settings.filter(send_email=True).annotate(
            _send_email=Case(
                When(
                    email_type__in=unsubscribed_emails,
                    then=False,
                ),
                default=F('send_email')
            )
        ).order_by('email_type')
        return queryset

    def list(self, request, *args, **kwargs):
        return Response(UserEmailGroupSettingSerializer(self.get_queryset()).data)


