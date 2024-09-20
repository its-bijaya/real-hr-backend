from django.db.models import Count, Q
from django.shortcuts import HttpResponse, get_list_or_404
from openpyxl import Workbook
from openpyxl.writer.excel import save_virtual_workbook
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from irhrs.core.constants.organization import PAYROLL_ACKNOWLEDGED_BY_USER
from irhrs.core.utils.common_utils import get_users_list_from_permissions
from irhrs.core.utils.email import send_email_as_per_settings
from irhrs.payroll.models.payroll import CONFIRMED, PAYSLIP_GENERATED

from irhrs.core.mixins.viewset_mixins import RetrieveViewSetMixin, UserMixin, ListRetrieveViewSetMixin, \
    OrganizationMixin
from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.hris.api.v1.permissions import EmployeePayrollViewPermission
from irhrs.notification.utils import notify_organization
from irhrs.organization.models import FiscalYear, Organization
from irhrs.payroll.api.v1.serializers.payslip import (
    PaySlipSerializer,
    PayslipReportSettingSerializer,
    YTDSerializer,
    PaySlipAcknowledgeSerializer,
    PaySlipResponseSerializer,
    PaySlipTaxDetailsSerializer,
    MonthlyTaxReportSerializer,
)
from irhrs.payroll.models import EmployeePayroll, ReportRowRecord, PAYSLIP_ACKNOWLEDGEMENT_PENDING, \
    PAYSLIP_ACKNOWLEDGED, OrganizationPayrollConfig, PayrollApprovalSetting
from irhrs.payroll.models.payslip_report_setting import PayslipReportSetting
from irhrs.payroll.utils.employee_payroll import get_employee_payrolls_via_settings
from irhrs.payroll.utils.payslip_excel import (
    ExcelPayslip,
    ExcelTaxReport
)
from irhrs.permission.constants.permissions import PAYROLL_REPORT_PERMISSION, \
    GENERATE_PAYROLL_PERMISSION, HAS_PERMISSION_FROM_METHOD
from irhrs.permission.constants.permissions.hrs_permissions import CAN_CREATE_PAYSLIP_REPORT_SETTING_PERMISSION
from irhrs.permission.permission_classes import permission_factory


def get_payslip_acknowledge_frontend_url(organization: Organization) -> str:
    return f"/admin/{organization.slug}/payroll/response"


