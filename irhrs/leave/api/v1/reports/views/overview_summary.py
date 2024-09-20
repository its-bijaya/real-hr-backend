import dateutil.parser as dateparser
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, OuterRef, Subquery, fields as dj_fields, \
    Window, F, Sum
from django.http import Http404
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from irhrs.attendance.constants import NO_LEAVE, WORKDAY
from irhrs.attendance.models import TimeSheet
from irhrs.attendance.utils.attendance import get_present_employees
from irhrs.core.mixins.serializers import create_read_only_dummy_serializer
from irhrs.core.mixins.viewset_mixins import OrganizationMixin, \
    ListViewSetMixin, ActiveMasterSettingMixin, DateRangeParserMixin, \
    SupervisorQuerysetViewSetMixin, UserMixin, \
    RetrieveViewSetMixin, PastUserParamMixin, PastUserTimeSheetFilterMixin
from irhrs.core.utils.common import get_today
from irhrs.core.utils.filters import FilterMapBackend
from irhrs.leave.api.v1.permissions import LeaveReportPermission
from irhrs.leave.api.v1.reports.serializers.overview import \
    MostLeaveActionSerializer
from irhrs.leave.api.v1.reports.views.mixins import LeaveReportPermissionMixin
from irhrs.leave.constants.model_constants import APPROVED, REQUESTED, DENIED, \
    FORWARDED
from irhrs.leave.models import LeaveType, LeaveRequest, LeaveRequestHistory
from irhrs.leave.models.request import LeaveSheet
from irhrs.leave.utils.leave_request import get_on_leave_employees
from irhrs.users.models import UserDetail

USER = get_user_model()


class LeaveOverViewSummaryMixin:
    @staticmethod
    def get_present_qs(org, filters=None):
        fil = filters or dict()
        fil.update({
            'detail__organization': org
        })
        return get_present_employees(
            filters=fil,
            date=get_today()
        ).count()

    @staticmethod
    def get_on_leave_qs(org, filters=None):
        fil = filters or dict()
        fil.update({
            'detail__organization': org
        })
        return get_on_leave_employees(
                filters=fil,
                date=get_today()
            ).count()


class LeaveOverViewSummaryViewSet(LeaveOverViewSummaryMixin,
                                  ActiveMasterSettingMixin,
                                  LeaveReportPermissionMixin,
                                  OrganizationMixin,
                                  ListViewSetMixin):

    def list(self, request, *args, **kwargs):
        organization = self.get_organization()
        today = get_today()

        # supervisor filters
        user_filter = dict()
        subordinate_id_filter = dict()
        leave_user_filter = dict()
        supervisor = self.request.query_params.get('supervisor')
        subordinate_id_filter.update({
            'detail__organization': organization,
        })
        leave_user_filter.update({
            "leave_rules__leave_requests__user__detail__organization":
                organization
        })
        user_filter.update({
            'detail__organization': organization
        })
        if supervisor:
            if supervisor == str(self.request.user.id):
                subordinate_id_filter.update({
                    'id__in': self.request.user.subordinates_pks
                })
                leave_user_filter.update({
                    'leave_rules__leave_requests__user_id__in': self.request.user.subordinates_pks
                })
                user_filter.update({
                    "id__in": self.request.user.subordinates_pks
                })

        total = USER.objects.all().current().filter(**user_filter).count()
        present = self.get_present_qs(organization, user_filter)
        on_leave = self.get_on_leave_qs(organization, user_filter)

        types = LeaveType.objects.filter(
            master_setting=self.active_master_setting
        ).annotate(
            requests=Count(
                'leave_rules__leave_requests',
                filter=Q(
                    leave_rules__leave_requests__status=APPROVED,
                    leave_rules__leave_requests__start__date__lte
                    =today,
                    leave_rules__leave_requests__end__date__gte
                    =today,
                    **leave_user_filter
                ),
                distinct=True
            )
        ).values('id', 'name', 'requests')

        return Response({
            'total': total,
            'present': present,
            'on_leave': on_leave,
            'types': types
        })


class LeaveOverViewAllLeaveReport(ActiveMasterSettingMixin,
                                  PastUserParamMixin,
                                  OrganizationMixin,
                                  LeaveReportPermissionMixin,
                                  ListViewSetMixin):
    def list(self, request, *args, **kwargs):
        org = self.get_organization()
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        supervisor_ = request.query_params.get('supervisor')
        division = request.query_params.get('division')
        branch = request.query_params.get('branch')
        user_status = self.user_type

        try:
            supervisor = int(supervisor_)
        except (TypeError, ValueError):
            supervisor = None

        today = get_today()
        a_week_ago = today - timezone.timedelta(days=7)
        start_date_parsed = None
        end_date_parsed = None

        try:
            start_date_parsed = dateparser.parse(start_date)
        except (TypeError, ValueError):
            pass
        try:
            end_date_parsed = dateparser.parse(end_date)
        except (TypeError, ValueError):
            pass

        start_date_parsed = start_date_parsed or a_week_ago
        end_date_parsed = end_date_parsed or today
        query = Q(
            leave_rules__leave_requests__user__detail__organization=org,
            leave_rules__leave_requests__status=APPROVED,
            leave_rules__leave_requests__start__date__lte=end_date_parsed,
            leave_rules__leave_requests__end__date__gte=start_date_parsed
        )
        if supervisor:
            if supervisor != self.request.user.id:
                return LeaveType.objects.none()
            else:
                query &= Q(
                    leave_rules__leave_requests__user_id__in
                    =self.request.user.subordinates_pks
                )
        if division:
            query &= Q(
                leave_rules__leave_requests__user__detail__division__slug
                =division
            )
        if branch:
            query &= Q(
                leave_rules__leave_requests__user__detail__branch__slug=branch
            )
        if user_status == 'past':
            query &= ~Q(
                leave_rules__leave_requests__user__user_experiences__is_current
                =True
            )
        else:
            query &= Q(
                leave_rules__leave_requests__user__user_experiences__is_current
                =True
            )
        return Response(
            LeaveType.objects.filter(
                master_setting=self.active_master_setting
            ).annotate(
                requests=Count(
                    'leave_rules__leave_requests',
                    filter=query,
                    distinct=True
                )
            ).values('id', 'name', 'requests')
        )


