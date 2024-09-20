from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.appraisal.constants import APPRAISAL_TYPE, THREE_SIXTY_PERFORMANCE_APPRAISAL, \
    REVIEWER_EVALUATION, KEY_ACHIEVEMENTS_AND_RATING, SUBORDINATE_APPRAISAL, PEER_TO_PEER_FEEDBACK
from irhrs.appraisal.models.appraiser_setting import Appraisal
from irhrs.appraisal.models.performance_appraisal_setting import AppraisalSetting, \
    ScoreAndScalingSetting, DeadlineExtendCondition, DeadlineExceedScoreDeductionCondition, \
    StepUpDownRecommendation, FormReviewSetting, ExceptionalAppraiseeFilterSetting
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils import nested_getattr
from irhrs.core.utils.common import DummyObject
from irhrs.organization.api.v1.serializers.branch import OrganizationBranchSerializer
from irhrs.organization.api.v1.serializers.division import OrganizationDivisionSerializer
from irhrs.organization.api.v1.serializers.employment import EmploymentStatusSerializer, \
    EmploymentLevelSerializer
from irhrs.organization.models import OrganizationBranch, OrganizationDivision, EmploymentStatus, \
    EmploymentLevel
from irhrs.users.api.v1.serializers.thin_serializers import UserThumbnailSerializer

User = get_user_model()


class SubPerformanceAppraisalSlotSerializerMixin(DynamicFieldsModelSerializer):
    def create(self, validated_data):
        validated_data['sub_performance_appraisal_slot'] = self.sub_performance_appraisal_slot
        return super().create(validated_data)

    @property
    def sub_performance_appraisal_slot(self):
        return self.context[
            'sub_performance_appraisal_slot']

    @property
    def sub_performance_appraisal_slot_config(self):
        return self.context['sub_performance_appraisal_slot_config']


class AppraisalSettingSerializer(DynamicFieldsModelSerializer):
    branches = OrganizationBranchSerializer(fields=('slug', 'name'), many=True)
    divisions = OrganizationDivisionSerializer(fields=('slug', 'name'), many=True)
    employment_types = EmploymentStatusSerializer(fields=('slug', 'title'), many=True)
    employment_levels = EmploymentLevelSerializer(fields=('slug', 'title'), many=True)

    class Meta:
        model = AppraisalSetting
        fields = (
            'id', 'duration_of_involvement', 'duration_of_involvement_type', 'branches',
            'divisions', 'employment_types', 'employment_levels'
        )

    def get_fields(self):
        fields = super().get_fields()
        if self.request.method.lower() == 'post':
            fil = {
                'organization': self.context.get('organization')
            }
            fields['branches'] = serializers.SlugRelatedField(
                queryset=OrganizationBranch.objects.filter(**fil),
                many=True,
                slug_field='slug'
            )
            fields['divisions'] = serializers.SlugRelatedField(
                queryset=OrganizationDivision.objects.filter(**fil),
                many=True,
                slug_field='slug'
            )
            fields['employment_types'] = serializers.SlugRelatedField(
                queryset=EmploymentStatus.objects.filter(**fil),
                many=True,
                slug_field='slug'
            )
            fields['employment_levels'] = serializers.SlugRelatedField(
                queryset=EmploymentLevel.objects.filter(**fil),
                many=True,
                slug_field='slug'
            )
        return fields

    def create(self, validated_data):
        extra_fields = ['branches', 'divisions', 'employment_types', 'employment_levels']
        extracted_data = {}
        for key in extra_fields:
            extracted_data[key] = validated_data.pop(key, [])
        instance, created = AppraisalSetting.objects.update_or_create(
            sub_performance_appraisal_slot=self.context.get('sub_performance_appraisal_slot'),
            defaults=validated_data
        )
        if created:
            for key, value in extracted_data.items():
                getattr(instance, key).set(value)
        else:
            for key, value in extracted_data.items():
                getattr(instance, key).clear()
                getattr(instance, key).set(value)
        return instance


