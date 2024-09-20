from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.serializers import DummySerializer
from irhrs.core.mixins.viewset_mixins import (
    OrganizationCommonsMixin, OrganizationMixin, RetrieveUpdateViewSetMixin,
    ListCreateRetrieveUpdateViewSetMixin
)
from irhrs.organization.api.v1.permissions import ApplicationSettingPermission, \
    OrganizationEmailNotificationSettingPermission
from irhrs.organization.api.v1.serializers.settings import \
    ContractSettingsSerializer, ApplicationSettingsSerializer, EmailNotificationSettingSerializer, \
    EmailNotificationSettingBulkUpdateSerializer, EmailGroupNotificationSettingSerializer
from irhrs.organization.models.settings import ContractSettings, \
    ApplicationSettings, EmailNotificationSetting
from irhrs.permission.constants.permissions import HRIS_PERMISSION, HRIS_CONTRACT_SETTINGS_PERMISSION
from irhrs.permission.permission_classes import permission_factory


class ContractSettingsView(OrganizationMixin, OrganizationCommonsMixin,
                           RetrieveUpdateViewSetMixin):
    queryset = ContractSettings.objects.all()
    serializer_class = ContractSettingsSerializer
    permission_classes = [permission_factory.build_permission(
        "ContractSettingsPermission",
        allowed_to=[
            HRIS_PERMISSION,
            HRIS_CONTRACT_SETTINGS_PERMISSION
        ]
    )]

    def get_object(self):
        return self.get_queryset().first()


class ApplicationSettingView(OrganizationMixin, OrganizationCommonsMixin,
                             ModelViewSet):
    queryset = ApplicationSettings.objects.all()
    serializer_class = ApplicationSettingsSerializer

    permission_classes = [ApplicationSettingPermission]
    http_methods_names = [u'get', u'post', u'patch', u'delete', u'options', u'head']


class EmailNotificationSettingViewSet(OrganizationMixin, OrganizationCommonsMixin,
                                      ListCreateRetrieveUpdateViewSetMixin):
    queryset = EmailNotificationSetting.objects.all().order_by('email_type')
    serializer_class = EmailNotificationSettingSerializer
    permission_classes = [OrganizationEmailNotificationSettingPermission]

    def get_serializer_class(self):
        if self.action == 'create':
            return EmailNotificationSettingBulkUpdateSerializer
        return super().get_serializer_class()

    @action(methods=['POST'], detail=False, serializer_class=DummySerializer)
    def reset(self, request, **kwargs):
        organization = self.organization
        EmailNotificationSetting.reset_setting(organization)
        return Response({
            'message': 'Reset Successful'
        })

    def list(self, request, *args, **kwargs):
        return Response(EmailGroupNotificationSettingSerializer(super().get_queryset()).data)


