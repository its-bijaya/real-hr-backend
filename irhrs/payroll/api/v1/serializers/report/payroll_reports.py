from dateutil.relativedelta import relativedelta
from django.db.models import Sum, Q
from django.utils.functional import cached_property
from rest_framework import serializers

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils import nested_getattr
from irhrs.core.utils.common import get_today
from irhrs.organization.api.v1.serializers.branch import OrganizationBranchSerializer
from irhrs.payroll.models import EmployeePayroll, ReportRowRecord, SSFReportSetting, CONFIRMED, \
    DisbursementReportSetting, BackdatedCalculation, TaxReportSetting, GENERATED
from irhrs.payroll.utils.headings import get_heading_details
from irhrs.users.api.v1.serializers.thin_serializers import \
    UserFieldThinSerializer, UserThickSerializer


class TaxReportSerializer(DynamicFieldsModelSerializer):
    t_date = serializers.SerializerMethodField()
    employee = UserThickSerializer(
        fields=['id', 'full_name', 'username', 'profile_picture', 'cover_picture', 'organization', 'is_current', 'job_title']
    )
    date_type = serializers.ReadOnlyField(default="AD")
    pan_number = serializers.SerializerMethodField()
    heading_amounts = serializers.SerializerMethodField()

    class Meta:
        model = EmployeePayroll
        fields = [
            "id",
            "employee",
            "pan_number",
            "t_date",
            "date_type",
            "tds_type",
            "heading_amounts"
        ]

    @staticmethod
    def get_t_date(obj):
        return obj.payroll.approved_date.date() if obj.payroll.approved_date else None

    def get_heading_amounts(self, obj):
        tax_headings_id = TaxReportSetting.objects.filter(
            organization = self.context.get('organization')
        ).values_list('headings', flat=True)
        row_report_records = ReportRowRecord.objects.filter(
            employee_payroll=obj,
            heading__in=tax_headings_id,
            employee_payroll__payroll__status__in=[GENERATED, CONFIRMED]
        )
        res = dict()
        for row_report_record in row_report_records:
            heading_id = row_report_record.heading.id
            res[heading_id] = row_report_record.amount
        return res

    @staticmethod
    def get_pan_number(obj):
        return nested_getattr(obj.employee, 'legal_info.pan_number', default="-")

    @staticmethod
    def get_heading_amount(employee_payroll, heading):
        record = ReportRowRecord.objects.filter(
            employee_payroll=employee_payroll,
            heading=heading
        ).first()
        return getattr(record, 'amount', None)


class PFReportSerializer(DynamicFieldsModelSerializer):
    employee = UserThickSerializer(
        fields=['id', 'full_name', 'username', 'profile_picture', 'cover_picture', 'organization', 'is_current', 'job_title']
    )
    designation = serializers.ReadOnlyField(
        source='user_experience_package_slot.user_experience.job_title.title', allow_null=True)
    pf_number = serializers.SerializerMethodField()
    total_fund_deducted = serializers.SerializerMethodField()
    deducted_from_employee = serializers.SerializerMethodField()
    contribution_from_company = serializers.SerializerMethodField()

    class Meta:
        model = EmployeePayroll
        fields = [
            "id",
            "employee",
            "pf_number",
            "designation",
            "total_fund_deducted",
            "deducted_from_employee",
            "contribution_from_company"
        ]

    def __init__(self, instance=None, *args, **kwargs):
        super().__init__(instance, *args, **kwargs)
        self.obj = None
        self.amounts = {}

    @staticmethod
    def get_pf_number(obj):
        return nested_getattr(obj.employee, 'legal_info.pf_number', default=None)

    def get_total_fund_deducted(self, obj):
        self.obj = obj
        return (self.pf_amounts['addition'] or 0.0) + (self.pf_amounts['deduction'] or 0.0)

    def get_deducted_from_employee(self, obj):
        self.obj = obj
        return self.pf_amounts['deduction']

    def get_contribution_from_company(self, obj):
        self.obj = obj
        return self.pf_amounts['addition']

    @property
    def pf_amounts(self):
        # this method is placed here just to cache results
        # for calculating total amount

        if self.obj.id in self.amounts:
            return self.amounts[self.obj.id]

        amount = self.get_pf_amounts(self.obj)
        self.amounts[self.obj.id] = amount

        # could not use instance as it was list of list serializer
        return amount

    @staticmethod
    def get_pf_amounts(obj):
        return ReportRowRecord.objects.filter(
            employee_payroll=obj,
            heading__payroll_setting_type='Provident Fund'
        ).aggregate(
            addition=Sum('amount', filter=Q(heading__type='Addition')),
            deduction=Sum('amount', filter=Q(heading__type='Deduction'))
        )


