from rest_framework import filters
from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.change_request import ChangeRequestMixin
from irhrs.users.api.v1.serializers.volunteer_experience import \
    UserVolunteerExperienceSerializer
from irhrs.users.models import UserVolunteerExperience


class UserVolunteerExperienceViewSet(ChangeRequestMixin, ModelViewSet):
    """
    list:
    Lists User Volunteer Experience for the selected User.

    create:
    Create new User Volunteer Experience for the given User.

    retrieve:
    Get User Volunteer Experience of the User.

    delete:
    Deletes the selected User Volunteer Experience of the User.

    update:
    Updates the selected User Volunteer Experience details for the given User.

    """
    queryset = UserVolunteerExperience.objects.all()
    serializer_class = UserVolunteerExperienceSerializer
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('title',)
    ordering_fields = ('title',)

