from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.change_request import ChangeRequestMixin
from irhrs.users.api.v1.serializers.insurance import UserInsuranceSerializer
from irhrs.users.models import UserInsurance


class UserInsuranceViewSet(ChangeRequestMixin, ModelViewSet):
    """
    list:
    Lists User Insurance Details for the selected User.

    create:
    Create new User Insurance detail for the given User.

    retrieve:
    Get User User Insurance Detail of the User.

    delete:
    Deletes the selected User Insurance Details of the User.

    update:
    Updates the selected User Insurance Details details for the given User.

    """
    queryset = UserInsurance.objects.all()
    serializer_class = UserInsuranceSerializer
