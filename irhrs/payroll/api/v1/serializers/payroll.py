import time
from collections import OrderedDict
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django_q.tasks import async_task
from django.db.models import F, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import LimitOffsetPagination

from irhrs.attendance.constants import APPROVED
from irhrs.core.mixins.serializers import DummySerializer, DynamicFieldsModelSerializer
from irhrs.export.utils.helpers import save_workbook
from irhrs.organization.api.v1.serializers.fiscal_year import FiscalYearSerializer
from irhrs.organization.models import Organization, validate_past_date, GLOBAL, FiscalYear
from irhrs.organization.models.branch_and_division import OrganizationBranch, OrganizationDivision
from irhrs.payroll.api.v1.serializers import HeadingSerializer
from irhrs.payroll.constants import YEARLY
from irhrs.payroll.models import (
    Heading,
    ReportRowRecord,
    PayrollGenerationHistory,
    YearlyHeadingDetail, SSFReportSetting, DisbursementReportSetting, TaxReportSetting,
    PayrollCollectionDetailReportSetting, ExtraHeadingReportSetting, RebateSetting, EmployeePayroll
)
from irhrs.payroll.models.payroll import ExcelPayrollPackage, OrganizationPayrollConfig, Package, \
    Payroll, PayrollDifferenceDetailReportSetting
from irhrs.payroll.utils.excel_packages import ExcelDictPackage, create_bulk_packages
from irhrs.payroll.utils.headings import is_rebate_type_used_in_heading
from irhrs.payroll.utils.helpers import get_last_confirmed_payroll_generated_date, get_appoint_date
from irhrs.payroll.utils.user_detail_for_payroll import get_user_detail_for_payroll
from irhrs.payroll.utils.user_voluntary_rebate import get_default_fiscal_months_amount, \
    get_ordered_fiscal_months_amount, get_all_payroll_generated_months
Employee = get_user_model()
ADD_VALUES_TO_BASIC = getattr(settings, 'ADD_VALUES_TO_BASIC', False)
BASIC_SALARY_NAME = getattr(settings, 'BASIC_SALARY_NAME', 'Basic Salary')


def get_fiscal_month_for_date(organization, for_month_end_date, doj_minus_for_month):
    from irhrs.organization.models import FiscalYear
    fy = FiscalYear.objects.active_for_date(organization, for_month_end_date)
    if not fy:
        return -999
    fym = fy.fiscal_months.filter(end_at__gte=for_month_end_date).order_by('start_at').first()
    if not fym:
        return -999
    days_in_month = (fym.end_at - fym.start_at).days
    short_days = days_in_month - doj_minus_for_month
    if short_days > 0:
        return round(short_days / days_in_month, 2)
    return 1


def calculate_percentage_of_month_worked(employee, for_month_end_date):
    # unless the dates are in close quarters of 35 days, do not compute.
    doj_minus_for_month = (for_month_end_date - employee.detail.joined_date).days + 1
    # include lower limit.
    if doj_minus_for_month > 35:
        return 1
    return get_fiscal_month_for_date(
        employee.detail.organization,
        for_month_end_date,
        doj_minus_for_month
    )


class EmployeeFilterSerializer(DummySerializer):
    id__in = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(),
        many=True,
        required=False
    )
    id__excludes = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(),
        many=True,
        required=False
    )
    detail__branch__in = serializers.PrimaryKeyRelatedField(
        queryset=OrganizationBranch.objects.all(),
        many=True,
        required=False
    )
    detail__division__in = serializers.PrimaryKeyRelatedField(
        queryset=OrganizationDivision.objects.all(),
        many=True,
        required=False
    )

    @staticmethod
    def get_filter_and_excludes(validated_data):
        filters = {}
        excludes = {}
        if validated_data.get('id__in'):
            filters['id__in'] = [u.id for u in validated_data['id__in']]
        if validated_data.get('id__excludes'):
            excludes['id__in'] = [u.id for u in validated_data['id__excludes']]
        if validated_data.get('detail__branch__in'):
            filters['detail__branch__in'] = [u.id for u in validated_data['detail__branch__in']]
        if validated_data.get('detail__division__in'):
            filters['detail__division__in'] = [u.id for u in validated_data['detail__division__in']]
        return filters, excludes


