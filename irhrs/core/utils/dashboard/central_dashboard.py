from django.contrib.auth import get_user_model
from irhrs.core.mixins.viewset_mixins import ListViewSetMixin

USER = get_user_model()


class CentralDashboardMixin(ListViewSetMixin):
    @staticmethod
    def get_user_queryset(org):
        queryset = USER.objects.all().current()

        queryset = queryset.filter(detail__organization=org)

        return queryset
