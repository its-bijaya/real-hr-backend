from rest_framework import filters
from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.change_request import ChangeRequestMixin
from irhrs.core.mixins.viewset_mixins import UserCommonsMixin
from irhrs.users.api.v1.serializers.contact_detail import \
    UserContactDetailSerializer
from irhrs.users.models import UserContactDetail


class UserContactDetailsViewSet(ChangeRequestMixin, ModelViewSet):
    """
    list:
    Lists User Contact Details for the selected User.

    create:
    Create new Contact Details Address for the given User.

    retrieve:
    Get User Contact Details of the User.

    delete:
    Deletes the selected User Contact Details of the User.

    update:
    Updates the selected User Contact Details details for the given User.

    """
    queryset = UserContactDetail.objects.all()
    serializer_class = UserContactDetailSerializer
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name', )
    ordering_fields = ('name',)

    def get_queryset(self):
        dependent = self.request.query_params.get('dependent')
        queryset = super().get_queryset()
        if dependent and dependent.lower() == 'true':
            queryset = queryset.filter(is_dependent=True)
        return queryset.select_related(
            'user', 'user__detail', 'user__detail__job_title', 'user__detail__employment_level',
            'user__detail__organization', 'user__detail__division'
        ).distinct()

