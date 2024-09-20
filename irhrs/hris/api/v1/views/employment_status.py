from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.response import Response

from irhrs.core.constants.user import MALE, FEMALE, OTHER
from irhrs.core.mixins.viewset_mixins import ListViewSetMixin, OrganizationMixin
from irhrs.core.utils.common import get_today
from irhrs.core.utils.filters import FilterMapBackend
from irhrs.hris.api.v1.permissions import HRISPermission, HRISReportPermission, \
    HRISReportPermissionMixin
from irhrs.hris.api.v1.serializers.employment_status import \
    EmploymentStatusOverviewSerializer
from irhrs.organization.models import EmploymentStatus
from irhrs.users.models import UserExperience


class EmploymentStatusOverviewViewSet(OrganizationMixin,
                                      HRISReportPermissionMixin,
                                      ListViewSetMixin):
    """
    list:

    filters `is_archived`

    date range filters `start_date`, `end_date` will filter according to the
    joined date of user
    """

    queryset = UserExperience.objects.filter(is_current=True)
    serializer_class = EmploymentStatusOverviewSerializer
    filter_backends = (FilterMapBackend, )

    filter_map = {
        'division': 'division__slug',
        'employment_status': 'employment_status__slug',
        'employment_level': 'employee_level__slug',
        'branch': 'branch__slug',
        'date_of_join': 'user__detail__joined_date',
        'joined_after': 'user__detail__joined_date__gte',
        'gender': 'user__detail__gender',
        'code': 'user__detail__code'
    }

    def get_queryset(self):
        supervisor_id = self.request.query_params.get('supervisor')
        fil = dict()

        if supervisor_id:
            if supervisor_id == str(self.request.user.id):
                fil.update({
                    'user_id__in':
                        self.request.user.subordinates_pks
                })
            else:
                # if supervisor does not match return none
                return super().get_queryset().none()
        else:
            # only use organization filter if supervisor is not passed in
            # query params, else filter by subordinates
            fil.update({'organization': self.get_organization()})

        return super().get_queryset().filter(**fil).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=get_today())
        )

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date',
                                                 timezone.now().date())

        if start_date:
            try:
                queryset = queryset.filter(
                    user__detail__joined_date__gte=start_date,
                    user__detail__joined_date__lte=end_date
                )
            except (TypeError, ValidationError):
                pass
        return queryset

    def list(self, request, *args, **kwargs):
        annotates = [('male', MALE), ('female', FEMALE), ('other', OTHER)]

        is_archived = request.query_params.get('is_archived')
        es_filter = {}
        if is_archived in ['true', 'false']:
            es_filter.update({'is_archived': is_archived == 'true'})

        queryset = self.filter_queryset(self.get_queryset())
        annotate = {name: Count(
            'id',
            filter=Q(user__detail__gender=value,
                     is_current=True),
            distinct=True
        ) for name, value in annotates}
        employment_statuses = EmploymentStatus.objects.filter(
            organization=self.get_organization(),
            **es_filter
        )
        result = list()
        for employment_status in employment_statuses:
            data = {
                "title": employment_status.title,
                "slug": employment_status.slug,
                "count": queryset.filter(
                    employment_status=employment_status
                ).count()
            }
            data.update(queryset.filter(employment_status=employment_status).aggregate(
                **annotate
            ))
            result.append(data)
        return Response({"results": result})
