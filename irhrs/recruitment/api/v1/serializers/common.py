from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.hris.api.v1.serializers.onboarding_offboarding import LetterTemplateSerializer
from irhrs.recruitment.constants import (
    APPROVED, SHORTLIST_MEMORANDUM_PARAMS,
    SHORTLIST_MEMORANDUM, INTERVIEW_MEMORANDUM,
    INTERVIEW_MEMORANDUM_PARAMS,
    NO_OBJECTION_LETTER, NO_OBJECTION_LETTER_PARAMS,
    EXTERNAL_USER_LETTER_PARAMS, SALARY_DECLARATION_LETTER_PARAMS,
    CANDIDATE_LETTER_PARAMS, CANDIDATE_LETTER, EXTERNAL_USER_LETTER,
    EMPLOYMENT_AGREEMENT_PARAMS, EMPLOYMENT_AGREEMENT, SALARY_DECLARATION_LETTER
)

from irhrs.recruitment.models import (
    Salary, Language,
    DocumentCategory, JobCategory,
    JobSetting,
    JobBenefit, City, Location,
    Template)


class GetOrCreateSerializer(DynamicFieldsModelSerializer):
    """
    This serializer mixin will call get_or_create instead of just create
    in create method.
    """

    def create(self, validated_data):
        ModelClass = self.Meta.model

        instance, _ = ModelClass.objects.get_or_create(**validated_data)
        return instance


class SalarySerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Salary
        fields = [
            'currency', 'operator',
            'minimum', 'maximum', 'unit'
        ]

    def validate(self, attrs):
        minimum = attrs.get('minimum', ...)
        maximum = attrs.get('maximum', ...)
        operator = attrs.get('operator', ...)

        if minimum is ...:
            if self.partial and self.instance:
                minimum = self.instance.minimum
            else:
                minimum = None

        if maximum is ...:
            if self.partial and self.instance:
                maximum = self.instance.maximum
            else:
                maximum = None

        if operator is ...:
            if self.partial and self.instance:
                operator = self.instance.operator
            else:
                operator = None

        if minimum is None:
            raise serializers.ValidationError(
                {'minimum': _("This field is required.")})

        if maximum is None and not operator:
            raise serializers.ValidationError(
                {'operator': _("This field is required.")}
            )

        if (minimum is not None) and (maximum is not None) \
            and maximum < minimum:
            raise serializers.ValidationError({
                'minimum':
                    _("Minimum salary must be lesser than maximum salary.")
            })
        return attrs


class LanguageSerializer(GetOrCreateSerializer):
    class Meta:
        model = Language
        fields = '__all__'
        extra_kwargs = {
            'name': {
                'validators': [UniqueValidator(
                    queryset=Language.objects.filter(status=APPROVED)
                )]
            }
        }


class DocumentCategorySerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = DocumentCategory
        fields = '__all__'


class JobCategorySerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = JobCategory
        fields = '__all__'


class LocationSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = Location
        fields = '__all__'
        extra_kwargs = {
            'country': {
                'required': True,
                'allow_null': False
            },
            'city_name': {
                'required': True,
                'allow_blank': False
            },
        }


class JobSettingSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = JobSetting
        exclude = ['job', 'id']


class JobBenefitSerializer(GetOrCreateSerializer):
    class Meta:
        model = JobBenefit
        fields = '__all__'
        extra_kwargs = {
            'name': {
                'validators': [UniqueValidator(
                    queryset=JobBenefit.objects.filter(status=APPROVED)
                )]
            }
        }


class CitySerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = City
        fields = '__all__'


class QuestionSerializer(DynamicFieldsModelSerializer):

    class Meta:
        fields = '__all__'


class TemplateSerializer(LetterTemplateSerializer):

    allowed_templates = {
            CANDIDATE_LETTER: CANDIDATE_LETTER_PARAMS.keys(),
            EXTERNAL_USER_LETTER: EXTERNAL_USER_LETTER_PARAMS.keys(),
            SALARY_DECLARATION_LETTER: SALARY_DECLARATION_LETTER_PARAMS.keys(),
            NO_OBJECTION_LETTER: NO_OBJECTION_LETTER_PARAMS.keys(),

            SHORTLIST_MEMORANDUM: SHORTLIST_MEMORANDUM_PARAMS.keys(),
            INTERVIEW_MEMORANDUM: INTERVIEW_MEMORANDUM_PARAMS.keys(),
            EMPLOYMENT_AGREEMENT: EMPLOYMENT_AGREEMENT_PARAMS.keys()
        }

    class Meta:
        model = Template
        fields = (
            'title', 'message', 'type', 'status'
        )
