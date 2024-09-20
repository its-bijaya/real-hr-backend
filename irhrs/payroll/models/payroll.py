import itertools

from django.conf import settings
from django.contrib.postgres.indexes import HashIndex
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.db import models
from django.db.models import JSONField
from django.contrib.postgres.fields import ArrayField

# Create your models here.
from django.db.models import Max, Sum
from django.db.models.functions import Coalesce
from django.utils.functional import cached_property

from irhrs.common.models import BaseModel, TimeStampedModel
from irhrs.core.utils.common import get_upload_path
from irhrs.organization.models import Organization, FiscalYear, FY
from irhrs.payroll.constants import VOLUNTARY_REBATE_DURATION_UNIT_CHOICES
from irhrs.payroll.utils.helpers import get_last_payroll_generated_date
from irhrs.users.models import UserExperience
from irhrs.payroll.utils.mixins import SoftDeletionModel, VueRouteMixin

USER = get_user_model()

DURATION_UNITS = (
    ('Hourly', 'Hourly'),
    ('Daily', 'Daily'),
    ('Monthly', 'Monthly'),
    ('Yearly', 'Yearly'),
    ('Unit Of Work', 'Unit Of Work'),
)

EXTRA_ADDITION, EXTRA_DEDUCTION = 'Extra Addition', 'Extra Deduction'
HEADING_TYPES = (
    ('Addition', 'Addition'),
    (EXTRA_ADDITION, EXTRA_ADDITION),
    ('Deduction', 'Deduction'),
    (EXTRA_DEDUCTION, EXTRA_DEDUCTION),
    ('Tax Deduction', 'Tax Deduction'),
    ('Type1Cnst', 'Type1Cnst'),
    ('Type2Cnst', 'Type2Cnst')
)

json_schema = {
    'sum_type': 'amount'  # 'rate' or 'amount'
}

BENEFIT_TYPES = (
    ('Monetary Benefit', 'Monetary Benefit'),
    ('Non Monetary Benefit', 'Non Monetary Benefit'),
    ('No Benefit', 'No Benefit')
)

QUEUED = "Queued"
PROCESSING = "Processing"
FAILED = "Failed"
COMPLETED = "Completed"

PAYROLL_GENERATION_STATUS = (
    (QUEUED, "Queued"),
    (PROCESSING, "Processing"),
    (FAILED, "Failed"),
    (COMPLETED, "Completed")
)

DEFAULT_HEADING_FIELDS_OF_PAYROLL_SETTING_TYPE = {
    'Salary Structure': {
        'available_types': ['Addition'],
        'type': 'Addition',
    },
    'Allowance Settings': {
        'available_types': ['Addition'],
        'type': 'Addition',
    },

    'Fringe Benefits': {
        'available_types': ['Addition', 'Extra Addition'],
        'type': 'Addition'
    },
    'Provident Fund': {
        'available_types': ['Deduction', 'Addition'],
        'type': 'Deduction'
    },
    'CIT': {
        'available_types': ['Deduction'],
        'type': 'Deduction'
    },
    'Social Security Fund': {
        'available_types': ['Addition', 'Deduction'],
        'type': 'Addition',
    },
    'Salary TDS': {
        'available_types': ['Tax Deduction'],
        'type': 'Tax Deduction',
    },
    'Loan or Advances': {
        'available_types': ['Extra Addition'],
        'type': 'Extra Addition',
    },
    'Expense Settlement': {
        'available_types': ['Extra Deduction'],
        'type': 'Extra Deduction',
    },
    'Penalty/Deduction': {
        'available_types': ['Extra Deduction'],
        'type': 'Extra Deduction',
    }
}

PAYROLL_SETTING_TYPES = [
    (setting, setting)
    for setting in DEFAULT_HEADING_FIELDS_OF_PAYROLL_SETTING_TYPE.keys()
]

HEADING_TYPES_NULL_FIELDS = {
    'Extra Addition': ['duration_unit', 'absent_days_impact'],
    'Extra Deduction': ['duration_unit', 'absent_days_impact'],
    'Tax Deduction': ['duration_unit', 'taxable', 'absent_days_impact'],
    'Type1Cnst': ['taxable', 'benefit_type', 'absent_days_impact'],
    'Type2Cnst': ['duration_unit', 'taxable', 'benefit_type', 'absent_days_impact']
}

HH_OVERTIME, HH_TOTAL_HOURLY_AMOUNT = 'Overtime', 'Total Hour Worked'

AVAILABLE_HOURLY_HEADINGS = [
    HH_OVERTIME,
    HH_TOTAL_HOURLY_AMOUNT,
]

HOURLY_HEADING_SOURCE_CHOICES = (
    (HH_OVERTIME, 'Overtime'),
    (HH_TOTAL_HOURLY_AMOUNT, 'Total Hour Worked')
)

