from django.conf import settings
from datetime import timedelta
from django.db.models import Sum, When, Case, F, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.functional import cached_property
from rest_framework import serializers
from irhrs.attendance.utils.get_lost_hours_as_per_shift import get_lost_hours_for_date_range
from irhrs.attendance.utils.payroll import (
    get_timesheet_penalty_days,
    get_working_days_from_organization_calendar,
    get_worked_days,
    get_absent_days, get_overtime_seconds,
    get_work_duration,
    get_expected_work_hours,
    get_work_days_count_from_simulated_timesheets
)
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer, DummySerializer
from irhrs.core.utils.common import DummyObject, humanize_interval
from irhrs.leave.utils.payroll import get_leave_balance_report, get_all_leave_days, get_leave_days, \
    get_unpaid_leave_days
from irhrs.organization.models import FiscalYear, FY

from irhrs.payroll.api.v1.serializers import EmployeeThinSerializer
from irhrs.payroll.api.v1.serializers.payroll_serializer import HeadingSerializer
from irhrs.payroll.api.v1.serializers.report.payroll_reports import BackdatedCalculationSerializer
from irhrs.payroll.constants import PAYSLIP_HEADING_CHOICES
from irhrs.payroll.models import (
    EmployeePayroll,
    ReportRowRecord,
    PAYSLIP_ACKNOWLEDGED,
    Heading,
    PAYSLIP_ACKNOWLEDGEMENT_PENDING,
    OrganizationPayrollConfig,
    MonthlyTaxReportSetting
)
from irhrs.payroll.models.payroll import CONFIRMED
from irhrs.payroll.utils.datework.date_helpers import DateWork
from irhrs.payroll.utils.helpers import get_days_to_be_paid
from irhrs.payroll.utils.calculator import NoEmployeeSalaryCalculator
from irhrs.users.api.v1.serializers.user_bank import UserBankSerializer

from irhrs.payroll.models.payslip_report_setting import MONTHLY_TAX_REPORT_SETTING_CATEGORY_CHOICES, PayslipReportSetting


class FromToPropertySerializerMixin:

    @property
    def from_date(self):
        return self.context.get('from_date')

    @property
    def to_date(self):
        return self.context.get('to_date')

    @property
    def actual_to_date(self):
        ")""actual attendance considered upto"""
        if self.simulated_from:
            return self.simulated_from - timezone.timedelta(days=1)
        return self.context.get('to_date')

    @property
    def simulated_from(self):
        return self.context.get('simulated_from')

    @cached_property
    def _previous_payroll_adjusted_from(self):
        assert self.instance

        previous_payroll = EmployeePayroll.objects.filter(
            employee=self.instance
        ).filter(
            payroll__from_date__lt=self.from_date
        ).order_by(
            '-payroll__to_date'
        ).first()

        if previous_payroll:
            return previous_payroll.payroll.simulated_from
        return None

    @property
    def adjust_previous_payroll_from_or_from_date(self):
        return self._previous_payroll_adjusted_from or self.from_date

    @cached_property
    def simulated_working_days(self):
        assert self.instance

        return get_work_days_count_from_simulated_timesheets(
            self.instance, self.simulated_from, self.to_date
        )


class HourlyAttendanceDetails(FromToPropertySerializerMixin, DummySerializer):
    total_worked_hours = serializers.SerializerMethodField()
    actual_overtime_hours = serializers.SerializerMethodField()
    normalized_overtime_hours = serializers.SerializerMethodField()
    lost_hours = serializers.SerializerMethodField()

    @cached_property
    def hourly_details(self):
        assert self.instance

        actual_overtime_s, normalized_overtime_s = get_overtime_seconds(
            self.instance,
            self.adjust_previous_payroll_from_or_from_date,
            self.actual_to_date
        )
        worked_s = get_work_duration(
            self.instance, self.adjust_previous_payroll_from_or_from_date,
            self.actual_to_date
        ).total_seconds()
        lost_s = get_lost_hours_for_date_range(
            self.instance.id, self.instance.detail.organization, 
            self.adjust_previous_payroll_from_or_from_date, self.to_date,
            calculate_unpaid_breaks=settings.CALCULATE_UNPAID_BREAKS_IN_INTERNAL_PLUGIN,
            ignore_seconds=settings.IGNORE_SECOND_IN_TOTAL_LOST_HOURS
        )

        return {
            "total_worked_hours": humanize_interval(worked_s),
            "normalized_overtime_hours": humanize_interval(normalized_overtime_s),
            "actual_overtime_hours": humanize_interval(actual_overtime_s),
            "lost_hours": round(lost_s/3600, 2)
        }

    def get_total_worked_hours(self, obj):
        return self.hourly_details["total_worked_hours"]

    def get_normalized_overtime_hours(self, obj):
        return self.hourly_details["normalized_overtime_hours"]

    def get_actual_overtime_hours(self, obj):
        return self.hourly_details["actual_overtime_hours"]
    
    def get_lost_hours(self, obj):
        return self.hourly_details["lost_hours"]

