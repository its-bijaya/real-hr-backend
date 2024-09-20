from django.contrib.auth import get_user_model
from django.db.models import Prefetch, Case, When, Value, F
from django.http import Http404
from django.utils.functional import cached_property
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from irhrs.attendance.api.v1.serializers.shift_roster import TimeSheetRosterCreateSerializer, \
    TimeSheetRosterListSerializer, TimeSheetRosterBulkCreateSerializer
from irhrs.attendance.models import IndividualUserShift, IndividualAttendanceSetting
from irhrs.attendance.models.shift_roster import TimeSheetRoster
from irhrs.core.mixins.serializers import DummySerializer
from irhrs.core.mixins.viewset_mixins import ListCreateViewSetMixin, OrganizationMixin
from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.subordinates import find_immediate_subordinates, find_all_subordinates
from irhrs.core.utils.filters import OrderingFilterMap, FilterMapBackend
from irhrs.organization.models import FiscalYearMonth
from irhrs.permission.constants.permissions import ATTENDANCE_TIMESHEET_ROSTER_PERMISSION

USER = get_user_model()


# class IncludeExcludeUserHelper(DummySerializer):
#     # immediate_subordinates = serializers.BooleanField(write_only=True)
#     include = serializers.PrimaryKeyRelatedField(
#         write_only=True,
#         allow_null=True,
#         required=False,
#         allow_empty=True,
#         many=True,
#         queryset=USER.objects.all()
#     )
#     exclude = serializers.PrimaryKeyRelatedField(
#         write_only=True,
#         allow_null=True,
#         required=False,
#         allow_empty=True,
#         many=True,
#         queryset=USER.objects.all()
#     )


class TimeSheetRosterView(OrganizationMixin, ListCreateViewSetMixin):
    filter_backends = (
        SearchFilter, OrderingFilterMap, FilterMapBackend
    )
    search_fields = ('first_name', 'middle_name', 'last_name', 'username')
    ordering_fields_map = {
        "full_name": (
            "first_name",
            "middle_name",
            "last_name",
        ),
        "username": "username"
    }
    filter_map = {
        'branch': 'detail__branch__slug',
        'division': 'detail__division__slug',
        'employment_level': 'detail__employment_level__slug'
    }

    def get_serializer_class(self):
        if self.action == 'list':
            return TimeSheetRosterListSerializer
        # if self.action == 'populate':
        #     return IncludeExcludeUserHelper
        return TimeSheetRosterBulkCreateSerializer

    def get_queryset(self):
        user_filter = self.user_filter
        if not self.fiscal_month:
            raise Http404
        qs = USER.objects.filter(
            **user_filter
        ).prefetch_related(
            Prefetch(
                'timesheet_rosters',
                TimeSheetRoster.objects.filter(
                    date__range=(self.fiscal_month.start_at, self.fiscal_month.end_at)
                ).select_related(
                    'shift',
                    'shift__work_shift_legend'
                ),
                to_attr='_roster_qs'
            ),
            Prefetch(
                'attendance_setting',
                IndividualAttendanceSetting.objects.filter(
                ).prefetch_related(
                    Prefetch(
                        'individual_setting_shift',
                        IndividualUserShift.objects.filter().annotate(
                            _end_date=Case(
                                When(
                                    applicable_to__isnull=True,
                                    then=Value(self.fiscal_month.end_at)
                                ),
                                default=F('applicable_to')
                            )
                        ).filter(
                            _end_date__range=(self.fiscal_month.start_at, self.fiscal_month.end_at)
                        ).select_related(
                            'shift',
                            'shift__work_shift_legend'
                        ),
                        to_attr="_shift"
                    )
                ),
                to_attr='_attendance_setting'
            )
        ).select_related(
            'detail',
            'detail__job_title'
        ).current()
        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['organization'] = self.get_organization()
        ctx['fiscal_month'] = self.fiscal_month
        ctx['subordinate_ids'] = self.subordinate_ids
        ctx['user_filter'] = self.user_filter
        return ctx

    @cached_property
    def user_filter(self):
        selected_employees = self.request.query_params.get('selected_employees', '')
        user_filter = {
            'detail__organization': self.get_organization(),
        }
        user_id = self.request.user.id
        if self.mode == 'hr':
            # move the organization filter to be generic.
            if not validate_permissions(
                self.request.user.get_hrs_permissions(
                    self.get_organization()
                ),
                ATTENDANCE_TIMESHEET_ROSTER_PERMISSION
            ):
                raise self.permission_denied(self.request)
        elif self.mode == 'supervisor':
            immediate_subordinates = self.request.query_params.get('immediate_subordinates')
            subordinates_id = find_immediate_subordinates(user_id)
            if immediate_subordinates != 'true':
                subordinates_id = find_all_subordinates(user_id)
            user_filter.update({
                'id__in': subordinates_id
            })
        else:
            user_filter.update({'id': user_id})
        if selected_employees:
            user_filter.update({'id__in': selected_employees.split(',')})
        return user_filter

    @cached_property
    def fiscal_month(self):
        return FiscalYearMonth.objects.filter(
                fiscal_year__organization=self.get_organization(),
                id=self.request.query_params.get('fiscal_month')
            ).first()

    @cached_property
    def subordinate_ids(self):
        return set(self.request.user.as_supervisor.filter(
            # authority_order=1
        ).values_list('user', flat=True))

    @cached_property
    def mode(self):
        return {
            'hr': 'hr',
            'supervisor': 'supervisor'
        }.get(self.request.query_params.get('as'), 'user')

    # @action(detail=False, methods=['POST'])
    # def populate(self, *args, **kwargs):
    #     """
    #     Take include and exclude list and populate details for the month.
    #     """
    #     return Response({
    #         'detail': 'TimeSheet Roster is being created.'
    #     })
