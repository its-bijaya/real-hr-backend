from rest_framework import filters
from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.change_request import ChangeRequestMixin
from irhrs.users.api.v1.serializers.training import UserTrainingSerializer
from irhrs.users.models import UserTraining


class UserTrainingViewSet(ChangeRequestMixin,
                          ModelViewSet):
    """
    list:
    Lists User Training for the selected User.

    create:
    Create new User Training for the given User.

    retrieve:
    Get UserTraining of the User.

    delete:
    Deletes the selected User Training of the User.

    update:
    Updates the selected User Training details for the given User.

    """
    queryset = UserTraining.objects.all()
    serializer_class = UserTrainingSerializer
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('title',)
    ordering_fields = ('title',)