class SSFReportSerializer(DynamicFieldsModelSerializer):
    employee = UserThickSerializer(
        fields=['id', 'full_name', 'username', 'profile_picture', 'organization', 'is_current', 'is_online']
    )
    designation = serializers.ReadOnlyField(
        source='user_experience_package_slot.user_experience.job_title.title', allow_null=True
    )
    ssf_number = serializers.SerializerMethodField()
    heading_amounts = serializers.SerializerMethodField()

    class Meta:
        model = EmployeePayroll
        fields = [
            "id",
            "employee",
            "ssf_number",
            "designation",
            "heading_amounts"
            ]

    def __init__(self, instance=None, *args, **kwargs):
        super().__init__(instance, *args, **kwargs)
        self.obj = None
        self.amounts = {}

    @staticmethod
    def get_ssf_number(obj):
        return nested_getattr(obj.employee, 'legal_info.ssfid', default=None)

    def get_heading_amounts(self, obj):
        ssf_headings_id = SSFReportSetting.objects.filter(
            organization=self.context.get('organization')
        ).values_list('headings', flat=True)
        row_report_records = ReportRowRecord.objects.filter(
            employee_payroll=obj,
            heading__in=ssf_headings_id,
            employee_payroll__payroll__status__in=[GENERATED, CONFIRMED]
        )
        res = dict()
        for row_report_record in row_report_records:
            heading_id = row_report_record.heading.id
            res[heading_id] = row_report_record.amount
        return res


class DisbursementReportSerializer(DynamicFieldsModelSerializer):
    employee = UserThickSerializer(
        fields=['id', 'full_name', 'username', 'profile_picture', 'organization', 'is_current', 'is_online']
    )
    designation = serializers.ReadOnlyField(
        source='user_experience_package_slot.user_experience.job_title.title', allow_null=True
    )
    bank_name = serializers.SerializerMethodField()
    bank_account_number = serializers.SerializerMethodField()
    bank_branch_name = serializers.SerializerMethodField()

    heading_amounts = serializers.SerializerMethodField()

    class Meta:
        model = EmployeePayroll
        fields = [
            "id",
            "employee",
            "bank_name",
            "bank_account_number",
            "bank_branch_name",
            "designation",
            "heading_amounts"
            ]

    def __init__(self, instance=None, *args, **kwargs):
        super().__init__(instance, *args, **kwargs)
        self.obj = None
        self.amounts = {}

    @staticmethod
    def get_bank_name(obj):
        return nested_getattr(obj.employee, 'userbank.bank.name', default=None)

    @staticmethod
    def get_bank_account_number(obj):
        return nested_getattr(obj.employee, 'userbank.account_number', default=None)

    @staticmethod
    def get_bank_branch_name(obj):
        return nested_getattr(obj.employee, 'userbank.branch', default=None)

    def get_heading_amounts(self, obj):
        disbursement_headings_id = self.context.get('headings')
        return get_heading_details(obj, disbursement_headings_id)


class PayrollGeneralReportSerializer(UserFieldThinSerializer):
    branch = OrganizationBranchSerializer(
        fields=['name', 'slug'],
        source='detail.branch',
        read_only=True
    )
    marital_status = serializers.ReadOnlyField(
        source='detail.marital_status', allow_null=True
    )
    joined_date = serializers.ReadOnlyField(
        source='detail.joined_date', allow_null=True
    )
    username = serializers.SerializerMethodField()
    resigned_date = serializers.ReadOnlyField(
        source='detail.last_working_date', allow_null=True
    )
    records = serializers.SerializerMethodField()

    def get_username(self, instance):
        return instance.username

    def get_records(self, instance):
        records = dict()
        for heading_id in self.context["heading_ids"]:
            records.update({str(heading_id): getattr(instance, str(heading_id), None) or 0.0})
        return records


class PackageWiseSalarySerializer(PayrollGeneralReportSerializer):
    current_step = serializers.ReadOnlyField(source='current_experience.current_step')
    years_of_service = serializers.SerializerMethodField()
    joined_date = serializers.ReadOnlyField(source='detail.joined_date')

    @staticmethod
    def get_years_of_service(instance):
        rd = relativedelta(
            dt2=instance.detail.joined_date,
            dt1=get_today()
        )
        return {
            'years': rd.years,
            'months': rd.months,
            'days': rd.days
        }

    def get_records(self, instance):
        records = dict()
        for heading_id in self.context["heading_ids"]:
            records.update({
                str(heading_id): getattr(instance, str(heading_id), None)
            })
        return records


class BackdatedCalculationSerializer(DynamicFieldsModelSerializer):
    heading = serializers.SerializerMethodField()
    package_slot = serializers.SerializerMethodField()

    class Meta:
        model = BackdatedCalculation
        fields = ('previous_amount', 'current_amount',
                  'package_slot', 'heading')

    def get_heading(self, instance):
        return instance.heading.name

    def get_package_slot(self, instance):
        return instance.package_slot.package.name
