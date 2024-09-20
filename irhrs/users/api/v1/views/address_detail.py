from rest_framework import filters
from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.change_request import ChangeRequestMixin
from irhrs.users.api.v1.serializers.address_detail import UserAddressSerializer
from irhrs.users.models import UserAddress


class UserAddressViewSet(ChangeRequestMixin, ModelViewSet):
    """
    list:
    Lists User Address for the selected User.

    create:
    Create new User Address for the given User.

    retrieve:
    Get User Address of the User.

    delete:
    Deletes the selected User Address of the User.

    update:
    Updates the selected User Address details for the given User.

    """
    queryset = UserAddress.objects.all()
    serializer_class = UserAddressSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('address', 'city', 'country_ref', )
    ordering_fields = ('address', 'city', 'country_ref', )

    def get_serializer(self, *args, **kwargs):
        # only on get userdetail was added so removed for this view
        if self.request.method.upper() == 'GET':
            kwargs.update({'exclude_fields': ['user']})
        return super().get_serializer(*args, **kwargs)
