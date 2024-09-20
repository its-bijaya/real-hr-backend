from rest_framework import filters
from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.change_request import ChangeRequestMixin
from irhrs.users.api.v1.serializers.past_experience import \
    UserPastExperienceSerializer
from irhrs.users.models import UserPastExperience


class UserPastExperienceViewSet(ChangeRequestMixin, ModelViewSet):
    """
    list:
    Lists User Past Experience for the selected User.

    create:
    Create new User Past Experience for the given User.

    retrieve:
    Get User Past Experience of the User.

    delete:
    Deletes the selected User Past Experience of the User.

    update:
    Updates the selected User Past Experience details for the given User.

    """
    queryset = UserPastExperience.objects.all()
    serializer_class = UserPastExperienceSerializer
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('title',)
    ordering_fields = ('title',)

