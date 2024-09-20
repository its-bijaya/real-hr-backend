from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from ....models.fiscal_year import FiscalYear, FiscalYearMonth


class FiscalYearMonthSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = FiscalYearMonth
        fields = '__all__'

    def get_fields(self):
        fields = super().get_fields()
        if (self.request and
            self.request.method.lower() == 'get'
        ) or self.context.get('read_only_mode'):
            fields['all_dates'] = serializers.ListField(
                child=serializers.DateField(), read_only=True)
        return fields


class FiscalYearSerializer(DynamicFieldsModelSerializer):
    months = FiscalYearMonthSerializer(many=True,
                                       exclude_fields=('fiscal_year',),
                                       write_only=True)
    description = serializers.CharField(max_length=500)
    can_update_or_delete = serializers.BooleanField(read_only=True)

    class Meta:
        model = FiscalYear
        fields = '__all__'
        read_only_fields = 'organization', 'slug',

    def get_fields(self):
        fields = super().get_fields()
        if (self.request and
            self.request.method.lower() == 'get'
        ) or self.context.get('read_only_mode'):
            fields['months'] = FiscalYearMonthSerializer(many=True,
                                                         source='fiscal_months',
                                                         read_only=True,
                                                         fields=('month_index',
                                                                 'start_at',
                                                                 'end_at',
                                                                 'id',
                                                                 'display_name',
                                                                 'all_dates'),
                                                         context=self.context)

        return fields

    def validate(self, attrs):
        months = attrs.get('months')
        fy_start_date = attrs.get('start_at')
        fy_end_date = attrs.get('end_at')
        applicable_from = attrs.get('applicable_from')
        applicable_to = attrs.get('applicable_to')

        org = self.context.get('organization')
        name = attrs.get('name')
        instance = self.instance
        category = instance.category if instance else attrs.get('category')
        if instance and not instance.can_update_or_delete:
            raise ValidationError({
                'detail': 'You can\'t update active or previous fiscal year.'
            })

        if FiscalYear.objects.filter(
            organization=org,
            name=name,
            category=category
        ).exists() and not instance:
            raise ValidationError({
                'name': ['Fiscal Year name has already been taken for this category.']
            })

        if fy_start_date > fy_end_date:
            raise serializers.ValidationError(
                {"end_at": "Fiscal Year end date should "
                           "be greater then start date"})
        if (fy_end_date - fy_start_date).days + 1 > 366:
            raise serializers.ValidationError(
                {"end_at": "Should be within 1 Year From Start Date"})

        if applicable_from > applicable_to:
            raise serializers.ValidationError(
                {
                    "applicable_to": "Should be greater than Applicable From Date"})
        if not applicable_from >= fy_start_date:
            raise serializers.ValidationError(
                {"applicable_from": "Should be greater than or "
                                    "equals to Start Date"})
        if not applicable_to <= fy_end_date:
            raise serializers.ValidationError(
                {"applicable_to": "Should be less than or equals to End Date"})

        _exclude_dict = {}
        if instance:
            _exclude_dict['id'] = instance.id
        for _fy in FiscalYear.objects.filter(
            organization=org,
            category=category
        ).exclude(
            **_exclude_dict
        ):
            overlapping_days = max(0, (
                min(applicable_to, _fy.applicable_to) -
                max(applicable_from, _fy.applicable_from)).days + 1)
            if overlapping_days > 0:
                raise serializers.ValidationError(
                    f"Applicable dates overlaps {_fy.name} by {overlapping_days} days"
                )
        _check_for_past = True
        _check_for_future = True
        if instance and instance.applicable_from == attrs.get('applicable_from'):
            _check_for_past = False
        if instance and instance.applicable_to == attrs.get('applicable_to'):
            _check_for_future = False

        if _check_for_future:
            _future_fy = FiscalYear.objects.filter(
                organization=org,
                category=category
            ).exclude(
                **_exclude_dict
            ).filter(
                applicable_from__gte=applicable_from
            ).exists()
            if _future_fy:
                _future_fy_obj = FiscalYear.objects.filter(
                    organization=org,
                    category=category
                ).exclude(
                    **_exclude_dict
                ).order_by('applicable_from').first()
                _should_be = _future_fy_obj.applicable_from - timezone.timedelta(days=1)
                if _should_be != applicable_to:
                    raise serializers.ValidationError(
                        f"Fiscal Year applicable to date "
                        f"should be {_should_be}"
                    )
        if _check_for_past:
            _past_fy = FiscalYear.objects.filter(
                organization=org,
                category=category
            ).exclude(
                **_exclude_dict
            ).filter(
                applicable_from__lte=applicable_from
            ).exists()
            if _past_fy:
                _past_fy_obj = FiscalYear.objects.filter(
                    organization=org,
                    category=category
                ).exclude(
                    **_exclude_dict
                ).order_by('applicable_from').last()
                _should_be = (_past_fy_obj.applicable_to +
                              timezone.timedelta(days=1))
                if applicable_from != _should_be:
                    raise serializers.ValidationError(
                        f"Fiscal Year applicable from "
                        f"date should be {_should_be}"
                    )

        _unique_indexes = []

        def _validate_unique_index(data):
            index = data.get('month_index')
            if index not in _unique_indexes:
                _unique_indexes.append(index)
                return True
            return False

        unique_months = list(filter(_validate_unique_index, months))
        if len(months) != len(unique_months):
            raise serializers.ValidationError(
                {'months': 'Duplicate month index found '})

        sorted_months = sorted(unique_months,
                               key=lambda x: x.get('month_index'))
        _error_message = {}
        for month_index, m in enumerate(sorted_months):
            if month_index == 0:  # first month
                if m.get('start_at') != fy_start_date:
                    _error_message[
                        'month'
                    ] = f"Start date of {m.get('display_name')} " \
                        f"should be the FY start Date"
                    break
            else:
                if m.get('start_at') != sorted_months[month_index - 1].get(
                    'end_at') + timezone.timedelta(days=1):
                    _error_message[
                        'month'
                    ] = 'Start date for {} is incorrect'.format(
                        m.get('display_name'))
                    break
        else:
            return attrs
        raise serializers.ValidationError(_error_message)

    @transaction.atomic
    def create(self, validated_data):
        org = self.context.get('organization')
        validated_data.update({'organization': org})
        months = validated_data.pop('months')
        fy = super().create(validated_data)
        self._create_months(months, fy)
        self.fields['months'] = FiscalYearMonthSerializer(
            many=True, source='fiscal_months', read_only=True,
            fields=('month_index', 'start_at',
                    'end_at', 'display_name', 'all_dates'),
            context=self.context)
        return fy

    @transaction.atomic
    def update(self, instance, validated_data):
        months = validated_data.pop('months')
        fy = super().update(instance, validated_data)
        _ = fy.fiscal_months.all().delete()
        self._create_months(months, fy)
        self.fields['months'] = FiscalYearMonthSerializer(
            many=True, source='fiscal_months', read_only=True,
            fields=('month_index', 'start_at',
                    'end_at', 'display_name', 'all_dates'),
            context=self.context)
        return fy

    @staticmethod
    def _create_months(months, fy):
        _instances = [FiscalYearMonth(fiscal_year=fy, **i) for i in months]
        FiscalYearMonth.objects.bulk_create(_instances)
