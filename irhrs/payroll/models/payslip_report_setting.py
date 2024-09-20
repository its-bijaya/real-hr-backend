from irhrs.payroll.constants import PAYSLIP_HEADING_CHOICES
from irhrs.payroll.models.payroll import Heading
from irhrs.common.models import BaseModel
from irhrs.organization.models import Organization
from django.db import models


(
    EMPLOYMENT_INCOME,
    LESS_ALLOWABLE_DEDUCTION,
    LESS_ALLOWABLE_REDUCTION,
    TAX_CALCULATION
) = (
    'Employment Income',
    'Less: Allowable Deductions',
    'Less: Allowable Reductions',
    'Tax Calculation'
)

MONTHLY_TAX_REPORT_SETTING_CATEGORY_CHOICES = (
    (EMPLOYMENT_INCOME, EMPLOYMENT_INCOME),
    (LESS_ALLOWABLE_DEDUCTION, LESS_ALLOWABLE_DEDUCTION),
    (LESS_ALLOWABLE_REDUCTION, LESS_ALLOWABLE_REDUCTION),
    (TAX_CALCULATION, TAX_CALCULATION)
)


class MonthlyTaxReportSetting(BaseModel):
    organization = models.ForeignKey(
        Organization,
        related_name='monthly_employee_tax_report_settings',
        on_delete=models.CASCADE
    )

    category = models.CharField(
        max_length=200,
        choices=MONTHLY_TAX_REPORT_SETTING_CATEGORY_CHOICES
    )

    heading = models.ForeignKey(
        Heading,
        related_name='monthly_employee_tax_report_setting_particulars',
        on_delete=models.CASCADE
    )

    is_highlighted = models.BooleanField(default=False)

    is_nested = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'organization',
                    'category',
                    'heading'
                ],
                name='unique_organization_category_heading')
        ]

class PayslipReportSetting(BaseModel):
    organization = models.ForeignKey(
        Organization,
        related_name='payslip_report_settings',
        on_delete=models.CASCADE
    )
    category = models.CharField(
        max_length=200,
        choices=PAYSLIP_HEADING_CHOICES,
    )
    headings = models.ManyToManyField(
        Heading,
        related_name='payslip_particulars'
    )

    class Meta:
        ordering = ('created_at', 'modified_at')

    def __str__(self):
        return f"{self.organization}: {self.category}"
