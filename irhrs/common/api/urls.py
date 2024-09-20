from django.urls import path
from rest_framework.routers import DefaultRouter

from irhrs.common.api.views.id_card import IdCardSampleViewSet
from irhrs.common.api.views.system_log import SystemEmailLogViewSet
from irhrs.common.api.views.user_activity import UserActivityViewSet
from .views.commons import (
    ReligionEthnicityView, DocumentCategoryView,
    IndustryListView, DisabilityViewSet,
    HolidayCategoryView, ConstantViewSet, BankViewSet,
    EquipmentCategoryViewSet, OpenKnowledgeSkillAbilityViewSet,
    FrontendLinkListViewSet)
from .views.exchange_rate import ExchangeRateViewSet
from .views.duty_station import DutyStationViewSet
from .views.all_request_summary import AllRequestsSummaryViewSet
from .views.travel_request import TravelAttendanceRequestStatsViewSet
from .views.link_preview import LinkPreview
from .views.subordinate_stats import SubordinateStatsForAttendanceAndLeave
from .views.notification_template import (
    NotificationTemplateViewSet, NotificationTemplateContentViewSet
)
from .views.smtp_server import SMTPServerViewSet

app_name = 'commons'

router = DefaultRouter()

# Default Commons
router.register('constants', ConstantViewSet, basename='constants')
router.register('religion-ethnicity',
                ReligionEthnicityView,
                basename='religion-ethnicity')

router.register('document-category',
                DocumentCategoryView,
                basename='document-category')

router.register('holiday-category',
                HolidayCategoryView,
                basename='holiday-category')

router.register('disabilities',
                DisabilityViewSet,
                basename='disability')

router.register('bank',
                BankViewSet,
                basename='bank')
router.register('recent-activity',
                UserActivityViewSet,
                basename='recent-activity')
router.register('duty-station',
                DutyStationViewSet,
                basename='duty-station')
router.register('subordinates/attendance-leave',
                SubordinateStatsForAttendanceAndLeave,
                basename='subordinates-stats-attendance-leave')
router.register('all-request-summary',
                AllRequestsSummaryViewSet,
                basename='all-request-summary')
router.register('travel-attendance',
                TravelAttendanceRequestStatsViewSet,
                basename='travel-attendance-summary')
router.register(r'email-templates/(?P<template_slug>[\w\-]+)/content',
                NotificationTemplateContentViewSet,
                basename='notification-templates-content')
router.register('email-templates',
                NotificationTemplateViewSet,
                basename='notification-templates')
router.register('id-card-samples',
                IdCardSampleViewSet,
                basename='id-card-sample')
router.register('system-email-log',
                SystemEmailLogViewSet,
                basename='system-email-log')
router.register(r'equipment-category',
                EquipmentCategoryViewSet,
                basename='equipment-category')
router.register(r'exchange-rate',
                ExchangeRateViewSet,
                basename='exchange-rate')

router.register(r'smtp-server',
                SMTPServerViewSet,
                basename='smtp-server')

router.register(r'smtp-server',  # implement other fields if necessary
                OpenKnowledgeSkillAbilityViewSet,
                basename='ksa-settings'
                )

extra_app_types = [
    'stats', 'reference-check', 'interview',
    'advance-salary', 'reimbursement', 'settlement',
    'exit-interview', 'pre-screening', 'post-screening',
    'pre-screening-interview', 'assessment', 'payroll-approval',
    'resignation', 'leave-request', 'form-approval', 'cancel-request'
]

router.register(
    r'extra-apps/(?P<type>({}))'.format('|'.join(extra_app_types)),
    FrontendLinkListViewSet,
    basename='frontend_links'
)

urlpatterns = router.urls
urlpatterns += [
    path('industry/', IndustryListView.as_view({'get': 'list'})),
    path('link-preview/', LinkPreview.as_view()),
]