class ExceptionalAppraiseeFilterSettingSerializer(serializers.Serializer):
    appraisal_type = serializers.ChoiceField(
        choices=list(dict(APPRAISAL_TYPE).keys())
    )
    action_type = serializers.ChoiceField(
        choices=['include', 'exclude']
    )

    def get_fields(self):
        fields = super().get_fields()
        fields['users'] = serializers.PrimaryKeyRelatedField(
            queryset=User.objects.filter(
                detail__organization=self.context.get('organization')
            ).current(),
            many=True
        )
        return fields

    @staticmethod
    def include_appraisee(instance, validated_data):
        exclude_users = set(instance.exclude_users.all())
        appraisees = set(validated_data.get('users'))

        common_appraisees = exclude_users.intersection(appraisees)
        if common_appraisees:
            instance.exclude_users.remove(*common_appraisees)

        instance.include_users.add(*appraisees)
        instance.save()

    def exclude_appraisee(self, instance, validated_data):
        include_users = set(instance.include_users.all())
        appraisees = set(validated_data.get('users'))
        sub_pa_slot = instance.sub_performance_appraisal_slot

        appraisals = set(
            User.objects.annotate(
                is_selected=Exists(
                    Appraisal.objects.filter(
                        sub_performance_appraisal_slot=sub_pa_slot,
                        appraisal_type=validated_data.get('appraisal_type'),
                        appraisee=OuterRef('id')
                    )
                )
            ).filter(is_selected=True)
        )

        common_users = include_users.intersection(appraisees)
        if common_users:
            instance.include_users.remove(*common_users)

        if not appraisals.isdisjoint(appraisees):
            Appraisal.objects.filter(
                sub_performance_appraisal_slot=sub_pa_slot,
                appraisal_type=validated_data.get('appraisal_type'),
                appraisee__in=appraisees
            ).delete()

        instance.exclude_users.add(*appraisees)
        instance.save()

    def create(self, validated_data):
        sub_pa_slot = self.context.get('sub_performance_appraisal_slot')
        appraisal_type = validated_data.get('appraisal_type')
        action_type = validated_data.get('action_type')

        exceptional_appraisee, created = ExceptionalAppraiseeFilterSetting.objects.get_or_create(
            sub_performance_appraisal_slot=sub_pa_slot,
            appraisal_type=appraisal_type
        )

        # calling function dynamically
        getattr(self, f'{action_type}_appraisee')(exceptional_appraisee, validated_data)

        return DummyObject(**validated_data)


class ScoreAndScalingSettingSerializer(SubPerformanceAppraisalSlotSerializerMixin):
    class Meta:
        model = ScoreAndScalingSetting
        fields = 'id', 'name', 'scale', 'score'


class DeadlineExtendConditionSerializer(SubPerformanceAppraisalSlotSerializerMixin):
    class Meta:
        model = DeadlineExtendCondition
        fields = (
            'total_appraise_count_ranges_from', 'total_appraise_count_ranges_to',
            'extended_days'
        )

    def validate(self, attrs):
        range_from = attrs.get('total_appraise_count_ranges_from')
        range_to = attrs.get('total_appraise_count_ranges_to')
        if range_from > range_to:
            raise ValidationError({
                'non_field_errors': ['Invalid appraise count ranges supplied.']
            })
        return super().validate(attrs)


class DeductionCriteriaSerializer(SubPerformanceAppraisalSlotSerializerMixin):
    class Meta:
        model = DeadlineExceedScoreDeductionCondition
        fields = 'total_exceed_days_from', 'total_exceed_days_to', 'deduct_value'

    def validate(self, attrs):
        total_exceed_days_from = attrs.get('total_exceed_days_from')
        total_exceed_days_to = attrs.get('total_exceed_days_to')
        if total_exceed_days_from > total_exceed_days_to:
            raise ValidationError({'non_field_errorss': ['Invalid days ranges.']})
        return super().validate(attrs)


class DeadlineExceedScoreDeductionConditionSerializer(DynamicFieldsModelSerializer):
    deduction_criteria = DeductionCriteriaSerializer(many=True)

    class Meta:
        model = DeadlineExceedScoreDeductionCondition
        fields = 'deduction_type', 'deduction_criteria'

    def validate(self, attrs):
        deduction_criteria = attrs.get('deduction_criteria')
        for index, datum in enumerate(deduction_criteria):
            if index > 0:
                if datum['total_exceed_days_from'] <= deduction_criteria[index - 1].get(
                    'total_exceed_days_to'):
                    raise ValidationError({
                        'non_field_errors': ['Total exceed day ranges should not overlap.']
                    })
        return super().validate(attrs)

    def create(self, validated_data):
        deduction_type = self.initial_data.get('deduction_type')
        deduction_criteria = self.initial_data.get('deduction_criteria')

        deduction_criteria_list = []
        for criteria in deduction_criteria:
            deduction_criteria_list.append(
                DeadlineExceedScoreDeductionCondition(
                    sub_performance_appraisal_slot=self.context['sub_performance_appraisal_slot'],
                    deduction_type=deduction_type,
                    **criteria
                )
            )

        if deduction_criteria_list:
            DeadlineExceedScoreDeductionCondition.objects.bulk_create(deduction_criteria_list)
        return DummyObject(**validated_data)


class StepUpDownCriteriaSerializer(SubPerformanceAppraisalSlotSerializerMixin):
    class Meta:
        model = StepUpDownRecommendation
        fields = ('score_acquired_from', 'score_acquired_to', 'change_step_by')

    def validate(self, attrs):
        score_acquired_from = attrs.get('score_acquired_from')
        score_acquired_to = attrs.get('score_acquired_to')
        if score_acquired_from > score_acquired_to:
            raise ValidationError({'non_field_errorss': ['Invalid score ranges.']})
        return super().validate(attrs)


