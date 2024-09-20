from django.contrib.auth import get_user_model
from rest_framework.filters import OrderingFilter

from irhrs.common.api.serializers.user_activity import UserActivitySerializer
from irhrs.common.models.user_activity import UserActivity
from irhrs.core.mixins.viewset_mixins import ListViewSetMixin
from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.filters import FilterMapBackend
from irhrs.permission.constants.permissions import HRIS_PERMISSION

USER = get_user_model()


class UserActivityViewSet(ListViewSetMixin):
    serializer_class = UserActivitySerializer
    filter_backends = [FilterMapBackend, OrderingFilter]
    filter_map = {
        'category': 'category',
        'actor': 'actor',
        'organization': 'actor__detail__organization__slug'
    }
    ordering = '-id'

    def get_queryset(self):
        queryset = UserActivity.objects.select_related('actor', 'actor__detail',
                                                       'actor__detail__job_title',
                                                       'actor__detail__organization',
                                                       'actor__detail__division',
                                                       'actor__detail__employment_level')
        supervisor = self.request.query_params.get('supervisor')
        organization = self.request.query_params.get('organization')

        fil = dict()

        if organization:
            fil.update({
                'actor__detail__organization__slug': organization
            })

        if supervisor:
            if supervisor == str(self.request.user.id):
                fil.update({
                    'actor_id__in': self.request.user.subordinates_pks
                })
            else:
                return queryset.none()

        elif not validate_permissions(
                self.request.user.get_hrs_permissions(),
                HRIS_PERMISSION
        ):
            fil.update(actor_id=self.request.user.id)
        return queryset.filter(**fil)