class PayslipAttendanceDetailsSerializer(FromToPropertySerializerMixin, DummySerializer):
    working_days = serializers.SerializerMethodField()
    worked_days = serializers.SerializerMethodField()
    absent_days = serializers.SerializerMethodField()
    leave_days = serializers.SerializerMethodField()
    leave_days_on_workdays = serializers.SerializerMethodField()
    unpaid_leave_days = serializers.SerializerMethodField()
    simulated_from = serializers.SerializerMethodField()
    previous_payroll_adjusted_from = serializers.SerializerMethodField()
    paid_days = serializers.SerializerMethodField()
    days_deduction_from_penalty = serializers.SerializerMethodField()

    def get_days_deduction_from_penalty(self, obj):
        return get_timesheet_penalty_days(obj, self.from_date, self.actual_to_date)

    def get_working_days(self, obj):
        include_holiday_offday = self.context.get('include_holiday_offday') or False
        working_days = get_working_days_from_organization_calendar(
            obj,
            self.from_date,
            self.actual_to_date,
            include_holiday_offday=include_holiday_offday
        )
        if self.simulated_from:
            working_days += self.simulated_working_days
        return working_days

    def get_worked_days(self, obj):
        include_holiday_offday = self.context.get('include_holiday_offday') or False
        worked_days = get_worked_days(
            obj, self.from_date, self.actual_to_date,
            include_non_working_days=include_holiday_offday
        )
        if self.simulated_from:
            worked_days += self.simulated_working_days
        return worked_days

    def get_absent_days(self, obj):
        return get_absent_days(obj, self.adjust_previous_payroll_from_or_from_date,
                               self.actual_to_date)

    def get_leave_days(self, obj):
        return get_all_leave_days(obj, self.adjust_previous_payroll_from_or_from_date,
                                  self.actual_to_date)

    def get_leave_days_on_workdays(self, obj):
        return get_leave_days(obj, self.adjust_previous_payroll_from_or_from_date,
                              self.actual_to_date, is_workday=True)

    def get_unpaid_leave_days(self, obj):
        return get_unpaid_leave_days(obj, self.adjust_previous_payroll_from_or_from_date,
                                     self.actual_to_date)

    def get_simulated_from(self, obj):
        return self.simulated_from

    def get_previous_payroll_adjusted_from(self, obj):
        return self._previous_payroll_adjusted_from

    def get_paid_days(self, obj):
        payroll_settings = OrganizationPayrollConfig.objects.filter(
            organization=obj.detail.organization
        ).first()
        count_off_day_holiday_as_worked = getattr(
            payroll_settings,
            "include_holiday_offday_in_calculation",
            False
        )

        worked_days = 0
        actual_worked_days = get_days_to_be_paid(
            obj,
            self.from_date,
            self.actual_to_date,
            count_offday_holiday_as_worked=count_off_day_holiday_as_worked
        )
        worked_days += actual_worked_days

        if self.simulated_from:
            if count_off_day_holiday_as_worked:
                worked_days += (
                    self.to_date - self.simulated_from
                ).days + 1
            else:
                worked_days += self.simulated_working_days

        if self._previous_payroll_adjusted_from:
            adjusted_absent_days = get_absent_days(
                obj,
                self._previous_payroll_adjusted_from,
                self.from_date - timezone.timedelta(days=1)
            )
            adjusted_unpaid_leave_days = get_unpaid_leave_days(
                obj,
                self._previous_payroll_adjusted_from,
                self.from_date - timezone.timedelta(days=1)
            )

            worked_days = worked_days - \
                (adjusted_absent_days + adjusted_unpaid_leave_days)
        return worked_days


class PayslipLeaveDetailSerializer(DummySerializer):
    leave_type = serializers.ReadOnlyField(source="rule.leave_type.name")
    category = serializers.ReadOnlyField(source="rule.leave_type.category")
    opening = serializers.ReadOnlyField()
    closing = serializers.ReadOnlyField()
    used = serializers.ReadOnlyField()


