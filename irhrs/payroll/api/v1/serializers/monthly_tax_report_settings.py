from rest_framework.serializers import (
    ModelSerializer,
    Serializer
)

from rest_framework import serializers

from irhrs.payroll.models import (
    MonthlyTaxReportSetting,
    Heading
)

from irhrs.payroll.models.payslip_report_setting import MONTHLY_TAX_REPORT_SETTING_CATEGORY_CHOICES


class MonthlyTaxReportCategoryHeading(serializers.Serializer):
    is_highlighted = serializers.BooleanField(default=False)
    is_nested = serializers.BooleanField(default=False)

    def get_fields(self, *args, **kwargs):
        fields = super().get_fields(*args, **kwargs)
        fields['heading'] = serializers.PrimaryKeyRelatedField(
            queryset=Heading.objects.filter(
                organization=self.context['organization']
            )
        )
        return fields


class MonthlyTaxReportSettingSerializer(serializers.Serializer):
    category = serializers.ChoiceField(
        choices=MONTHLY_TAX_REPORT_SETTING_CATEGORY_CHOICES
    )

    headings = MonthlyTaxReportCategoryHeading(many=True)

class MonthlyTaxReportBulkSettingSerializer(serializers.Serializer):
    settings = MonthlyTaxReportSettingSerializer(many=True)

    def validate(self, initial_data):
        errors = dict()
        used_categories = list()
        settings = initial_data.get('settings')

        for setting in settings:
            if not setting.get('category') in used_categories:
                used_categories.append(
                    setting.get('category')
                )
            else:
                errors['non_field_errors'] = "Please post settings with unique category."
        
        if errors.keys():
            raise serializers.ValidationError(errors)

        return initial_data


    def create(self, validated_data):
        organization = self.context['organization']
        settings = validated_data.get('settings')

        MonthlyTaxReportSetting.objects.filter(
            organization=organization,
        ).delete()

        bulk_create_args = list()

        for setting in settings:
            for heading in setting.get('headings'):
                bulk_create_args.append(
                    MonthlyTaxReportSetting(
                        organization=organization,
                        category=setting.get('category'),
                        heading=heading.get('heading'),
                        is_highlighted=heading.get('is_highlighted'),
                        is_nested=heading.get('is_nested')
                    )
                )
        
        MonthlyTaxReportSetting.objects.bulk_create(
            bulk_create_args
        )

        return self.initial_data

