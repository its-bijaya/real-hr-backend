from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from irhrs.common.api.serializers.id_card import IdCardSampleSerializer
from irhrs.common.models import IdCardSample
from irhrs.core.utils.common import validate_permissions
from irhrs.permission.constants.permissions import (HRIS_ID_CARD_PERMISSION, HRIS_PERMISSION,
                                                    ALL_COMMON_SETTINGS_PERMISSION,
                                                    COMMON_ID_CARD_PERMISSION,
                                                    HAS_PERMISSION_FROM_METHOD, )
from irhrs.permission.permission_classes import permission_factory


class IdCardSampleViewSet(ModelViewSet):
    serializer_class = IdCardSampleSerializer
    queryset = IdCardSample.objects.all()
    permission_classes = [
        permission_factory.build_permission(
            "IDCardSamplePermission",
            limit_write_to=[
                ALL_COMMON_SETTINGS_PERMISSION,
                COMMON_ID_CARD_PERMISSION
            ],
            limit_read_to=[
                ALL_COMMON_SETTINGS_PERMISSION,
                COMMON_ID_CARD_PERMISSION,
                HAS_PERMISSION_FROM_METHOD
            ]
        )
    ]

    filter_backends = [SearchFilter, OrderingFilter]
    ordering_fields = ('name', 'created_at', 'modified_at')
    search_fields = ('name',)
    ordering = "-modified_at"

    def has_user_permission(self):
        user = self.request.user
        # guess which organization granted user to access this page.
        return validate_permissions(
            user.get_hrs_permissions(user.switchable_organizations_pks),
            HRIS_ID_CARD_PERMISSION,
            HRIS_PERMISSION
        )
