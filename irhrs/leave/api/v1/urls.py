from django.urls import path, include
from rest_framework.routers import DefaultRouter

from irhrs.leave.api.v1.reports.views.balance_report import \
    IndividualLeaveBalanceReport, CarryForwardLeaveDetails
from irhrs.leave.api.v1.reports.views.by_month import LeaveByMonth, \
    SummarizedYearlyLeaveReport
from irhrs.leave.api.v1.reports.views.central_dashboard import LeaveDashboardViewSet
from irhrs.leave.api.v1.reports.views.department_report import \
    LeaveDepartmentReport, DivisionAverageLeaveReport
from irhrs.leave.api.v1.reports.views.employee_profile_report import \
    EmployeeProfileLeaveDetails
from irhrs.leave.api.v1.reports.views.encashment import LeaveEncashmentViewSet
from irhrs.leave.api.v1.reports.views.leave_irregularities import \
    LeaveIrregularitiesViewSet
from irhrs.leave.api.v1.reports.views.on_leave import OnLeaveViewSet, \
    OnLeaveByLeaveTypeViewSet, UserOnLeaveViewSet, IndividualMonthlyLeaveDetail, \
    CompensatoryLeaveReport
from irhrs.leave.api.v1.reports.views.overview_summary import \
    LeaveOverViewSummaryViewSet, LeaveOverViewAllLeaveReport, \
    MostLeaveActionViewSet, NormalUserLeaveOverviewViewSet
from irhrs.leave.api.v1.reports.views.recurrance import RecurrenceLeaveReport
from irhrs.leave.api.v1.views.account import (
    UserLeaveAssignViewSet, LeaveAccountViewSet,
    UserLeaveRequestStatistics, UserLeaveAccountHistoryViewSet,
    MigrateOldLeaveAccountView)
from irhrs.leave.api.v1.views.compensatory import CompensatoryManageViewSet
from irhrs.leave.api.v1.views.leave_request import LeaveRequestViewSet, \
    AdminLeaveRequest, LeaveRequestDeleteViewSet
from irhrs.leave.api.v1.views.rule import LeaveRuleViewSet
from irhrs.leave.api.v1.views.settings import MasterSettingViewSet, \
    LeaveTypeViewSet, LeaveApprovalViewSet

app_name = "leave"

router = DefaultRouter()

router.register('dashboard', LeaveDashboardViewSet, basename='leave-dashboard')

leave_org_router = DefaultRouter()

leave_org_router.register(
    'request',
    LeaveRequestViewSet,
    basename='leave-request'
)

leave_org_router.register(
    'delete-request',
    LeaveRequestDeleteViewSet,
    basename='leave-delete-request'
)

leave_org_router.register(
    'request-on-behalf',
    AdminLeaveRequest,
    basename='request-on-behalf'
)
leave_org_router.register(
    'master-settings',
    MasterSettingViewSet,
    basename="master-setting"
)
leave_org_router.register(
    'leave-types',
    LeaveTypeViewSet,
    basename="leave-type"
)
leave_org_router.register(
    'leave-approval-setting',
    LeaveApprovalViewSet,
    basename='leave_approval_setting'
)
leave_org_router.register(
    'leave-rules',
    LeaveRuleViewSet,
    basename="leave-type"
)
leave_org_router.register(
    'assign-user',
    UserLeaveAssignViewSet,
    basename="assign-user"
)

leave_org_router.register(
    r'user-balance/(?P<user_id>\d+)/(?P<balance_id>\d+)/history',
    UserLeaveAccountHistoryViewSet,
    basename='user-balance-history'
)

leave_org_router.register(
    r'user-balance/(?P<user_id>\d+)/(?P<account_id>\d+)/manage',
    CompensatoryManageViewSet,
    basename='manage-compensatory'
)

leave_org_router.register(
    r'user-balance',
    LeaveAccountViewSet,
    basename='user-balance'
)

leave_org_router.register(
    r'migrate-balance',
    MigrateOldLeaveAccountView,
    basename='migrate-balance'
)

leave_org_router.register(
    r'user/(?P<user_id>\d+)/requests',
    UserLeaveRequestStatistics,
    basename='user-requests'
)

# Report URLS
leave_report_router = DefaultRouter()

leave_report_router.register(
    'on-leave',
    OnLeaveViewSet,
    basename='on-leave'
)
leave_report_router.register(
    'leave-irregularities',
    LeaveIrregularitiesViewSet,
    basename='leave-irregularities'
)

leave_report_router.register(
    'individual-leave-balance',
    IndividualLeaveBalanceReport,
    basename='individual-leave-balance-report'
)

leave_report_router.register(
    'carry-forward-details',
    CarryForwardLeaveDetails,
    basename='carry-forward-details'
)

leave_report_router.register(
    'overview/summary',
    LeaveOverViewSummaryViewSet,
    basename='overview-summary'
)
leave_report_router.register(
    'overview/all-leaves',
    LeaveOverViewAllLeaveReport,
    basename='all-leave-report'
)

leave_report_router.register(
    'overview/division/average-leave',
    DivisionAverageLeaveReport,
    basename='division-report'
)
leave_report_router.register(
    'overview/division',
    LeaveDepartmentReport,
    basename='division-report'
)

leave_report_router.register(
    'recurrence',
    RecurrenceLeaveReport,
    basename='recurrence-report'
)

leave_report_router.register(
    'leave-type-report',
    OnLeaveByLeaveTypeViewSet,
    basename='on-leave-by-type'
)

leave_report_router.register(
    'individual-leave-detail/(?P<user_id>\d+)',
    IndividualMonthlyLeaveDetail,
    basename='individual-leave-detail'
)

leave_report_router.register(
    'compensatory-leave-report',
    CompensatoryLeaveReport,
    basename='compensatory-leave-report'
)

leave_report_router.register(
    'by-month',
    LeaveByMonth,
    basename='by-month'
)

leave_report_router.register(
    'yearly-report',
    SummarizedYearlyLeaveReport,
    basename='yearly-report'
)

leave_report_router.register(
    'on-leave-users',
    UserOnLeaveViewSet,
    basename='on-leave-users'
)
leave_report_router.register(
    'most-leaves',
    MostLeaveActionViewSet,
    basename='most-leave-action'
)

leave_report_router.register(
    'user-overview',
    NormalUserLeaveOverviewViewSet,
    basename='leave-user-overview'
)

leave_report_router.register(
    'encashments',
    LeaveEncashmentViewSet,
    basename='encashments'
)

# employee profile data
leave_emp_profile = DefaultRouter()
leave_emp_profile.register(
    'detail',
    EmployeeProfileLeaveDetails,
    basename='leave-employee-profile'
)

urlpatterns = router.urls

urlpatterns += [
    path(
        '<slug:organization_slug>/',
        include(leave_org_router.urls)
    ),
    path(
        '<slug:organization_slug>/reports/',
        include(leave_report_router.urls)
    ),
    path(
        '<int:user_id>/',
        include(leave_emp_profile.urls)
    )
]
