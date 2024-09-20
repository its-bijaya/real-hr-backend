from django.contrib.auth import get_user_model
from django.db.models import Sum, OuterRef, Exists, Window, F, Subquery, \
    fields as dj_fields, FloatField, Case, When
from django.db.models.functions import Coalesce
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response

from irhrs.core.mixins.viewset_mixins import ListViewSetMixin, \
    OrganizationMixin, DateRangeParserMixin, PastUserFilterMixin
from irhrs.core.utils.filters import FilterMapBackend, \
    NullsAlwaysLastOrderingFilter
from irhrs.leave.api.v1.reports.serializers.leave_irregularities import \
    IndividualLeaveIrregularitiesSerializer, \
    MostLeavesReportSerializer, LeaveIrregularitiesOverviewSerializer
from irhrs.leave.api.v1.reports.views.mixins import LeaveReportPermissionMixin
from irhrs.leave.constants.model_constants import APPROVED, HOURLY_LEAVE_CATEGORIES
from irhrs.leave.models import LeaveAccount, LeaveType, LeaveRule, MasterSetting
from irhrs.leave.models.request import LeaveSheet
from irhrs.leave.tasks import get_active_master_setting

USER = get_user_model()


def leave_requests__status(args):
    pass


class LeaveIrregularitiesViewSet(
    OrganizationMixin, PastUserFilterMixin, DateRangeParserMixin,
    LeaveReportPermissionMixin, ListViewSetMixin
):
    """

    """
    queryset = USER.objects.all()
    serializer_class = IndividualLeaveIrregularitiesSerializer
    filter_backends = (
        FilterMapBackend,
        SearchFilter,
        NullsAlwaysLastOrderingFilter
    )
    filter_map = {
        'branch': 'detail__branch__slug',
        'division': 'detail__division__slug',
        'employee_level': 'detail__employment_level__slug',
        'user': 'id'
    }
    search_fields = (
        'first_name', 'middle_name', 'last_name'
    )
    ordering_fields_map = {
        'full_name': (
            'first_name', 'middle_name', 'last_name'
        ),
        'num_leaves': 'num_leaves'
    }

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        st, ed = self.get_parsed_dates()
        ctx.update({
            'active_setting': get_active_master_setting(
                self.get_organization()
            ),
            'start_period': st,
            'end_period': ed,
            'lim_type': self.periodic_limit_type
        })
        return ctx

    def get_queryset(self):

        supervisor_id = self.request.query_params.get('supervisor')
        fil = dict(
            detail__organization=self.organization
        )

        if supervisor_id:
            if supervisor_id == str(self.request.user.id):
                fil.update({
                    'id__in':
                        self.request.user.subordinates_pks
                })
            else:
                # if supervisor does not match return none
                return super().get_queryset().none()
        return super().get_queryset().filter(
            **fil
        ).select_related(
            'detail',
            'detail__organization',
            'detail__division',
            'detail__job_title',
            'detail__employment_level'
        ).distinct()

    def get_master_settings_filter(self, key):
        supervisor_id = self.request.query_params.get('supervisor')
        if supervisor_id:
            return {f"{key}__in": MasterSetting.objects.all().active()}
        else:
            return {key: get_active_master_setting(self.get_organization())}

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        leave_account_filter = {
            'user_id': OuterRef('id'),
            'is_archived': False
        }

        has_leave_account = LeaveAccount.objects.filter(**leave_account_filter)

        queryset = queryset.annotate(
            has_leave_account=Exists(has_leave_account)
        ).filter(
            has_leave_account=True,
        )
        start_date, end_date = self.get_parsed_dates()

        if self.action == 'get_most_leaves_overview':

            balance = LeaveSheet.objects.filter(
                request__leave_account__user=OuterRef('pk'),
                # request__leave_account__is_archived=False,
                request__is_archived=False,
                request__is_deleted=False
            ).exclude(
                request__leave_rule__leave_type__category__in=HOURLY_LEAVE_CATEGORIES
            ).filter(
                request__status=APPROVED,
                leave_for__range=[start_date, end_date]
            ).annotate(
                count=Window(
                    expression=Sum('balance'),
                    partition_by=[F('request__leave_account__user')],
                ),
            ).values('count')[:1]

            queryset = queryset.annotate(
                num_leaves=Coalesce(
                    Subquery(
                        balance,
                        output_field=dj_fields.FloatField(default=0.0)
                    ), 0.0)
            )
        else:
            irregulars = LeaveRule.objects.filter(
                irregularity_report=True,
                leave_irregularity__isnull=False,
                **self.get_master_settings_filter('leave_type__master_setting')
            )
            balance = LeaveSheet.objects.filter(
                request__leave_account_id=OuterRef('pk'),
                request__status=APPROVED,
                request__is_deleted=False,
                leave_for__range=[start_date, end_date]
            ).annotate(
                count=Window(
                    expression=Sum('balance'),
                    partition_by=[F('request__leave_account')],
                ),
            ).values('count')[:1]

            lim_type = self.periodic_limit_type
            accounts = LeaveAccount.objects.filter(
                rule__in=irregulars
            ).filter(
                id=OuterRef('leave_accounts')
            ).annotate(
                val=Subquery(balance, output_field=FloatField(default=0)),
                limit=F(f'rule__leave_irregularity__{lim_type}')
            )[:1]

            limits = queryset.annotate(
                consumed=Subquery(accounts.values('val'),
                                  output_field=FloatField()),
                limit=Subquery(accounts.values('limit'),
                               output_field=FloatField())
            ).annotate(
                lim_exceeded=F('consumed') - F('limit')
            ).order_by().values('id').annotate(
                total=Sum(
                    Case(
                        When(lim_exceeded__gt=0, then=F('lim_exceeded')),
                        default=0,
                        output_field=FloatField()
                    )
                )
            )
            queryset = queryset.filter(
                leave_accounts__rule__in=irregulars
            ).annotate(
                num_leaves=Subquery(
                    limits.filter(id=OuterRef('pk')).values('total')[:1],
                    output_field=FloatField()
                )
            )

        return queryset.distinct()

    @property
    def periodic_limit_type(self):
        allowed_limits = {
            'weekly': 'weekly_limit',
            'fortnightly': 'fortnightly_limit',
            'monthly': 'monthly_limit',
            'quarterly': 'quarterly_limit',
            'semi_annually': 'semi_annually_limit',
            'annually': 'annually_limit',
        }
        periodic_limit = allowed_limits.get(
            self.request.query_params.get('periodic')
        ) if self.request.query_params.get('periodic') in allowed_limits.keys(
        ) else 'monthly_limit'
        return periodic_limit

    def list(self, request, *args, **kwargs):
        ret = super().list(request, *args, **kwargs)

        # List of Leave Types with Irregularity Only
        irregularity_leave_rule = LeaveRule.objects.filter(
            leave_type=OuterRef('pk'),
            irregularity_report=True,
            leave_irregularity__isnull=False
        )
        qs = LeaveType.objects.filter(
            master_setting=get_active_master_setting(
                self.get_organization()
            )
        ).annotate(
            has_irregularity=Exists(irregularity_leave_rule)
        ).filter(
            has_irregularity=True
        ).values(
            'id', 'name'
        ).order_by('name')

        ret.data.update({
            'applicable_leaves': qs
        })
        return ret

    @action(methods=['get'], detail=False, url_name='irregularity-overview',
            url_path='irregularity-overview')
    def get_irregularity_overview(self, *args, **kwargs):
        """
        :return: top 5 irregularity
        """
        qs = self.filter_queryset(
            self.get_queryset()
        ).filter(
            num_leaves__gt=0.0
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = LeaveIrregularitiesOverviewSerializer(
                page, many=True,
                context=self.get_serializer_context()
            )
            resp = self.get_paginated_response(serializer.data)
            return resp
        return Response()

    @action(methods=['get'], detail=False, url_name='most-leaves',
            url_path='most-leaves')
    def get_most_leaves_overview(self, *args, **kwargs):
        """
        :return: top 5 irregularity
        pass ordering=result or ordering=-result
        """
        order_by = self.request.query_params.get("ordering", "result")

        qs = self.filter_queryset(
            self.get_queryset()
        ).order_by('num_leaves' if order_by != "result" else "-num_leaves")

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = MostLeavesReportSerializer(
                page, many=True,
                context=self.get_serializer_context()
            )
            resp = self.get_paginated_response(serializer.data)
            return resp
        return Response()