PAYSLIP_GENERATED, PAYSLIP_ACKNOWLEDGEMENT_PENDING, PAYSLIP_ACKNOWLEDGED = (
    "Generated", "Pending", "Acknowledged"
)
PAYSLIP_ACKNOWLEDGEMENT_CHOICES = (
    (PAYSLIP_GENERATED, "Generated"),
    (PAYSLIP_ACKNOWLEDGEMENT_PENDING, "Pending"),
    (PAYSLIP_ACKNOWLEDGED, "Acknowledged")
)

TEMPLATE_1, TEMPLATE_2 = "Template 1", "Template 2"
PAYSLIP_TEMPLATE_CHOICES = (
    (TEMPLATE_1, TEMPLATE_1),
    (TEMPLATE_2, TEMPLATE_2)
)


class Heading(SoftDeletionModel):
    organization = models.ForeignKey(
        Organization,
        related_name='headings',
        on_delete=models.CASCADE,
        editable=False
    )

    dependencies = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='makes_dependency',
        through='HeadingDependency'
    )

    name = models.CharField(
        max_length=150
    )

    verbose_name = models.CharField(
        max_length=150,
        blank=True
    )

    type = models.CharField(
        choices=HEADING_TYPES,
        max_length=50
    )
    payroll_setting_type = models.CharField(
        choices=PAYROLL_SETTING_TYPES,
        max_length=50
    )

    duration_unit = models.CharField(
        choices=DURATION_UNITS,
        max_length=50,
        null=True,
        blank=True
    )
    taxable = models.BooleanField(
        null=True,
        blank=True
    )
    benefit_type = models.CharField(
        choices=BENEFIT_TYPES,
        max_length=50,
        null=True,
        blank=True
    )
    absent_days_impact = models.BooleanField(
        null=True,
        blank=True
    )
    year_to_date = models.BooleanField(default=False)

    hourly_heading_source = models.CharField(
        help_text="Choose Hourly Record",
        choices=HOURLY_HEADING_SOURCE_CHOICES,
        max_length=25,
        null=True,
        blank=True
    )

    # settings for daily headings
    deduct_amount_on_leave = models.BooleanField(null=True, default=None)
    pay_when_present_holiday_offday = models.BooleanField(null=True, default=None)
    deduct_amount_on_remote_work = models.BooleanField(null=True, default=None)

    order = models.PositiveIntegerField()

    """
    If multiple rules:

    [
        {
          "condition": "codition",
          "rule": "0",
          "rule_validator": {
            "editable": True,
            "numberOnly": True
          },

          // if type = tax deduction
          "tds_type": "22"
        },
        {
          "condition": "codition",
          "rule": "equation" ,
          "rule_validator": {
            "editable": True,
            "numberOnly": True
          },

          // if type = tax deduction
          "tds_type": "22"
        }
    ]

    For Single Rule:

    [
        {
          "condition": None,
          "rule": "equation",
          "rule_validator": {
            "editable": True,
            "numberOnly": True
          },

          // if type = tax deduction
          "tds_type": "22"
        },
    ]
    """
    is_editable = models.BooleanField(default=True)
    rules = JSONField()
    is_hidden = models.BooleanField(default=False)
    visible_in_package_basic_view = models.BooleanField(default=False)

    def rule_is_valid(self, **kwargs):
        from irhrs.payroll.utils.rule_validator import HeadingRuleValidator

        kwargs['heading'] = self
        validator = HeadingRuleValidator(
            **kwargs
        )
        return validator.is_valid, validator

    @classmethod
    def get_next_heading_order(cls, organization__slug):
        max_order = cls.objects.filter(
            organization__slug=organization__slug
        ).aggregate(
            Max('order')
        )['order__max']
        if max_order:
            return max_order + 1
        else:
            return 1

    @property
    def is_heading_used(self):
        """
        :returns whether heading is used by packages or is dependency of others
        """
        return self.makes_heading_dependencies.exists() or PackageHeading.objects.filter(
            heading=self).exists()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order']
        unique_together = (('organization', 'name'),)
        indexes = [
            models.Index(fields=('order', 'organization'))
        ]


class AbstractReportSetting(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE
    )
    headings = models.ManyToManyField(
        Heading,
        related_name='+'
    )

    class Meta:
        abstract = True


class PayrollCollectionDetailReportSetting(AbstractReportSetting):
    pass


class PayrollDifferenceDetailReportSetting(AbstractReportSetting):
    pass

class SSFReportSetting(AbstractReportSetting):
    pass


class DisbursementReportSetting(AbstractReportSetting):
    pass


class TaxReportSetting(AbstractReportSetting):
    pass


