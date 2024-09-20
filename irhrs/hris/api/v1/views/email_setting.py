from django.contrib.auth import get_user_model
from rest_framework.filters import SearchFilter
from rest_framework.decorators import action
from rest_framework.response import Response

from irhrs.core.mixins.viewset_mixins import OrganizationMixin, OrganizationCommonsMixin, \
    ListViewSetMixin
from irhrs.hris.api.v1.serializers.email_setting import EmailSettingSerializer, \
    EmailSettingPostSerializer
from irhrs.permission.constants.permissions import (
    EMAIL_SETTING_PERMISSION, HRIS_READ_ONLY_PERMISSION
)
from irhrs.permission.permission_classes import permission_factory

User = get_user_model()


class EmailSettingViewSet(OrganizationMixin, OrganizationCommonsMixin, ListViewSetMixin):
    serializer_class = EmailSettingSerializer
    queryset = User.objects.all().current()
    filter_backends = [SearchFilter]
    search_fields = ('first_name', 'middle_name', 'last_name')
    permission_classes = [
        permission_factory.build_permission(
            "EmailSettingPermission",
            allowed_to=[EMAIL_SETTING_PERMISSION],
            limit_read_to=[HRIS_READ_ONLY_PERMISSION]
        )
    ]

    organization_field = 'detail__organization'

    def get_queryset(self):
        return super().get_queryset().select_related(
            'detail', 'detail__job_title'
        ).prefetch_related(
            'email_setting'
        )

    @action(methods=['POST'], detail=False, url_path='create-setting',
            serializer_class=EmailSettingPostSerializer)
    def create_setting(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