class PayrollCreateSerializer(DummySerializer):
    """
    Serializer used to validate data sent while generating/saving payroll
    """
    title = serializers.CharField(max_length=100, allow_null=False, required=True)
    from_date = serializers.DateField(validators=[validate_past_date])
    to_date = serializers.DateField()
    cutoff_date = serializers.DateField(allow_null=True, required=False)
    organization_slug = serializers.SlugRelatedField(
        queryset=Organization.objects.all(),
        slug_field='slug'
    )
    save = serializers.BooleanField(default=False)
    employees_filter = EmployeeFilterSerializer()
    exclude_not_eligible = serializers.BooleanField()
    initial_extra_headings = serializers.PrimaryKeyRelatedField(
        queryset=Heading.objects.all(),
        many=True,
        default=list()
    )
    extra_headings = serializers.JSONField(allow_null=True, required=False)
    edited_general_headings = serializers.JSONField(
        allow_null=True, required=False)
    include_past_employee = serializers.BooleanField(default=False)

    def validate(self, attrs):
        errors = {}
        from_date = attrs.get("from_date")
        to_date = attrs.get("to_date")
        cutoff_date = attrs.get("cutoff_date")
        if from_date > to_date:
            errors.update({"to_date": ["Must be less than from date."]})
        if cutoff_date and (cutoff_date < from_date or cutoff_date > to_date):
            errors.update({"cutoff_date": ["Must be between payroll from date and to date."]})
        if errors:
            raise ValidationError(errors)
        return attrs


class PayrollUpdateSerializer(DummySerializer):
    extra_headings = serializers.JSONField(allow_null=True, required=False)
    edited_general_headings = serializers.JSONField(
        allow_null=True, required=False)
    remarks = serializers.JSONField(write_only=True)

    @staticmethod
    def validate_remarks(remarks):
        if not remarks:
            raise ValidationError(
                "Please enter remarks to recalculate"
            )
        if not all(map(
                lambda key: key.isdigit(),
                remarks
        )):
            raise ValidationError(
                "The key to remarks must be integer."
            )
        if not all(map(bool, remarks.values())):
            raise ValidationError("The remarks may not be empty.")

        if any(map(lambda x: len(str(x)) > 255, remarks.values())):
            raise ValidationError("Remarks must be less than 255")

        return remarks

    @staticmethod
    def validate_edited_general_headings(data):
        error_dict = {}
        for user_id, user_data in data.items():
            user_error_detail = {}
            for heading_id, heading_detail in user_data.items():
                heading_error = {}
                if heading_id != 'incomeDifference':
                    try:
                        float(heading_detail['currentValue'])
                    except (ValueError, TypeError):
                        heading_error['currentValue'] = ["Invalid amount."]

                    if heading_detail['initialValue'] is not None:
                        try:
                            float(heading_detail['initialValue'])
                        except (ValueError, TypeError):
                            heading_error['initialValue'] = ["Invalid amount."]
                    if heading_error:
                        user_error_detail[heading_id] = heading_error
            if user_error_detail:
                error_dict[user_id] = user_error_detail

        if error_dict:
            raise serializers.ValidationError(error_dict)
        return data


