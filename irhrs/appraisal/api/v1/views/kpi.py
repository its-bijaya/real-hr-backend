from itertools import groupby
from operator import itemgetter

from django.db import transaction
from django.db.models import F, Case, When, Value, Q
from django.db.models.functions import Concat
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from irhrs.appraisal.api.v1.permissions import \
    AssignKPIPermission, KPIPermission
from irhrs.appraisal.api.v1.serializers.kpi import KPISerializer, ExtendedIndividualKPISerializer, \
    IndividualKPISerializer, IndividualKPICollectionSerializer
from irhrs.appraisal.models.kpi import KPI, IndividualKPI, ExtendedIndividualKPI
from irhrs.appraisal.utils.kpi import send_notification_and_create_history
from irhrs.core.mixins.viewset_mixins import OrganizationMixin, OrganizationCommonsMixin, \
    GetStatisticsMixin
from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.core.utils.subordinates import find_immediate_subordinates
from irhrs.export.mixins.export import BackgroundExcelExportMixin
from irhrs.notification.utils import add_notification
from irhrs.permission.constants.permissions import INDIVIDUAL_KPI_PERMISSION, KPI_PERMISSION
from irhrs.users.api.v1.serializers.thin_serializers import UserThickSerializer
from irhrs.users.models import User, UserDetail


class KPIViewSet(OrganizationMixin, OrganizationCommonsMixin, ModelViewSet):
    queryset = KPI.objects.all().select_related('organization')
    serializer_class = KPISerializer
    permission_classes = [KPIPermission]
    filter_backends = [DjangoFilterBackend, FilterMapBackend, SearchFilter, OrderingFilter]
    filter_map = {
        'job_title': 'job_title__slug',
        'division': 'division__slug',
        'employment_level': 'employment_level__slug'
    }
    search_fields = ('title',)


def get_success_criteria(kpi: IndividualKPI):
    # this function can be useful for export of kpi success criteria
    # add 'Success Criteria': 'get_success_criteria' in export fields in KPIBackgroundMixin
    success_criteria = ""
    for index, data in enumerate(list(kpi.extended_individual_kpis.values_list('success_criteria', flat=True)), 1):
        text = f'\n{index}. ' + data if index > 1 else f'{index}. ' + data
        success_criteria += text
    return success_criteria


class KPIBackgroundExportMixin(BackgroundExcelExportMixin):
    export_type = 'Key performance Indicator'
    export_fields = {
        'S.N': '#SN',
        'Full name': 'user.full_name',
        'Username': 'user.username',
        'Fiscal Year': 'fiscal_year',
        'Title': 'title',
        'Status': 'status',
    }

    def get_notification_permissions(self):
        if self.mode == 'hr':
            return [KPI_PERMISSION]

    def get_frontend_redirect_url(self):
        if self.mode == 'supervisor':
            return '/user/supervisor/kpi/assign-kpi'


