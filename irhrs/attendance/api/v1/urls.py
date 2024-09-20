from django.urls import include, path
from rest_framework.routers import DefaultRouter

from irhrs.attendance.api.v1.views.adjustment import AttendanceAdjustmentViewSet, AttendanceBulkAdjustmentViewSet, \
    AttendanceAdjustmentUpdateDeleteEntryViewSet
from irhrs.attendance.api.v1.views.attendance import (AttendanceUserMapViewSet,
                                                      EmployeeOnLeaveFieldVisitAndAbsentViewSet,
                                                      IndividualAttendanceSettingViewSet,
                                                      ManualAttendanceViewSet,
                                                      OverTimeAndLeaveNoticeboardStatsViewset,
                                                      SingleAPIForLeaveFieldVisitAndAbsentViewSet,
                                                      TimeSheetEntrySoftDeleteViewSet,
                                                      TimeSheetViewSet,
                                                      UserTimeSheetViewSet, WebAttendanceViewSet,
                                                      IndividualSettingShiftView)
from irhrs.attendance.api.v1.views.attendance_data_server import AttendanceServerImportViewSet
from irhrs.attendance.api.v1.views.calendar import AttendanceCalendar
from irhrs.attendance.api.v1.views.import_attendance import AttendanceImportView
from irhrs.attendance.api.v1.views.issues import AttendanceIssuesViewSet
from irhrs.attendance.api.v1.views.shift_roster import TimeSheetRosterView
from irhrs.attendance.api.v1.views.source import AttendanceSourceViewSet, ConnectionTest
from irhrs.attendance.api.v1.views.travel_attendance import (TravelAttendanceDeleteRequestViewSet,
                                                             TravelAttendanceRequestViewSet,
                                                             TravelAttendanceSettingViewSet)
from irhrs.attendance.api.v1.views.workshift import (UserActiveWorkShiftViewSet, WorkShiftLegendViewSet,
                                                     WorkShiftViewSet, WorkTimingViewSet)

from .reports.views.central_dashboard import AttendanceDashboardViewSet
from .views.approve import TimeSheetApprovalViewSet
from .views.breakout_penalty import BreakOutPenaltySettingView, BreakoutPenaltyView, \
    BreakoutPenaltyUserView
from .views.credit_hours import (CreditHourDeleteRequestViewSet, CreditHourPreApprovalRequestViewSet,
                                 CreditHourSettingViewSet)
from .views.overtime import (OvertimeClaimBulkUpdateViewSet, OvertimeClaimEditViewSet,
                             OvertimeClaimHistoryViewSet,
                             OvertimeClaimViewSet, OvertimeSettingViewSet,
                             IndividualOvertimeExportView)
from .views.pre_approval import PreApprovalOvertimeViewSet
from .views.timesheet_registration_report_settings import TimeSheetRegistrationReportSettingsViewSet
from .views.timesheet_report_request import TimeSheetReportRequestViewSet

app_name = 'attendance'

router = DefaultRouter()

router.register(
    'dashboard',
    AttendanceDashboardViewSet,
    basename='attendance-dashboard'
)

# all timesheets

router.register(
    'accept',
    AttendanceServerImportViewSet,
    basename='accept-attendance'
)

router.register(
    r'timesheets',
    TimeSheetViewSet,
    basename='timesheets'
)
router.register(
    r'issues',
    AttendanceIssuesViewSet,
    basename='issues'
)


# user specific urls
router.register(
    r'users/(?P<user_id>\d+)/timesheets',
    UserTimeSheetViewSet,
    basename='user-timesheets'
)

router.register(
    r'users/(?P<user_id>\d+)/active-shift',
    UserActiveWorkShiftViewSet,
    basename='users-shift-info'
)

router.register(
    r'web',
    WebAttendanceViewSet,
    basename='web-attendance'
)
router.register(
    r'manual',
    ManualAttendanceViewSet,
    basename='manual-attendance'
)

# organization specific urls
router.register(
    r'(?P<organization_slug>[\w\-]+)/user/noticeboard/stats',
    SingleAPIForLeaveFieldVisitAndAbsentViewSet,
    basename='user-on-leave-field-visit'
)


router.register(
    r'(?P<organization_slug>[\w\-]+)/users/on/(?P<action>(leave|field-visit))',
    EmployeeOnLeaveFieldVisitAndAbsentViewSet,
    basename='user-on-leave-field-visit'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/users/(?P<action>(absent))',
    EmployeeOnLeaveFieldVisitAndAbsentViewSet,
    basename='absent-user'
)


router.register(
    r'(?P<organization_slug>[\w\-]+)/user-map',
    AttendanceUserMapViewSet,
    basename=''
)
router.register(
    r'(?P<organization_slug>[\w\-]+)/work-shifts/legend',
    WorkShiftLegendViewSet,
    basename='work-shift-legend'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/work-shifts',
    WorkShiftViewSet,
    basename='work-shift'
)
router.register(
    r'(?P<organization_slug>[\w\-]+)/work-timings',
    WorkTimingViewSet,
    basename='work-timings'
)


