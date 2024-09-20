from rest_framework import filters
from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.change_request import ChangeRequestMixin
from irhrs.users.api.v1.serializers.language import UserLanguageSerializer
from irhrs.users.models import UserLanguage


class UserLanguageViewSet(ChangeRequestMixin, ModelViewSet):
    """
    list:
    Lists User Language Details for the selected User.

    create:
    Create new User Language Address for the given User.

    retrieve:
    Get User User Language of the User.

    delete:
    Deletes the selected User Language Details of the User.

    update:
    Updates the selected User Language Details details for the given User.

    """
    queryset = UserLanguage.objects.all()
    serializer_class = UserLanguageSerializer
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name', )
    ordering_fields = ('name',)
