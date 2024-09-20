from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils.common import get_today
from irhrs.payroll.models import PayrollIncrement, UserExperiencePackageSlot
from irhrs.payroll.utils.calculator import create_package_rows
from irhrs.payroll.utils.helpers import get_last_payroll_generated_date
from irhrs.users.api.v1.serializers.thin_serializers import UserThumbnailSerializer


class PayrollIncrementSerializer(DynamicFieldsModelSerializer):
    is_used_increment = serializers.SerializerMethodField()

    class Meta:
        model = PayrollIncrement
        fields = '__all__'

    @staticmethod
    def get_is_used_increment(obj):
        last_payroll_generated_date = get_last_payroll_generated_date(obj.employee)
        if last_payroll_generated_date and obj.effective_from <= last_payroll_generated_date:
            return True
        return False

    def get_fields(self):
        fields = super().get_fields()

        if self.request and self.request.method.upper() == 'GET':
            if 'employee' in fields:
                fields['employee'] = UserThumbnailSerializer()
            if 'created_by' in fields:
                fields['created_by'] = UserThumbnailSerializer()

        return fields

    def validate(self, attrs):
        employee = attrs.get('employee')
        if not employee and self.instance:
            employee = self.instance.employee

        effective_from = attrs.get('effective_from')
        if self.instance:
            effective_from = self.instance.effective_from

        last_payroll_generated_date = get_last_payroll_generated_date(employee)
        if last_payroll_generated_date and effective_from and (
            effective_from <= last_payroll_generated_date
        ):
            if self.instance:
                raise serializers.ValidationError(
                    _("Can not change this increment."
                      " It has already been used to generate payroll.")
                )
            else:
                raise serializers.ValidationError({
                    "effective_from": _(
                        "This value must be after last payroll generated date"
                        f" {last_payroll_generated_date}"
                    )
                })
        return attrs

    def create(self, validated_data):
        instance = super().create(validated_data)
        self.after_create_or_update(instance)
        return instance

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        self.after_create_or_update(instance)
        return instance

    def after_create_or_update(self, instance):
        if instance.effective_from <= get_today():
            user = instance.employee
            self.recalibrate_package_amount_after_increment_update(user)

    @staticmethod
    def recalibrate_package_amount_after_increment_update(user):
        current_experience = user.current_experience

        changed_package_slot = UserExperiencePackageSlot.objects.filter(
            user_experience=current_experience
        ).order_by('active_from_date').last()
        if changed_package_slot:
            create_package_rows(changed_package_slot)

