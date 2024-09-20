from django.utils.functional import cached_property
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ValidationError

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.payroll.models import EmployeePayroll
from irhrs.users.api.v1.serializers.thin_serializers import UserSupervisorDivisionSerializer


class SalaryDifferenceSheetSerializer(DynamicFieldsModelSerializer):
    employee = UserSupervisorDivisionSerializer(exclude_fields=('supervisor', 'is_current', 'is_online', 'last_online'))
    early_payroll = SerializerMethodField()
    late_payroll = SerializerMethodField()
    difference = SerializerMethodField()

    class Meta:
        model = EmployeePayroll
        fields = ['employee', 'early_payroll', 'late_payroll', 'difference']

    def get_payroll_amounts(self, obj, payroll_ids):
        heading_amounts = {}
        heading_setting_ids = self.context.get('heading_setting_ids')
        payroll_employees = EmployeePayroll.objects.filter(payroll_id__in=payroll_ids,
                                                           employee=obj.employee)

        for payroll_employee in payroll_employees:
            for row in payroll_employee.report_rows.filter(heading_id__in=heading_setting_ids):
                row_heading_id = str(row.heading_id)
                if row_heading_id in heading_amounts:
                    heading_amounts[row_heading_id] = heading_amounts[row_heading_id] + row.amount
                else:
                    heading_amounts[row_heading_id] = row.amount
        return heading_amounts

    def get_early_payroll(self, obj):
        early_payroll_ids = self.context.get('early_payroll_ids')
        if not early_payroll_ids:
            raise ValidationError("No Early payroll")
        return self.get_payroll_amounts(obj, early_payroll_ids)

    def get_late_payroll(self, obj):
        late_payroll_ids = self.context.get('late_payroll_ids')
        if not late_payroll_ids:
            raise ValidationError("No late payroll")
        return self.get_payroll_amounts(obj, late_payroll_ids)

    def get_difference(self, obj):
        heading_setting_ids = [str(key) for key in self.context.get('heading_setting_ids')]
        payroll_difference = {
            key: self.get_early_payroll(obj).get(key, 0) - self.get_late_payroll(obj).get(key, 0) for key in heading_setting_ids
        }
        return payroll_difference
