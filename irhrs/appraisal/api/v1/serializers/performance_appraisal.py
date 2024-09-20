from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.appraisal.api.v1.serializers.kaar_appraiser import KAARAppraiserSerializer
from irhrs.appraisal.constants import IDLE, COMPLETED, ACTIVE, SENT, \
    THREE_SIXTY_PERFORMANCE_APPRAISAL, REVIEWER_EVALUATION, \
    KEY_ACHIEVEMENTS_AND_RATING, PEER_TO_PEER_FEEDBACK, SUBORDINATE_APPRAISAL, SELF_APPRAISAL, \
    SUPERVISOR_APPRAISAL
from irhrs.appraisal.models.performance_appraisal import PerformanceAppraisalYear, \
    SubPerformanceAppraisalSlot, SubPerformanceAppraisalSlotMode
from irhrs.appraisal.models.form_design import ResendPAForm
from irhrs.appraisal.utils.common import _validate_total_weight
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils import nested_getattr
from irhrs.core.utils.common import DummyObject
from irhrs.organization.api.v1.serializers.fiscal_year import FiscalYearSerializer
from irhrs.appraisal.models.key_achievement_and_rating_pa import KAARAppraiserConfig


class PerformanceAppraisalYearSlotSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = SubPerformanceAppraisalSlot
        fields = 'id', 'title', 'weightage', 'from_date', 'to_date', 'status'
        read_only_fields = 'status',

    def create(self, validated_data):
        instance = super().create(validated_data)
        return instance

    def get_fields(self):
        fields = super().get_fields()
        fields['id'] = serializers.IntegerField(label='ID', allow_null=True, required=False)
        if self.request and self.request.method.upper() == 'GET' and self.context.get('mode') == 'user':
            fields['appraisers'] = serializers.SerializerMethodField()
        return fields

    def validate(self, attrs):
        if attrs.get('from_date') > attrs.get('to_date'):
            raise ValidationError({
                'non_field_errors': ['"From Date" must be less then "To Date".']
            })
        return super().validate(attrs)

    def get_appraisers(self, instance):
        appraisers = KAARAppraiserConfig.objects.filter(
            kaar_appraisal__sub_performance_appraisal_slot = instance,
            kaar_appraisal__appraisee = self.request.user
        ).exclude(appraiser_type=SELF_APPRAISAL)
        return KAARAppraiserSerializer(
            appraisers,
            fields=['appraiser_type', 'appraiser'],
            many=True,
            context=self.context
        ).data