class PayslipAPIViewSet(UserMixin, RetrieveViewSetMixin):
    queryset = EmployeePayroll.objects.all()
    lookup_url_kwarg = 'payroll_id'
    serializer_class = PaySlipSerializer
    permission_classes = [
        permission_factory.build_permission(
            "PayslipPermission",
            allowed_to=[HAS_PERMISSION_FROM_METHOD]
        )
    ]

    def get_organization(self):
        org_slug = self.request.query_params.get('organization_slug')
        if org_slug:
            return Organization.objects.filter(slug=org_slug).first()
        return self.request.user.detail.organization

    @property
    def mode(self):
        if self.request.query_params.get('as') == 'hr':
            return 'hr'
        if self.request.query_params.get('as') == 'approver':
            return 'approver'
        return 'user'

    def has_user_permission(self):
        if self.mode == 'hr':
            org_slug = self.request.query_params.get('organization_slug')
            if not (org_slug and self.get_organization()):
                return False
            return validate_permissions(
                    self.request.user.get_hrs_permissions(
                        self.get_organization()
                    ),
                    GENERATE_PAYROLL_PERMISSION,
                    PAYROLL_REPORT_PERMISSION
                )
        return True

    def get_queryset(self):
        organization = self.get_organization()
        qs = super().get_queryset().filter(
            employee__detail__organization=organization
        )
        approver_id = self.request.user.id
        approver_list = PayrollApprovalSetting.objects.all().values_list('user', flat=True)
        if self.mode == 'hr' or self.mode == 'approver' and approver_id in approver_list:
            return qs

        qs = qs.filter(employee=self.request.user)
        return get_employee_payrolls_via_settings(qs, organization)

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())

        user = self.user
        payroll_id = self.kwargs.get('payroll_id')

        obj = get_object_or_404(
            queryset=queryset,
            employee=user,
            payroll_id=payroll_id
        )

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def get_report_row_for_ytd(self, heading_id):
        employee_payroll = self.get_object()
        return get_object_or_404(
            employee_payroll.report_rows.all(),
            heading_id=heading_id,
            heading__year_to_date=True
        )

    def retrieve(self, request, *args, **kwargs):
        res = super().retrieve(request, *args, **kwargs)
        payroll_config=OrganizationPayrollConfig.objects.filter(
            organization=self.get_organization()
        ).first()
        if not payroll_config:
            return res

        show_zero_amount_row_records = payroll_config.display_heading_with_zero_value
        if show_zero_amount_row_records:
            return res

        res.data['report_rows'] = list(filter(lambda x : x['amount'] != 0, res.data["report_rows"]))
        return res

    @action(detail=True, methods=['GET'], url_path=r'ytd/(?P<heading_id>\d+)', serializer_class=YTDSerializer)
    def ytd(self, request, heading_id, **kwargs):
        report_row = self.get_report_row_for_ytd(heading_id)
        organization = self.user.detail.organization

        fiscal_year = FiscalYear.objects.active_for_date(
            organization,
            report_row.to_date
        )

        queryset = ReportRowRecord.objects.filter(
                employee_payroll__employee=self.user,
                from_date__gte=fiscal_year.applicable_from,
                to_date__lte=report_row.to_date,
                heading=report_row.heading
        ).order_by('-from_date')

        page = self.paginate_queryset(queryset)
        return self.get_paginated_response(self.serializer_class(page, many=True).data)

    @action(detail=True, methods=['POST'], serializer_class=PaySlipAcknowledgeSerializer)
    def acknowledge(self, request, **kwargs):
        employee_payroll = self.get_object()
        if self.mode == 'hr' or self.request.user != employee_payroll.employee:
            self.permission_denied(request=request, message="Only employee can acknowledge payslip.")

        serializer = self.get_serializer(self.get_object(), request.data)
        serializer.is_valid(raise_exception=True)
        employee_payroll = serializer.save()

        organization = employee_payroll.payroll.organization

        notification_text = f"{self.request.user.full_name} acknowledged " \
                            f"payslip of payroll " \
                            f"({employee_payroll.payroll.from_date} - {employee_payroll.payroll.to_date})"

        notify_organization(
            actor=self.request.user,
            action=employee_payroll,
            text=notification_text,
            organization=organization,
            url=get_payslip_acknowledge_frontend_url(organization),
            permissions=[
                GENERATE_PAYROLL_PERMISSION,
                PAYROLL_REPORT_PERMISSION
            ]
        )
        hrs = get_users_list_from_permissions(
            permission_list=[
                GENERATE_PAYROLL_PERMISSION,
                PAYROLL_REPORT_PERMISSION
            ],
            organization=organization
        )
        send_email_as_per_settings(
            recipients=hrs,
            subject="Payslip acknowledged.",
            email_text=notification_text,
            email_type=PAYROLL_ACKNOWLEDGED_BY_USER
        )

        return Response(serializer.data)

    @action(detail=True, methods=['GET'], serializer_class=PaySlipTaxDetailsSerializer, url_path='tax-detail')
    def tax_detail(self, *args, **kwargs):
        return self.retrieve(*args, **kwargs)

    @action(detail=True, methods=['GET'], serializer_class=MonthlyTaxReportSerializer, url_path='tax-report')
    def monthly_tax_report(self, request, *args, **kwargs):
        employee_payroll = self.get_object()
        payroll_config=OrganizationPayrollConfig.objects.filter(
            organization=self.get_organization()
        ).first()
        show_zero_amount_row_records = False
        if payroll_config:
            show_zero_amount_row_records = payroll_config.display_heading_with_zero_value

        context = {
            'show_heading_with_zero_value' : show_zero_amount_row_records
        }
        serializer = self.serializer_class(employee_payroll,context=context)
        try:
            return Response(serializer.data)
        except NotImplementedError as err:
            return Response(
                dict(
                    non_field_errors=err.args[0]
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, url_path="payslip-excel")
    def payslip_excel(self, request, *args, **kwargs):
        employee_payroll = self.get_object()
        data = PaySlipSerializer(employee_payroll).data


        payroll_config = OrganizationPayrollConfig.objects.filter(
            organization=self.get_organization()
        ).first()
        template = payroll_config and payroll_config.payslip_template

        workbook = ExcelPayslip(data, template=template).create_workbook()

        response = HttpResponse(
            save_virtual_workbook(workbook),
            content_type='application/vnd.ms-excel'
        )
        response['Content-Disposition'] = 'attachment; filename="payslip.xlsx"'
        return response

    @action(detail=True, url_path="tax-report-excel")
    def tax_report_excel(self, request, *args, **kwargs):
        employee_payroll = self.get_object()
        payroll_config = OrganizationPayrollConfig.objects.filter(
            organization=self.get_organization()
        ).first()
        show_zero_amount_row_records = False
        if payroll_config:
            show_zero_amount_row_records = payroll_config.display_heading_with_zero_value

        context = {
            'show_heading_with_zero_value': show_zero_amount_row_records
        }
        data = MonthlyTaxReportSerializer(employee_payroll, context=context).data

        workbook = ExcelTaxReport(data).create_workbook()

        response = HttpResponse(
            save_virtual_workbook(workbook),
            content_type='application/vnd.ms-excel'
        )
        response['Content-Disposition'] = 'attachment; filename="tax_report.xlsx"'
        return response



class PaySlipResponseViewSet(OrganizationMixin, ListRetrieveViewSetMixin):
    """
    HR View of PaySlip Response

    filter:

    DATE Filter:
        start_date, end_date

    for fiscal year and month pass applicable_from and applicable_to
    of fiscal year or month selected
    """
    serializer_class = PaySlipResponseSerializer
    queryset = EmployeePayroll.objects.annotate(
        total_comment=Count('employee_payroll_comments')
    ).order_by('-total_comment')
    filter_backends = (FilterMapBackend, SearchFilter, OrderingFilterMap)
    permission_classes = [EmployeePayrollViewPermission]

    filter_map = {
        "employee": "employee",
        "start_date": "payroll__to_date__gte",
        "end_date": "payroll__from_date__lte",
        "acknowledgement_status": "acknowledgement_status"
    }

    search_fields = (
        'employee__first_name',
        'employee__middle_name',
        'employee__last_name',
    )

    ordering_fields_map = {
        'employee': ('employee__first_name',
                     'employee__middle_name',
                     'employee__last_name',),
        'acknowledged_at': 'acknowledged_at',
        'acknowledgement_status': 'acknowledgement_status',
        'total_comment': 'total_comment'
    }

    def get_queryset(self):
        organization = self.get_organization()
        qs =  super().get_queryset().filter(
            employee__detail__organization=organization
        )
        return get_employee_payrolls_via_settings(qs, organization)

    def get_counts(self):
        # Do not aggregate if filter by acknowledgement_status
        self.filter_map = {
            "employee": "employee",
            "start_date": "payroll__to_date__gte",
            "end_date": "payroll__from_date__lte"
        }
        return self.filter_queryset(self.get_queryset()).aggregate(
            total=Count('id', distinct=True),
            generated=Count(
                'id',
                filter=Q(acknowledgement_status=PAYSLIP_GENERATED)
            ),
            pending=Count(
                'id',
                filter=Q(acknowledgement_status=PAYSLIP_ACKNOWLEDGEMENT_PENDING),
                distinct=True
            ),
            acknowledged=Count(
                'id',
                filter=Q(acknowledgement_status=PAYSLIP_ACKNOWLEDGED),
                distinct=True
            )
        )

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data.update({
            "counts": self.get_counts(),
            "payslip_template": OrganizationPayrollConfig.get_payslip_template(self.organization)
        })
        return response


class PayslipReportSettingViewSet(viewsets.ViewSet, OrganizationMixin):

    permission_classes = [
        permission_factory.build_permission(
            "PayslipReportPermission",
            limit_write_to=[CAN_CREATE_PAYSLIP_REPORT_SETTING_PERMISSION]
        )
    ]

    def list(self,request, **kwargs):
        context = {
            "organization": self.organization,
            "request": request
        }
        queryset = PayslipReportSetting.objects.filter(organization=self.organization)
        serializer = PayslipReportSettingSerializer(queryset, many=True, context=context)
        return Response(serializer.data)

    def create(self, request, **kwargs):
        PayslipReportSetting.objects.filter(organization=self.organization).delete()
        context = {
            "organization": self.organization,
            "request": request
        }
        serializer = PayslipReportSettingSerializer(
            data=request.data,
            context=context,
            many=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