router.register(
    r'(?P<organization_slug>[\w\-]+)/adjustments/bulk-update',
    AttendanceBulkAdjustmentViewSet,
    basename='adjustments-bulk'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/(?P<adjustment_action>(edit|delete))-entry',
    AttendanceAdjustmentUpdateDeleteEntryViewSet,
    basename='update-entries'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/adjustments',
    AttendanceAdjustmentViewSet,
    basename='adjustments'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/users/settings',
    IndividualAttendanceSettingViewSet,
    basename='individual-settings'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/users/settings/(?P<user_id>\d+)/shifts',
    IndividualSettingShiftView,
    basename='individual-setting-shift'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/overtime/claims/'
    r'(?P<ot_claim_id>\d+)/history',
    OvertimeClaimHistoryViewSet,
    basename='overtime-claim-histories'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/overtime/claims/bulk-update',
    OvertimeClaimBulkUpdateViewSet,
    basename='overtime-claims-bulk-update'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/overtime/claims',
    OvertimeClaimViewSet,
    basename='overtime-claims'
)

router.register(
    r'source',
    AttendanceSourceViewSet,
    basename='attendance-sources'
)
router.register(
    r'(?P<organization_slug>[\w\-]+)/overtime/settings',
    OvertimeSettingViewSet,
    basename='overtime-settings'
)
router.register(
    'calendar',
    AttendanceCalendar,
    basename='attendance-calendar'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/import',
    AttendanceImportView,
    basename='attendance-import'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/travel-attendance/delete-request',
    TravelAttendanceDeleteRequestViewSet,
    basename='travel-attendance-delete-request'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/travel-attendance',
    TravelAttendanceRequestViewSet,
    basename='travel-attendance'
)

router.register(
    r'noticeboard/stats',
    OverTimeAndLeaveNoticeboardStatsViewset,
    basename='overtime-leave-noticeboard-stats'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/overtime/pre-approval',
    PreApprovalOvertimeViewSet,
    basename='pre-approval-overtime'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/credit-hour/settings',
    CreditHourSettingViewSet,
    basename='credit-hour-setting'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/credit-hour/pre-approval',
    CreditHourPreApprovalRequestViewSet,
    basename='credit-hour-request'
)
router.register(
    r'(?P<organization_slug>[\w\-]+)/timesheet-report-requests',
    TimeSheetReportRequestViewSet,
    basename='timesheet-report-request'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/credit-hour/delete-requests',
    CreditHourDeleteRequestViewSet,
    basename='credit-hour-delete-requests'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/request',
    TimeSheetApprovalViewSet,
    basename='attendance-request'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/timesheet-penalty-user-report',
    BreakoutPenaltyUserView,
    basename='timesheet-penalty-user-report',
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/timesheet-penalty-report',
    BreakoutPenaltyView,
    basename='timesheet-penalty-report',
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/timesheets',
    TimeSheetEntrySoftDeleteViewSet,
    basename='timesheet-entry'
)

router.register(
    # roster /n/: a list or plan showing turns of duty
    # or leave for individuals in organization
    r'(?P<organization_slug>[\w\-]+)/timesheet-roster',
    TimeSheetRosterView,
    basename='timesheet-roster'
)
router.register(
    r'(?P<organization_slug>[\w\-]+)/breakout-penalty-settings',
    BreakOutPenaltySettingView,
    basename='breakout-penalty-settings'
)
router.register(
    r'(?P<organization_slug>[\w\-]+)/overtime-claims/individual/(?P<user_id>\d+)',
    IndividualOvertimeExportView,
)

urlpatterns = router.urls

urlpatterns += [
    path('<slug:organization_slug>/overtime/',
         include([
             path('claims/<int:claim>/edit/',
                  OvertimeClaimEditViewSet.as_view({
                      'get': 'retrieve',
                      'put': 'update',
                  }), name='overtime-claim-detail')
         ])),
    path('<slug:organization_slug>/reports/', include(
        'irhrs.attendance.api.v1.reports.urls')),
    path('<slug:organization_slug>/travel-attendance-setting/',
         TravelAttendanceSettingViewSet.as_view({
             'get': 'retrieve',
             'put': 'update',
         }), name='travel-attendance-settings'),
    path('<slug:organization_slug>/timesheet-record-report-settings/',
         TimeSheetRegistrationReportSettingsViewSet.as_view({
             'get': 'retrieve',
             'put': 'update',
         }), name='timesheet-record-report-settings'),
]

urlpatterns += [
    path('connection-test/', ConnectionTest.as_view(), name='source-connection-test'),
]
