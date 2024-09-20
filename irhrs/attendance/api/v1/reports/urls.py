from django.conf.urls import url
from rest_framework.routers import DefaultRouter

from irhrs.attendance.api.v1.reports.serializers.averages import \
    WorkHoursAverageViewSet
from irhrs.attendance.api.v1.reports.views.adjustments import AdjustmentReportViewSet
from irhrs.attendance.api.v1.reports.views.attendance_by_category import \
    AttendanceByCategoryViewSet, AttendanceByCategorySummaryViewSet, \
    UserByAttendanceCategoryFrequencyViewSet
from irhrs.attendance.api.v1.reports.views.break_in_break_out import \
    BreakInBreakOutReportView
from irhrs.attendance.api.v1.reports.views.late_in_early_out import \
    DepartmentAbsentReportViewSet, AttendanceIrregularitiesViewSet, \
    TimeSheetEntryCategoryViewSet, UserAttendanceIrregularityViewSet
from irhrs.attendance.api.v1.reports.views.monthly_attendance import \
    MonthlyAttendanceReport
from irhrs.attendance.api.v1.reports.views.most_missing import \
    MostMissingPunchViewSet
from irhrs.attendance.api.v1.reports.views.overtime import OverTimeClaimReport
from irhrs.attendance.api.v1.reports.views.shift_overview import \
    WorkShiftOverViewViewSet
from irhrs.attendance.api.v1.reports.views.summary import \
    AttendanceSummaryInformation, AttendanceOverviewViewSet, \
    NormalUserAttendanceOverviewViewSet
from .views import TimeSheetEntryReportViewSet
from .views.actionable_report import AttendanceActionableReport
from .views.individual_attendance_report import \
    IndividualAttendanceReport, IndividualAttendanceOverviewView, \
    MonthlyAttendanceOverview, OvertimeDetailReport, ComparativeOvertimeReport, \
    AttendanceGeoLocationReport, DailyAttendanceReconciliationReport, EmployeeAttendanceInsight, \
    AttendanceHeadingReportSettingViewSet

router = DefaultRouter()

router.register(
    r'by-category',
    AttendanceByCategorySummaryViewSet,
    basename='attendance-by-category-summary'
)
router.register(
    r'by-category/most/(?P<category>[\w-]+)',
    UserByAttendanceCategoryFrequencyViewSet,
    basename='attendance-most-by-category-summary'
)

router.register(
    r'by-category/(?P<category>[\w-]+)',
    AttendanceByCategoryViewSet,
    basename='attendance-by-category'
)

router.register(
    r'most-missing/(?P<category>[\w-]+)',
    MostMissingPunchViewSet,
    basename='most-missing-punch'
)

router.register(
    'work-shift/overview',
    WorkShiftOverViewViewSet,
    basename='shift-overview'
)

router.register(
    'summary',
    AttendanceSummaryInformation,
    basename='attendance-summary-information'
)
router.register(
    r'individual',
    IndividualAttendanceReport,
    basename='individual-attendance-report'
)
router.register(
    r'geo-location',
    AttendanceGeoLocationReport,
    basename='geo-location-report'
)
router.register(
    r'individual-overview',
    IndividualAttendanceOverviewView,
    basename='individual-overview-report'
)

router.register(
    r'daily-attendance-reconciliation',
    DailyAttendanceReconciliationReport,
    basename='daily-attendance-reconciliation-report'
)

router.register(
    r'employee-attendance-insight',
    EmployeeAttendanceInsight,
    basename='employee-attendance-insight-report'
)
router.register(
    r'attendance-heading-report-setting',
    AttendanceHeadingReportSettingViewSet,
    basename='attendance-heading-report-setting'
)

router.register(
    r'overtime-overview',
    OvertimeDetailReport,
    basename='overtime-overview-report'
)

router.register(
    r'monthly-overview',
    MonthlyAttendanceOverview,
    basename='monthly-overview-report'
)

router.register(
    r'comparative-overtime-report',
    ComparativeOvertimeReport,
    basename='comparative-overtime-report'
)

router.register(
    'late-in-early-out',
    TimeSheetEntryReportViewSet,
    basename='late-in-early-out-report'
)

router.register(
    'average-report',
    WorkHoursAverageViewSet,
    basename='average-report'
)

router.register(
    'absent-report',
    DepartmentAbsentReportViewSet,
    basename='absent-report'
)

router.register(
    'irregularity-report',
    AttendanceIrregularitiesViewSet,
    basename='irregularity-report'
)

router.register(
    'breakout-report',
    TimeSheetEntryCategoryViewSet,
    basename='breakout-report'
)

router.register(
    'break-in-break-out-report',
    BreakInBreakOutReportView,
    basename='break-in-out-report'
)
router.register(
    'overtime-claim',
    OverTimeClaimReport,
    basename='overtime-claim-report'
)

router.register(
    'user-overview',
    NormalUserAttendanceOverviewViewSet,
    basename='user-overview'
)

router.register(
    r'user-irregularity/(?P<user_id>\d+)',
    UserAttendanceIrregularityViewSet,
    basename='user-overview'
)
router.register(
    'adjustment-report',
    AdjustmentReportViewSet,
    basename='adjustment-report'
)
router.register(
    'monthly-attendance-report',
    MonthlyAttendanceReport,
    basename='monthly-attendance-report'
)
router.register(
    r'yearly-report/(?P<user_id>\d+)',
    AttendanceActionableReport
)

urlpatterns = router.urls + [
    url(
        r'^overview/(?P<steps>([\w\-]+/?){1,2})',
        view=AttendanceOverviewViewSet.as_view({'get': 'retrieve'}),
        name='reports-overview'
    )
]