USERNAME, JOB_TITLE, DIVISION, EMPLOYMENT_LEVEL, EMPLOYMENT_TYPE, EMPLOYEE_LEVEL_HIERARCHY, BRANCH, STEP, \
PACKAGE_NAME, WORKING_DAYS, WORKED_DAYS, ABSENT_DAYS, WORKED_HOURS, OVERTIME_HOURS, \
SSF_NUMBER, BANK_NAME, BANK_BRANCH, BANK_ACCOUNT_NUMBER, PF_NUMBER, PAN_NUMBER, \
CIT_NUMBER = ("Username", "Job Title", "Division", "Employment Level", "Employment Type",
              "Employee Level Hierarchy", "Branch", "Step", "Package Name", "Working Days",
              "Worked Days", "Absent Days", "Worked Hours", "Overtime Hours", "SSF Number",
              "Bank Name", "Bank Branch", "Bank Account Number", "PF Number", "PAN Number",
              "CIT Number")

EXTRA_HEADING_CHOICES = (
    (USERNAME, "Username"),
    (JOB_TITLE, "Job Title"),
    (DIVISION, "Division"),
    (EMPLOYMENT_LEVEL, "Employment Level"),
    (EMPLOYMENT_TYPE, "Employment Type"),
    (EMPLOYEE_LEVEL_HIERARCHY, 'Employee Level Hierarchy'),
    (BRANCH, "Branch"),
    (STEP, "Step"),
    (PACKAGE_NAME, "Package Name"),
    (WORKING_DAYS, "Working Days"),
    (WORKED_DAYS, "Worked Days"),
    (ABSENT_DAYS, "Absent Days"),
    (WORKED_HOURS, "Worked Hours"),
    (OVERTIME_HOURS, "Overtime Hours"),
    (SSF_NUMBER, "SSF Number"),
    (BANK_NAME, "Bank Name"),
    (BANK_BRANCH, "Bank Branch"),
    (BANK_ACCOUNT_NUMBER, "Bank Account Number"),
    (PF_NUMBER, "PF Number"),
    (PAN_NUMBER, "PAN Number"),
    (CIT_NUMBER, "CIT Number"),
)


class ExtraHeadingReportSetting(models.Model):
    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE
    )
    headings = ArrayField(
        models.CharField(max_length=30, choices=EXTRA_HEADING_CHOICES),
    )


class HeadingDependency(models.Model):
    source = models.ForeignKey(
        Heading,
        on_delete=models.CASCADE,
        related_name='heading_dependencies'
    )
    target = models.ForeignKey(
        Heading,
        on_delete=models.CASCADE,
        related_name='makes_heading_dependencies'
    )


class Package(SoftDeletionModel):
    organization = models.ForeignKey(
        Organization,
        related_name='packages',
        on_delete=models.CASCADE
    )
    name = models.CharField(
        max_length=150
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    is_template = models.BooleanField(default=True)
    excel_package = models.ForeignKey(
        'ExcelPayrollPackage',
        null=True,
        related_name='packages',
        on_delete=models.SET_NULL
    )

    def get_next_heading_order(self):
        max_order = self.package_headings.all().aggregate(Max('order'))[
            'order__max']
        if max_order:
            return max_order + 1
        else:
            return 1

    @property
    def is_used_package(self):
        return self.employee_payrolls.exists()

    # designed_for
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.pk and self.is_used_package:
            raise ValidationError('This used package cannot be edited')
        super().save(*args, **kwargs)


class PackageHeading(SoftDeletionModel):
    package = models.ForeignKey(
        Package, related_name='package_headings', on_delete=models.CASCADE)

    dependencies = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='makes_dependency',
        through='PackageHeadingDependency'
    )

    heading = models.ForeignKey(Heading, on_delete=models.PROTECT)

    order = models.PositiveIntegerField()

    # Heading overriding fields

    hourly_heading_source = models.CharField(
        help_text="Choose Hourly Record",
        choices=HOURLY_HEADING_SOURCE_CHOICES,
        max_length=25,
        null=True
    )
    absent_days_impact = models.BooleanField(null=True, blank=True)
    type = models.CharField(choices=HEADING_TYPES,
                            max_length=50, null=True, blank=True)
    duration_unit = models.CharField(
        choices=DURATION_UNITS, max_length=50, null=True, blank=True)
    taxable = models.BooleanField(null=True, blank=True)
    benefit_type = models.CharField(
        choices=BENEFIT_TYPES, max_length=50, null=True, blank=True)
    rules = JSONField()

    # settings for daily headings
    deduct_amount_on_leave = models.BooleanField(null=True, default=None)
    pay_when_present_holiday_offday = models.BooleanField(null=True, default=None)
    deduct_amount_on_remote_work = models.BooleanField(null=True, default=None)

    # End Heading overriding fields

    @property
    def name(self):
        return self.heading.name

    def rule_is_valid(self):
        from irhrs.payroll.utils.rule_validator import HeadingRuleValidator

        validator = HeadingRuleValidator(
            heading=self
        )
        return validator.is_valid, validator

    def save(self, *args, **kwargs):
        if self.pk and self.is_used_package_heading:
            raise ValidationError(
                'This used package heading cannot be modified')
        # if heading overriding fields is not set set it from heading object
        heading_overriding_fields = (
            'type', 'duration_unit', 'taxable', 'benefit_type', 'absent_days_impact',
            'hourly_heading_source', 'deduct_amount_on_leave',
            'pay_when_present_holiday_offday', 'deduct_amount_on_remote_work'
        )
        for field in heading_overriding_fields:
            if getattr(self, field) is None:
                setattr(self, field, getattr(self.heading, field))
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.package) + '-' + str(self.heading)

    def validate_unique(self, exclude=None):
        super().validate_unique(exclude)
        qs = PackageHeading.objects.filter(package=self.package)
        if not self._state.adding:
            qs = qs.exclude(pk=self.pk)
        if (
            self.heading.type not in ['Type1Cnst', 'Type2Cnst']
            or self.type not in ['Type1Cnst', 'Type2Cnst']
        ) and qs.filter(
            heading=self.heading
        ).exists():
            raise ValidationError(
                'Package and Non-(Type1|Type2)Cnst heading must be unique')

    @property
    def is_used_package_heading(self):
        return self.package.employee_payrolls.exists()

    def get_vue_route_name(self):
        return 'admin-slug-payroll-settings-packages-edit-pk'

    def get_vue_route_params(self):
        return {
            'slug': self.package.organization.slug,
            'pk': self.package.id
        }

    def get_vue_route_queries(self):
        return {}

    @property
    def is_editable(self):
        return self.heading.is_editable

    class Meta:
        unique_together = (('heading', 'package'),)
        ordering = ['order']


