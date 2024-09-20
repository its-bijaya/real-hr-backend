from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter

from irhrs.hris.api.v1.views.birthday_and_anniversary import \
    UpcomingBirthdayViewSet, UpcomingAnniversaryViewSet, UpcomingEventsViewSet
from irhrs.hris.api.v1.views.branch import BranchOverView
from irhrs.hris.api.v1.views.central_dashboard import HRISDashboardViewSet
from irhrs.hris.api.v1.views.change_request import ChangeRequestViewSet
from irhrs.hris.api.v1.views.contract_status import UserContractStatusView
from irhrs.hris.api.v1.views.division import DivisionOverView
from irhrs.hris.api.v1.views.documents_library import UserDocumentsLibraryViewSet
from irhrs.hris.api.v1.views.dynamic_report import DynamicHRISReportViewSet
from irhrs.hris.api.v1.views.employment_status import \
    EmploymentStatusOverviewViewSet
from irhrs.hris.api.v1.views.hierarchy_chart import HierarchyChartView
from irhrs.hris.api.v1.views.id_card import IdCardTemplateViewSet, IdCardViewSet
from irhrs.hris.api.v1.views.offer_letter import PerformOfferLetter
from irhrs.hris.api.v1.views.onboarding_offboarding import (
    TaskTemplateTitleViewSet, TaskFromTemplateViewSet,
    PreEmploymentView, LetterTemplateView,
    EmployeeLettersView, ChangeTypeView,
    EmploymentReviewViewSet, EmployeeSeparationTypeView, EmployeeSeparationView,
    TaskFromTemplateAttachmentViewSet, EmployeeSeparationLeaveViewSet)
from irhrs.hris.api.v1.views.reports import (
    NoOfEmployeesVsYearsOfServiceView,
    MarriedVsAgeVsGender, EmploymentLevelVsAgeGroup)
from irhrs.hris.api.v1.views.statistics import HRStatisticsView, \
    HRISOverviewSummary
from irhrs.hris.api.v1.views.user import UserEmploymentViewSet, \
    UserDirectoryViewSet
from irhrs.hris.api.v1.views.duty_station_assignment import (
    DutyStationAssignmentViewSet,
    CurrentDutyStationAssignmentViewSet
)
from irhrs.hris.api.v1.views.profile_completeness import ProfileCompletenessViewSet
from irhrs.users.api.v1.views.key_skill_ability import UserKSAOList
from .views.core_task import (
    ResultAreaViewSet,
    CoreTaskViewSet, UserCoreTaskListRetrieveViewSet,
    UserAssignCoreTaskViewSet)
from .views.email_setting import EmailSettingViewSet
from .views.exit_interview import ExitInterviewViewSet, ExitInterviewQuestionSetViewSet
from .views.resignation import ResignationApprovalSettingViewSet, UserResignationViewSet
from .views.supervisor_authority import UserSupervisorsList, UserAllowedPermission, \
    UserSupervisorViewSet

app_name = 'hris'

router = DefaultRouter()

router.register(
    r'dashboard',
    HRISDashboardViewSet,
    basename='hris-dashboard'
)

router.register(
    r'employee-directory',
    UserDirectoryViewSet,
    basename='user-directory'
)
router.register(
    r'(?P<organization_slug>[\w\-]+)/document-library',
    UserDocumentsLibraryViewSet,
    basename='document-library'
)

router.register(r'(?P<organization_slug>[\w\-]+)/upcoming/birthdays',
                UpcomingBirthdayViewSet,
                basename='upcoming-birthdays')
router.register(r'(?P<organization_slug>[\w\-]+)/upcoming/anniversaries',
                UpcomingAnniversaryViewSet,
                basename='upcoming-anniversaries')
router.register(r'(?P<organization_slug>[\w\-]+)/upcoming/events',
                UpcomingEventsViewSet,
                basename='upcoming-events')
router.register(r'(?P<organization_slug>[\w\-]+)/overview/summary',
                HRISOverviewSummary, basename='overview-summary')
router.register(r'(?P<organization_slug>[\w\-]+)/statistics',
                HRStatisticsView)

router.register(r'(?P<organization_slug>[\w\-]+)/reports/no-vs-yos',
                NoOfEmployeesVsYearsOfServiceView,
                basename='report-no-vs-yos')
router.register(r'(?P<organization_slug>[\w\-]+)/reports/ms-vs-age-vs-gender',
                MarriedVsAgeVsGender,
                basename='report-no-vs-yos')
router.register(
    r'(?P<organization_slug>[\w\-]+)/reports/employment-level-vs-age-group',
    EmploymentLevelVsAgeGroup,
    basename='report-no-vs-yos'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/email-setting',
    EmailSettingViewSet,
    basename='email-setting'
)

router.register(r'(?P<organization_slug>[\w\-]+)/users',
                UserEmploymentViewSet,
                basename='users')

router.register(r'(?P<organization_slug>[\w\-]+)/employment-status/overview',
                EmploymentStatusOverviewViewSet,
                basename='employment-status-overview')
