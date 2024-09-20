from django.db.models import Count, Q
from django.utils import timezone
from django_filters import rest_framework as filters
from rest_framework.response import Response
from rest_framework import status

from irhrs.core.mixins.viewset_mixins import ListViewSetMixin, \
    OrganizationMixin
from irhrs.core.utils.common import apply_filters
from irhrs.core.utils.common import get_today
from irhrs.event.constants import ACCEPTED, PUBLIC, PUBLIC, PRIVATE
from irhrs.event.models import Event
from irhrs.event.api.v1.serializers.event import EventSerializer
from irhrs.hris.api.v1.filters import EventFilterSet
from irhrs.hris.api.v1.serializers.birthday_and_aaniversary import \
    UpcomingBirthdaySerializer, UpcomingAnniversarySerializer
from irhrs.permission.constants.permissions import HRIS_PERMISSION, \
    HAS_PERMISSION_FROM_METHOD
from irhrs.permission.permission_classes import permission_factory
from irhrs.users.models import User
from ....utils import upcoming_birthdays, upcoming_anniversaries


class BirthdayAnniversaryMixin:
    queryset = User.objects.filter(
        is_active=True
    )

    def get_queryset(self):
        return super().get_queryset().filter(
            user_experiences__is_current=True,
        ).select_related('detail', 'detail__job_title',
                         'detail__organization', 'detail__division',
                         'detail__employment_level')

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(
            queryset
        ).filter(detail__organization=self.get_organization())
        supervisor = self.request.query_params.get('supervisor')

        if supervisor:
            if supervisor == str(self.request.user.id):
                queryset = queryset.filter(
                    id__in=self.request.user.subordinates_pks
                )
            else:
                queryset = queryset.none()

        queryset = apply_filters(
            self.request.query_params,
            {
                'branch': 'detail__branch__slug',
                'division': 'detail__division__slug'
            },
            queryset
        )
        return queryset


class UpcomingBirthdayViewSet(OrganizationMixin, BirthdayAnniversaryMixin,
                              ListViewSetMixin):
    """
    list
        filters: "branch" , "division" accepts slug
    """
    serializer_class = UpcomingBirthdaySerializer

    def filter_queryset(self, queryset):
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        queryset = upcoming_birthdays(super().filter_queryset(queryset))

        if start_date and end_date:
            try:
                queryset = queryset.filter(
                    next_birthday__lte=end_date,
                    next_birthday__gte=start_date
                )
            except TypeError:
                pass
        return queryset


class UpcomingAnniversaryViewSet(OrganizationMixin, BirthdayAnniversaryMixin,
                                 ListViewSetMixin):
    serializer_class = UpcomingAnniversarySerializer

    def filter_queryset(self, queryset):
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        queryset = upcoming_anniversaries(super().filter_queryset(queryset))

        if start_date and end_date:
            try:
                queryset = queryset.filter(
                    next_anniversary__lte=end_date,
                    next_anniversary__gte=start_date
                )
            except TypeError:
                pass
        return queryset


class UpcomingEventsViewSet(OrganizationMixin, ListViewSetMixin):
    """
    Get upcoming events stats

    filters

      role=HR
      role=supervisor

      by default normal user display will be sent
    """
    queryset = Event.objects.all()
    permission_classes = [permission_factory.build_permission(
        "UpcomingEventPermission",
        allowed_to=[HAS_PERMISSION_FROM_METHOD]
    )]
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = EventFilterSet

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params.get("for", None) == "supervisor":
            queryset = queryset.filter(
                Q(created_by_id__in=self.request.user.subordinates_pks) | Q(
                    event_members__user_id__in=self.request.user.subordinates_pks)
            )
        return queryset

    def has_user_permission(self):
        role = self.request.query_params.get("for", None)
        if role == "HR" and HRIS_PERMISSION.get("code") not in self.request.user.get_hrs_permissions(
            getattr(self, 'organization', None)
        ):
            return False
        return True

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        upcoming_events_qs =  qs.filter(
            Q(
                Q(event_type=PUBLIC) |
                Q(
                    Q(event_type=PRIVATE) &
                    Q(
                        Q(members__in=[self.request.user.id]) |
                        Q(created_by=self.request.user.id)
                    )
                )
            )
        ).order_by('start_at').distinct()
        upcoming_events = EventSerializer(
            upcoming_events_qs,
            many=True,
            fields=('id', 'title','start_at','end_at')
        ).data
        response = {
            "upcoming_events": upcoming_events,
            "stats": {
                "count": upcoming_events_qs.count()
            }
        }
        return Response(response, status=status.HTTP_200_OK)
