from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.db.models import Q, Case, When, F, Prefetch, IntegerField
from django.utils import timezone
from django_filters import filters
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.rest_framework import FilterSet
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response

from irhrs.core.mixins.viewset_mixins import (
    ListRetrieveViewSetMixin, CreateUpdateDeleteViewSetMixin,
    RetrieveUpdateViewSetMixin, OrganizationMixin, OrganizationCommonsMixin,
    ListCreateRetrieveViewSetMixin, PastUserGenericFilterMixin)
from irhrs.core.utils import nested_getattr
from irhrs.core.utils.common import apply_filters, validate_permissions
from irhrs.core.utils.filters import OrderingFilterMap, FilterMapBackend
from irhrs.export.mixins.export import BackgroundExcelExportMixin
from irhrs.hris.api.v1.permissions import PayrollBulkApplyToUserPermission, \
    PayrollWriteHeadingPermission, \
    AssignPayrollPackagePermission, \
    GeneratePayrollPermission, HoldPayrollPermission, ViewPayrollReportPermission, \
    PayrollRebatePermission, \
    ViewEmployeeExperiencePackage, PayrollSettingsPermission, PayrollHeadingPermission, \
    EmployeePayrollViewPermission
from irhrs.organization.models import Organization, FiscalYear
from irhrs.payroll.api.v1.serializers import (
    HeadingSerializer,
    PackageSerializer,
    PackageListSerializer,
    PackageHeadingSerializer,
    SalaryHoldingSerializer,
    EmployeeSerializer,
    ReportRowRecordSerializer,
    UserExperiencePackageSlotCreateAndUpdateSerializer,
    UserPackageListSerializer,
    OrganizationOverviewConfigSerializer,
    OrganizationPayrollConfigUpdateSerializer,
    ExternalTaxDiscountSerializer,
    SalaryHoldingReleaseSerializer,
    SwitchPackageHeadingOrderSerializer,
)

from irhrs.payroll.api.v1.serializers.payroll import (
    RebateSettingSerializer
)

from irhrs.payroll.api.v1.serializers.heading import HeadingSwitchSerializer, HeadingGetVariablesSerializer
from irhrs.payroll.api.v1.serializers.heading import (
    PackageHeadingGetVariablesSerializer,
    DragHeadingSerializer,
    UpdatePackageHeadingInputSerializer
)
from irhrs.payroll.api.v1.serializers.payroll import (
    YearlyHeadingDetailSerializer
)
from irhrs.payroll.api.v1.serializers.payroll_serializer import BasicViewPackageSerializer
from irhrs.payroll.constants import INITIAL_VARIABLES, TYPE_TWO_CONSTANT_VARIABLES
from irhrs.payroll.models import (
    Heading,
    Package,
    PackageHeading,
    SalaryHolding,
    ReportRowRecord,
    UserExperiencePackageSlot,
    OverviewConfig,
    OrganizationPayrollConfig,
    ExternalTaxDiscount,
    YearlyHeadingDetail,
    RebateSetting, UNASSIGNED, PACKAGE_DELETED
)
from irhrs.payroll.tasks import create_package_activity
from irhrs.payroll.utils.generate import \
    raise_validation_error_if_payroll_in_generated_or_processing_state, \
    validate_if_package_heading_updated_after_payroll_generated_previously
from irhrs.payroll.utils.headings import is_rebate_type_used_in_heading
from irhrs.payroll.utils.helpers import (
    ExtendedPageNumberPagination,
    EmployeeConditionalVariableAdapter,
    EmployeeRuleVariableAdapter,
    get_variable_name
)
from irhrs.payroll.utils.mixins import InputChoiceMixin, \
    DestroyProtectedModelMixin
from irhrs.payroll.utils.rule_validator import HeadingRuleValidator
from irhrs.permission.constants.permissions import GENERATE_PAYROLL_PERMISSION, \
    PAYROLL_REPORT_PERMISSION

from irhrs.users.models import UserExperience

Employee = get_user_model()


class HeadingFilter(FilterSet):
    exclude_variable = filters.BooleanFilter(
        method='get_exclude_variable'
    )
    pf_headings = filters.BooleanFilter(
        method='get_pf_headings'
    )
    cit_headings = filters.BooleanFilter(
        method='get_cit_headings'
    )

    extra_headings = filters.BooleanFilter(
        method='get_extra_headings'
    )

    def get_exclude_variable(self, queryset, name, value):
        exclude_dict = dict()
        if value:
            exclude_dict = {'type__in': ['Type1Cnst', 'Type2Cnst']}

        return queryset.exclude(
            **exclude_dict
        )

    def get_pf_headings(self, queryset, name, value):
        filter_dict = dict()
        if value:
            filter_dict = {'payroll_setting_type__in': [
                'Provident Fund Office Addition', 'Provident Fund'
            ]}

        return queryset.filter(
            **filter_dict
        )

    def get_cit_headings(self, queryset, name, value):
        filter_dict = dict()
        if value:
            filter_dict = {'payroll_setting_type__in': [
                'Self CIT Office Addition', 'Self CIT'
            ]}

        return queryset.filter(
            **filter_dict
        )

    def get_extra_headings(self, queryset, name, value):
        filter_dict = dict()
        if value:
            filter_dict = {'type__in': [
                'Extra Addition', 'Extra Deduction'
            ]}

        return queryset.filter(
            **filter_dict
        )

    class Meta:
        model = Heading
        fields = {
            'name': ['icontains'],
            'organization__slug': ['exact'],
            'duration_unit': ['exact'],
            'type': ['exact', ],
            'taxable': ['exact'],
            'benefit_type': ['exact'],
            'payroll_setting_type': ['exact'],
        }


