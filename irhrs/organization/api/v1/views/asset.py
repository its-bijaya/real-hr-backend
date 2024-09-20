from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Count, Q, Subquery, OuterRef, Value, Prefetch
from django.db.models.functions import Concat
from django.utils import timezone
from django.utils.functional import cached_property
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.fields import ReadOnlyField
from rest_framework import status
from rest_framework.filters import SearchFilter
from django_filters import rest_framework as filters
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from irhrs.common.models.commons import EquipmentCategory
from irhrs.core.constants.common import (
    INTANGIBLE, ORGANIZATION_ASSET_CHOICES)
from irhrs.core.constants.organization import USED, IDLE, DAMAGED, \
    ASSET_STATUS, ASSIGNED_TO_CHOICES
from irhrs.core.mixins.file_import_mixin import (BackgroundFileImportMixin)
from irhrs.core.mixins.serializers import DummySerializer
from irhrs.core.mixins.viewset_mixins import (
    OrganizationMixin,
    OrganizationCommonsMixin, ListCreateViewSetMixin, UserMixin)
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.export.mixins.export import BackgroundExcelExportMixin
from irhrs.organization.api.v1.filters import OrganizationEquipmentFilterSet
from irhrs.organization.models import (
    EquipmentAssignedTo,
    OrganizationEquipment,
    AssignedEquipmentStatus, MeetingRoom, OrganizationDivision, OrganizationBranch)
from irhrs.permission.constants.permissions import (
    ORGANIZATION_PERMISSION,
    ORGANIZATION_SETTINGS_PERMISSION)
from ..permissions import (
    EquipmentAssignedToPermission, OfficeEquipmentPermission)
from ..serializers.asset import (
    OrganizationEquipmentSerializer,
    EquipmentAssignedToSerializer,
    EquipmentAssignedToBulkSerializer,
    EquipmentAssignedToHistorySerializer
)

User = get_user_model()
used_filter = OrganizationEquipment.is_currently_assigned_filter(
    called_from_equipment_model=True
)
idle_filter = Q(~Q(used_filter), is_damaged=False)


