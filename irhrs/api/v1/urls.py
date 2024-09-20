from django.conf import settings
from django.urls import path, include
from django.urls import path, include, re_path
from rest_framework_simplejwt.views import TokenObtainPairView, \
    TokenRefreshView

from irhrs.api.v1.views import ServerInfoView
from irhrs.users.api.v1.serializers.auth import CustomTokenRefreshView, \
    CustomTokenObtainView

app_name = 'api_v1'

urlpatterns = [
    # authentication urls
    # custom token obtain for authenticating user with username, email and password
    path('auth/', include((
        [
            path('obtain/', CustomTokenObtainView.as_view(), name='obtain'),
            path('refresh/', CustomTokenRefreshView.as_view(),
                 name='refresh'),
        ], 'jwt'))),

    # modules
    path('users/', include('irhrs.users.api.v1.urls')),
    path('permission/', include('irhrs.permission.api.v1.urls')),
    path('org/', include('irhrs.organization.api.v1.urls')),
    path('noticeboard/', include('irhrs.noticeboard.api.v1.urls')),
    path('notifications/', include('irhrs.notification.api.v1.urls')),
    path('hrstatement/', include('irhrs.hrstatement.api.v1.urls')),
    path('help/', include('irhrs.help.api.v1.urls')),
    path('hris/', include('irhrs.hris.api.v1.urls')),
    path('documents/', include('irhrs.document.api.v1.urls')),
    # # Common URLs
    path('commons/', include('irhrs.common.api.urls')),
    path('exports/', include('irhrs.export.api.v1.urls')),
    path('work-log/', include('irhrs.worklog.api.v1.urls')),
    path('portal/', include('irhrs.portal.api.v1.urls')),

    # Recruitment
    path('recruitment/', include('irhrs.recruitment.api.v1.urls')),

    # Reimbursement
    path('reimbursement/', include('irhrs.reimbursement.api.v1.urls')),

    # appraisal
    path('appraisal/', include('irhrs.appraisal.api.v1.urls')),

    path('server-info/', ServerInfoView.as_view())
]

# Attendance URLs
if 'irhrs.attendance' in settings.INSTALLED_APPS:
    urlpatterns += [
        path('attendance/', include('irhrs.attendance.api.v1.urls')),
    ]

    # Leave URLs < Require attendance to be in installed apps
if 'irhrs.leave' in settings.INSTALLED_APPS:
    urlpatterns += [
        path('leave/', include('irhrs.leave.api.v1.urls')),
    ]

if 'irhrs.task' in settings.INSTALLED_APPS:
    urlpatterns += [
        path('task/', include('irhrs.task.api.v1.urls')),
    ]

if 'irhrs.event' in settings.INSTALLED_APPS:
    urlpatterns += [
        path('event/', include('irhrs.event.api.v1.urls')),
    ]

# Payroll URLS
if 'irhrs.payroll' in settings.INSTALLED_APPS:
    urlpatterns += [
        path('payroll/', include('irhrs.payroll.api.v1.urls')),
    ]

# Report Builder URLS
if 'irhrs.builder' in settings.INSTALLED_APPS:
    urlpatterns += [
        path('builder/', include('irhrs.builder.api.v1.urls')),
    ]

# Training URLs
if 'irhrs.training' in settings.INSTALLED_APPS:
    urlpatterns += [
        path('training/', include('irhrs.training.api.v1.urls')),
    ]
# Questionnaire URLs.
if 'irhrs.questionnaire' in settings.INSTALLED_APPS:
    urlpatterns += [
        path('questionnaire/', include('irhrs.questionnaire.api.v1.urls')),
    ]

# Assessment URLs.
if 'irhrs.assessment' in settings.INSTALLED_APPS:
    urlpatterns += [
        path('assessment/', include('irhrs.assessment.api.v1.urls')),
    ]

# Forms URLs.
if 'irhrs.forms' in settings.INSTALLED_APPS:
    urlpatterns += [
        path('forms/', include('irhrs.forms.api.v1.urls')),
    ]
