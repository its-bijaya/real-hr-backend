from django.urls import path
from rest_framework.routers import DefaultRouter

from irhrs.users.api.v1.views.address_detail import UserAddressViewSet
from irhrs.users.api.v1.views.bulk_employment_experience import UserExperienceImportViewSet
from irhrs.users.api.v1.views.bulk_import_contact_detail import UserContactDetailImportViewSet
from irhrs.users.api.v1.views.contact_detail import \
    UserContactDetailsViewSet
from irhrs.users.api.v1.views.education import UserEducationView
from irhrs.users.api.v1.views.experience import UserExperienceViewSet, \
    UserExperienceHistoryViewSet
from irhrs.users.api.v1.views.key_skill_ability import UserKSAOViewSet
from irhrs.users.api.v1.views.language import UserLanguageViewSet
from irhrs.users.api.v1.views.legal_info import UserLegalInfoView, UserLegalInfoImportView
from irhrs.users.api.v1.views.medical_info import UserMedicalInfoView
from irhrs.users.api.v1.views.past_experience import UserPastExperienceViewSet
from irhrs.users.api.v1.views.published_content import \
    UserPublishedContentViewSet
from irhrs.users.api.v1.views.social_activity import UserSocialActivityViewSet
from irhrs.users.api.v1.views.training import UserTrainingViewSet
from irhrs.users.api.v1.views.user_bank import UserBankViewSet, UserBankImportViewSet
from irhrs.users.api.v1.views.equipments import UserEquipmentViewSet
from irhrs.users.api.v1.views.user_document import UserDocumentViewSet
from irhrs.users.api.v1.views.user_import import UserImportView
from irhrs.users.api.v1.views.volunteer_experience import \
    UserVolunteerExperienceViewSet
from .views.cv import UserCVViewSet
from .views.email_setting import UserEmailNotificationSettingViewSet
from .views.insurance import UserInsuranceViewSet
from .views.user import UserDetailViewSet, PasswordResetViewSet, \
    AccountActivationViewSet, UserAutoComplete

app_name = 'users'

router = DefaultRouter()
router.register('import', UserImportView, basename='user-import')
router.register('password-reset', PasswordResetViewSet,
                basename='password-reset')
router.register('activation', AccountActivationViewSet,
                basename='account-activation')
router.register('autocomplete', UserAutoComplete,
                basename='users-autocomplete')
router.register('', UserDetailViewSet, basename='users')

# Employee Details
router.register(r'(?P<user_id>\d+)/address',
                UserAddressViewSet,
                basename='user-address')
router.register(r'(?P<user_id>\d+)/contact',
                UserContactDetailsViewSet,
                basename='user-contact-details')
router.register(r'(?P<user_id>\d+)/language',
                UserLanguageViewSet,
                basename='user-language')
router.register(r'(?P<user_id>\d+)/experience',
                UserExperienceViewSet,
                basename='user-experience')
router.register(r'(?P<user_id>\d+)/experience-history',
                UserExperienceHistoryViewSet,
                basename='experience-history')
router.register(r'(?P<user_id>\d+)/volunteer-experience',
                UserVolunteerExperienceViewSet,
                basename='user-volunteer-experience')
router.register(r'(?P<user_id>\d+)/published-content',
                UserPublishedContentViewSet,
                basename='user-published-content')
router.register(r'(?P<user_id>\d+)/training',
                UserTrainingViewSet,
                basename='user-training')
router.register(r'(?P<user_id>\d+)/education',
                UserEducationView,
                basename='user-education')
router.register(r'(?P<user_id>\d+)/past-experience',
                UserPastExperienceViewSet,
                basename='user-past-experience')
router.register(r'(?P<user_id>\d+)/social-activity',
                UserSocialActivityViewSet,
                basename='social-activity')
router.register(r'(?P<user_id>\d+)/documents',
                UserDocumentViewSet,
                basename='user-document')
router.register(r'(?P<user_id>\d+)/equipments',
                UserEquipmentViewSet,
                basename='user-equipment')
router.register(r'(?P<user_id>\d+)/ksaos',
                UserKSAOViewSet,
                basename='user-ksao')
router.register(r'(?P<user_id>\d+)/cv',
                UserCVViewSet,
                basename='user-cv')
router.register(
    r'(?P<user_id>\d+)/insurance',
    UserInsuranceViewSet,
    basename='user-insurance'
)
router.register(
    r'(?P<user_id>\d+)/email-setting',
    UserEmailNotificationSettingViewSet,
    basename='user-email-setting'
)
router.register(
    r'(?P<organization_slug>[\w\-]+)/user-experience-import',
    UserExperienceImportViewSet,
    basename='user-experience-import'
)
router.register(
    r'(?P<organization_slug>[\w\-]+)/user-bank-info',
    UserBankImportViewSet,
    basename='user-bank-info-import'
)
router.register(
    r'(?P<organization_slug>[\w\-]+)/user-contact-detail-import',
    UserContactDetailImportViewSet,
    basename='user-contact-detail-import'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/user-legal-info',
    UserLegalInfoImportView,
    basename='user-legal-info-import'
)


urlpatterns = router.urls
urlpatterns += [
    path('<int:user_id>/medical-info/',
         UserMedicalInfoView.as_view({
             'get': 'retrieve',
             'put': 'update',
         }), name='user-medical-info'),
    path('<int:user_id>/legal-info/',
         UserLegalInfoView.as_view({
             'get': 'retrieve',
             'put': 'update',
             'patch': 'partial_update'
         }), name='user-legal-info'),
    path('<int:user_id>/bank/',
         UserBankViewSet.as_view({
             'get': 'retrieve',
             'put': 'update',
             'delete': 'destroy'
         }), name='user-bank-info'),
]
