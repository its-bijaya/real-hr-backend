"""merojob_payroll URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import re_path
from rest_framework.routers import DefaultRouter

from irhrs.payroll.api.v1 import views as payroll_api
from irhrs.payroll.api.v1.views.advance_salary_request import AdvanceSalaryRequestViewSet, \
    AdvanceSalarySurplusRequestViewSet
from irhrs.payroll.api.v1.views.advance_salary_settings import (EligibilitySettingViewSet,
                                                                AmountSettingViewSet,
                                                                ApprovalSettingViewSet)
from irhrs.payroll.api.v1.views.clone_package import ClonePackageViewSet
from irhrs.payroll.api.v1.views.employee_metics_report import EmployeeMetricsReportViewSet, \
    EmployeeMetricHeadingReportSettingViewSet
from irhrs.payroll.api.v1.views.package_activity import PayrollPackageActivityViewSet
from irhrs.payroll.api.v1.views.payroll import (
    ExcelPayrollPackageViewSet,
    PayrollAPIViewSet,
    EmployeePayrollAPIViewSet,
    PayrollDetailExportViewSet,
    PayrollGenerationHistoryViewSet,
    PayrollApprovalViewSet,
    SignedPayrollHistoryAPIViewSet,
    EmployeePayrollCommentAPIViewSet
)
from irhrs.payroll.api.v1.views.payroll_approval_settings import PayrollApprovalSettingsViewSet
from irhrs.payroll.api.v1.views.payroll_increment import PayrollIncrementViewSet
from irhrs.payroll.api.v1.views.payroll_views import show_generated_payslip, \
    RebateSettingAPIViewSet, get_payroll_generated_employee_count
from irhrs.payroll.api.v1.views.payslip import PayslipAPIViewSet, PaySlipResponseViewSet, PayslipReportSettingViewSet
from irhrs.payroll.api.v1.views.reports import PayrollTaxReportViewSet, PayrollPFReportViewSet, \
    PayrollGeneralReportViewSet, PackageWiseSalaryViewSet, HeadingWiseExpenditureViewSet, \
    BackdatedCalculationReportViewSet, \
    YearlyPayslipReport, PayrollSSFReportViewSet, PayrollSSFReportSettingViewSet, \
    PayrollDisbursementReportSettingViewSet, PayrollDisbursementReportViewSet, \
    PayrollTaxReportSettingViewSet, PayrollCollectionDetailSettingViewSet, \
    PayrollExtraHeadingReportSettingViewSet, PayrollDifferenceDetailSettingViewSet
from irhrs.payroll.api.v1.views.salary_difference_sheet import SalaryDifferenceSheet
from irhrs.payroll.api.v1.views.unit_of_work_requests import UnitOfWorkRequestViewSet
from irhrs.payroll.api.v1.views.unit_of_work_settings import OperationViewSet, \
    OperationCodeViewSet, OperationRateViewSet, UserOperationRateViewSet

from irhrs.payroll.api.v1.views.monthly_tax_report_settings import MonthlyTaxReportSettingViewSet

from irhrs.payroll.api.v1.views.user_voluntary_rebate_requests import UserVoluntaryRebateApiViewset

app_name = 'payroll'

router = DefaultRouter()

router.register('packages', payroll_api.PackageAPIViewSet)
router.register('user-experience-package',
                payroll_api.UserExperiencePackageSlotAPIViewSet)
router.register('headings', payroll_api.HeadingAPIViewSet)
router.register('package-headings', payroll_api.PackageHeadingAPIViewSet)


# router.register('designations', payroll_api.DesignationAPIViewSet)
router.register('employees', payroll_api.EmployeeAPIViewSet)
router.register(r'employees/(?P<user_id>\d+)/payslip', PayslipAPIViewSet, basename='payslip')
router.register('payrolls', PayrollAPIViewSet, basename='payrolls')
router.register(r'(?P<organization_slug>[\w\-]+)/payrolls-difference', SalaryDifferenceSheet,
                basename='payrolls-difference')
router.register(r'(?P<organization_slug>[\w\-]+)/payroll-package-activity',
                PayrollPackageActivityViewSet, basename='payroll-package-activity'),
router.register('approvals', PayrollApprovalViewSet, basename='approval')
router.register(r'payrolls/(?P<payroll_id>\d+)', PayrollDetailExportViewSet, basename='payroll-export')
router.register(
    r'employee-payrolls/(?P<employee_payroll_id>\d+)/comments',
    EmployeePayrollCommentAPIViewSet
)

router.register(
    r'payrolls/(?P<payroll_id>\d+)/signed-payrolls',
    SignedPayrollHistoryAPIViewSet,
    basename='signed_payroll'
)
router.register('employee-payroll', EmployeePayrollAPIViewSet)

router.register('report-rows', payroll_api.ReportRowRecordAPIViewSet)
router.register('overview-configs', payroll_api.OrganizationOverviewConfigAPIViewSet, basename='payroll-overview-configs')
router.register('organization-payroll-configs', payroll_api.OrganizationPayrollConfigAPIViewSet,
                basename='payroll-config')

router.register(
    r'(?P<organization_slug>[\w\-]+)/yearly-heading-details', payroll_api.YearlyHeadingDetailAPIViewSet)
router.register(
    r'(?P<organization_slug>[\w\-]+)/payroll-history', PayrollGenerationHistoryViewSet)

# TODO remove 'external-tax-discount' url along with it dependencies
router.register(
    r'(?P<organization_slug>[\w\-]+)/external-tax-discounts', payroll_api.ExternalTaxDiscountAPIViewSet)
router.register(r'(?P<organization_slug>[\w\-]+)/user-experience-package-list',
                payroll_api.EmployeeUserExperiencePackageListViewSet)
router.register(r'(?P<organization_slug>[\w\-]+)/payslip/response',
                PaySlipResponseViewSet)
router.register(
    r'(?P<organization_slug>[\w\-]+)/salary-holdings', payroll_api.SalaryHoldingAPIViewSet)
router.register(
    r'(?P<organization_slug>[\w\-]+)/packages/clone', ClonePackageViewSet)
router.register(r'(?P<organization_slug>[\w\-]+)/tax-report-setting',
                PayrollTaxReportSettingViewSet)
router.register(r'(?P<organization_slug>[\w\-]+)/payrolls/(?P<payroll_id>\d+)/reports/tax',
                PayrollTaxReportViewSet, basename='tax-report')
router.register(r'(?P<organization_slug>[\w\-]+)/payrolls/(?P<payroll_id>\d+)/reports/pf',
                PayrollPFReportViewSet)
router.register(r'(?P<organization_slug>[\w\-]+)/payroll-extra-heading-setting',
                PayrollExtraHeadingReportSettingViewSet, basename='payroll-extra-heading-setting')
router.register(r'(?P<organization_slug>[\w\-]+)/payroll-collection-report-setting',
                PayrollCollectionDetailSettingViewSet, basename='payroll-collection-report-setting')
router.register(r'(?P<organization_slug>[\w\-]+)/payroll-difference-heading-setting',
                PayrollDifferenceDetailSettingViewSet, basename='payroll-difference-heading-setting')
router.register(r'(?P<organization_slug>[\w\-]+)/ssf-report-setting',
                PayrollSSFReportSettingViewSet)
router.register(r'(?P<organization_slug>[\w\-]+)/payrolls/(?P<payroll_id>\d+)/reports/ssf',
                PayrollSSFReportViewSet)
router.register(r'(?P<organization_slug>[\w\-]+)/disbursement-report-setting',
                PayrollDisbursementReportSettingViewSet, basename='disbursement-report-setting')
router.register(r'(?P<organization_slug>[\w\-]+)/payrolls/(?P<payroll_id>\d+)/reports/disbursement',
                PayrollDisbursementReportViewSet, basename='disbursement-report')
router.register(r'(?P<organization_slug>[\w\-]+)/reports/general-info',
                PayrollGeneralReportViewSet, basename='payroll-general-info')
router.register(
    r'(?P<organization_slug>[\w\-]+)/reports/package-info',
    PackageWiseSalaryViewSet,
    basename='payroll-package-info'
)
router.register(
    r'(?P<organization_slug>[\w\-]+)/reports/heading-expenditure',
    HeadingWiseExpenditureViewSet,
    basename='payroll-heading-expenditure'
)
router.register(
    r'(?P<organization_slug>[\w\-]+)/reports/yearly-payslip',
    YearlyPayslipReport,
    basename='yearly-payslip'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/reports/backdated-calculations/(?P<package_slot_id>\d+)',
    BackdatedCalculationReportViewSet,
    basename='backdated-calculations'
)
router.register(
    r'(?P<organization_slug>[\w\-]+)/settings/advance-salary/(?P<setting_type>(eligibility|disbursement))',
    EligibilitySettingViewSet,
    basename='eligibility-setting'
)


router.register(
    r'(?P<organization_slug>[\w\-]+)/advance-salary/requests',
    AdvanceSalaryRequestViewSet,
    basename='advance-salary-request'
)
router.register(
    r'(?P<organization_slug>[\w\-]+)/advance-salary/surplus-requests',
    AdvanceSalarySurplusRequestViewSet,
    basename='advance-salary-surplus-request'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/tax-report-settings',
    MonthlyTaxReportSettingViewSet,
    basename='tax-report-settings'
)
router.register(
    r'(?P<organization_slug>[\w\-]+)/rebate-setting', RebateSettingAPIViewSet,
    basename='rebate-setting'
)


router.register(
    r'(?P<organization_slug>[\w\-]+)/settings/advance-salary/amount',
    AmountSettingViewSet,
    basename='amount-setting'
)
router.register(
    r'(?P<organization_slug>[\w\-]+)/settings/advance-salary/approval',
    ApprovalSettingViewSet,
    basename='approval-setting'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/settings/unit-of-work/operations',
    OperationViewSet,
    basename='unit-of-work-operation'
)
router.register(
    r'(?P<organization_slug>[\w\-]+)/settings/unit-of-work/operation-codes',
    OperationCodeViewSet,
    basename='unit-of-work-operation-code'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/settings/unit-of-work/operation-rates',
    OperationRateViewSet,
    basename='unit-of-work-operation-rate'
)
router.register(
    r'(?P<organization_slug>[\w\-]+)/settings/unit-of-work/operation-rates/'
    r'(?P<operation_rate_id>\d+)/assign-users',
    UserOperationRateViewSet,
    basename='unit-of-work-user-operation-rate'
)
router.register(
    r'(?P<organization_slug>[\w\-]+)/settings/payroll-approval',
    PayrollApprovalSettingsViewSet,
    basename='payroll-approval-settings'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/unit-of-work/requests',
    UnitOfWorkRequestViewSet,
    basename='unit-of-work-request'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/payroll-increments',
    PayrollIncrementViewSet,
    basename='payroll-increment'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/user-voluntary-rebates',
    UserVoluntaryRebateApiViewset,
    basename='payroll-user-voluntary-rebates'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/payslip-setting',
    PayslipReportSettingViewSet,
    basename='payslip-setting'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/excel-bulk-assign',
    ExcelPayrollPackageViewSet,
    basename='excel-bulk-assign'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/employee-metrics-report',
    EmployeeMetricsReportViewSet,
    basename='employee-metrics-report'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/employee-metrics-report-setting',
    EmployeeMetricHeadingReportSettingViewSet,
    basename='employee-metrics-report-setting'
)

urlpatterns = router.urls
urlpatterns += [
    re_path(
        r'(?P<organization_slug>[\w\-]+)/show-generated-payslip',
        show_generated_payslip,
        name='show-generated-payslip'
    ),
    re_path(
        r'get-payroll-generated-employee-detail',
        get_payroll_generated_employee_count,
        name='show-generated-payslip'
    ),
]