class HeadingAPIViewSet(DestroyProtectedModelMixin, InputChoiceMixin,
                        viewsets.ModelViewSet):
    pagination_class = ExtendedPageNumberPagination
    permission_classes = [
        PayrollHeadingPermission
    ]
    queryset = Heading.objects.all()
    serializer_class = HeadingSerializer
    choice_fields = (
        'id',
        'label',
        'payroll_setting_type',
        'duration_unit',
        'taxable',
        'benefit_type',
        'absent_days_impact',
        'order',
        'type',
        'dependencies',
        'makes_dependency'
    )
    filter_class = HeadingFilter

    # filter_fields = {
    #     'name': ['icontains'],
    #     'duration_unit': ['exact'],
    #     'type': ['exact', ],
    #     'taxable': ['exact'],
    #     'benefit_type': ['exact'],
    #     'payroll_setting_type': ['exact'],
    # }

    def get_permission_classes(self):
        """
        :return: solve conflict between limit_write_to and actions permissions
        """
        if self.action == 'bulk_apply_to_users':
            return [PayrollBulkApplyToUserPermission]
        return self.permission_classes

    def get_paginated_response(self, data, extra_data):
        """
        Return a paginated style `Response` object for the given output data.
        """
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data, extra_data)

    def list(self, request, *args, **kwargs):
        organization__slug = self.request.query_params.get(
            'organization__slug')
        choice_list = kwargs.get('choice_list', False)
        queryset = self.filter_queryset(
            self.get_queryset()
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data, {
                'next_order': Heading.get_next_heading_order(
                    organization__slug)
            })

        serializer = self.get_serializer(queryset, many=True)
        if choice_list:
            return Response(serializer.data)
        else:
            return Response({'list': serializer.data, 'extra_data': {
                'next_order': Heading.get_next_heading_order(
                    organization__slug)
            }})

    @action(methods=['POST'], detail=False, serializer_class=HeadingGetVariablesSerializer)
    def get_variables(self, request):
        from irhrs.payroll.utils.calculator_variable import CalculatorVariable


        serializer = self.serializer_class(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        order = data.get('order')
        current_duration_unit = data.get('current_duration_unit')
        current_heading_type = data.get('current_heading_type')
        organization__slug = data.get('organization__slug').slug

        calculator_variable = CalculatorVariable(
            organization__slug,
            order=order,
            current_duration_unit=current_duration_unit,
            current_heading_type=current_heading_type,
        )

        return Response(
            {
                'conditional_variables': list(
                    calculator_variable.get_heading_scoped_variables(conditional=True)
                ),
                'rule_variables': list(
                    calculator_variable.get_heading_scoped_variables()
                ),
                'functions': CalculatorVariable.get_registered_methods()
            }, status=status.HTTP_200_OK)


    @staticmethod
    def get_variable_list(current_heading_type, dependent_package_headings):
        variables = list()
        variables.extend(INITIAL_VARIABLES)
        # try:
        # employee fields
        # variables += EmployeeAndDesignationCommonFieldAdapter().get_variables_list()
        conditional_adapter_variables = EmployeeConditionalVariableAdapter(
            'EMPLOYEE_',
            model=Employee
        ).generate_variables_only()
        rule_adapter_variables = EmployeeRuleVariableAdapter(
            'EMPLOYEE_',
            model=Employee
        ).generate_variables_only()
        # variables += DesignationVariableAdapter().generate_variables_only()
        # START: Addition, Deduction and Type1Cnst can only use Type1Cnst with current duration unit
        # if current_heading_type in ['Addition', 'Deduction',
        #                             'Type1Cnst'] and current_duration_unit:
        #     exclude_query = Q(
        #         Q(
        #             Q(type__in=['Type1Cnst', 'Addition', 'Deduction']) &
        #             ~Q(duration_unit=current_duration_unit)
        #         ) | Q(type='Type2Cnst')
        #     )
        # Typ2Cnst can obly use Type2Cnst, Addition and Deduction
        exclude_query = Q()
        if current_heading_type in ['Type2Cnst', 'Addition', 'Deduction']:

            variables.extend(TYPE_TWO_CONSTANT_VARIABLES)

            if current_heading_type == 'Type2Cnst':
                exclude_query = Q(
                    Q(type='Type1Cnst')
                )
        dependent_package_headings = dependent_package_headings.exclude(exclude_query)
        # 'Tax Deduction', 'Type1Cnst', 'Type2Cnst', 'Extra Addition' =tve
        tve_headings = []
        not_tve_headings = []
        # conditional_variables = set(['__TOTAL_GROSS_REMUNERATION__', '__BASIC_REMUNERATION__'])
        conditional_variables = set([])
        # if current_heading_type == 'Tax Deduction':
        conditional_variables.add('__ANNUAL_GROSS_SALARY__')
        for pkg_head in dependent_package_headings:
            if pkg_head.type not in [
                'Tax Deduction',
                'Type1Cnst',
                'Type2Cnst',
                'Extra Addition'
            ]:
                not_tve_headings.append(pkg_head)
            else:
                tve_headings.append(pkg_head)

            # if pkg_head.type == 'Gross Remuneration Contributing Addition':
            #     conditional_variables.add('__TOTAL_GROSS_REMUNERATION__')
        variables += list(conditional_variables)
        variables += [
            '__' +
            get_variable_name(pkg_head.name) +
            '__' for pkg_head in tve_headings
        ]
        heading_variables = [get_variable_name(
            pkg_head.name) for pkg_head in not_tve_headings]
        # variables += ['__' + get_variable_name(name, '_PAYABLE_AMOUNT') + '__' for name in heading_variables]
        # # variables += [get_variable_name(name, '_GROSS_AMOUNT') for name in heading_variables]
        # variables += ['__' + get_variable_name(name, '_UNIT_AMOUNT') + '__' for name in heading_variables]
        variables += [
            '__' +
            get_variable_name(name, '') +
            '__' for name in heading_variables
        ]
        # variables += [get_variable_name(name, '_GROSS_AMOUNT') for name in heading_variables]
        # variables += ['__' + get_variable_name(name, '_UNIT_AMOUNT') + '__' for name in heading_variables]
        return conditional_adapter_variables, rule_adapter_variables, variables

    @staticmethod
    def get_new_order(heading, from_order, to_order, displacement_type):
        """
        displacement type can be top_to_bottom or bottom_to_top
        """
        to_order, from_order = int(to_order), int(from_order)
        if heading:
            if heading.order == from_order:
                return to_order
            elif from_order <= heading.order <= to_order and displacement_type == 'top_to_bottom':
                return heading.order - 1
            elif to_order <= heading.order <= from_order and displacement_type == 'bottom_to_top':
                return heading.order + 1
            else:
                return heading.order
        return None

    @action(methods=['POST'], detail=False)
    def switch_order(self, request):
        serializer = HeadingSwitchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        from_obj_order = data.get('from_obj_order')
        to_obj_order = data.get('to_obj_order')
        organization__slug = data.get('organization__slug').slug

        shift_type = 'top_to_bottom' if from_obj_order < to_obj_order else 'bottom_to_top'
        is_valid = True

        # --- taxable below tax validation -- #
        heading = Heading.objects.filter(
            organization__slug=organization__slug, order=from_obj_order
        ).first()
        if heading:
            latest_tax_deduction_heading = Heading.objects.filter(
                type="Tax Deduction",
                organization__slug=organization__slug
            ).order_by('-order').first()
            first_tax_deduction_heading = Heading.objects.filter(
                type="Tax Deduction",
                organization__slug=organization__slug
            ).order_by('order').first()
            latest_tax_deduction_heading_order = self.get_new_order(
                latest_tax_deduction_heading, from_obj_order, to_obj_order, shift_type
            )
            oldest_taxable_addition = Heading.objects.filter(
                type="Addition",
                organization__slug=organization__slug,
                taxable=True
            ).order_by('-order').first()
            oldest_taxable_addition_order = self.get_new_order(
                oldest_taxable_addition, from_obj_order, to_obj_order, shift_type
            )

            oldest_non_taxable_deduction = Heading.objects.filter(
                type="Deduction",
                taxable=False,
                organization__slug=organization__slug
            ).order_by('-order').first()
            oldest_non_taxable_deduction_order = self.get_new_order(
                oldest_non_taxable_deduction, from_obj_order, to_obj_order, shift_type
            )

            error_message, is_valid = HeadingRuleValidator.validate_tax_deduction_order(
                heading=heading,
                latest_tax_deduction_heading_order=latest_tax_deduction_heading_order,
                oldest_taxable_addition_order=oldest_taxable_addition_order,
                oldest_non_taxable_deduction_order=oldest_non_taxable_deduction_order,
            )
            if not is_valid:
                raise ValidationError({'non_field_errors': [error_message]})

        if shift_type == 'top_to_bottom':
            # todo @Ravi validity check middle objects with new order
            upward_displaced_headings = Heading.objects.filter(
                order__gt=from_obj_order,
                order__lte=to_obj_order,
                organization__slug=organization__slug
            )

            for upward_displaced_heading in upward_displaced_headings:
                # no need to fake here
                # upward_displaced_heading.order = upward_displaced_heading.order - 1
                is_valid = upward_displaced_heading.rule_is_valid(
                    exclude_headings_order=[from_obj_order]
                )[0]
                # todo @Ravi: include self order-1
                if not is_valid:
                    break

            if is_valid:
                downward_displaced_heading = Heading.objects.get(
                    order=from_obj_order,
                    organization__slug=organization__slug
                )
                downward_displaced_heading.order = to_obj_order
                is_valid = downward_displaced_heading.rule_is_valid()[0]

            if is_valid:
                Heading.objects.filter(
                    order__gte=from_obj_order,
                    order__lte=to_obj_order,
                    organization__slug=organization__slug
                ).update(
                    order=Case(
                        When(order=from_obj_order, then=to_obj_order),
                        default=F('order') - 1,
                        output_field=IntegerField()
                    )
                )
        else:
            # todo @Ravi: validity check actual object with new order
            upward_displaced_heading = Heading.objects.get(
                order=from_obj_order,
                organization__slug=organization__slug
            )
            upward_displaced_heading.order = to_obj_order
            is_valid = upward_displaced_heading.rule_is_valid()[0]
            if is_valid:
                Heading.objects.filter(
                    order__gte=to_obj_order,
                    order__lte=from_obj_order,
                    organization__slug=organization__slug
                ).update(
                    order=Case(
                        When(order=from_obj_order, then=to_obj_order),
                        default=F('order') + 1,
                        output_field=IntegerField()
                    )
                )
        new_orders = Heading.objects.filter(
            organization__slug=organization__slug
        ).order_by('order').values_list('order', flat=True)

        if is_valid:
            return Response(
                {
                    'success': True,
                    'new_orders': new_orders
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    'detail': "Sorting is not successful."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.makes_heading_dependencies.exists():
            return Response(
                {
                    'error_message': 'Cannot delete heading that makes dependency'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

    def get_organization(self):
        switchable_organizations = self.request.user.switchable_organizations_pks
        return Organization.objects.filter(
            slug=self.request.query_params.get('organization__slug')
        ).filter(
            id__in=[
                *switchable_organizations,
                self.request.user.detail.organization.id
            ]
        ).first()

    def get_queryset(self):
        qs = super().get_queryset()
        # Block is_hidden by default
        if self.request.query_params.get('all_headings', 'f') == 'true':
            return qs
        return qs.exclude(is_hidden=True)


    @action(
        detail=True, methods=['POST'], url_path="bulk-apply-to-users",
        serializer_class=UpdatePackageHeadingInputSerializer
    )
    def bulk_apply_to_users(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            self.get_object(),
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(status=status.HTTP_200_OK)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['organization'] = self.get_organization()
        return ctx

    def get_organization(self):
        organization = None
        org_slug = self.request.query_params.get('organization__slug')
        if org_slug is not None:
            organization = get_object_or_404(
                Organization, slug=org_slug
            )
        return organization


class PackageFilter(FilterSet):
    class Meta:
        model = Package
        fields = ['organization__slug']


class PackageAPIViewSet(DestroyProtectedModelMixin, InputChoiceMixin,
                        viewsets.ModelViewSet):

    queryset = Package.objects.all()
    permission_classes = [PayrollWriteHeadingPermission]
    serializer_class = PackageSerializer
    list_serializer_class = PackageListSerializer
    choice_fields = ('id', 'label')
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    ordering_fields = ('name', 'created_at')
    search_fields = (
        'name', 'excel_package__name',
        'id'

    )
    filter_class = PackageFilter

    def get_serializer_class(self):
        if self.action == 'list':
            return self.list_serializer_class
        return super().get_serializer_class()

    def get_organization(self):
        return get_object_or_404(
            Organization.objects.filter(
                id__in=self.request.user.switchable_organizations_pks
            ),
            slug=self.request.query_params.get('organization__slug')
        )


    @action(methods=['GET'], detail=True, url_path='basic-view',
            serializer_class=BasicViewPackageSerializer)
    def basic_view(self, request, pk=None):
        package = self.get_object()
        basic_view = self.request.query_params.get('basic_view')
        package_heading = package.package_headings.all()
        if basic_view:
            package_heading = package_heading.filter(
                heading__visible_in_package_basic_view=basic_view
            )
        serializer = self.get_serializer(
            package_heading, many=True
        )
        return Response(serializer.data)

    @transaction.atomic
    def perform_destroy(self, instance):
        title = f'{self.request.user.full_name} has {PACKAGE_DELETED} a package named "{instance.name}"'
        create_package_activity(title=title, package=instance, action=PACKAGE_DELETED)
        super().perform_destroy(instance)


class UserExperiencePackageSlotAPIViewSet(CreateUpdateDeleteViewSetMixin):
    queryset = UserExperiencePackageSlot.objects.all()
    permission_classes = [AssignPayrollPackagePermission]
    serializer_class = UserExperiencePackageSlotCreateAndUpdateSerializer
    # detail_serializer = UserExperiencePackageDetailSerializer
    # create_or_update_serializer = UserExperiencePackageSlotCreateAndUpdateSerializer
    # bulk_create_serializer = UserExperiencePackageSlotBulkCreateSerializer

    # def get_serializer_class(self):
    #     if self.action in ('create', 'update'):
    #         return self.create_or_update_serializer
    #     if self.action == 'retrieve':
    #         return self.detail_serializer
    #     if self.action == 'create_in_bulk':
    #         return self.bulk_create_serializer
    #     return self.detail_serializer

    def destroy(self, request, *args, **kwargs):
        raise_validation_error_if_payroll_in_generated_or_processing_state(
            organization=self.get_organization()
        )
        instance = self.get_object()
        user_package = instance.package
        package_user = instance.user_experience.user
        latest_package = UserExperiencePackageSlot.objects.filter(
            user_experience__user=package_user
        ).order_by('active_from_date').last()
        if instance != latest_package:
            raise ValidationError("Latest packages must be deleted first.")
        if instance.is_used_package:
            return Response(status=status.HTTP_306_RESERVED)
        self.perform_destroy(instance)
        title = f'{self.request.user.full_name} has {UNASSIGNED} a package named "{user_package.name}" to {package_user.full_name}'
        create_package_activity(title=title, package=user_package, action=UNASSIGNED,
                                assigned_to=package_user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # @action(detail=False, methods=['post'])
    # def create_in_bulk(self, request):
    #     response_data = dict()
    #     serializer = self.bulk_create_serializer(data=request.data)
    #     if serializer.is_valid(raise_exception=True):
    #         response_data = serializer.create(serializer.validated_data)
    #     return Response(response_data, status=status.HTTP_201_CREATED)

    def get_organization(self):
        return get_object_or_404(
            Organization.objects.filter(
                id__in=self.request.user.switchable_organizations_pks
            ),
            slug=self.request.query_params.get(
                'user_experience__user__detail__organization__slug'
            )
        )


class PackageHeadingFilter(FilterSet):
    extra_headings = filters.CharFilter(
        method='get_extra_headings', label='Extra headings'
    )

    def get_extra_headings(self, queryset, name, value):
        filter_dict = dict()
        if value:
            filter_dict = {'heading__type__in': [
                'Extra Addition', 'Extra Deduction']}

        return queryset.filter(
            **filter_dict
        )

    class Meta:
        model = PackageHeading
        fields = {
            'id': ['exact'],
            'package__id': ['exact'],
        }


class PackageHeadingAPIViewSet(DestroyProtectedModelMixin, InputChoiceMixin, viewsets.ModelViewSet):
    queryset = PackageHeading.objects.all()
    permission_classes = [
        PayrollWriteHeadingPermission
    ]
    serializer_class = PackageHeadingSerializer
    choice_fields = (
        'id',
        'label',
        'rules',
        'heading',
        'is_editable'
    )
    filter_class = PackageHeadingFilter

    # def create(self, request, *args, **kwargs):
    #     import ipdb
    #     ipdb.set_trace()
    #     super().create(request, *args, **kwargs)
    @action(methods=['POST'], detail=False, serializer_class=PackageHeadingGetVariablesSerializer)
    def get_variables(self, request):
        from irhrs.payroll.utils.calculator_variable import CalculatorVariable

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        order = data.get('order')
        current_duration_unit = data.get('current_duration_unit')
        current_heading_type = data.get('current_heading_type')
        package = data.get('package_id')


        calculator_variable = CalculatorVariable(
            package.organization.slug,
            order=order,
            current_duration_unit=current_duration_unit,
            current_heading_type=current_heading_type,
            package=package
        )

        return Response(
            {
                'conditional_variables': list(
                    calculator_variable.get_heading_scoped_variables(conditional=True)
                ),
                'rule_variables': list(
                    calculator_variable.get_heading_scoped_variables()
                ),
                'functions': CalculatorVariable.get_registered_methods()
            }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def switch_order(self, request):
        raise_validation_error_if_payroll_in_generated_or_processing_state(
            organization=self.get_organization()
        )

        ser = SwitchPackageHeadingOrderSerializer(
            data=request.data,
            context={
                "request": request,
            }
        )
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        from_obj_order = data.get('from_obj_order')
        to_obj_order = data.get('to_obj_order')
        package_id = data.get('package_id')

        shift_type = 'top_to_bottom' if from_obj_order < to_obj_order else 'bottom_to_top'
        is_valid = True

        # --- taxable below tax validation -- #
        heading = PackageHeading.objects.filter(
            package_id=package_id, order=from_obj_order
        ).first()
        if heading:
            latest_tax_deduction_heading = PackageHeading.objects.filter(
                type="Tax Deduction",
                package_id=package_id,
            ).order_by('-order').first()
            latest_tax_deduction_heading_order = HeadingAPIViewSet.get_new_order(
                latest_tax_deduction_heading, from_obj_order, to_obj_order, shift_type
            )

            oldest_taxable_addition = PackageHeading.objects.filter(
                type="Addition",
                package_id=package_id,
                taxable=True
            ).order_by('-order').first()
            oldest_taxable_addition_order = HeadingAPIViewSet.get_new_order(
                oldest_taxable_addition, from_obj_order, to_obj_order, shift_type
            )

            oldest_non_taxable_deduction = PackageHeading.objects.filter(
                type="Deduction",
                taxable=False,
                package_id=package_id,
            ).order_by('-order').first()
            oldest_non_taxable_deduction_order = HeadingAPIViewSet.get_new_order(
                oldest_non_taxable_deduction, from_obj_order, to_obj_order, shift_type
            )

            error_message, is_valid = HeadingRuleValidator.validate_tax_deduction_order(
                heading=heading,
                latest_tax_deduction_heading_order=latest_tax_deduction_heading_order,
                oldest_taxable_addition_order=oldest_taxable_addition_order,
                oldest_non_taxable_deduction_order=oldest_non_taxable_deduction_order,
            )
            if not is_valid:
                raise ValidationError({'non_field_errors': [error_message]})

        if shift_type == 'top_to_bottom':
            upward_displaced_headings = PackageHeading.objects.filter(
                order__gt=from_obj_order,
                order__lte=to_obj_order,
                package_id=package_id
            )

            for upward_displaced_heading in upward_displaced_headings:
                upward_displaced_heading.order = upward_displaced_heading.order - 1
                is_valid = upward_displaced_heading.rule_is_valid()[0]
                if not is_valid:
                    break

            if is_valid:
                downward_displaced_heading = PackageHeading.objects.get(
                    order=from_obj_order,
                    package_id=package_id
                )
                downward_displaced_heading.order = to_obj_order
                is_valid = downward_displaced_heading.rule_is_valid()[0]

            if is_valid:
                PackageHeading.objects.filter(
                    package_id=package_id,
                    order__gte=from_obj_order,
                    order__lte=to_obj_order).update(
                    order=Case(
                        When(order=from_obj_order, then=int(to_obj_order)),
                        default=F('order') - 1,
                        output_field=IntegerField()
                    )
                )
        else:
            upward_displaced_heading = PackageHeading.objects.get(
                order=from_obj_order,
                package_id=package_id
            )
            upward_displaced_heading.order = to_obj_order
            is_valid = upward_displaced_heading.rule_is_valid()[0]
            if is_valid:
                PackageHeading.objects.filter(
                    package_id=package_id,
                    order__gte=to_obj_order,
                    order__lte=from_obj_order).update(
                    order=Case(
                        When(order=from_obj_order, then=to_obj_order),
                        default=F('order') + 1,
                        output_field=IntegerField()
                    )
                )

        new_orders = PackageHeading.objects.filter(
            package_id=package_id
        ).order_by('order').values_list('order', flat=True)

        if is_valid:
            return Response(
                {
                    'success': True,
                    'new_orders': new_orders
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    'success': False
                },
                status=status.HTTP_200_OK
            )

    @action(detail=False, methods=['POST'], serializer_class=DragHeadingSerializer)
    def drag_heading(self, request):
        raise_validation_error_if_payroll_in_generated_or_processing_state(
            organization=self.get_organization()
        )
        context = self.get_serializer_context()
        context['organization'] = self.get_organization()
        context['auto_resolve'] = self.request.query_params.get("auto_resolve", "false") == "true"
        serializer = self.serializer_class(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        raise_validation_error_if_payroll_in_generated_or_processing_state(
            organization=self.get_organization()
        )
        instance = self.get_object()
        validate_if_package_heading_updated_after_payroll_generated_previously(instance.package)
        if not instance.makes_package_heading_dependencies.exists():
            return super().destroy(request, *args, **kwargs)
        else:
            return Response(
                {
                    'error_message': 'Cannot delete package heading that makes dependency'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def get_organization(self):
        return get_object_or_404(
            Organization.objects.filter(
                id__in=self.request.user.switchable_organizations_pks
            ),
            slug=self.request.query_params.get(
                'package__organization__slug'
            )
        )


class SalaryHoldingAPIViewSet(OrganizationMixin, OrganizationCommonsMixin, ListCreateRetrieveViewSetMixin):
    queryset = SalaryHolding.objects.all()
    permission_classes = [HoldPayrollPermission]
    serializer_class = SalaryHoldingSerializer
    filter_backends = (FilterMapBackend, OrderingFilterMap)

    filter_map = {
        'employee': 'employee',
        'end_date': 'from_date__date__lte'
    }
    ordering_fields_map = {
        'employee': ('employee__first_name',
                     'employee__middle_name',
                     'employee__last_name',),
        'from_date': 'from_date',
        'to_date': 'to_date'
    }

    def get_queryset(self):
        return self.queryset.filter(employee__detail__organization=self.get_organization()).annotate(
            to_date_patched=Case(
                When(
                    to_date__isnull=True,
                    then=timezone.now()
                ),
                default=F('to_date'),
                output_field=models.DateTimeField()
            )
        )

    def filter_queryset(self, queryset):
        queryset = apply_filters(
            self.request.query_params,
            {
                'start_date': 'to_date_patched__date__gte',
            },
            queryset
        )
        queryset = super().filter_queryset(queryset)
        return queryset

    @action(detail=True, methods=['POST'], serializer_class=SalaryHoldingReleaseSerializer)
    def release(self, *args, **kwargs):
        holding = self.get_object()
        if holding.released:
            return Response({"non_field_errors": ["Hold is already released"]}, 400)

        ser = self.get_serializer(holding, self.request.data)
        ser.is_valid(raise_exception=True)

        holding.release_remarks = ser.validated_data.get('release_remarks')
        holding.released = True
        holding.to_date = timezone.now()
        holding.save()

        return Response(SalaryHoldingSerializer(holding).data)


class EmployeeAPIViewSet(InputChoiceMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Employee.objects.all().current()
    serializer_class = EmployeeSerializer
    choice_fields = ('id', 'label')
    filter_fields = ['detail__organization__slug']
    permission_classes = [GeneratePayrollPermission]

    def get_organization(self):
        return get_object_or_404(
            Organization.objects.filter(
                id__in=self.request.user.switchable_organizations_pks
            ),
            slug=self.request.query_params.get('detail__organization__slug')
        )


class ReportRowRecordAPIViewSet(viewsets.ModelViewSet):
    queryset = ReportRowRecord.objects.all()
    permission_classes = [ViewPayrollReportPermission]
    serializer_class = ReportRowRecordSerializer
    # choice_fields = ('id', 'label')
    filter_fields = []

    def get_organization(self):
        return get_object_or_404(
            Organization.objects.filter(
                id__in=self.request.user.switchable_organizations_pks
            ),
            slug=self.request.query_params.get(
                'employee_payroll__employee__detail__organization__slug'
            )
        )


class YearlyHeadingDetailAPIViewSet(
    OrganizationMixin,
    OrganizationCommonsMixin,
    viewsets.ModelViewSet
):
    queryset = YearlyHeadingDetail.objects.all()
    organization_field = 'heading__organization'
    serializer_class = YearlyHeadingDetailSerializer
    filter_backends = (
        DjangoFilterBackend,
    )
    permission_classes = [EmployeePayrollViewPermission]
    # allowed_to=[GENERATE_PAYROLL_PERMISSION],
    # limit_read_to=[GENERATE_PAYROLL_PERMISSION, PAYROLL_REPORT_PERMISSION]

    filter_fields = [
        'fiscal_year_id',
        'heading_id'
    ]


class RebateSettingAPIViewSet(
    OrganizationMixin,
    OrganizationCommonsMixin,
    viewsets.ModelViewSet
):
    queryset = RebateSetting.objects.all()
    serializer_class = RebateSettingSerializer
    filter_backends = (
        FilterMapBackend,
        OrderingFilterMap
    )
    ordering_fields_map = {
        "title": "title"
    }
    filter_map = {
        "archived": "is_archived"
    }

    permission_classes = [EmployeePayrollViewPermission]

    def check_permissions(self, request):
        if self.mode == "user":
            return True
        super().check_permissions(request)

    def get_queryset(self):
        return super().get_queryset().filter(
            organization=self.get_organization()
        )

    @property
    def mode(self):
        mode = self.request.query_params.get('as')
        if mode in ["supervisor", "hr"]:
            return mode
        return "user"

    @property
    def is_hr(self):
        if self.mode == "hr" and validate_permissions(
            self.request.user.get_hrs_permissions(self.organization),
            GENERATE_PAYROLL_PERMISSION, PAYROLL_REPORT_PERMISSION
        ):
            return True
        return False

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["user_id"] = self.request.user.id
        ctx["fiscal_year"] = self.request.query_params.get('fiscal_year')
        if self.is_hr:
            ctx["user_id"] = self.request.query_params.get('user_id')
        return ctx

    def destroy(self, request, *args, **kwargs):
        title = self.get_object().title
        if is_rebate_type_used_in_heading(self.get_organization(), title):
            raise ValidationError({
                "non_field_errors": ["This rebate is already used in payroll heading."]
            })

        return super().destroy(request, *args, **kwargs)


class EmployeeUserExperiencePackageListViewSet(
    PastUserGenericFilterMixin,
    OrganizationMixin,
    ListRetrieveViewSetMixin,
    BackgroundExcelExportMixin
):
    """
    ViewSet to list the users with their assigned experiences and attached
    result areas.
    """
    queryset = Employee.objects.all().order_by('first_name')
    serializer_class = UserPackageListSerializer
    permission_classes = [ViewEmployeeExperiencePackage]
    filter_backends = (
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
        FilterMapBackend,
    )
    filter_map={
        'username': 'username',
    }

    search_fields = (
        'first_name', 'middle_name', 'last_name', 'username'
    )
    export_type = 'Assign Package Export'
    export_fields = {
        'Name': 'full_name',
        'User Name': 'username',
        'Current Working Experience': 'working_experience',
        'Total Experiences': 'total_experience',
        'Associate Package': 'current_package',
        'Active From Date': 'current_package_active_date'
    }

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        queryset = super().get_queryset()
        if user_id:
            queryset = queryset.filter(id=int(user_id))
        return queryset.filter(
            detail__organization__slug=self.kwargs['organization_slug']
        ).select_related('detail', 'detail__organization', 'detail__division',
                         'detail__job_title', 'detail__employment_level',
                         'detail__employment_status') \
            .prefetch_related(
            Prefetch(
                'user_experiences',
                queryset=UserExperience.objects.all()
                .select_related('organization', 'job_title')
                .prefetch_related('user_result_areas')
            )
        )

    @staticmethod
    def prepare_export_object(obj, **kwargs):
        setattr(obj, 'total_experience', obj.user_experiences.count())
        latest_experience = obj.user_experiences.first()
        package_slot = UserExperiencePackageSlot.objects.filter(
            user_experience__user=obj, user_experience=latest_experience).order_by(
            '-active_from_date').first()

        if package_slot:
            setattr(obj, 'current_package', nested_getattr(package_slot, 'package.name'))
            setattr(obj, 'current_package_active_date',
                    nested_getattr(package_slot, 'active_from_date'))

        if latest_experience.is_current:
            setattr(obj, 'working_experience',
                    nested_getattr(latest_experience, 'job_title.title'))
        return obj

class OrganizationOverviewConfigAPIViewSet(viewsets.ModelViewSet):
    lookup_field = 'organization__slug'
    queryset = OverviewConfig.objects.all()
    serializer_class = OrganizationOverviewConfigSerializer
    filter_fields = ['organization__slug']
    permission_classes = [PayrollSettingsPermission]

    def get_object(self):
        org = self.get_organization()
        try:
            obj = OverviewConfig.objects.get(
                organization=org
            )
        except OverviewConfig.DoesNotExist:
            obj = OverviewConfig.objects.create(
                organization=org
            )
        return obj

    def get_organization(self):
        return get_object_or_404(
            Organization.objects.filter(
                id__in=self.request.user.switchable_organizations_pks
            ),
            slug=self.kwargs.get(self.lookup_field)
        )


class OrganizationPayrollConfigAPIViewSet(RetrieveUpdateViewSetMixin):
    """
    Configure payroll for organization

    put data

        {
            "start_fiscal_year": fiscal_year_id,
            "include_holiday_offday_in_calculation": false,
            "enable_unit_of_work": true,
        }
    """
    lookup_field = 'organization__slug'
    queryset = OrganizationPayrollConfig.objects.all()
    serializer_class = OrganizationPayrollConfigUpdateSerializer
    filter_fields = ['organization__slug']
    http_method_names = [u'get', u'patch']
    permission_classes = [PayrollSettingsPermission]

    def get_object(self):
        org = self.get_organization()
        try:
            obj = OrganizationPayrollConfig.objects.get(
                organization=org
            )
        except OrganizationPayrollConfig.DoesNotExist:
            obj = OrganizationPayrollConfig.objects.create(
                organization=org
            )
        return obj

    def get_organization(self):
        return get_object_or_404(
            Organization.objects.filter(
                id__in=self.request.user.switchable_organizations_pks
            ),
            slug=self.kwargs.get(self.lookup_field)
        )


class ExternalTaxDiscountAPIViewSet(OrganizationMixin,
                                    OrganizationCommonsMixin,
                                    viewsets.ModelViewSet):
    queryset = ExternalTaxDiscount.objects.all()
    serializer_class = ExternalTaxDiscountSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilterMap)
    permission_classes = [PayrollRebatePermission]
    filter_fields = ["employee", "fiscal_year"]
    search_fields = (
        'employee__first_name',
        'employee__middle_name',
        'employee__last_name',
    )
    ordering_fields_map = {
        'employee': ('employee__first_name',
                     'employee__middle_name',
                     'employee__last_name',),
        'title': 'title',
        'amount': 'amount',
        'modified_at': 'modified_at',
        'created_at': 'created_at'
    }

    def get_queryset(self):
        return self.queryset.filter(
            employee__detail__organization=self.get_organization()
        )

    def update(self, request, *args, **kwargs):
        self.validate_can_act()
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self.validate_can_act()
        return super().destroy(request, *args, **kwargs)

    def validate_can_act(self):
        organization = self.get_organization()

        # get active fiscal year for the organization
        fy = FiscalYear.objects.active_for_date(organization=organization)

        obj = self.get_object()

        if obj.fiscal_year != fy:
            raise ValidationError({
                "non_field_error": ["Can only update/delete records for current fiscal year."]
            })


@api_view()
def show_generated_payslip(request, organization_slug):
    organization = get_object_or_404(Organization, slug=organization_slug)
    payroll_config = getattr(organization, 'organization_payroll_config', None)
    show_generated_payslip = False
    if payroll_config:
        show_generated_payslip = payroll_config.show_generated_payslip

    return Response({"show_generated_payslip":  show_generated_payslip})


@api_view()
def get_payroll_generated_employee_count(request):
    from django.core.cache import cache
    return Response({
        "generated_employee_count": cache.get('payroll_generated_employee_count') or 0,
        "total_employee_count": cache.get('total_number_of_payroll_to_be_generated') or 0,
        "current_employee_name": cache.get("payroll_generated_employee_name") or "N/A"
    })
