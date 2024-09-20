from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from openpyxl.writer.excel import save_virtual_workbook
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter

from irhrs.core.constants.organization import GLOBAL
from irhrs.core.mixins.viewset_mixins import ListViewSetMixin, OrganizationMixin
from irhrs.core.utils import nested_getattr
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.export.mixins.export import BackgroundExcelExportMixin
from irhrs.export.utils.export import SalaryDifferneceExport
from irhrs.hris.api.v1.permissions import EmployeePayrollViewPermission
from irhrs.organization.models import FiscalYearMonth
from irhrs.payroll.api.v1.serializers.salary_difference_sheet import \
    SalaryDifferenceSheetSerializer
from irhrs.payroll.models import EmployeePayroll, PayrollCollectionDetailReportSetting, \
    PayrollDifferenceDetailReportSetting, Payroll


class SalaryDifferenceSheet(OrganizationMixin, ListViewSetMixin, BackgroundExcelExportMixin):
    queryset = EmployeePayroll.objects.all()
    permission_classes = [EmployeePayrollViewPermission]
    serializer_class = SalaryDifferenceSheetSerializer
    filter_backends = [SearchFilter, OrderingFilterMap, FilterMapBackend]
    search_fields = ('employee__first_name', 'employee__middle_name', 'employee__last_name', 'employee__username')
    filter_map = {
        'branch': 'employee__detail__branch__slug',
        'division': 'employee__detail__division__slug',
        'job_title': 'employee__detail__job_title__slug',
        'employment_level': 'employee__detail__employment_level__slug',
        'employment_type': 'employee__detail__employment_status__slug',
    }
    export_type = 'Salary Difference sheet'
    # notification_permissions = []
    @classmethod
    def get_exported_file_content(cls, data, title, columns, extra_content,
                                  description=None, **kwargs):
        organization = extra_content.get('organization')
        wb = SalaryDifferneceExport.process(
            data,
            title=title,
            columns=columns,
            description=description,
            prepare_export_object=cls.prepare_export_object,
            prepare_export_object_context=extra_content.get('prepare_export_object_context'),
            freeze_first_column=cls.export_freeze_first_column,
            organization=organization
        )
        return ContentFile(save_virtual_workbook(wb))
    def get_payroll_amounts(self, obj, payroll_ids):
        heading_amounts = {}
        heading_setting_ids = self.get_heading_setting_ids or [178]
        payroll_employees = EmployeePayroll.objects.filter(payroll_id__in=payroll_ids,
                                                           employee=obj.employee)

        for payroll_employee in payroll_employees:
            for row in payroll_employee.report_rows.filter(heading_id__in=heading_setting_ids):
                row_heading_name = nested_getattr(row, 'heading.name')
                if row_heading_name in heading_amounts:
                    heading_amounts[row_heading_name] = heading_amounts[row_heading_name] + row.amount
                else:
                    heading_amounts[row_heading_name] = row.amount
        return heading_amounts


    def get_export_fields(self):
        fields_map ={
                "Name": "employee.full_name",
                "Username": "employee.username",
                "Job Title": "employee.job_title",
                "Division": "employee.division.name",
                "Branch": "employee.branch.name",
            }
        for title in ['early_payroll', 'late_payroll', 'difference']:
            for heading_id, name in self.get_heading_setting_id_and_name:
                fields_map[f'{title} {name}'] = f"{title}.{heading_id}"

        return fields_map

    def get_extra_export_data(self):
        data = super().get_extra_export_data()
        data['prepare_export_object_context'] = {'heading_setting_ids': self.get_heading_setting_ids,
                                      'early_payroll_ids': self.get_early_payroll_ids,
                                      'late_payroll_ids': self.get_late_payroll_ids,
                                      'salary_months_info': [
                                            self.get_early_payroll_months,
                                            self.get_late_payroll_months, 'Difference']
        }
        return data

    @staticmethod
    def prepare_export_object(obj, **kwargs):
        ser_data = SalaryDifferenceSheetSerializer(obj, context=kwargs).data
        return ser_data

    @property
    def get_early_payroll_ids(self):
        initial_ids = self.request.query_params.get('initial', [])
        if not len(initial_ids):
            raise ValidationError("Missing early payroll")
        return [value for value in initial_ids.split(",") if value.isdigit()]

    @property
    def get_late_payroll_ids(self):
        late_ids = self.request.query_params.get('late', [])
        if not len(late_ids):
            raise ValidationError("Missing late payroll")
        return [value for value in late_ids.split(",") if value.isdigit()]

    @staticmethod
    def get_payroll_months(payroll_month_id):
        payroll = get_object_or_404(Payroll, pk=payroll_month_id)
        if payroll:
            from_date = payroll.from_date
            to_date = payroll.to_date
            fiscal_month = FiscalYearMonth.objects.filter(start_at__lte=from_date,
                                                          end_at__gte=to_date,
                                                          fiscal_year__category=GLOBAL
                                                          ).first()
            return f'{fiscal_month.display_name} - {fiscal_month.fiscal_year.name}'
        return

    @property
    def get_early_payroll_months(self):
        return self.get_payroll_months(self.get_early_payroll_ids[0])

    @property
    def get_late_payroll_months(self):
        return self.get_payroll_months(self.get_late_payroll_ids[0])

    @property
    def get_combined_payroll_ids(self):
        return self.get_early_payroll_ids + self.get_late_payroll_ids

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            employee__detail__organization=self.organization
        )
        queryset = queryset.filter(payroll__in=self.get_combined_payroll_ids).distinct('employee')
        user_ids = self.request.query_params.get('user_ids')
        user_ids = [value for value in user_ids.split(",") if value.isdigit()]
        if user_ids:
            return queryset.filter(employee__id__in=user_ids)
        return queryset

    @property
    def get_heading_setting_ids(self):
        fil = {}
        heading_setting = PayrollDifferenceDetailReportSetting.objects.filter(
            organization=self.organization).first()
        if heading_setting:
            heading_id__in = heading_setting.headings.values_list('id', flat=True)
            return heading_id__in
        return fil

    @property
    def get_heading_setting_id_and_name(self):
        fil = []
        heading_setting = PayrollDifferenceDetailReportSetting.objects.filter(
            organization=self.organization).first()
        if heading_setting:
            heading_id__in = heading_setting.headings.values_list('id', 'name')
            return heading_id__in
        return fil

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['heading_setting_ids'] = self.get_heading_setting_ids
        context['early_payroll_ids'] = self.get_early_payroll_ids
        context['late_payroll_ids'] = self.get_late_payroll_ids
        return context