class YearlyHeadingDetail(SoftDeletionModel):
    heading = models.ForeignKey(
        Heading,
        related_name="yearly_heading_details",
        on_delete=models.CASCADE
    )

    fiscal_year = models.ForeignKey(
        FiscalYear,
        related_name="yearly_heading_details",
        on_delete=models.CASCADE
    )

    # Should lie in between selected fiscal year
    date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f'{self.heading}--{self.fiscal_year}'

    class Meta:
        unique_together = ('heading', 'fiscal_year')


class RebateSetting(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE,
                                     related_name="rebate_settings", null=True, blank=True)
    title = models.CharField(max_length=30)
    duration_type = models.CharField(
        choices=VOLUNTARY_REBATE_DURATION_UNIT_CHOICES,
        max_length=20
    )
    amount = models.FloatField(null=True)
    is_archived = models.BooleanField(default=False)

    class Meta:
        unique_together = ('title', 'organization')

    def __str__(self):
        return self.title


class PackageHeadingDependency(models.Model):
    source = models.ForeignKey(
        PackageHeading,
        on_delete=models.CASCADE,
        related_name='package_heading_dependencies'
    )
    target = models.ForeignKey(
        PackageHeading,
        on_delete=models.CASCADE,
        related_name='makes_package_heading_dependencies'
    )


CUSTOM_INCREMENT_HOLDING_TYPES = (
    ('Grade', 'Grade'),
    ('Step', 'Step'),
)

GENERATED, APPROVED, REJECTED, APPROVAL_PENDING, CONFIRMED = (
    'Generated', 'Approved', 'Rejected', 'Approval Pending', 'Confirmed'
)

GENERATED_PAYROLL_STATUS = (
    (PROCESSING, 'Processing'),
    (GENERATED, 'Generated'),
    (APPROVAL_PENDING, 'Approval Pending'),
    (APPROVED, 'Approved'),
    (REJECTED, 'Rejected'),
    (CONFIRMED, 'Confirmed'),
)


