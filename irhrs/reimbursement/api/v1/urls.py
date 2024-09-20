from django.urls import re_path
from rest_framework.routers import DefaultRouter

from irhrs.reimbursement.api.v1.views.advance_cancel import AdvanceExpenseCancelRequestViewSet
from irhrs.reimbursement.api.v1.views.reimbursement import AdvanceExpenseRequestViewSet, \
    AdvanceExpenseRequestDocumentsViewSet
from irhrs.reimbursement.api.v1.views.setting import (
    ReimbursementSettingViewSet,
    get_reimbursement_rates
)
from irhrs.reimbursement.api.v1.views.settlement import ExpenseSettlementViewSet

app_name = 'reimbursement'

router = DefaultRouter()

router.register(
    r'(?P<organization_slug>[\w\-]+)/setting',
    ReimbursementSettingViewSet,
    basename='reimbursement-setting'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/advance-expense/request',
    AdvanceExpenseRequestViewSet,
    basename='advance-expense-request'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/advance-expense/request/(?P<expense_id>\d+)/documents',
    AdvanceExpenseRequestDocumentsViewSet,
    basename='advance-expense-request-documents'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/settlement/request',
    ExpenseSettlementViewSet,
    basename='expense-settlement'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/advance-expense-cancel/request',
    AdvanceExpenseCancelRequestViewSet,
    basename='advance-expense-cancel-request'
)

urlpatterns = router.urls

urlpatterns += [
    re_path(
        r'(?P<organization_slug>[\w\-]+)/rates',
        get_reimbursement_rates,
        name='reimbursement-rates'
    )
]
