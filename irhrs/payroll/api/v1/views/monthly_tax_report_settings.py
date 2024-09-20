from rest_framework import status
from rest_framework.response import Response
from irhrs.core.mixins.viewset_mixins import (
    OrganizationCommonsMixin,
    OrganizationMixin,
    ListUpdateViewSetMixin
)

from irhrs.payroll.models import MonthlyTaxReportSetting

from irhrs.payroll.api.v1.serializers.monthly_tax_report_settings import (
    MonthlyTaxReportBulkSettingSerializer,
    MonthlyTaxReportSettingSerializer
)


class MonthlyTaxReportSettingViewSet(
    OrganizationCommonsMixin,
    OrganizationMixin,
    ListUpdateViewSetMixin
):
    queryset=MonthlyTaxReportSetting.objects.all()
    serializer_class = MonthlyTaxReportBulkSettingSerializer


    def create(self, request, *args, **kwargs):
        serializer = MonthlyTaxReportBulkSettingSerializer(
            data=request.data,
            context=dict(
                organization=self.organization
            )
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        return Response(data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        queryset = self.queryset.filter(
            organization=self.organization
        ).select_related('heading').order_by('pk')

        class TaxReportCategory(object):
            def __init__(self, category, headings):
                self.category = category
                self.headings = headings

            def add_headings(self, heading):
                self.headings.append(heading)

        tax_report_categories = list()

        for item in queryset:
            category_is_present = list(
                filter(
                    lambda x: x.category == item.category,
                    tax_report_categories
                )
            )

            if not category_is_present:
                tax_report_categories.append(
                    TaxReportCategory(
                        item.category,
                        [item]
                    )
                )
            else:
                category_is_present[0].add_headings(item)
        serializer = MonthlyTaxReportSettingSerializer(
            tax_report_categories,
            many=True,
            context=dict(
                organization=self.organization
            )
        )

        return Response(serializer.data)