class PerformanceAppraisalYearSerializer(DynamicFieldsModelSerializer):
    slots = PerformanceAppraisalYearSlotSerializer(
        many=True
    )

    class Meta:
        model = PerformanceAppraisalYear
        fields = 'id', 'name', 'year', 'slots', 'performance_appraisal_type'

    @staticmethod
    def get_status(obj):
        slots = obj.slots.all()
        status = [slot.status for slot in slots]
        if all(map(lambda x: x == IDLE, status)):
            return IDLE
        elif all(map(lambda x: x == COMPLETED, status)):
            return COMPLETED
        return ACTIVE

    def get_fields(self):
        fields = super().get_fields()
        if self.request.method.lower() == 'get':
            fields['year'] = FiscalYearSerializer(
                fields=('id', 'name')
            )
            fields['slots'] = serializers.SerializerMethodField()

            fields['status'] = serializers.SerializerMethodField()
        return fields

    def get_slots(self, obj):
        fil = dict()
        if self.context.get('mode') == "user":
            fil["question_set_status"] = SENT
        return PerformanceAppraisalYearSlotSerializer(
            obj.slots.filter(**fil),
            many=True,
            context=self.context
        ).data

    @staticmethod
    def create_slots(slots, instance):
        new_slots = []
        for slot in slots:
            new_slots.append(
                SubPerformanceAppraisalSlot(
                    performance_appraisal_year=instance,
                    **slot
                )
            )
        if new_slots:
            SubPerformanceAppraisalSlot.objects.bulk_create(new_slots)

    def validate(self, attrs):
        slots = attrs.get('slots')
        name = attrs.get('name')
        year = attrs.get('year')
        performance_appraisal_type = attrs.get('performance_appraisal_type')
        if performance_appraisal_type and self.instance and \
            performance_appraisal_type != self.instance.performance_appraisal_type:
            raise ValidationError({
                'non_field_errors': 'Can not update appraisal type.'
            })
        if not year:
            raise ValidationError({
                'year': 'This field may not be null.'
            })

        if not self.instance and PerformanceAppraisalYear.objects.filter(
            year=year,
            organization=self.context.get('organization')
        ).exists():
            raise ValidationError({
                'year': 'Performance Appraisal with this year already exists.'
            })

        if not self.instance and PerformanceAppraisalYear.objects.filter(
            name__iexact=name,
            organization=self.context.get('organization')
        ).exists():
            raise ValidationError({
                'name': 'Performance Appraisal with this name already exists.'
            })

        _validate_total_weight(
            slots,
        )
        self._validate_overlapped_date_ranges(slots, year)
        self._validate_unique_frequency_title(slots)
        attrs['organization'] = self.context.get('organization')
        return super().validate(attrs)

    @staticmethod
    def _validate_unique_frequency_title(slots):
        frequency_title = [slot.get('title') for slot in slots]
        if len(frequency_title) != len(set(frequency_title)):
            raise ValidationError({
                'non_field_errors': ['Frequency title must be unique.']
            })

    @staticmethod
    def _validation_date_between_fiscal_year(date, year):
        if not year.applicable_from <= date <= year.applicable_to:
            raise ValidationError({
                'non_field_errors': ['Date ranges must be within appraisal year.']
            })

    def _validate_overlapped_date_ranges(self, slots, year):
        for index, slot in enumerate(slots):
            self._validation_date_between_fiscal_year(slot['from_date'], year)
            self._validation_date_between_fiscal_year(slot['to_date'], year)
            if index > 0:
                if slot['from_date'] < slots[index - 1].get('to_date'):
                    raise ValidationError({
                        'non_field_errors': ['Date ranges should not overlap.']
                    })

    @transaction.atomic
    def create(self, validated_data):
        slots = validated_data.pop('slots', [])
        validated_data['organization'] = self.context.get('organization')
        instance = super().create(validated_data)
        self.create_slots(slots, instance)
        return DummyObject(**validated_data, slots=slots)

    @transaction.atomic
    def update(self, instance, validated_data):
        slots = validated_data.pop('slots', [])

        instance = super().update(instance, validated_data)

        get_slot_id = {slot.get('id') for slot in slots if slot.get('id')}
        existing_slots = set(instance.slots.values_list('id', flat=True))

        deleted_ids = existing_slots - get_slot_id
        updated_ids = get_slot_id - deleted_ids
        updated_slots = [slot for slot in slots if slot.get('id') in updated_ids]
        new_slots = [slot for slot in slots if not slot.get('id')]

        instance.slots.exclude(id__in=get_slot_id).delete()
        self.create_slots(new_slots, instance)

        for updated_slot in updated_slots:
            slot = instance.slots.get(id=updated_slot.get('id'))
            slot.title = updated_slot.get('title')
            slot.weightage = updated_slot.get('weightage')
            slot.from_date = updated_slot.get('from_date')
            slot.to_date = updated_slot.get('to_date')
            slot.save()

        return DummyObject(**validated_data, slots=slots)


class ResendPAFormSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = ResendPAForm
        fields = "reason",


class SubPerformanceAppraisalSlotModeSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = SubPerformanceAppraisalSlotMode
        fields = 'id', 'appraisal_type', 'weightage', 'start_date', 'deadline'

    def validate(self, attrs):
        # TODO @shital also validate conditions as described in model class docstring.
        attrs['sub_performance_appraisal_slot'] = self.sub_performance_appraisal_slot
        return super().validate(attrs)

    def validate_appraisal_type(self, value):
        slot_mapper = {
            THREE_SIXTY_PERFORMANCE_APPRAISAL: [SELF_APPRAISAL, SUBORDINATE_APPRAISAL,
                                                PEER_TO_PEER_FEEDBACK, SUPERVISOR_APPRAISAL],
            KEY_ACHIEVEMENTS_AND_RATING: [SELF_APPRAISAL, SUPERVISOR_APPRAISAL,
                                          REVIEWER_EVALUATION]
        }
        if value not in slot_mapper.get(self.performance_appraisal_type, []):
            raise ValidationError({
                'appraisal_type': f'You can not assign {value} '
                                  f'in {self.performance_appraisal_type}'
            })
        return value

    @property
    def sub_performance_appraisal_slot(self):
        return self.context['sub_performance_appraisal_slot']

    @property
    def performance_appraisal_type(self):
        return nested_getattr(
            self.sub_performance_appraisal_slot,
            'performance_appraisal_year.performance_appraisal_type'
        )
