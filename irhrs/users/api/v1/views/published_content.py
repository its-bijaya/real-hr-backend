from rest_framework import filters
from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.change_request import ChangeRequestMixin
from irhrs.users.api.v1.serializers.published_content import \
    UserPublishedContentSerializer
from irhrs.users.models import UserPublishedContent


class UserPublishedContentViewSet(ChangeRequestMixin, ModelViewSet):
    """
    list:
    Lists User Publication for the selected User.

    create:
    Create new User Publication for the given User.

    retrieve:
    Get User Publication of the User.

    delete:
    Deletes the selected User Publication of the User.

    update:
    Updates the selected User Publication details for the given User.

    """
    queryset = UserPublishedContent.objects.all()
    serializer_class = UserPublishedContentSerializer
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('name',)