class ReportRowSerializer(DynamicFieldsModelSerializer):
    heading_id = serializers.ReadOnlyField(source="heading.id")
    heading = serializers.ReadOnlyField(source="heading.name")
    heading_type = serializers.ReadOnlyField(
        source="heading.type", allow_null=True)
    year_to_date = serializers.SerializerMethodField()

    class Meta:
        model = ReportRowRecord
        fields = (
            "heading_id", "heading", "heading_type", "amount", "package_amount", "year_to_date"
        )

    @staticmethod
    def get_year_to_date(obj):
        if obj.heading and obj.heading.year_to_date:
            employee_payroll = obj.employee_payroll

            employee = employee_payroll.employee
            payroll = obj.employee_payroll.payroll
            organization = payroll.organization

            fiscal_year = FiscalYear.objects.active_for_date(
                organization,
                payroll.to_date
            )

            return ReportRowRecord.objects.filter(
                employee_payroll__employee=employee,
                from_date__gte=fiscal_year.applicable_from,
                to_date__lte=obj.to_date,
                heading=obj.heading
            ).aggregate(
                total_amount=Coalesce(Sum('amount'), 0.0)
            )["total_amount"]
        return None


class PaySlipSerializer(DynamicFieldsModelSerializer):
    report_rows = ReportRowSerializer(many=True)
    employee = EmployeeThinSerializer()
    from_date = serializers.ReadOnlyField(source='payroll.from_date')
    to_date = serializers.ReadOnlyField(source='payroll.to_date')
    approved_date = serializers.ReadOnlyField(source='payroll.approved_date')
    bank = UserBankSerializer(
        exclude_fields=["user"],
        source="employee.userbank",
    )
    leave_details = serializers.SerializerMethodField()
    attendance_details = serializers.SerializerMethodField()
    hourly_attendance = serializers.SerializerMethodField()
    expected_working_hours = serializers.SerializerMethodField()
    payslip_note = serializers.SerializerMethodField()
    masked_values = serializers.SerializerMethodField()
    adjusted_backdated_calculations = BackdatedCalculationSerializer(many=True)
    is_confirmed = serializers.SerializerMethodField()
    earnings = serializers.SerializerMethodField()
    deductions = serializers.SerializerMethodField()

    class Meta:
        model = EmployeePayroll
        fields = (
            "employee",
            "bank",
            "from_date",
            "to_date",
            "approved_date",
            "report_rows",
            "leave_details",
            "attendance_details",
            "hourly_attendance",
            "acknowledgement_status",
            "expected_working_hours",
            "user_note",
            "payslip_note",
            "masked_values",
            "adjusted_backdated_calculations",
            "is_confirmed",
            "earnings",
            "deductions"
        )
        read_only_fields = ["user_note", ]

    def get_fields(self):
        fields = super().get_fields()
        fields["bank"] = UserBankSerializer(
            exclude_fields=["user"],
            source="employee.userbank",
            context=self.context
        )
        return fields

    def get_is_confirmed(self, obj):
        return obj.payroll.status == CONFIRMED

    def get_masked_values(self, obj):
        cash_in_hand_heading = None
        organization = obj.payroll.organization
        if hasattr(organization, 'overview_report_config'):
            cash_in_hand_heading = organization.overview_report_config.cash_in_hand
        cash_in_hand = obj.report_rows.filter(
            heading=cash_in_hand_heading).first()
        return {
            'cash_in_hand': cash_in_hand.amount if cash_in_hand else None
        }

    @staticmethod
    def get_leave_details(obj):
        return PayslipLeaveDetailSerializer(get_leave_balance_report(
            obj.employee,
            obj.payroll.from_date,
            obj.payroll.to_date
        ).filter(used__gt=0), many=True).data

    def _get_incomes(self,obj,category):
        earning_headings = PayslipReportSetting.objects.filter(
            organization=obj.payroll.organization,
            category=category
        ).values_list("headings", flat=True)
        records = obj.report_rows.select_related("heading__name").filter(
            heading_id__in=earning_headings
        ).values("heading__name", "amount")
        return list(records)

    def get_earnings(self,obj):
        return self._get_incomes(obj, category="Earning")

    def get_deductions(self,obj):
        return self._get_incomes(obj, category="Deduction")

    @staticmethod
    def get_attendance_details(obj):
        return PayslipAttendanceDetailsSerializer(
            obj.employee,
            context={
                "from_date": obj.payroll.from_date,
                "to_date": obj.payroll.to_date,
                "simulated_from": obj.payroll.simulated_from
            }
        ).data

    @staticmethod
    def get_hourly_attendance(obj):
        return HourlyAttendanceDetails(
            obj.employee,
            context={
                "from_date": obj.payroll.from_date,
                "to_date": obj.payroll.to_date,
                "simulated_from": obj.payroll.simulated_from
            }
        ).data

    @staticmethod
    def get_expected_working_hours(obj):

        ser = PayslipAttendanceDetailsSerializer(
            obj.employee,
            context={
                "from_date": obj.payroll.from_date,
                "to_date": obj.payroll.to_date,
                "simulated_from": obj.payroll.simulated_from
            }
        )

        return humanize_interval(
            get_expected_work_hours(
                user=obj.employee,
                start=ser.adjust_previous_payroll_from_or_from_date,
                end=ser.actual_to_date
            ) * 60  # converting it into seconds
        )

    def get_payslip_note(self, obj):
        config = OrganizationPayrollConfig.objects.filter(
            organization=obj.payroll.organization
        ).first()
        return getattr(config, 'payslip_note', '')


class YTDSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = ReportRowRecord
        fields = ("from_date", "to_date", "amount")


class PaySlipAcknowledgeSerializer(DynamicFieldsModelSerializer):
    acknowledgement_status = serializers.ChoiceField(
        choices=(
            (PAYSLIP_ACKNOWLEDGED, "Acknowledged")
        )
    )

    class Meta:
        model = EmployeePayroll
        fields = ('acknowledgement_status', )

    def validate(self, attrs):
        # Serializer only Supports Update Validations
        if not self.instance:
            return

        if self.instance.acknowledgement_status != PAYSLIP_ACKNOWLEDGEMENT_PENDING:
            raise serializers.ValidationError(
                "Can only act on pending payslips.")

        return attrs

    def create(self, validated_data):
        return DummyObject(**validated_data)

    def update(self, instance, validated_data):
        validated_data["acknowledged_at"] = timezone.now()
        return super().update(instance, validated_data)


class PaySlipResponseSerializer(DynamicFieldsModelSerializer):
    payroll_id = serializers.ReadOnlyField(source='payroll.id')
    employee = EmployeeThinSerializer()
    from_date = serializers.ReadOnlyField(source='payroll.from_date')
    to_date = serializers.ReadOnlyField(source='payroll.to_date')
    approved_date = serializers.ReadOnlyField(source='payroll.approved_date')

    total_comment = serializers.ReadOnlyField(allow_null=True)

    class Meta:
        model = EmployeePayroll
        fields = (
            "id",
            "payroll_id",
            "employee",
            "from_date",
            "to_date",
            "acknowledgement_status",
            "acknowledged_at",
            "approved_date",
            "total_comment"
        )


class PaySlipTaxDetailsSerializer(PaySlipSerializer):
    class Meta:
        model = EmployeePayroll
        fields = (
            "employee",
            "bank",
            "from_date",
            "to_date",
            "annual_gross_salary",
            "rebate_amount",
            "annual_gross_salary_after_rebate",
            "annual_tax",
            "paid_tax",
            "tax_to_be_paid",
            "tax_rule",
            "tax_condition",
            "acknowledgement_status",
        )


class MonthlyTaxReportCategoryHeading(serializers.Serializer):
    is_highlighted = serializers.ReadOnlyField(
        source="setting_item.is_highlighted"
    )
    is_nested = serializers.ReadOnlyField(
        source="setting_item.is_nested"
    )
    heading = serializers.ReadOnlyField(
        source="setting_item.heading.id"
    )

    heading_name = serializers.SerializerMethodField()

    ytd_amount = serializers.FloatField()
    remaining_after_ytd = serializers.FloatField()
    yearly_const = serializers.FloatField()

    def get_heading_name(self, obj):
        return obj.setting_item.heading.name or obj.setting_item.heading.verbose_name


class MonthlyTaxReportResultSerializer(serializers.Serializer):
    category = serializers.ChoiceField(
        choices=MONTHLY_TAX_REPORT_SETTING_CATEGORY_CHOICES
    )

    headings = MonthlyTaxReportCategoryHeading(many=True)