router.register(r'(?P<organization_slug>[\w\-]+)/division/overview',
                DivisionOverView,
                basename='division-overview')
router.register(r'(?P<organization_slug>[\w\-]+)/branch/overview',
                BranchOverView,
                basename='division-overview')

router.register(r'(?P<organization_slug>[\w\-]+)/contract-status',
                UserContractStatusView, basename='contract-status')

router.register(r'(?P<organization_slug>[\w\-]+)/change-requests',
                ChangeRequestViewSet,
                basename='change-requests')

router.register(r'(?P<organization_slug>[\w\-]+)/result-area',
                ResultAreaViewSet,
                basename='result-area')

router.register(r'(?P<organization_slug>[\w\-]+)/result-area/(?P<result_area_id>\d+)/core-task',
                CoreTaskViewSet,
                basename='core-task')
router.register(r'assign/user-result-areas',
                UserAssignCoreTaskViewSet,
                basename='user-result-areas-assign')
router.register(r'(?P<organization_slug>[\w\-]+)/user-result-areas',
                UserCoreTaskListRetrieveViewSet,
                basename='user-result-areas-view')

router.register(r'(?P<organization_slug>[\w\-]+)/dynamic-report',
                DynamicHRISReportViewSet,
                basename='dynamic-report')

router.register(r'(?P<organization_slug>[\w\-]+)/id-card-templates',
                IdCardTemplateViewSet,
                basename='id-card-template')
router.register(r'(?P<organization_slug>[\w\-]+)/id-cards',
                IdCardViewSet,
                basename='id-card')
router.register(
    '(?P<organization_slug>[\w\-]+)/ksaos',
    UserKSAOList,
    basename='ksao-list'
)
router.register(
    r'organization-chart/(?P<category>(children|siblings|parent|family))/user',
    HierarchyChartView,
    basename='hierarchy-chart'
)
router.register(
    r'(?P<organization_slug>[\w\-]+)/exit-interview/question-set',
    ExitInterviewQuestionSetViewSet,
    basename='question-set'
)
router.register(
    r'(?P<organization_slug>[\w\-]+)/exit-interview',
    ExitInterviewViewSet,
    basename='exit-interview'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/resignation/setting',
    ResignationApprovalSettingViewSet,
    basename='resignation-setting'
)

router.register(r'(?P<organization_slug>[\w\-]+)/profile-completeness',
                ProfileCompletenessViewSet,
                basename='profile-completeness')

router.register(r'(?P<organization_slug>[\w\-]+)/duty-station',
                DutyStationAssignmentViewSet,
                basename='assign-duty-station')

router.register(r'(?P<organization_slug>[\w\-]+)/current-duty-stations',
                CurrentDutyStationAssignmentViewSet,
                basename='currently-assigned-duty-stations')

router.register(
    r'(?P<organization_slug>[\w\-]+)/resignation',
    UserResignationViewSet,
    basename='user-resignation'
)

router.register('assign/supervisors',
                UserSupervisorViewSet,
                basename='user-supervisor-assign')

router.register(
    '(?P<organization_slug>[\w\-]+)/supervisors',
    UserSupervisorsList,
    basename='users-supervisors'
)

router.register(
    'subordinate/(?P<user_id>\d+)/permissions',
    UserAllowedPermission,
    basename='users-supervisors'
)

urlpatterns = router.urls

employment_router = DefaultRouter()  # begins with '<org_slug>/employment/'

employment_router.register(
    prefix='template',
    viewset=TaskTemplateTitleViewSet,
    basename='template'
)

employment_router.register(
    prefix='template-detail',
    viewset=TaskFromTemplateViewSet,
    basename='template-detail'
)

employment_router.register(
    prefix=r'template-detail/(?P<template_id>\d+)/attachments',
    viewset=TaskFromTemplateAttachmentViewSet,
    basename='template-detail'
)

employment_router.register(
    prefix='pre-employment',
    viewset=PreEmploymentView,
    basename='pre-employment'
)

employment_router.register(
    prefix='letter-template',
    viewset=LetterTemplateView,
    basename='letter-template'
)

employment_router.register(
    prefix='letters',
    viewset=EmployeeLettersView,
    basename='generated-letters'
)

employment_router.register(
    prefix='employment-review',
    viewset=EmploymentReviewViewSet,
    basename='employment-review'
)

employment_router.register(
    prefix='change-type',
    viewset=ChangeTypeView,
    basename='change-type'
)

employment_router.register(
    prefix='separation-type',
    viewset=EmployeeSeparationTypeView,
    basename='separation-type'
)

employment_router.register(
    prefix='separation',
    viewset=EmployeeSeparationView,
    basename='separation'
)
employment_router.register(
    prefix=r'separation/(?P<separation_id>\d+)/leaves',
    viewset=EmployeeSeparationLeaveViewSet,
    basename='separation-leave'
)

urlpatterns += [
    path(
        '<slug:organization_slug>/employment/',
        include(employment_router.urls)
    ),
    re_path(
        'offer-letter/(?P<uri>[^/.]+)', PerformOfferLetter.as_view({
            'get': 'retrieve',
            'post': 'update'
        })
    )
]
