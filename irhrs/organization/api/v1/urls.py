from django.urls import path
from rest_framework.routers import DefaultRouter

from irhrs.organization.api.v1.views import (EmploymentStatusView,
                                             EmploymentLevelView,
                                             EmploymentJobTitleView,
                                             EmploymentStepViewSet,
                                             UserDataTableView)
from irhrs.organization.api.v1.views.account_setup import \
    OrganizationAccountSetupStatus
from irhrs.organization.api.v1.views.asset import (
    OrganizationEquipmentViewSet, EquipmentAssignedToViewSet)
from irhrs.organization.api.v1.views.bank import OrganizationBankViewSet
from irhrs.organization.api.v1.views.calendar import (
    OrganizationCalenderView, OrganizationCalenderDetailView)
from irhrs.organization.api.v1.views.division import (
    OrganizationDivisionViewSet)
from irhrs.organization.api.v1.views.ethics import (
    OrganizationEthicsViewSet)
from irhrs.organization.api.v1.views.knowledge_skill_ability import (
    KnowledgeSkillAbilityView)
from irhrs.organization.api.v1.views.meeting_room import MeetingRoomViewSet
from irhrs.organization.api.v1.views.organization_documents import (
    OrganizationDocumentView)
from irhrs.organization.api.v1.views.other import \
    (NotificationTemplateMapViewSet,
     OrganizationSetupInfo)
from irhrs.organization.api.v1.views.settings import (ContractSettingsView,
                                                      ApplicationSettingView,
                                                      EmailNotificationSettingViewSet)
from .views.branch import OrganizationBranchViewSet
from .views.fiscal_year import FiscalYearViewSet
from .views.organization import OrganizationViewSet, HolidayViewSet
from ...api.v1.views.message_to_user import MessageToUserView
from ...api.v1.views.mission_and_vision import \
    (OrganizationMissionViewSet, OrganizationVisionViewSet)

app_name = 'organization'

router = DefaultRouter()

# meeting-room conflicts with organization_slug url so it is in top
router.register(r'(?P<organization_slug>[\w\-]+)/meeting-room',
                MeetingRoomViewSet,
                basename='meeting-room')

router.register(r'(?P<organization_slug>[\w\-]+)/setup-info',
                OrganizationSetupInfo,
                basename='organization-setup-info')

router.register(r'(?P<organization_slug>[\w\-]+)/bank',
                OrganizationBankViewSet,
                basename='organization-bank')
router.register(r'(?P<organization_slug>[\w\-]+)/documents',
                OrganizationDocumentView,
                basename='organization-document')
router.register(r'(?P<organization_slug>[\w\-]+)/division',
                OrganizationDivisionViewSet,
                basename='organization-division')
router.register('',
                OrganizationViewSet,
                basename='get-update-organization')

router.register(r'(?P<organization_slug>[\w\-]+)/equipment/assign',
                EquipmentAssignedToViewSet,
                basename='assigned-equipment')

router.register(r'(?P<organization_slug>[\w\-]+)/equipment',
                OrganizationEquipmentViewSet,
                basename='organization-equipment')

router.register(r'(?P<organization_slug>[\w\-]+)/ethics',
                OrganizationEthicsViewSet,
                basename='organization-ethics')

# Employment
router.register(r'(?P<organization_slug>[\w\-]+)/employment/status',
                EmploymentStatusView,
                basename='employment-status')
router.register(r'(?P<organization_slug>[\w\-]+)/employment/level',
                EmploymentLevelView,
                basename='employment-level')
router.register(r'(?P<organization_slug>[\w\-]+)/employment/job-title',
                EmploymentJobTitleView,
                basename='employment-job-title')
router.register(r'(?P<organization_slug>[\w\-]+)/branch',
                OrganizationBranchViewSet,
                basename='organization-branch')
router.register(r'(?P<organization_slug>[\w\-]+)/employment/step',
                EmploymentStepViewSet,
                basename='employment-step')

router.register(r'(?P<organization_slug>[\w\-]+)/mission',
                OrganizationMissionViewSet,
                basename='organization-mission')

router.register(r'(?P<organization_slug>[\w\-]+)/templates',
                NotificationTemplateMapViewSet,
                basename='templates-map')

router.register(r'message/users',
                MessageToUserView,
                basename='message-to-user')

# Holiday
router.register(r'(?P<organization_slug>[\w\-]+)/holiday',
                HolidayViewSet,
                basename='organization-holiday')

router.register(r'(?P<organization_slug>[\w\-]+)/fiscal-year',
                FiscalYearViewSet,
                basename='fiscal-year')

# Application Settings
router.register(r'(?P<organization_slug>[\w\-]+)/setting/applications',
                ApplicationSettingView,
                basename='application-settings')

router.register(r'(?P<organization_slug>[\w\-]+)/setting/'
                r'(?P<ksa_type>(knowledge|skill|ability|other_attributes))',
                KnowledgeSkillAbilityView,
                basename='ksa-settings')

router.register(r'(?P<organization_slug>[\w\-]+)/setting/email',
                EmailNotificationSettingViewSet,
                basename='email-setting')


urlpatterns = router.urls

urlpatterns += [
    path('<slug:organization_slug>/settings/contract/',
         ContractSettingsView.as_view({
             'get': 'retrieve',
             'put': 'update',
             'patch': 'partial_update'
         }), name='org-contract-settings'),
    path('<slug:organization_slug>/employee-data/',
         UserDataTableView.as_view({
             'get': 'list'
         }), name='user-list'),
    path('<slug:organization_slug>/vision/',
         OrganizationVisionViewSet.as_view({
             'get': 'retrieve',
             'put': 'update',
         }), name='organization-vision'),
    path('<slug:organization_slug>/calender/',
         OrganizationCalenderView.as_view(), name='org-calender'),
    path('<slug:organization_slug>/calender/detail/',
         OrganizationCalenderDetailView.as_view(), name='org-calender-detail'),
    path('<slug:organization_slug>/account-setup-status/',
         OrganizationAccountSetupStatus.as_view(),
         name='org-account-setup-status'),

]