class MonthlyTaxReportSerializer(serializers.ModelSerializer):
    fiscal_year_name = serializers.SerializerMethodField()
    employee = EmployeeThinSerializer()
    from_date = serializers.ReadOnlyField(source="payroll.from_date")
    to_date = serializers.ReadOnlyField(source="payroll.to_date")
    results = serializers.SerializerMethodField()

    class Meta:
        model = EmployeePayroll
        fields = (
            "fiscal_year_name",
            "employee",
            "from_date",
            "to_date",
            "results"
        )

    def get_fiscal_year_name(self, obj):
        return self.get_fiscal_year(obj).name

    def get_fiscal_year(self, obj):
        return FY(
            obj.payroll.organization
        ).fiscal_obj(
            date=obj.payroll.from_date
        )

    def get_data_from_projected_values(
        self,
        setting_item,
        record_rows
    ):
        heading_id = setting_item.heading.id

        filtered_rows_by_heading_id = list(
            filter(
                lambda x: x.get('heading_id') == heading_id,
                record_rows
            )
        )

        if filtered_rows_by_heading_id:
            return_dict = filtered_rows_by_heading_id[0]
            return_dict.pop('heading_id')
            return return_dict
        else:
            return dict(
                ytd_amount=None,
                remaining_after_ytd=None,
                yearly_const=None
            )

    def get_results(self, obj):
        queryset = MonthlyTaxReportSetting.objects.filter(
            organization=obj.payroll.organization
        ).select_related('heading').order_by('pk')

        if not queryset:
            raise serializers.ValidationError(
                'Monthly tax report settings not configured.'
            )

        ytd_from_date = self.get_fiscal_year(obj).start_at

        ytd_to_date = obj.payroll.to_date

        show_heading_with_zero_value = self.context.get('show_heading_with_zero_value',False)

        headings_amount_from_record = ReportRowRecord.objects.filter(
            employee_payroll__employee=obj.employee,
            from_date__gte=ytd_from_date,
            to_date__lte=ytd_to_date,
        ).values('heading_id').annotate(
            ytd_amount=Sum('amount'),
            remaining_after_ytd=Sum(
                Case(
                    When(
                        employee_payroll=obj,
                        heading__duration_unit__in=['Yearly', 'Monthly'],
                        then=F('projected_amount')
                    ),
                    default=None,
                )
            ),
            yearly_const=Sum(
                Case(
                    When(
                        employee_payroll=obj,
                        heading__type__in=['Type2Cnst'],
                        then=F('amount')
                    ),
                    default=None,
                )
            )
        )

        class TaxReportCategoryItem(object):
            def __init__(
                self,
                setting_item,
                ytd_amount=None,
                remaining_after_ytd=None,
                yearly_const=None
            ):
                self.setting_item = setting_item
                self.ytd_amount = ytd_amount
                self.remaining_after_ytd = remaining_after_ytd
                self.yearly_const = yearly_const

        class TaxReportByCategory(object):
            def __init__(self, category, headings):
                self.category = category
                self.headings = headings

            def add_headings(self, heading):
                self.headings.append(heading)

        tax_report_categories = list()

        for item in queryset:
            category_is_present = list(
                filter(
                    lambda x: x.category == item.category,
                    tax_report_categories
                )
            )

            report_item = TaxReportCategoryItem(
                item,
                **self.get_data_from_projected_values(
                    item,
                    headings_amount_from_record
                )
            )

            if not category_is_present:
                if not (show_heading_with_zero_value or report_item.ytd_amount):
                    continue

                tax_report_categories.append(
                    TaxReportByCategory(
                        item.category,
                        [report_item]
                    )
                )
            else:
                if not (show_heading_with_zero_value or report_item.ytd_amount):
                    continue
                category_is_present[0].add_headings(report_item)
        serializer = MonthlyTaxReportResultSerializer(
            tax_report_categories,
            many=True
        )

        return serializer.data


class PayslipReportSettingSerializer(serializers.Serializer):
    headings = serializers.PrimaryKeyRelatedField(
        allow_empty=True,
        many=True,
        queryset=Heading.objects.all()
    )
    category = serializers.ChoiceField(choices=PAYSLIP_HEADING_CHOICES)

    def create(self, validated_data):
        payslip_setting = PayslipReportSetting.objects.create(
            organization=self.context['organization'],
            category=validated_data.get('category')
        )
        payslip_setting.headings.set(validated_data['headings'])
        return payslip_setting