class EmployeePayrollExportSerializer(DummySerializer):
    employee_code = serializers.ReadOnlyField(source='employee.detail.code')
    full_name = serializers.ReadOnlyField(source='employee.full_name')
    username = serializers.ReadOnlyField(source='employee.username')
    job_title = serializers.ReadOnlyField(
        source='employee.detail.job_title.title')
    division = serializers.ReadOnlyField(source='employee.detail.division.name')
    employment_level = serializers.ReadOnlyField(source='employee.detail.employment_level.title')
    employee_level_hierarchy = serializers.ReadOnlyField(source='employee.detail.employment_level.order_field')
    employment_status = serializers.ReadOnlyField(source='employee.detail.employment_status.title')
    branch = serializers.ReadOnlyField(source='employee.detail.branch.name')
    user_detail = serializers.SerializerMethodField()
    ssf_number = serializers.ReadOnlyField(source='employee.legal_info.ssfid')
    bank_name = serializers.ReadOnlyField(source='employee.userbank.bank.name')
    bank_branch = serializers.ReadOnlyField(source='employee.userbank.branch')
    bank_account_number = serializers.ReadOnlyField(source='employee.userbank.account_number')
    pf_number = serializers.ReadOnlyField(source='employee.legal_info.pf_number')
    pan_number = serializers.ReadOnlyField(source='employee.legal_info.pan_number')
    cit_number = serializers.ReadOnlyField(source='employee.legal_info.cit_number')

    heading_amounts = serializers.SerializerMethodField()
    joined_date = serializers.ReadOnlyField(
        source='employee.detail.joined_date'
    )

    def get_user_detail(self, instance):
        user_detail, _ = get_user_detail_for_payroll(instance, self.context.get('organization'))
        return user_detail

    @staticmethod
    def get_heading_amounts(instance):
        data = dict()
        for report_row in ReportRowRecord.objects.filter(employee_payroll=instance).annotate(
            heading_name=F('heading__name')
        ):
            data[str(report_row.heading_name)] = report_row.amount
        if ADD_VALUES_TO_BASIC and BASIC_SALARY_NAME in data:
            percentage_of_month = calculate_percentage_of_month_worked(
                instance.employee, instance.payroll.to_date
            )
            data.update({
                "percentage_of_month_worked": percentage_of_month,
            })
        return data


class PayrollGenerationHistorySerializer(DynamicFieldsModelSerializer):
    errors = serializers.SerializerMethodField()

    class Meta:
        model = PayrollGenerationHistory
        fields = '__all__'

    def get_errors(self, obj):
        errors = obj.errors
        if errors and errors.get('not_eligibles'):
            pagination = LimitOffsetPagination()
            page = pagination.paginate_queryset(
                errors['not_eligibles'],
                self.request
            )
            errors['not_eligibles'] = OrderedDict([
                ('count', pagination.count),
                ('next', pagination.get_next_link()),
                ('previous', pagination.get_previous_link()),
                ('results', page)
            ])
        return errors


class YearlyHeadingDetailSerializer(DynamicFieldsModelSerializer):

    def validate(self, obj):
        fiscal_year = obj.get('fiscal_year')
        heading = obj.get('heading')
        date = obj.get('date')

        validation_errors = dict()

        if date and not (fiscal_year.start_at <= date <= fiscal_year.end_at):
            validation_errors['date'] = _('Date must be in between selected fiscal year.')

        if heading.organization != self.context['organization']:
            validation_errors['organization'] = _('Please select correct organization heading.')

        if fiscal_year.organization != self.context['organization']:
            validation_errors['fiscal_year'] = _('Please select correct organization fiscal year.')

        if fiscal_year.category != GLOBAL:
            validation_errors['fiscal_year'] = _('Please select fiscal year of category global.')

        if validation_errors:
            raise serializers.ValidationError(validation_errors)

        return obj

    def get_fields(self):
        fields = super().get_fields()

        if self.request and self.request.method.lower() == 'get':
            fields['heading'] = HeadingSerializer(fields=['id', 'label'])
            fields['fiscal_year'] = FiscalYearSerializer(fields=('id', 'name'))

        return fields

    class Meta:
        model = YearlyHeadingDetail
        fields = '__all__'


class RebateSettingSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = RebateSetting
        fields = ('id', 'title', 'duration_type', 'amount', 'is_archived')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        attrs["organization"] = self.context.get("organization")
        organization = attrs.get('organization')
        title = attrs.get('title')
        if not self.instance and RebateSetting.objects.filter(
            title=title,
            organization=organization
        ).exists():
            raise ValidationError("This title is already used.")
        return attrs

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.upper() == 'GET':
            fields["fiscal_months_amount"] = serializers.SerializerMethodField()
            fields["payroll_generated_months"] = serializers.SerializerMethodField()
        return fields

    def get_fiscal_months_amount(self, obj):
        organization = self.context.get('organization')
        fiscal_year = self.context.get('fiscal_year')
        if not organization or obj.duration_type == YEARLY or self.context.get(
            "hide_fiscal_months_amount"
        ):
            return {}

        user_rebate = obj.voluntary_rebates.filter(
            user=self.context.get('user_id'),
            statuses__action=APPROVED
        ).first()
        if not user_rebate:
            return get_ordered_fiscal_months_amount(
                organization, get_default_fiscal_months_amount(organization, fiscal_year=fiscal_year), fiscal_year=fiscal_year
            )

        return get_ordered_fiscal_months_amount(organization, user_rebate.fiscal_months_amount, fiscal_year=fiscal_year)

    def get_payroll_generated_months(self, obj):
        user_id = self.context.get('user_id')
        if not user_id:
            return []
        user = Employee.objects.get(id=user_id)
        organization = self.context.get('organization')
        fiscal_year = self.context.get('fiscal_year')

        return get_all_payroll_generated_months(user, organization, fiscal_year)

    def update(self, instance, validated_data):
        title = validated_data.get('title')
        previous_title = instance.title
        is_rebate_heading_used = is_rebate_type_used_in_heading(
            self.context.get('organization'), previous_title)

        if is_rebate_heading_used and title != previous_title:
            raise ValidationError({
                "title": "This rebate is already used in payroll heading."
            })

        return super().update(instance, validated_data)


