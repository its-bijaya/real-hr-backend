from rest_framework.response import Response

from irhrs.core.mixins.viewset_mixins import (
    OrganizationCommonsMixin, OrganizationMixin,
    ListCreateViewSetMixin, CreateListModelMixin,
    ListCreateDestroyViewSetMixin, ApprovalSettingViewSetMixin)
from irhrs.payroll.api.permissions import AdvanceSalarySettingPermission
from irhrs.payroll.api.v1.serializers.advance_salary_settings import (
    EligibilitySettingSerializer,
    AmountSettingSerializer,
    DisbursementSettingSerializer,
    ApprovalSettingSerializer, ApprovalSettingBulkSerializer)
from irhrs.payroll.models.advance_salary_settings import (
    AmountSetting, AdvanceSalarySetting,
    ApprovalSetting)


class AdvanceSalaryCommonMixin(OrganizationMixin, OrganizationCommonsMixin):
    def get_queryset(self):
        queryset = self.queryset
        organization = self.organization
        if hasattr(organization, 'advance_salary_setting'):
            return queryset.filter(advance_salary_setting=organization.advance_salary_setting)
        return queryset.none()

    @property
    def advance_salary_setting(self):
        organization = self.organization

        if hasattr(organization, 'advance_salary_setting'):
            advance_salary_setting = organization.advance_salary_setting
        else:
            advance_salary_setting = AdvanceSalarySetting(organization=organization)
            advance_salary_setting.save()

        return advance_salary_setting

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['advance_salary_setting'] = self.advance_salary_setting
        return context


class EligibilitySettingViewSet(OrganizationCommonsMixin,
                                OrganizationMixin,
                                ListCreateViewSetMixin):
    queryset = AdvanceSalarySetting.objects.all()
    serializer_class = EligibilitySettingSerializer
    permission_classes = [AdvanceSalarySettingPermission]

    def get_serializer_class(self):
        setting_type = self.kwargs.get('setting_type')
        if setting_type == "eligibility":
            return super().get_serializer_class()
        elif setting_type == 'disbursement':
            return DisbursementSettingSerializer

    def list(self, request, *args, **kwargs):
        instance = self.get_queryset().first()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class AmountSettingViewSet(AdvanceSalaryCommonMixin, CreateListModelMixin,
                           ListCreateViewSetMixin):
    queryset = AmountSetting.objects.all()
    serializer_class = AmountSettingSerializer
    permission_classes = [AdvanceSalarySettingPermission]

    def list(self, request, *args, **kwargs):
        amount_data = {
            'payroll_heading': self.advance_salary_setting.amount_setting.all(),
            'limit_upto': self.advance_salary_setting
        }
        serializer = self.get_serializer(amount_data)
        return Response(serializer.data)


class ApprovalSettingViewSet(AdvanceSalaryCommonMixin,
                             ApprovalSettingViewSetMixin,
                             CreateListModelMixin,
                             ListCreateDestroyViewSetMixin):
    queryset = ApprovalSetting.objects.all()
    serializer_class = ApprovalSettingBulkSerializer
    permission_classes = [AdvanceSalarySettingPermission]

    def get_queryset(self):
        return super().get_queryset().order_by('approval_level')

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        return queryset.filter(advance_salary_setting=self.advance_salary_setting)

    def get_serializer_class(self):
        if self.action == "list":
            return ApprovalSettingSerializer
        return super().get_serializer_class()

    def delete_settings(self):
        return self.advance_salary_setting.approval_setting.all().delete()