class MostLeaveActionViewSet(OrganizationMixin,
                             SupervisorQuerysetViewSetMixin,
                             LeaveReportPermissionMixin,
                             DateRangeParserMixin,
                             GenericViewSet):
    """
    Most leaves by action
    """
    serializer_class = MostLeaveActionSerializer
    queryset = USER.objects.all()

    action_to_status = {"pending": [REQUESTED, FORWARDED], "denied": [DENIED]}

    def filter_queryset(self, queryset):
        status = self.action_to_status.get(self.action)

        if not status:
            raise Http404

        requests = LeaveRequest.objects.filter(
            recipient=OuterRef('pk'),
            status__in=status,
            user__detail__organization=self.get_organization()
        )

        if self.action == 'denied':
            start_date, end_date = self.get_parsed_dates()
            requests = requests.annotate(
                denied_date=Subquery(LeaveRequestHistory.objects.filter(
                    request=OuterRef('pk'),
                    action=DENIED
                ).values(
                    'created_at'
                )[:1])
            ).exclude(denied_date__isnull=True).filter(
                denied_date__date__gte=start_date,
                denied_date__date__lte=end_date
            )

        requests_count = requests.annotate(
            requests_count=Window(
                expression=Count('pk'),
                partition_by=[F('recipient')]
            ),
        ).values('requests_count')[:1]

        return queryset.annotate(
            count=Subquery(
                requests_count,
                output_field=dj_fields.IntegerField(default=0)
            )
        ).filter(count__isnull=False).order_by('-count')

    def list(self, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(methods=["GET"], detail=False)
    def pending(self, *args, **kwargs):
        """Supervisor with most pending leave requests"""
        return self.list(*args, *kwargs)

    @action(methods=["GET"], detail=False)
    def denied(self, *args, **kwargs):
        """Supervisor with most denied leave requests, date range filter can be applied (start_date, end_date)"""
        return self.list(*args, *kwargs)


class NormalUserLeaveOverviewViewSet(OrganizationMixin,
                                     PastUserTimeSheetFilterMixin,
                                     UserMixin,
                                     RetrieveViewSetMixin):
    """
    Normal User Leave Overview views

    detail:

    summary of user's days (present, on_leave, work_days)

    leave_history:

    leave history of user

    filters
    -------
        start_date,
        end_date
    """
    queryset = TimeSheet.objects.all()
    lookup_url_kwarg = 'user_id'
    permission_classes = [LeaveReportPermission]
    filter_backends = [FilterMapBackend]
    filter_map = {
        "start_date": "timesheet_for__gte",
        "end_date": "timesheet_for__lte"
    }

    serializer_class = create_read_only_dummy_serializer(fields=['leave_days', 'present_days', 'working_days'])

    def get_queryset(self):
        if self.action == 'leave_history':
            return LeaveSheet.objects.filter(
                request__user__detail__organization=self.get_organization(),
                request__user=self.user,
                request__status=APPROVED
            )
        return super().get_queryset().filter(
            timesheet_user__detail__organization=self.get_organization(),
            timesheet_user=self.user
        )

    def has_user_permission(self):
        return self.user == self.request.user

    @staticmethod
    def get_summary(queryset):
        return queryset.aggregate(
            leave_days=Count('id', filter=~Q(leave_coefficient=NO_LEAVE)),
            present_days=Count('id', filter=Q(is_present=True)),
            working_days=Count('id', filter=Q(coefficient=WORKDAY)),
        )

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        return self.get_summary(queryset)

    @action(detail=True,
            methods=['GET'],
            url_path='leave-history',
            serializer_class=create_read_only_dummy_serializer(fields=["leave_type", "total_consumed", "category"]),
            filter_map={
                "start_date": "leave_for__gte",
                "end_date": "leave_for__lte"
            })
    def leave_history(self, request, **kwargs):
        """
        Units are minutes if category=='Time Off' else units are days

        filters --> `start_date`, `end_date`

        `ordering=-total_consumed` or `ordering=total_consumed`
        """
        qs = self.filter_queryset(self.get_queryset()).filter(
            request__is_archived=False,
            request__is_deleted=False
        ).order_by('request__leave_rule__leave_type__name').values(
            'request__leave_rule__leave_type__name'
        ).annotate(
            total_consumed=Sum('balance')
        ).annotate(
            leave_type=F('request__leave_rule__leave_type__name'),
            category=F('request__leave_rule__leave_type__category')
        )

        ordering = self.request.query_params.get('ordering')
        if ordering in ['total_consumed', '-total_consumed']:
            qs = qs.order_by(ordering)

        return self.get_paginated_response(
            self.get_serializer(
                self.paginate_queryset(qs),
                many=True
            ).data
        )
