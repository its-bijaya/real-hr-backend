from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, action
from rest_framework import permissions
from rest_framework.response import Response
from irhrs.core.mixins.viewset_mixins import OrganizationMixin, OrganizationCommonsMixin, \
    ListCreateViewSetMixin
from irhrs.reimbursement.api.v1.permissions import ExpenseSettingReadPermission
from irhrs.reimbursement.api.v1.serializers.setting import (
    ExpenseApprovalSettingSerializer,
    OverallReimbursementSetting,
    SettlementApprovalSettingSerializer
)
from irhrs.reimbursement.models.setting import ReimbursementSetting

class SafePermission(permissions.BasePermission):
    def has_permission(self,request, view):
        allowed_actions = ["get_request_approvers", "get_settlement_approvers"]
        return request.user.is_authenticated and view.action in allowed_actions

class ReimbursementSettingViewSet(
    OrganizationMixin, OrganizationCommonsMixin,
    ListCreateViewSetMixin
):
    serializer_class = OverallReimbursementSetting
    permission_classes = [ExpenseSettingReadPermission|SafePermission]
    queryset = ReimbursementSetting.objects.all()

    def get_object(self):
        return get_object_or_404(
            ReimbursementSetting,
            organization=self.organization
        )

    @action(
        detail=False,
        methods=['get'],
        url_path='request-approvers'
    )
    def get_request_approvers(self, request, *args, **kwargs):
        organization = self.organization
        expense_settings = organization.expense_setting.filter(
            select_employee=True
        )
        serializer = ExpenseApprovalSettingSerializer(
            expense_settings,
            fields=["approval_level", "employee"],
            many=True
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get'],
        url_path='settlement-approvers'
    )
    def get_settlement_approvers(self, request, *args, **kwargs):
        organization = self.organization
        settlement_settings = organization.settlement_setting.filter(
            select_employee=True
        )
        serializer = SettlementApprovalSettingSerializer(
            settlement_settings,
            fields=["approval_level", "employee"],
            many=True
        )
        return Response(serializer.data)

@api_view()
def get_reimbursement_rates(request, organization_slug):
    reimbursement_setting = get_object_or_404(
        ReimbursementSetting,
        organization__slug=organization_slug
    )
    return Response(
        {
            "lodging_rate": reimbursement_setting.lodging_rate,
            "per_diem_rate": reimbursement_setting.per_diem_rate,
            'others_rate': reimbursement_setting.others_rate
        }
    )