class OrganizationEquipmentViewSet(BackgroundFileImportMixin,
                                   OrganizationMixin,
                                   OrganizationCommonsMixin,
                                   ModelViewSet, BackgroundExcelExportMixin):
    queryset = OrganizationEquipment.objects.all()
    serializer_class = OrganizationEquipmentSerializer
    lookup_field = 'slug'
    filter_backends = (SearchFilter, FilterMapBackend,
                       filters.DjangoFilterBackend, OrderingFilterMap)
    filterset_class = OrganizationEquipmentFilterSet
    filter_map = {
        'type': 'category__type',
        'category': 'category__slug'
    }
    search_fields = ['name', 'code']
    permission_classes = [OfficeEquipmentPermission]
    ordering_fields_map = {
        'name': 'name',
        'user': 'employee_full_name',
        'assigned_date': 'assigned_date',
        'category': 'category__name'
    }
    import_fields = [
        'NAME', 'CATEGORY', 'BRAND NAME', 'CODE', 'AMOUNT', 'PURCHASED DATE', 'SERVICE ORDER', 'BILL NUMBER',
        'REFERENCE NUMBER', 'ASSIGNED TO', 'REMARK', 'SPECIFICATIONS'
    ]
    sample_file_name = 'office_equipment'
    background_task_name = 'office_equipment'
    values = [
        'Chair 121', '', 'Chaudhary Group', '123xxa', '123', '2015-12-12', '123asd123', '12aa1',
        '123asd', 'User', 'This is remark of equipment.',
        'This is specifications of equipment.'
    ]
    non_mandatory_field_value = {
        'brand_name': '',
        'service_order': '',
        'bill_number': '',
        'reference_number': '',
        'specifications': '',
        'remark': '',
        'amount': 0
    }
    export_type = "Office Equipment"
    export_fields = {
        "Name": "name",
        "Category": "category",
        "Code": "code",
        "Assigned To": "assigned_to",
        "Assigned Date": "assigned_date",
        "Status": "status",
        "Assigned detail": "user_details",
    }

    def get_queryset(self):
        ordering_by = self.request.query_params.get(
            'ordering', '').split('-')[-1]
        queryset = super().get_queryset().filter(
            organization=self.organization
        ).select_related(
            'category', 'organization'
        ).prefetch_related(
            Prefetch(
                'assignments',
                queryset=EquipmentAssignedTo.objects.filter(
                    released_date__isnull=True
                ).select_related(
                    'division',
                    'user',
                    'user__detail',
                    'user__detail__job_title',
                    'branch',
                    'meeting_room',
                ),
                to_attr='assigned_equipment'
            )
        )
        if ordering_by in ['user', 'assigned_date']:
            ordering_dict = dict(
                assigned_date={
                    'assigned_date': Subquery(
                        EquipmentAssignedTo.objects.filter(
                            equipment_id=OuterRef('id'),
                            released_date__isnull=True
                        ).values('assigned_date')[:1],
                        output_field=models.DateField()
                    )
                },
                user={
                    'employee_full_name': Subquery(
                        EquipmentAssignedTo.objects.filter(
                            equipment_id=OuterRef('id'),
                            released_date__isnull=True
                        ).annotate(full_name=Concat(
                            'user__first_name', Value(' '),
                            'user__middle_name', Value(' '),
                            'user__last_name', Value(' ')
                        )).values('full_name')[:1],
                        output_field=models.CharField()
                    )
                }
            )
            queryset = queryset.annotate(
                **ordering_dict.get(ordering_by)
            )

        return queryset

    def generate_filters(self):
        fil = dict()
        _add_filter = False
        if self.request.query_params.get('user'):
            _add_filter = True
            fil.update({
                'assignments__user': self.request.query_params.get(
                    'user')
            })
        if self.request.query_params.get('division'):
            _add_filter = True
            fil.update({
                'assignments__division__slug': self.request.query_params.get(
                    'division')
            })
        if self.request.query_params.get('branch'):
            _add_filter = True
            fil.update({
                'assignments__branch__slug': self.request.query_params.get(
                    'branch')
            })
        return _add_filter, fil

    def filter_queryset(self, queryset):
        # Type count should not be affected by filter
        # so we calculate it before filtering
        eq_type = self.request.query_params.get('type', None)
        self.status_filter_dict = {
            IDLE.lower(): queryset.filter(idle_filter).count(),
            USED.lower(): queryset.filter(used_filter).count(),
            DAMAGED.lower(): queryset.filter(is_damaged=True).count()
        }
        if eq_type:
            self.status_filter_dict = {
                IDLE.lower(): queryset.filter(idle_filter, category__type=eq_type).count(),
                USED.lower(): queryset.filter(used_filter, category__type=eq_type).count(),
                DAMAGED.lower(): queryset.filter(is_damaged=True, category__type=eq_type).count()
            }
        type_filters = dict(ORGANIZATION_ASSET_CHOICES).keys()
        self.type_filter_dict = {
            type_filter.lower(): self.get_queryset().filter(
                Q(category__type=type_filter)
            ).count()
            for type_filter in type_filters
        }
        _add_filter, fil = self.generate_filters()
        if _add_filter:
            return super().filter_queryset(queryset).filter(**fil)
        return super().filter_queryset(queryset)

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            kwargs.update({'exclude_fields': ['specifications']})
        if self.action == 'create':
            kwargs.update({'exclude_fields': ['status']})
        return super().get_serializer(*args, **kwargs)

    def get_serializer_class(self):
        if self.action == 'assign_equipment':
            return EquipmentAssignedToSerializer
        return super().get_serializer_class()

    def destroy(self, request, *args, **kwargs):
        if self.get_object().assignments.filter(
                released_date__isnull=True).exists():
            raise ValidationError({
                'user': 'This equipment has been assigned.'
            })
        return super().destroy(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        stats = {
            "all": self.get_queryset().count()
        }
        queryset = self.filter_queryset(self.get_queryset())
        stats.update(self.type_filter_dict)
        stats.update(self.status_filter_dict)
        response.data.update({
            'stats': stats
        })

        return response

    @ action(detail=True,
             methods=['post'],
             url_path=r'(?P<equipment_status>(unassign|damaged))',
             serializer_class=type(
                 'EquipmentReleaseSerializer',
                 (DummySerializer,),
                 {
                     "status": ReadOnlyField(),
                 }
             ))
    def release_equipment(self, request, equipment_status=None, *args,
                          **kwargs):
        equipment = self.get_object()
        if equipment.is_damaged:
            raise ValidationError({
                'detail': ['Equipment has been damaged.']
            })
        if equipment_status == 'unassign':
            _obj = equipment.assignments.filter(
                released_date__isnull=True).first()
            if not _obj:
                raise ValidationError({
                    'detail': ['Equipment is not assigned to '
                               'employee, division or branch']
                })
            released_date = timezone.now().date()

            equipment.save()

            _obj.released_date = released_date
            _obj.save()
        elif equipment_status == 'damaged':
            _obj = equipment.assignments.filter(
                released_date__isnull=True).first()
            equipment.is_damaged = True
            equipment.save()

            if _obj:
                _obj.released_date = timezone.now()
                _obj.save()

            AssignedEquipmentStatus.objects.create(assigned_equipment=_obj,
                                                   confirmed=True,
                                                   confirmed_by=self.request.user)

        else:
            raise ValidationError({'status': ['Status can be either'
                                              ' \'Unassign\' or \'Damaged\'']})
        return Response({})

    def get_queryset_fields_map(self):
        return {
            'category': EquipmentCategory.objects.all(),
            'assigned_to': list(dict(ASSIGNED_TO_CHOICES).keys())
        }

    def get_failed_url(self):
        return f"/admin/{self.organization.slug}/organization/settings/equipment/?status=failed"

    def get_success_url(self):
        return f"/admin/{self.organization.slug}/organization/settings/equipment/?status=success"
    # @action(
    #     detail=False,
    #     methods=['GET'],
    #     url_path="import/sample",
    #     serializer_class=FileImportSerializer
    # )
    # def sample_download(self, request, *args, **kwargs):
    #     self.values = [
    #         'eg; Dell Moniter', 'eg; 123xx', 'eg; 12345', 'eg; 2019-10-24', 'eg; 123asdz123',
    #         'eg; 123asd', 'eg; asd12sa', 'eg; This is remarks field',
    #         'eg; You can add specifications and configurations here'
    #     ]
    #     response = HttpResponse(
    #         content=self.generate_sample_with_dropdown(),
    #         content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    #     )
    #     response['Content-Disposition'] = f'attachment; ' \
    #                                       f'filename=office_equipement_sample.xlsx'
    #     return response

    @action(
        methods=['GET'],
        detail=True,
        url_path=r'history',
        url_name='history',
        serializer_class=EquipmentAssignedToHistorySerializer
    )
    def equipment_history(self, request, *args, **kwargs):
        queryset = self.get_object().assignments.all()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @staticmethod
    def prepare_export_object(obj, **kwargs):
        export_data = ('assigned_detail', 'status')
        data = OrganizationEquipmentSerializer(
            instance=obj, fields=export_data
        ).data
        assigned_detail = data.get('assigned_detail', {})

        mapping = {
            'user': (User.objects, 'full_name', 'user_details'),
            'meeting_room': (MeetingRoom.objects, 'name', 'user_details')
        }

        if assigned_detail:
            assigned_date = assigned_detail.get('assigned_date', None)
            setattr(obj, 'assigned_date', assigned_date)
            for key, (model_class, attribute, obj_attribute) in mapping.items():
                value = assigned_detail.get(key)

                if value is not None:
                    attribute_value = getattr(model_class.get(id=value), attribute)
                    setattr(obj, obj_attribute, attribute_value)

            division_slug = assigned_detail.get('division')
            branch_slug = assigned_detail.get('branch')

            if division_slug and not branch_slug:
                division = OrganizationDivision.objects.get(slug=division_slug).name
                setattr(obj, 'user_details', division)
            elif branch_slug and not division_slug:
                branch = OrganizationBranch.objects.get(slug=branch_slug).name
                setattr(obj, 'user_details', branch)
            elif branch_slug and division_slug:
                division = OrganizationDivision.objects.get(slug=division_slug).name
                branch = OrganizationBranch.objects.get(slug=branch_slug).name
                setattr(obj, 'user_details', f'{branch}/{division}')

        status = data.get('status')
        if status is not None:
            setattr(obj, 'status', status)
        return obj

    def get_export_data(self):
        export_data = super().get_export_data()
        return export_data


class EquipmentAssignedToViewSet(OrganizationMixin, ListCreateViewSetMixin, UserMixin):
    queryset = EquipmentAssignedTo.objects.all()
    serializer_class = EquipmentAssignedToSerializer
    permission_classes = [EquipmentAssignedToPermission]
    filter_fields = ['division', 'branch']

    def get_queryset(self):
        return super().get_queryset().filter(
            equipment__organization=self.organization
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['organization'] = self.get_organization()
        return context

    def has_user_permission(self):
        _permissions = self.request.user.get_hrs_permissions(
            organization=self.organization)
        _has_permission = ORGANIZATION_PERMISSION.get(
            "code") in _permissions or ORGANIZATION_SETTINGS_PERMISSION.get(
            "code") in _permissions

        if self.action == 'employee_equipments':
            return self.request.user == self._user or _has_permission or self.is_supervisor
        return _has_permission

    @action(detail=False, url_path=r'user/(?P<user_id>\d+)')
    def employee_equipments(self, request, user_id=None, *args, **kwargs):
        used_equipments = self.get_queryset().filter(
            released_date__isnull=True,
            user=self._user)
        if self.request.query_params.get('detail', 'True') in ['true', 'True',
                                                               '1']:
            page = self.paginate_queryset(used_equipments)
            if page is not None:
                serializer = EquipmentAssignedToSerializer(
                    page,
                    context=self.get_serializer_context(),
                    many=True
                )
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(used_equipments, many=True)

            return Response(serializer.data)
        return Response(
            {
                'equipments': used_equipments.exclude(
                    equipment__category__type=INTANGIBLE).values_list(
                    'equipment__name',
                    flat=True),
                'possessions': used_equipments.filter(
                    equipment__category__type=INTANGIBLE).values_list(
                    'equipment__name',
                    flat=True)
            }
        )

    @action(methods=['post'],
            detail=False,
            url_path=r'bulk',
            url_name='bulk',
            serializer_class=EquipmentAssignedToBulkSerializer)
    def employee_equipment_bulk_assign(self, request,
                                       *args, **kwargs):
        data = self.request.data
        serializer_class = self.get_serializer_class()
        organization = super().get_organization()
        context = super().get_serializer_context()
        context.update({'organization': organization})
        assignments = serializer_class(
            data=data,
            context=context,
        )
        assignments.is_valid(raise_exception=True)
        assignments.save()
        return Response(assignments.data, status=status.HTTP_201_CREATED)

    @cached_property
    def _user(self):
        try:
            user = User.objects.get(id=self.kwargs.get('user_id'))
        except User.DoesNotExist:
            user = None
        return user
