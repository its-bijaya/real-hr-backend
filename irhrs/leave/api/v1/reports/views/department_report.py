from django.db.models import Count, F, Window, Sum, OuterRef, Subquery, fields as dj_fields, Q
from django.db.models.functions import Coalesce
from rest_framework.fields import ReadOnlyField, SerializerMethodField
from rest_framework.generics import get_object_or_404

from irhrs.core.constants.common import OTHER
from irhrs.core.constants.user import MALE, FEMALE
from irhrs.core.mixins.serializers import DummySerializer
from irhrs.core.mixins.viewset_mixins import OrganizationMixin, \
    ListRetrieveViewSetMixin, DateRangeParserMixin, ListViewSetMixin
from irhrs.core.utils.common import get_applicable_filters, apply_filters
from irhrs.core.utils.filters import FilterMapBackend
from irhrs.leave.api.v1.permissions import LeavePermission, AdminOnlyLeaveReportPermission
from irhrs.leave.api.v1.reports.views.mixins import LeaveReportPermissionMixin
from irhrs.leave.constants.model_constants import APPROVED
from irhrs.leave.models import LeaveRequest
from irhrs.leave.models.request import LeaveSheet
from irhrs.organization.api.v1.serializers.division import OrganizationDivisionSerializer
from irhrs.organization.models import OrganizationDivision


class LeaveDepartmentReport(
    DateRangeParserMixin,
    OrganizationMixin,
    LeaveReportPermissionMixin,
    ListRetrieveViewSetMixin
):
    serializer_class = type(
        "LeaveDepartmentReportSerializer",
        (DummySerializer,),
        {
            "division": ReadOnlyField(),
            "leaves": ReadOnlyField(source="count_leaves"),
            "slug": ReadOnlyField()
        }
    )
    lookup_url_kwarg = 'division_slug'
    filter_backends = (
        FilterMapBackend,
    )
    filter_map = {
        'branch': 'user__detail__branch__slug',
        'division': 'user__detail__division__slug',
        'employee_level': 'user__detail__employment_level__slug'
    }

    def get_queryset(self):
        organization = self.get_organization()

        supervisor_id = self.request.query_params.get('supervisor')
        fil = dict(
            user__detail__organization=organization
        )

        if supervisor_id:
            if supervisor_id == str(self.request.user.id):
                fil.update({
                    'leave_account__user_id__in':
                        self.request.user.subordinates_pks
                })
            else:
                # if supervisor does not match return none
                return LeaveRequest.objects.none()

        start_date_parsed, end_date_parsed = self.get_parsed_dates()
        return LeaveRequest.objects.filter(
            start__date__lte=end_date_parsed,
            end__date__gte=start_date_parsed,
            user__user_experiences__is_current=True,
            status=APPROVED,
            **fil
        )

    def filter_queryset(self, queryset):
        return queryset.order_by().values(
            'user__detail__division__name',
            'user__detail__division__slug'
        ).annotate(
            num_leaves=Count('id', distinct=True),
            count_leaves=Coalesce(Sum(Coalesce('balance', 0.0)), 0.0),
            division=F('user__detail__division__name'),
            slug=F('user__detail__division__slug')
        )

    def retrieve(self, request, *args, **kwargs):
        division = self.get_object()

        queryset = self.get_queryset().filter(
            user__detail__division=division
        )

        annotated_queryset = queryset.order_by().values(
            'leave_rule__leave_type__name',
            'leave_rule__leave_type',
        ).annotate(
            requests=Count('id')
        )

        serializer = type(
            "SerializerHere",
            (DummySerializer,),
            {
                "leave_type": ReadOnlyField(
                    source='leave_rule__leave_type__name'),
                "type_id": ReadOnlyField(
                    source='leave_rule__leave_type'
                ),
                'requests': ReadOnlyField()
            }
        )

        data = serializer(
            self.paginate_queryset(
                annotated_queryset
            ),
            many=True).data
        response = self.get_paginated_response(data)

        response.data.update({
            "male": queryset.filter(user__detail__gender=MALE).count(),
            "female": queryset.filter(user__detail__gender=FEMALE).count(),
            "other": queryset.filter(user__detail__gender=OTHER).count()
        })
        return response

    def get_object(self):
        division_slug = self.kwargs.get('division_slug')
        return get_object_or_404(
            OrganizationDivision.objects.filter(
                slug=division_slug,
                organization=self.get_organization()
            )
        )


class DivisionAverageLeaveReport(
    DateRangeParserMixin,
    OrganizationMixin,
    ListViewSetMixin
):
    permission_classes = [AdminOnlyLeaveReportPermission]

    serializer_class = type(
        "DivisionAverageReportSerializer",
        (DummySerializer,),
        {
            "division": SerializerMethodField(),
            "avg_leave": ReadOnlyField(),
            "leave_balance": ReadOnlyField(),
            "user_count": ReadOnlyField(),
            "get_division": lambda _, obj: OrganizationDivisionSerializer(obj, fields=["name", "slug"]).data
        }
    )

    def get_queryset(self):
        return OrganizationDivision.objects.filter(organization=self.get_organization(), is_archived=False)

    def filter_queryset(self, queryset):
        return super().filter_queryset(self.annotate_queryset(queryset))

    def annotate_queryset(self, queryset):
        date_range = self.get_parsed_dates()

        leave_balance = LeaveSheet.objects.filter(request__leave_account__user__detail__division=OuterRef('pk')).filter(
            request__status=APPROVED,
            request__is_deleted=False,
            leave_for__range=date_range
        ).annotate(
            cost=Window(
                expression=Sum('balance'),
                partition_by=[F('request__leave_account__user__detail__division')]
            ),
        ).values('cost')[:1]

        return queryset.annotate(
            leave_balance=Coalesce(Subquery(
                leave_balance,
                output_field=dj_fields.FloatField()
            ), 0.0),
            user_count=Coalesce(
                Count(
                    'user_experiences', filter=Q(user_experiences__is_current=True),
                    output_field=dj_fields.FloatField()
                ), 0.0
            )
        ).filter(user_count__gt=0.0).annotate(avg_leave=F('leave_balance')/F('user_count')).order_by('-avg_leave')
