from django.conf import settings
from django.db.models import ProtectedError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.viewset_mixins import (
    ListCreateRetrieveUpdateViewSetMixin, OrganizationCommonsMixin,
    OrganizationMixin, DisallowPatchMixin
)
from irhrs.core.utils.common import validate_permissions
from irhrs.organization.api.v1.permissions import FiscalYearPermission
from irhrs.organization.api.v1.serializers.fiscal_year import FiscalYearSerializer
from irhrs.permission.constants.permissions import (
    ORGANIZATION_PERMISSION, ORGANIZATION_SETTINGS_PERMISSION, FISCAL_YEAR_PERMISSION
)
from ....models.fiscal_year import FiscalYear, FY


class FiscalYearViewSet(DisallowPatchMixin, OrganizationCommonsMixin,
                        OrganizationMixin,
                        ModelViewSet):
    """
    create:

        Create Fiscal Year and Fiscal Month

            {
                  "months": [
                        {"month_index":1,"display_name":"January","start_at":"2012-1-1","end_at":"2012-1-31"},
                        {"month_index":2,"display_name":"february","start_at":"2012-2-1","end_at":"2012-2-29"},
                        {"month_index":3,"display_name":"march","start_at":"2012-3-1","end_at":"2012-3-31"},
                        {"month_index":4,"display_name":"april","start_at":"2012-4-1","end_at":"2012-4-30"},
                        {"month_index":5,"display_name":"may","start_at":"2012-5-1","end_at":"2012-5-31"},
                        {"month_index":6,"display_name":"june","start_at":"2012-6-1","end_at":"2012-6-30"},
                        {"month_index":7,"display_name":"july","start_at":"2012-7-1","end_at":"2012-7-31"},
                        {"month_index":8,"display_name":"august","start_at":"2012-8-1","end_at":"2012-8-31"},
                        {"month_index":9,"display_name":"september","start_at":"2012-9-1","end_at":"2012-9-30"},
                        {"month_index":10,"display_name":"october","start_at":"2012-10-1","end_at":"2012-10-31"},
                        {"month_index":11,"display_name":"november","start_at":"2012-11-1","end_at":"2012-11-30"},
                        {"month_index":12,"display_name":"december","start_at":"2012-12-1","end_at":"2012-12-31"}
                  ],
                  "name": "first fiscal",
                  "start_at": "2012-1-1",
                  "end_at": "2012-12-31",
                  "description": "My fiscal Year",
                  "applicable_from":"2012-1-1",
                  "applicable_to":"2012-12-31"
            }

    """

    queryset = FiscalYear.objects.all()
    serializer_class = FiscalYearSerializer
    permission_classes = [FiscalYearPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter,
                       OrderingFilter]
    search_fields = (
        "name",
        "description",
    )

    ordering_fields = (
        'id',
        'start_at',
        'end_at',
    )
    filter_fields = (
        'organization', 'category'
    )

    def get_serializer(self, *args, **kwargs):
        fields = ['name', 'id', 'slug', 'applicable_from', 'applicable_to', 'months']
        # if self.request and not self.request.user.is_audit_user:
        if not validate_permissions(
            self.request.user.get_hrs_permissions(
                self.get_organization()
            ),
            ORGANIZATION_PERMISSION,
            ORGANIZATION_SETTINGS_PERMISSION,
            FISCAL_YEAR_PERMISSION
        ):
            kwargs.update({
                'fields': fields
            })
        if self.request and self.request.method.lower() in ['put', 'patch']:
            kwargs.update({
                'exclude_fields': ('category',)
            })
        return super().get_serializer(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            _errors = {}
            for k, v in serializer.errors.items():
                if k == 'months':
                    _errors['months'] = []
                    for i, d in enumerate(v, 1):
                        if d:
                            _errors['months'].append({i: d})
                else:
                    _errors[k] = v

            return Response(_errors, status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers=headers)

    def list(self, request, *args, **kwargs):
        ret = super().list(request, *args, **kwargs)
        ret.data.update({
            'current_fiscal': getattr(
                FiscalYear.objects.current(
                    self.organization
                ),
                'id',
                None
            )
        })
        return ret

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.can_update_or_delete:
            raise ValidationError({
                'detail': 'You can\'t update active or previous fiscal year.'
            })

        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            raise ValidationError({
                'detail': 'Could not delete fiscal year. Perhaps it is referenced in other places '
                          'such as Rebate, Payroll Settings etc.'
            })

    # this is made for QC only . Do not use this. But also do not remove.
    # if getattr(settings, 'DEBUG'):
    #     @action(detail=False)
    #     def test(self, request, *args, **kwargs):
    #         condition = self.request.query_params.get('as')
    #         if condition not in ['month', 'year']:
    #             return Response("Condition can be only in month , year")
    #         start = self.request.query_params.get('start')
    #         end = self.request.query_params.get('end')
    #         if not (start and end):
    #             return Response("Start and end is required")
    #         _start = start.split('-')
    #         _end = end.split('-')
    #         from datetime import datetime
    #         from_date = datetime(year=int(_start[0]),month=int(_start[1]),day=int(_start[2]))
    #         to_date = datetime(year=int(_end[0]),month=int(_end[1]),day=int(_end[2]))
    #         x = FY(self.get_organization())
    #         if condition == 'month':
    #             y = x.get_months_data_from_date_range(
    #                 employee_appoint_date=from_date,
    #                 from_date=from_date,
    #                 to_date=to_date
    #             )
    #         else:
    #             y = x.get_fiscal_year_data_from_date_range(
    #                 from_date=from_date,
    #                 to_date=to_date
    #             )
    #         return Response(y)
