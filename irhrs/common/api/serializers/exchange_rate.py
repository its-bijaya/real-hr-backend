import re
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.common.models.exchange_rate import ExchangeRate


class ExchangeRateSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = ExchangeRate
        fields = '__all__'

    @staticmethod
    def check_date_conflicts(qs, from_currency, to_currency, from_date, to_date):
        return qs.filter(
            from_date__lte=to_date,
            to_date__gte=from_date
        ).filter(
            from_currency__in=[from_currency, to_currency],
            to_currency__in=[from_currency, to_currency]
        ).exists()

    @staticmethod
    def validate_from_amount(from_amount):
        if not from_amount > 0.0:
            raise serializers.ValidationError(_("Make sure this value is more than 0.0"))
        if not re.match(r'^\d+(\.\d{1,2})?$', str(from_amount)):
            raise serializers.ValidationError(
                _("Values are allowed only two decimal places only.")
            )

        return from_amount

    @staticmethod
    def validate_to_amount(to_amount):
        if not to_amount > 0.0:
            raise serializers.ValidationError(_("Make sure this value is more than 0.0"))
        if not re.match(r'^\d+(\.\d{1,2})?$', str(to_amount)):
            raise serializers.ValidationError(
                _("Values are allowed only two decimal places only.")
            )
        return to_amount

    def validate(self, attrs):
        from_currency = attrs['from_currency']
        to_currency = attrs['to_currency']
        from_date = attrs['from_date']
        to_date = attrs['to_date']

        if from_currency == to_currency:
            raise serializers.ValidationError(_("From Currency and To Currency can not be same."))

        if from_date > to_date:
            raise serializers.ValidationError(_("From Date is after To Date."))

        qs = ExchangeRate.objects.all()
        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        if self.check_date_conflicts(qs, from_currency, to_currency, from_date, to_date):
            raise serializers.ValidationError(_("This exchange rate effective period merges with"
                                                " existing exchange rate."))

        return attrs