class ReportSettingSerializerMixin:

    def create(self, validated_data):
        headings = validated_data.pop('headings')
        organization = self.context.get('organization')
        report_setting = self.Meta.model.objects.filter(
            organization=organization
        ).first()
        if not report_setting:
            report_setting = self.Meta.model.objects.create(organization=organization)
            report_setting.headings.add(*headings)
            report_setting.save()
            return report_setting

        else:
            return self.update(report_setting, headings)

    def update(self, instance, headings):
        instance.headings.clear()
        instance.headings.add(*headings)
        return instance


class PayrollCollectionDetailReportSettingSerializer(
    ReportSettingSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = PayrollCollectionDetailReportSetting
        fields = ('headings',)


class PayrollDifferenceDetailReportSettingSerializer(
    ReportSettingSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = PayrollDifferenceDetailReportSetting
        fields = ('headings',)


class SSFReportSettingSerializer(ReportSettingSerializerMixin, serializers.ModelSerializer):

    class Meta:
        model = SSFReportSetting
        fields = ('headings',)


class DisbursementReportSettingSerializer(ReportSettingSerializerMixin, serializers.ModelSerializer):

    class Meta:
        model = DisbursementReportSetting
        fields = ('headings',)


class TaxReportSettingSerializer(ReportSettingSerializerMixin, serializers.ModelSerializer):

    class Meta:
        model = TaxReportSetting
        fields = ('headings',)


class PayrollExtraHeadingSettingSerializer(serializers.ModelSerializer):

    class Meta:
        model = ExtraHeadingReportSetting
        fields = ('headings',)

    def create(self, validated_data):
        organization = self.context.get('organization')
        report_setting = ExtraHeadingReportSetting.objects.filter(
            organization=organization
        ).first()
        if not report_setting:
            headings = validated_data.pop('headings')
            report_setting = ExtraHeadingReportSetting.objects.create(
                organization=organization, headings=headings)
            return report_setting
        return self.update(report_setting, validated_data)

    def update(self, instance, validated_data):
        headings = validated_data.pop('headings')
        instance.headings = headings
        instance.save()
        return instance


class ExcelPayrollPackageSerializer(DynamicFieldsModelSerializer):
    excel_file = serializers.FileField(
        max_length=100,
        validators=[
        FileExtensionValidator(
            allowed_extensions=['xlsx', 'xlsm', 'xltx', 'xltm']
        )],
        write_only=True
    )
    cloned_from = serializers.PrimaryKeyRelatedField(
        queryset=Package.objects.all()
    )
    class Meta:
        model = ExcelPayrollPackage
        fields = (
            "id",
            "name",
            "cloned_from",
            "modified_at",
            "assigned_date",
            "excel_file",
            "status"
        )

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method == "GET":
            fields["cloned_from"] = serializers.StringRelatedField()
        return fields

    def validate_assigned_date(self, assigned_date):
        active_fiscal_year = FiscalYear.objects.active_for_date(
            organization=self.context['organization'],
            date_=assigned_date,
            category=GLOBAL
        )
        if not active_fiscal_year:
            raise serializers.ValidationError(
                "Can not assign package. Fiscal year doesn't exist for given date."
            )
        return assigned_date

    @property
    def payroll_config(self):
        return OrganizationPayrollConfig.objects.filter(
            organization=self.context["organization"]
        ).first()

    def validate(self, attrs):
        if not self.payroll_config:
            raise ValidationError("Payroll configuration not found")

        excel_file = attrs.pop("excel_file")
        assigned_date = attrs["assigned_date"]

        excel_package = ExcelDictPackage(file=excel_file)
        header = excel_package.header
        self.validate_headers(header[1:], attrs)

        self.validate_rows(excel_package, assigned_date)

        if excel_package.errors:
            attrs["status"] = "Failed"
            self.save_error_file(excel_package.error_wb)

        attrs['excel_package'] = excel_package

        return attrs

    def save_error_file(self, workbook):
        import uuid
        filename = f"failed_package_errors_{uuid.uuid4()}.xlsx"
        save_workbook(workbook, filename)

        from django.conf import settings
        file_url = settings.BACKEND_URL + settings.MEDIA_URL + filename
        cache.set("failed_package_errors_timestamp", timezone.now())
        cache.set("failed_package_errors", file_url)

    def validate_headers(self, header, attrs):
        if len(header) > len(set(header)):
            raise ValidationError("Duplicate headings")
        package = attrs['cloned_from']

        if not hasattr(package, "package_headings"):
            raise ValidationError(
                "No package heading assigned in default package"
            )

        package_headings = package.package_headings.select_related(
            "heading__name"
        ).values_list("heading__name", flat=True)

        for heading in header:
            if heading not in package_headings:
                raise ValidationError(
                    f"Heading {heading} not found in {package}"
                )

    def validate_rows(self, excel_package, assigned_date):
        validated_users = set()
        for email, row in excel_package.items():
            errors = {}
            for heading, value in row.items():
                if value is None:
                    continue
                try:
                    float(value)
                except ValueError:
                    errors[heading] = f"Invalid number, {value}"

            user = Employee.objects.filter(
                Q(email=email) | Q(username=email)
            ).first()
            if user in validated_users:
                errors['duplicate_user'] = (f"User with this email/username: "
                                            f"{user.email}/ {user.username} has been duplicated.")
            validated_users.add(user)
            if not user:
                errors["email"] = f"User with this email/username doesn't exist"
                excel_package[email] = errors
                continue

            last_paid = get_last_confirmed_payroll_generated_date(user)
            if last_paid and assigned_date <= last_paid:
                errors["last_paid_date"] = (
                    "package assignment date cannot be before last paid"
                    f" date, {last_paid}"
                )

            appoint_date = get_appoint_date(user, self.payroll_config)
            if appoint_date is not None and assigned_date < appoint_date:
                errors["appoint_date"] = (
                    "package assignment date cannot be before "
                    f"appoint date, {appoint_date}"
                )

            user_experience = user.user_experiences.first()
            if not user_experience:
                errors['user_experience'] = "No current user experience found"
                excel_package[email] = errors
                continue

            if user_experience.end_date and (user_experience.end_date < assigned_date):
                errors['user_experience_end_date'] = (
                    'Cannot assign package to user with experience end date '
                    'before assigned date'
                )

            expected_package_name = f"{user.full_name} {user.username} {assigned_date} {time.strftime('%H:%M', time.localtime())}"
            if Package.objects.filter(name=expected_package_name).exists():
                errors['package'] = (
                    f"Package with "
                    f"{expected_package_name} already exists."
                )

            if Payroll.objects.filter(employees=user, to_date__gte=assigned_date).exclude(
                status="Rejected").exists():
                errors['payroll'] = (
                    f"Payroll of this employee for date {assigned_date} "
                    f"is already generated."
                )

            excel_package[email] = errors


    def create(self, validated_data):
        excel_package = validated_data.pop("excel_package")

        instance = ExcelPayrollPackage.objects.create(
            organization=self.context["organization"],
            **validated_data
        )
        if instance.status == "Failed":
            return instance

        excel_data = list(excel_package.items())
        async_task(
            create_bulk_packages,
            validated_data["assigned_date"],
            excel_data,
            instance,
            self.context["organization"],
            actor=self.request and self.request.user
        )

        return instance

class ExcelUpdateSerializer(serializers.Serializer):
    file = serializers.FileField(
        max_length=100,
        validators=[
        FileExtensionValidator(
            allowed_extensions=['xlsx', 'xlsm', 'xltx', 'xltm']
        )],
        write_only=True
    )
    remarks = serializers.CharField(max_length=100)