class IndividualKPIViewSet(OrganizationMixin, GetStatisticsMixin,
                           KPIBackgroundExportMixin, ModelViewSet):
    queryset = IndividualKPI.objects.all()
    serializer_class = IndividualKPISerializer
    filter_backends = [DjangoFilterBackend, FilterMapBackend, SearchFilter, OrderingFilterMap]
    filter_map = {
        'job_title': 'user__detail__job_title__slug',
        'division': 'user__detail__division__slug',
        'employment_level': 'user__detail__employment_level__slug',
        'fiscal_year': 'fiscal_year',
        'status': 'status',
        'username': 'user__username'
    }
    search_fields = ('user__first_name', 'user__middle_name', 'user__last_name')
    ordering_fields_map = {
        'name': ('user__first_name', 'user__middle_name', 'user__last_name'),
        'username': 'user__username',
    }
    statistics_field = 'status'

    @property
    def mode(self):
        mode = self.request.query_params.get('as', 'user')
        if mode not in ['supervisor', 'hr']:
            self.search_fields = ('title',)
            self.ordering_fields_map = {'title': 'title'}
            return 'user'
        if mode == 'hr':
            if not validate_permissions(
                self.user.get_hrs_permissions(self.get_organization()),
                INDIVIDUAL_KPI_PERMISSION
            ):
                raise PermissionDenied
        return mode

    @property
    def user(self):
        return self.request.user

    def perform_destroy(self, instance):
        add_notification(
            text=f"KPI {instance.title} is deleted by {self.user}.",
            recipient=instance.user,
            action=instance,
            actor=self.user,
            url='/user/pa/kpi'
        )
        super().perform_destroy(instance)

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            user__detail__organization=self.get_organization())
        if self.mode == 'supervisor':
            immediate_subordinates = find_immediate_subordinates(self.user.id)
            return queryset.filter(user_id__in=immediate_subordinates)
        elif self.mode == 'user':
            return queryset.filter(user=self.request.user)
        return queryset

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['mode'] = self.mode
        ctx['organization'] = self.get_organization()
        return ctx

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data.update({'counts': self.statistics})
        return response

    @action(
        methods=['POST'],
        detail=False,
        url_path='bulk-create'
    )
    def bulk_create(self, *args, **kwargs):
        ser = IndividualKPICollectionSerializer(
            data=self.request.data,
            context={'user': self.user, 'mode': self.mode, 'organization': self.organization}
        )
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response("Kpi assigned successfully", 201)

    @transaction.atomic
    @action(
        methods=['POST'],
        detail=False,
        url_path='bulk-assign'
    )
    def bulk_assign(self, *args, **kwargs):
        selected_user_ids = self.request.data.pop('users')
        data = self.request.data
        validated_serializers = []
        for user_id in selected_user_ids:
            data['individual_kpi']['user'] = user_id
            ser = IndividualKPICollectionSerializer(
                data=data,
                context={'user': self.user, 'mode': self.mode, 'organization': self.organization}
            )
            ser.is_valid(raise_exception=True)
            validated_serializers.append(ser)

        for ser in validated_serializers:
            ser.save()
        return Response("Kpi assigned successfully", 201)

    @transaction.atomic
    @action(
        methods=['PUT'],
        detail=True,
        url_path='bulk-update'
    )
    def bulk_update(self, *args, **kwargs):
        individual_kpi = self.request.data.get('individual_kpi', {})
        extended_kpis = self.request.data.get('extended_kpi', {})
        instance = self.get_object()
        ser = IndividualKPISerializer(
            instance,
            data=individual_kpi,
            context=self.get_serializer_context()
        )
        ser.is_valid(raise_exception=True)
        individual_kpi_instance = ser.save()
        extended_kpis_ids = []
        bulk_update = []
        for data in extended_kpis:
            extended_kpi_id = data.get('extended_kpi_id')
            if not extended_kpi_id:
                serializer = ExtendedIndividualKPISerializer(data=data)
            else:
                extended_kpis_ids.append(extended_kpi_id)
                obj = instance.extended_individual_kpis.filter(id=extended_kpi_id).first()
                serializer = ExtendedIndividualKPISerializer(obj, data=data)
            serializer.is_valid(raise_exception=True)
            bulk_update.append(serializer)
        total_weightage = sum([int(x['weightage']) for x in extended_kpis])
        instance.extended_individual_kpis.exclude(id__in=extended_kpis_ids).delete()
        if total_weightage != 100:
            raise ValidationError({"error": "Total weightage must be 100%."})
        for ser in bulk_update:
            ser.save()
        return Response("Individual KPI updated successfully.")

    @action(
        methods=['POST'],
        detail=True,
        url_path='bulk-delete'
    )
    def bulk_delete(self, *args, **kwargs):
        instance = self.get_object()
        extended_kpi_ids = self.request.data.get('extended_kpi_ids')
        instance.extended_individual_kpis.filter(id__in=extended_kpi_ids).delete()
        remarks = f"{len(extended_kpi_ids)} individual kpi removed by {self.user}."
        send_notification_and_create_history(instance, '/user/pa/kpi', remarks, self.user)
        return Response('Successfully deleted unchecked individualKPI.')

    @action(
        methods=['GET'],
        detail=False,
        url_path='get-employee'
    )
    def get_employee(self, *args, **kwargs):
        filter_mapper = {
            'division': 'detail__division__slug',
            'branch': 'detail__branch__slug',
            'job_title': 'detail__job_title__slug',
            'employment_type': 'detail__employment_status__slug__in',
            'employment_level': 'detail__employment_level__slug__in',
        }
        search = self.request.query_params.get('search')
        fil = {}
        for k, v in self.request.query_params.items():
            if not v or k not in filter_mapper.keys():
                continue
            if k in ['employment_type', 'employment_level']:
                v = v.split(",")
            fil[filter_mapper[k]] = v
        user_qs = User.objects.filter(detail__organization=self.organization).filter(
            **fil).current()
        if self.mode == 'supervisor':
            immediate_subordinates = find_immediate_subordinates(self.user.id)
            user_qs = user_qs.filter(id__in=immediate_subordinates)
        if self.mode == 'user':
            user_qs = user_qs.none()
        if search:
            search = search.strip()
            user_qs = user_qs.annotate(
                __full_name=Concat(
                    'first_name', Value(' '),
                    Case(
                        When(
                            ~Q(middle_name=''),
                            then=Concat(
                                'middle_name', Value(' ')
                            )
                        ),
                        default=Value('')
                    ),
                    'last_name', Value(' ')
                )
            ).filter(
                __full_name__icontains=search
            )
        page = self.paginate_queryset(user_qs.distinct())
        return self.get_paginated_response(
            UserThickSerializer(
                instance=page, many=True, context=self.get_serializer_context()).data
        )

    @action(
        methods=['GET'],
        detail=False,
        url_path='user/(?P<employee_id>\d+'r')',
    )
    def employee_kpis(self, *args, **kwargs):
        employee_id = kwargs.get('employee_id')
        employee = User.objects.filter(id=employee_id).first()
        if not employee:
            raise ValidationError({'error': 'Employee not found'})
        employee_detail = employee.detail
        kpi = KPI.objects.filter(
            organization=employee_detail.organization,
            is_archived=False
        ).filter(
            Q(job_title=employee_detail.job_title) |
            Q(division=employee_detail.division) |
            Q(employment_level=employee_detail.employment_level)
        ).distinct()
        serializer = KPISerializer(
            kpi,
            fields=['id', 'title', 'success_criteria'],
            context={'organization': employee.organization, 'request': self.request},
            many=True
        )
        return Response({'results': serializer.data})

    @action(
        methods=['GET'],
        detail=False,
        url_path='users-kpis',
    )
    def user_kpis(self, *args, **kwargs):
        user_ids = self.request.query_params.get('userIds', '').split(',')
        other_kpis = self.request.query_params.get('other_kpis', False)
        job_titles = self.request.query_params.get('job_title')
        user_details = UserDetail.objects.filter(
            user__id__in=user_ids
        ).values('job_title', 'division', 'employment_level')
        job_title_ids = set()
        division_ids = set()
        employment_level_ids = set()
        items = itemgetter('job_title', 'division', 'employment_level')
        for (job_title_id, division_id, employment_level_id), _ in groupby(user_details, items):
            job_title_ids.add(job_title_id)
            division_ids.add(division_id)
            employment_level_ids.add(employment_level_id)
        fil = (
            Q(job_title__in=job_title_ids) |
            Q(division__in=division_ids) |
            Q(employment_level__in=employment_level_ids)
        )
        kpis_qs = KPI.objects.filter(
            organization=self.organization,
            is_archived=False
        )
        if other_kpis == 'true':
            extra_fil = {}
            if job_titles:
                extra_fil = {
                    "job_title__slug":  job_titles
                }
            kpis_qs = kpis_qs.exclude(fil).filter(**extra_fil)
        else:
            kpis_qs = kpis_qs.filter(fil)
        serializer = KPISerializer(
            kpis_qs.distinct(),
            fields=['id', 'title', 'success_criteria'],
            context={'organization': self.organization, 'request': self.request},
            many=True
        )
        return Response({'results': serializer.data})

    @action(
        methods=['GET'],
        detail=False,
        url_path='user/(?P<employee_id>\d+'r')/other-kpis',
    )
    def other_kpis(self, *args, **kwargs):
        employee_id = kwargs.get('employee_id')
        employee = get_object_or_404(User, id=employee_id)

        employee_detail = employee.detail
        kpi = KPI.objects.filter(
            organization=employee_detail.organization,
            is_archived=False
        ).exclude(
            Q(job_title=employee_detail.job_title) |
            Q(division=employee_detail.division) |
            Q(employment_level=employee_detail.employment_level)
        ).distinct()

        latest_individual_kpi = employee.individual_kpis.filter(is_archived=False).first()
        if latest_individual_kpi:
            assigned_kpi_ids = latest_individual_kpi.extended_individual_kpis.values_list(
                'kpi__id', flat=True)
            kpi = kpi.exclude(id__in=assigned_kpi_ids)

        serializer = KPISerializer(
            kpi,
            fields=['id', 'title', 'success_criteria'],
            context={'organization': employee_detail.organization, 'request': self.request},
            many=True
        )
        return Response({'results': serializer.data})


class ExtendedIndividualKPIViewSet(OrganizationMixin, ModelViewSet):
    queryset = ExtendedIndividualKPI.objects.all()
    serializer_class = ExtendedIndividualKPISerializer

    permission_classes = [AssignKPIPermission]
    filter_backends = [DjangoFilterBackend, FilterMapBackend, OrderingFilter]

    filter_map = {
        'fiscal_year': 'individual_kpi__fiscal_year__name',
        'status': 'individual_kpi__status'
    }
