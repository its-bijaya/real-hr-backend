from django.db.models import Count, Sum, Avg, F, Q
from rest_framework.filters import SearchFilter
from irhrs.core.mixins.viewset_mixins import ListViewSetMixin, \
    WorkLogPermissionMixin, OrganizationMixin

from django.contrib.auth import get_user_model

from irhrs.permission.utils.base import ApplicationSettingsPermission
from irhrs.worklog.api.v1.serializers.dashboard import \
    WorkLogOverViewSerializer, WorkLogScoreDistributionOverviewSerializer
from irhrs.worklog.api.v1.views.worklog import WorkLogOrganizationMixin
from irhrs.worklog.models import WorkLog

from django.db.models import Func


class Round(Func):
    function = 'ROUND'
    template = '%(function)s(%(expressions)s, 2)'


class WorkLogOverview(WorkLogPermissionMixin, WorkLogOrganizationMixin, ListViewSetMixin):
    """
        List:

             List results and statistics for overview dashboard

        Filter backend:

             Filter backend and Order backend

             filter_fields = [start_date,end_date,as]
             ordering_fields  = [total_work_logs,total_score,average_score,efficiency]

        List Score Distribution

              follow /work-log/overview/score-distribution/

    """
    serializer_class = WorkLogOverViewSerializer
    filter_backends = [SearchFilter]
    permission_classes = [ApplicationSettingsPermission]

    search_fields = (
        'first_name',
        'middle_name',
        'last_name'
    )

    def get_queryset(self):
        organization = self.request.query_params.get('organization')
        if organization:
            _filter = dict(detail__organization__slug=organization)
        else:
            _filter = {}
        if self.request.query_params.get('as') == 'supervisor':
            _filter.update(
                {
                    'id__in': self.request.user.subordinates_pks
                }
            )
        else:
            _filter.update(
                {
                    'detail__organization':
                        self.request.user.detail.organization
                }
            )
        return get_user_model().objects.filter(
            **_filter
        ).current()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        from dateutil.parser import parse
        start_date = self.request.query_params.get('start_date', '')
        end_date = self.request.query_params.get('end_date', '')
        try:
            start_date = parse(start_date)
            end_date = parse(end_date)
        except (ValueError, OverflowError):
            start_date = None
            end_date = None
        _filters_from_user_to_work_log = Q()
        _filters_for_work_log = Q()
        if start_date and end_date:
            if start_date > end_date:
                start_date, end_date = end_date, start_date
            _filters_for_work_log = Q(date__gte=start_date, date__lte=end_date)
            _filters_from_user_to_work_log = Q(
                worklog_worklog_created__date__gte=start_date,
                worklog_worklog_created__date__lte=end_date
            )
        queryset = queryset.annotate(
            total_work_logs=Count('worklog_worklog_created',
                                  filter=_filters_from_user_to_work_log),
            total_score=Sum('worklog_worklog_created__score',
                            filter=_filters_from_user_to_work_log),
            average_score=Avg('worklog_worklog_created__score',
                              filter=_filters_from_user_to_work_log),
        ).annotate(
            efficiency=Round(((F('total_score') * 1.0) / (
                    F('total_work_logs') * 10.0)) * 100.0)
        ).order_by(F('total_score').desc(nulls_last=True))
        page = self.paginate_queryset(queryset)

        serializer = self.serializer_class(page,
                                           many=True,
                                           context=self.get_serializer_context())
        resp = self.get_paginated_response(serializer.data)

        agg_data = queryset.aggregate(
            total_work_logs=Count('worklog_worklog_created',
                                  filter=_filters_from_user_to_work_log),
            total_score=Sum('worklog_worklog_created__score',
                            filter=_filters_from_user_to_work_log),
            average_score=Round(Avg('worklog_worklog_created__score',
                                    filter=_filters_from_user_to_work_log)),
            pending_review=Count('worklog_worklog_created',
                                 filter=Q(
                                     worklog_worklog_created__score__isnull=True
                                 ) & _filters_from_user_to_work_log)
        )
        agg_data['efficiency'] = (((agg_data['total_score'] * 1.0) / (
                agg_data['total_work_logs'] * 10.0)) * 100.0) if agg_data[
            'total_score'] else 0.0

        resp.data.update(
            {'statistics': agg_data}
        )

        score_distribution_qs = WorkLog.objects.filter(
            _filters_for_work_log & Q(score__isnull=False) & Q(
                created_by__detail__organization=self.request.user.detail.organization),
        ).order_by('-modified_at')[:10]
        resp.data.update(
            {'score_distribution': WorkLogScoreDistributionOverviewSerializer(
                instance=score_distribution_qs, many=True
            ).data})

        return resp
