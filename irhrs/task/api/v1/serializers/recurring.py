from django.utils import timezone

from dateutil.parser import parse
from rest_framework import serializers

from irhrs.core.mixins.serializers import DummySerializer
from irhrs.core.validators import validate_recurring_rule


class RecurringTaskSerializer(DummySerializer):
    recurring_rule = serializers.CharField(
        validators=[validate_recurring_rule])
    recurring_first_run = serializers.DateField()

    @staticmethod
    def validate_recurring_first_run(value):
        if value < timezone.now().date():
            raise serializers.ValidationError('First run should be in future')
        return value

    def validate(self, attrs):
        if not all([attrs.get('recurring_rule'),
                    attrs.get('recurring_first_run')]):
            raise serializers.ValidationError(
                'Recurring Rule and first run is required')
        rule = attrs.get('recurring_rule')
        rule_dict = {i.split('=')[0].lower(): i.split('=')[1] for i in
                     rule.split(';')}
        if rule_dict.get('until'):
            _until = parse(rule_dict.get('until'))
            if _until.date() < attrs.get('recurring_first_run'):
                raise serializers.ValidationError(
                    'Recurring rule end date should be '
                    'greater than recurring first run')
        # elif rule_dict.get('count'):
        #     pass
        return attrs