class Payroll(models.Model):
    title = models.CharField(max_length=100, null=True)
    organization = models.ForeignKey(
        Organization,
        related_name='payrolls',
        on_delete=models.CASCADE,
        editable=False
    )
    extra_data = JSONField()
    employees = models.ManyToManyField(
        USER,
        related_name='payrolls',
        through='EmployeePayroll'
    )

    from_date = models.DateField()
    to_date = models.DateField()
    simulated_from = models.DateField(null=True)

    status = models.CharField(
        choices=GENERATED_PAYROLL_STATUS, max_length=50, default='Generated',
        db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    approved_date = models.DateTimeField(null=True)
    approved_by = models.ForeignKey(
        to=USER,
        null=True,
        related_name='approved_payrolls',
        on_delete=models.SET_NULL
    )
    approval_pending = models.ForeignKey(
        to=USER,
        null=True,
        related_name='pending_payroll_approvals',
        on_delete=models.SET_NULL
    )
    def __str__(self):
        return self.organization.name
    class Meta:
        ordering = ['from_date']
        indexes = [
            models.Index(fields=('organization', 'from_date', 'to_date')),
            HashIndex(fields=('status',))
        ]

    def get_heading_amount(self, employee, package_heading_obj):
        # for package heading added after payroll has been generated
        # return 0
        record = ReportRowRecord.objects.filter(
            employee_payroll__employee=employee,
            employee_payroll__payroll=self,
            heading=package_heading_obj.heading
        ).first()
        return record.amount if record else 0.0

    def total_addition(self, employee):
        return ReportRowRecord.objects.filter(
            employee_payroll__employee=employee,
            employee_payroll__payroll=self,
            heading__type__in=[
                'Addition',
                'Extra Addition',
            ]
        ).aggregate(
            total_amount=Coalesce(
                Sum('amount'),
                0
            )
        ).get('total_amount')

    def total_deduction(self, employee):
        return ReportRowRecord.objects.filter(
            employee_payroll__employee=employee,
            employee_payroll__payroll=self,
            heading__type__in=[
                'Deduction',
                'Extra Deduction',
                'Tax Deduction',
            ]
        ).aggregate(
            total_amount=Coalesce(
                Sum('amount'),
                0
            )
        ).get('total_amount')

    def get_cash_in_hand(self, employee):
        return self.total_addition(employee) - self.total_deduction(employee)

    # below function has no use
    def get_ctc_amount(self, employee):
        total_amount = self.rows.filter(
            employee=employee).aggregate(Sum('cost_to_company'))
        return total_amount.get('cost_to_company__sum', 0) or 0


class SignedPayrollHistory(BaseModel):
    payroll = models.ForeignKey(
        to=Payroll,
        related_name='signed_payrolls',
        on_delete=models.CASCADE
    )
    attachment = models.FileField(
        upload_to=get_upload_path,
        validators=[FileExtensionValidator(
            allowed_extensions=settings.ACCEPTED_FILE_FORMATS_LIST)]
    )
    is_latest = models.BooleanField(default=False)

    def save(self, **kwargs):
        SignedPayrollHistory.objects.filter(
            payroll=self.payroll).update(is_latest=False)
        self.is_latest = True
        super().save(**kwargs)


class PayrollGenerationHistory(BaseModel):
    payroll = models.OneToOneField(
        to=Payroll,
        related_name='generation',
        null=True,
        on_delete=models.SET_NULL
    )
    status = models.CharField(
        choices=PAYROLL_GENERATION_STATUS,
        max_length=10,
        db_index=True
    )
    organization = models.ForeignKey(
        to=Organization,
        null=False,
        on_delete=models.CASCADE
    )

    # input for payroll generation
    data = JSONField()

    # error response from payroll generation
    errors = JSONField()

    @property
    def is_deleted(self):
        """
        Payroll is deleted by user after generation.
        :return:
        """
        return self.status == COMPLETED and not self.payroll

    def __str__(self):
        return str(self.organization) + ' - ' + str(self.status)


class PayrollEmployeeAddedHistory(BaseModel):
    payroll = models.ForeignKey(Payroll, related_name='added_employees', on_delete=models.CASCADE)
    data = JSONField()
    errors = JSONField()

    def __str__(self):
        return f"added employee history of {self.payroll.title}."


(PROCESSING, DONE, FAILED) = ('Processing', 'Done', 'Failed')

excel_update_status_choices = (
    (PROCESSING, PROCESSING),
    (DONE, DONE),
    (FAILED, FAILED)
)


class PayrollExcelUpdateHistory(BaseModel):
    payroll = models.ForeignKey(
        Payroll,
        related_name="excel_updates",
        on_delete=models.CASCADE
    )

    excel_file = models.FileField(
        upload_to=get_upload_path
    )

    status = models.CharField(
        choices=excel_update_status_choices,
        max_length=150,
        db_index=True
    )


class EmployeePayroll(VueRouteMixin, models.Model):
    employee = models.ForeignKey(
        USER, related_name="employee_payrolls", on_delete=models.PROTECT)
    payroll = models.ForeignKey(
        Payroll,
        related_name='employee_payrolls',
        on_delete=models.CASCADE
    )

    # package kept here and now change other codes accordingly
    package = models.ForeignKey(
        Package,
        related_name='employee_payrolls',
        on_delete=models.PROTECT
    )

    # acknowledgement status
    acknowledgement_status = models.CharField(
        choices=PAYSLIP_ACKNOWLEDGEMENT_CHOICES,
        max_length=30,
        default=PAYSLIP_GENERATED,
        db_index=True
    )
    acknowledged_at = models.DateTimeField(null=True)

    # tax details
    annual_gross_salary = models.FloatField(default=0)
    rebate_amount = models.FloatField(default=0)
    annual_gross_salary_after_rebate = models.FloatField(default=0)
    annual_tax = models.FloatField(default=0)
    paid_tax = models.FloatField(default=0)
    tax_to_be_paid = models.FloatField(default=0)

    tax_rule = models.TextField(blank=True)
    tax_condition = models.TextField(blank=True)
    tds_type = models.TextField(blank=True)
    user_note = models.TextField(
        null=True, max_length=settings.TEXT_FIELD_MAX_LENGTH)

    class Meta:
        unique_together = (('employee', 'payroll'),)
        indexes = [
            models.Index(fields=('employee', 'payroll', 'package'), ),
        ]

    @cached_property
    def user_experience_package_slot(self):
        from_date = self.payroll.from_date
        to_date = self.payroll.to_date

        user_experience = self.employee.first_date_range_user_experiences(
            from_date,
            to_date
        )

        # TODO: @Ravi update uses of this method to handle None response
        if not user_experience:
            return None

        user_experience_packages = (
            user_experience.user_experience_packages.order_by(
                'active_from_date'
            )
        )

        return user_experience_packages.filter(
            active_from_date__lte=from_date,
            package=self.package
        ).last()

    @property
    def is_acknowledged(self):
        return self.acknowledgement_status == PAYSLIP_ACKNOWLEDGED

    def __str__(self):
        return f"{self.get_acknowledgement_status_display()} {self.employee} {self.payroll}"


class EmployeePayrollComment(TimeStampedModel):
    employee_payroll = models.ForeignKey(
        EmployeePayroll,
        related_name='employee_payroll_comments',
        on_delete=models.CASCADE
    )
    commented_by = models.ForeignKey(
        USER,
        related_name='employee_payroll_comments',
        on_delete=models.CASCADE
    )
    remarks = models.TextField(max_length=600)

    def __str__(self):
        return f"{self.commented_by} commented on {self.employee_payroll}"


class PayrollEditHistoryAmount(models.Model):
    payroll_history = models.ForeignKey(
        to='payroll.EmployeePayrollHistory',
        on_delete=models.CASCADE,
        related_name='amount_history'
    )
    # both fields are kept for transition phase
    package = models.ForeignKey(
        to=PackageHeading,
        related_name='+',
        on_delete=models.CASCADE,
        null=True
    )

    heading = models.ForeignKey(
        Heading,
        on_delete=models.CASCADE,
        null=True,
        related_name='+',
    )
    old_amount = models.FloatField(null=True)
    new_amount = models.FloatField(null=True)


class EmployeePayrollHistory(BaseModel):
    employee_payroll = models.ForeignKey(
        to=EmployeePayroll,
        related_name='history',
        on_delete=models.CASCADE
    )
    remarks = models.CharField(max_length=255)
    packages = models.ManyToManyField(
        to=Heading,
        through='PayrollEditHistoryAmount',
        related_name='+',
        # through_fields=('package', 'payroll_history')
    )

    def __str__(self):
        return self.remarks + str(self.employee_payroll.employee)


class ReportRowRecord(VueRouteMixin, models.Model):
    employee_payroll = models.ForeignKey(
        EmployeePayroll,
        related_name='report_rows',
        on_delete=models.CASCADE
    )
    from_date = models.DateField()
    to_date = models.DateField()

    # both fields are kept for transition phase
    package_heading = models.ForeignKey(
        PackageHeading,
        related_name='report_rows',
        null=True,
        on_delete=models.PROTECT
        # -- This field is to be deleted in next release -- #
    )
    heading = models.ForeignKey(
        Heading,
        related_name='report_rows',
        on_delete=models.PROTECT,
        null=True
    )
    amount = models.FloatField()

    # Remaining fiscal year projected amount
    # This will be available only for headings with duration unit
    # 'Yearly' and 'Monthly'
    projected_amount = models.FloatField(default=0.0)

    # default 0.0 is set to support migration and add package amount by running
    # self.package_amount = self.current_package_amount
    package_amount = models.FloatField(default=0.0)

    plugin_sources = JSONField(default=list)

    class Meta:
        ordering = ('heading__order',)
        indexes = [
            models.Index(
                fields=('employee_payroll', '-from_date', '-to_date'),
                name='report_row_composite_index'
            )
        ]

    @classmethod
    def get_current_fiscal_year_payroll_stat(cls, employee, today_date):
        output_data = dict()
        if not (employee.detail and employee.detail.organization):
            return output_data

        fy = FY(employee.detail.organization)

        fy_year_slots = fy.get_fiscal_year_data_from_date_range(
            today_date,
            today_date
        )
        if fy_year_slots:
            fy_start, fy_end = fy_year_slots[0].get('fy_slot')

            current_fy_report_rows = cls.objects.filter(
                from_date__gte=fy_start,
                to_date__lte=fy_end,
                employee_payroll__employee=employee
            )

            for row in current_fy_report_rows:
                if output_data.get(row.heading.name, None):
                    output_data[row.heading.name] += row.amount
                else:
                    output_data[row.heading.name] = row.amount
        return output_data

    @property
    def current_package_amount(self):
        package_slot = self.employee_payroll.user_experience_package_slot
        return getattr(
            package_slot.package_rows.filter(
                package_heading=self.package_heading).first(),
            'package_amount',
            None
        )


class SalaryHolding(models.Model):
    employee = models.ForeignKey(
        USER, related_name='salary_holdings', on_delete=models.CASCADE)
    from_date = models.DateTimeField(auto_now_add=True)
    to_date = models.DateTimeField(null=True, blank=True)
    released = models.BooleanField(default=False)
    hold_remarks = models.CharField(max_length=255)
    release_remarks = models.CharField(max_length=255, blank=True)

    @property
    def paid(self) -> bool:
        return Payroll.objects.filter(
            from_date=self.from_date,
            to_date=self.to_date,
            employees__in=[self.employee]
        ).distinct().exists()

    def __str__(self):
        return "%s-%s-%s" % (
            self.employee,
            self.from_date,
            self.to_date,
        )

    def save(self, *args, **kwargs):
        if not self.to_date and self.released:
            raise ValidationError(
                'Salary Holding cannot be released with to_date None'
            )
        super().save(*args, **kwargs)


class UserExperiencePackageSlot(SoftDeletionModel):
    user_experience = models.ForeignKey(
        UserExperience,
        related_name='user_experience_packages',
        on_delete=models.PROTECT
    )

    active_from_date = models.DateField()

    backdated_calculation_from = models.DateField(null=True, blank=True)
    backdated_calculation_generated = models.BooleanField(default=False)

    package = models.ForeignKey(
        Package,
        related_name='employee_payroll_packages',
        on_delete=models.PROTECT
    )
    excel_package = models.ForeignKey(
        to='ExcelPayrollPackage',
        related_name='package_slots',
        on_delete=models.SET_NULL,
        null=True
    )
    def __str__(self):
        return self.package.name
    class Meta:
        indexes = [
            models.Index(fields=('user_experience', 'package', '-active_from_date'))
        ]

    @property
    def is_used_package(self):
        # return self.package.employee_payrolls.filter(employee=self.user_experience.user).exists()
        last_paid = get_last_payroll_generated_date(self.user_experience.user)
        return last_paid and self.active_from_date <= last_paid

    @property
    def used_upto_date(self):
        package_latest_report_row_record = ReportRowRecord.objects.filter(
            employee_payroll__package=self.package,
        ).order_by('-to_date').first()

        return package_latest_report_row_record.to_date if (
            package_latest_report_row_record
        ) else None

    def get_vue_route_name(self):
        return 'admin-slug-payroll-settings-packages-edit-pk'

    def get_vue_route_params(self):
        return {
            'slug': self.package.organization.slug,
            'pk': self.package.id
        }

    def get_vue_route_queries(self):
        return {}


class ReportRowUserExperiencePackage(models.Model):
    """
    Package Amounts for headings in package slot
    """
    package_slot = models.ForeignKey(
        UserExperiencePackageSlot,
        related_name='package_rows',
        on_delete=models.CASCADE
    )
    package_heading = models.ForeignKey(
        PackageHeading,
        related_name='package_rows',
        on_delete=models.CASCADE
    )
    package_amount = models.FloatField()

    class Meta:
        unique_together = ('package_slot', 'package_heading')
        indexes = [
            models.Index(fields=('-package_slot', 'package_heading'))
        ]


class OverviewConfig(VueRouteMixin, models.Model):
    organization = models.OneToOneField(
        Organization,
        related_name='overview_report_config',
        on_delete=models.CASCADE
    )

    salary_payable = models.ForeignKey(
        Heading,
        related_name='salary_payable_overview_configs',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    tds_payment = models.ForeignKey(
        Heading,
        related_name='tds_payment_overview_configs',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    provident_fund = models.ForeignKey(
        Heading,
        related_name='provident_fund_overview_configs',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    cit = models.ForeignKey(
        Heading,
        related_name='cit_overview_configs',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    gratuity = models.ForeignKey(
        Heading,
        related_name='gratuity_overview_configs',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    payroll_cost = models.ForeignKey(
        Heading,
        related_name='payroll_cost_overview_configs',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    salary_range = models.ForeignKey(
        Heading,
        related_name='salary_range_overview_configs',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    cost_to_company = models.ForeignKey(
        Heading,
        related_name='cost_to_company_overview_configs',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    cash_in_hand = models.ForeignKey(
        Heading,
        related_name='cash_in_hand_overview_configs',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    actual_earned = models.ForeignKey(
        Heading,
        related_name='actual_earned_overview_configs',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    salary_payment_detail_bar_graph_headings = models.ManyToManyField(
        Heading,
        related_name='salary_payment_detail_bar_graph_headings_overview_configs',
        blank=True
    )

    def __str__(self):
        return f"Report Settings of {self.organization.name}"

    def get_vue_route_name(self):
        return 'admin-slug-payroll-settings-report-settings'

    def get_vue_route_params(self):
        return {
            'slug': self.organization.slug
        }


class OrganizationPayrollConfig(models.Model):
    organization = models.OneToOneField(
        Organization,
        related_name='organization_payroll_config',
        on_delete=models.CASCADE
    )

    start_fiscal_year = models.ForeignKey(
        FiscalYear,
        related_name='organization_payroll_config',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    include_holiday_offday_in_calculation = models.BooleanField(
        default=False,
        help_text='Include holiday/offday count in calculation. It will add'
                  'holiday/offday count in both working days and worked days.'
                  'In other words holiday/offday will be counted as present'
                  ' days.'
    )
    enable_unit_of_work = models.BooleanField(
        default=False,
        help_text='Enable unit of work feature.'
    )
    payslip_template = models.CharField(
        max_length=15, choices=PAYSLIP_TEMPLATE_CHOICES, default=TEMPLATE_1)
    payslip_note = models.TextField(max_length=600, blank=True)
    show_generated_payslip = models.BooleanField(
        default=False,
        help_text="Show payslip to users once generated if true."
                  "else, payslip is only shown when confirmed."
    )
    display_heading_with_zero_value = models.BooleanField(
        default=False,
        help_text="disly headings with zero values if true"
    )

    @classmethod
    def get_payslip_template(cls, organization):
        return getattr(cls.objects.filter(organization=organization).first(),
                       'payslip_template', TEMPLATE_1)


class ReportSalaryBreakDownRangeConfig(models.Model):
    overview_config = models.ForeignKey(
        OverviewConfig,
        related_name='salary_breakdown_ranges',
        on_delete=models.CASCADE
    )
    from_amount = models.PositiveIntegerField()
    to_amount = models.PositiveIntegerField()


class ExternalTaxDiscount(BaseModel):
    """
    External tax discount applicable for user in given fiscal year
    """

    employee = models.ForeignKey(
        USER,
        related_name='external_tax_discounts',
        on_delete=models.CASCADE
    )

    fiscal_year = models.ForeignKey(
        FiscalYear,
        related_name='external_tax_discounts',
        on_delete=models.PROTECT
    )

    title = models.CharField(max_length=200)
    description = models.TextField(max_length=1000)
    attachment = models.FileField(
        upload_to=get_upload_path,
        validators=[FileExtensionValidator(
            allowed_extensions=list(itertools.chain.from_iterable(
                settings.ACCEPTED_FILE_FORMATS.values()))
        )]
    )

    amount = models.FloatField(validators=[MinValueValidator(limit_value=0)])


class BackdatedCalculation(BaseModel):
    """
    Model to store backdated calculation
    """
    package_slot = models.ForeignKey(
        UserExperiencePackageSlot,
        related_name="backdated_calculations",
        on_delete=models.CASCADE
    )
    heading = models.ForeignKey(
        Heading, related_name="backdated_calculations", on_delete=models.PROTECT
    )
    previous_amount = models.FloatField(null=True, blank=True)
    current_amount = models.FloatField(null=True, blank=True)
    adjusted_payroll = models.ForeignKey(
        EmployeePayroll,
        on_delete=models.SET_NULL,
        null=True,
        help_text="Employee Payroll Instance where this record is adjusted",
        related_name='adjusted_backdated_calculations'
    )

    class Meta:
        ordering = ('heading__order', 'created_at')

    def get_vue_route_name(self):
        return 'admin-slug-payroll-settings'

    def get_vue_route_params(self):
        return {
            'slug': self.heading.organization.slug,
            'pk': self.id
        }

    def get_vue_route_queries(self):
        return {}

    def __str__(self):
        return f'{self.package_slot} - {self.heading.name}'

    @property
    def difference(self):
        current = self.current_amount if self.current_amount else 0
        previous = self.previous_amount if self.previous_amount else 0
        total = float('{:0.2f}'.format(current - previous))
        return total


class ExcelPayrollPackage(BaseModel):
    name=models.CharField(max_length=100, unique=True)
    organization=models.ForeignKey(to=Organization, on_delete=models.CASCADE)
    cloned_from= models.ForeignKey(to=Package, null=True, on_delete=models.SET_NULL)
    assigned_date = models.DateField()

    PROCESSING, COMPLETED, FAILED = "Processing", "Completed", "Failed"
    bulk_assign_status = (
        (PROCESSING, PROCESSING),
        (COMPLETED, COMPLETED),
        (FAILED, FAILED)
    )

    status = models.CharField(choices=bulk_assign_status, default=PROCESSING, max_length=10)


CREATED_PACKAGE, CLONED_PACKAGE, PACKAGE_DELETED, ASSIGNED, UNASSIGNED, UPDATED_PACKAGE = "Created", "Cloned", "Deleted", "Assigned", \
        "Unassigned", "Updated"
action = (
    (CREATED_PACKAGE, CREATED_PACKAGE),
    (CLONED_PACKAGE, CLONED_PACKAGE),
    (PACKAGE_DELETED, PACKAGE_DELETED),
    (ASSIGNED, ASSIGNED),
    (UNASSIGNED, UNASSIGNED),
    (UPDATED_PACKAGE, UPDATED_PACKAGE)
)


class PayrollPackageActivity(BaseModel):
    title = models.CharField(max_length=255)
    assigned_to = models.ForeignKey(USER, on_delete=models.CASCADE, null=True)
    action = models.CharField(choices=action, default="Created", max_length=10)
    package = models.ForeignKey(Package, on_delete=models.SET_NULL, null=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.title