class StepUpDownRecommendationSerializer(DynamicFieldsModelSerializer):
    recommendation_criteria = StepUpDownCriteriaSerializer(many=True)

    class Meta:
        model = StepUpDownRecommendation
        fields = ('recommendation_criteria',)

    def validate(self, attrs):
        recommendation_criteria = attrs.get('recommendation_criteria')
        serializer = StepUpDownCriteriaSerializer(data=recommendation_criteria, many=True)
        serializer.is_valid(raise_exception=True)
        for index, datum in enumerate(recommendation_criteria):
            if index > 0:
                if datum['score_acquired_from'] <= recommendation_criteria[index - 1].get(
                    'score_acquired_to'):
                    raise ValidationError({
                        'non_field_error': ['Acquired score ranges should not overlap.']
                    })

                if datum['change_step_by'] == recommendation_criteria[index - 1].get(
                    'change_step_by'):
                    raise ValidationError(
                        {'change_step_by': ['Change step by might not be equal.']})
        return super().validate(attrs)

    def create(self, validated_data):
        recommendation_criteria = self.initial_data.get('recommendation_criteria')
        step_up_down = []
        for criteria in recommendation_criteria:
            step_up_down.append(
                StepUpDownRecommendation(
                    sub_performance_appraisal_slot=self.context['sub_performance_appraisal_slot'],
                    **criteria
                )
            )
        if step_up_down:
            StepUpDownRecommendation.objects.bulk_create(step_up_down)
        return DummyObject(**validated_data)


class FormReviewSettingSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = FormReviewSetting
        fields = 'viewable_appraisal_submitted_form_type', 'can_hr_download_form',

    def validate(self, attrs):
        extracted_data = attrs.get('viewable_appraisal_submitted_form_type')
        if extracted_data and len(extracted_data) != len(set(extracted_data)):
            raise ValidationError({
                'viewable_appraisal_submitted_form_type': ['Duplicate appraisal type submitted.']
            })

        return super().validate(attrs)

    def validate_viewable_appraisal_submitted_form_type(self, value):
        if self.performance_appraisal_type == THREE_SIXTY_PERFORMANCE_APPRAISAL and REVIEWER_EVALUATION in value:
            raise ValidationError({
                'viewable_appraisal_submitted_form_type': f'Can not assign {REVIEWER_EVALUATION} '
                                                          f'in {THREE_SIXTY_PERFORMANCE_APPRAISAL}.'
            })
        if self.performance_appraisal_type == KEY_ACHIEVEMENTS_AND_RATING and (
            SUBORDINATE_APPRAISAL in value or PEER_TO_PEER_FEEDBACK in value):
            raise ValidationError({
                'viewable_appraisal_submitted_form_type': f'Can not assign {SUBORDINATE_APPRAISAL} or {PEER_TO_PEER_FEEDBACK} '
                                                          f'in {KEY_ACHIEVEMENTS_AND_RATING}.'
            })
        return value

    def create(self, validated_data):
        _ = FormReviewSetting.objects.update_or_create(
            sub_performance_appraisal_slot=self.context['sub_performance_appraisal_slot'],
            defaults={**validated_data}
        )
        return DummyObject(**validated_data)

    @property
    def performance_appraisal_type(self):
        return nested_getattr(self.context.get('sub_performance_appraisal_slot'),
                              'performance_appraisal_year.performance_appraisal_type')


class AppraiseeSettingActionValidation(serializers.Serializer):
    def _validate_type(self, fil):
        sub_performance_appraisal_slot = self.context.get('sub_performance_appraisal_slot')
        valid_appraisal_types = sub_performance_appraisal_slot.modes.filter(
            **fil
        )
        if not valid_appraisal_types.exists():
            raise ValidationError(
                'Appraisal Type must be one of these '
                f'{",".join(valid_appraisal_types.values_list("appraisal_type", flat=True))}'
            )
        elif not valid_appraisal_types:
            raise ValidationError('There are not any valid appraisal type.')


class AppraiseeSettingMultipleActionSerializer(AppraiseeSettingActionValidation):
    appraisal_types = serializers.MultipleChoiceField(
        choices=APPRAISAL_TYPE
    )

    def validate_appraisal_type(self, appraisal_types):
        self._validate_type({'appraisal_type__in': appraisal_types})
        return appraisal_types


class AppraiseeSettingSingleActionSerializer(AppraiseeSettingMultipleActionSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all().current()
    )

    def validate_appraisal_type(self, appraisal_types):
        self._validate_type({'appraisal_type__in': appraisal_types})
        return appraisal_types


class AppraiseeSettingListSerializer(UserThumbnailSerializer):
    appraisee = serializers.SerializerMethodField()
    joined_date = serializers.SerializerMethodField()

    class Meta(UserThumbnailSerializer.Meta):
        fields = (
            'id', 'full_name', 'profile_picture', 'cover_picture',
            'job_title', 'is_online', 'last_online', 'appraisee', 'joined_date'
        )

    @staticmethod
    def get_appraisee(obj):
        return {
            'id': obj.appraisee[0].id,
            'appraisal_types': getattr(obj, 'appraisal_types', [])
        } if obj.appraisee else None

    @staticmethod
    def get_joined_date(instance):
        detail = instance.detail if hasattr(instance, 'detail') else None
        return detail.joined_date if detail and detail.joined_date else 'Job Title N/A'
