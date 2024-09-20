from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer
from rest_framework.validators import UniqueValidator

from irhrs.common.models.commons import (
        Disability,
        Industry,
        Bank,
        EquipmentCategory,
        )
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils.common import _validate_uniqueness
from irhrs.core.validators import validate_title
from irhrs.recruitment.models import Province, Country, District
from ...models import DocumentCategory, ReligionAndEthnicity, HolidayCategory


class DocumentCategorySerializer(DynamicFieldsModelSerializer):
    """
    Serializer for listing document category. If no results found, option
    to add new category must be provided.
    """
    slug = serializers.ReadOnlyField()

    class Meta:
        model = DocumentCategory
        fields = ('created_at', 'modified_at',
                  'name', 'associated_with', 'slug',)

    def validate(self, attrs):
        if self.instance and self.instance.has_associated_documents:
            raise ValidationError(
                "Could not update document category. The document category has associated documents.")
        return attrs


class ReligionEthnicitySerializer(DynamicFieldsModelSerializer):
    """
    Serializer for Ethnicity and Religion.
    """
    slug = serializers.ReadOnlyField()

    class Meta:
        model = ReligionAndEthnicity
        fields = ('created_at', 'modified_at', 'name', 'category', 'slug',)
        extra_kwargs = {
            "name": {
                "validators": [UniqueValidator(
                    queryset=ReligionAndEthnicity.objects.all(),
                    lookup='iexact',
                    message='Religion/Ethnicity of this name already exists.'
                ), validate_title]
            }
        }


class HolidayCategorySerializer(DynamicFieldsModelSerializer):
    """
    Serializer class for list, create, update and delete Holiday Category.
    """
    slug = serializers.ReadOnlyField()

    class Meta:
        model = HolidayCategory
        fields = ('name', 'description', 'slug', 'created_at', 'modified_at')
        extra_kwargs = {
            "name": {
                "validators": [UniqueValidator(
                    queryset=HolidayCategory.objects.all(),
                    lookup='iexact',
                    message='Holiday Category already exists.'
                ), validate_title]
            }
        }


class DisabilitySerializer(DynamicFieldsModelSerializer):
    slug = serializers.ReadOnlyField()

    class Meta:
        model = Disability
        fields = ('title', 'description', 'slug',)


class IndustrySerializer(ModelSerializer):
    class Meta:
        model = Industry
        fields = ('name', 'slug',)


class BankSerializer(DynamicFieldsModelSerializer):
    """
    Serializer for Bank Model.
    TODO @Ravi: Write Test for Bank CRUD.
    """

    class Meta:
        model = Bank
        fields = ('id', 'created_at', 'modified_at', 'slug', 'name', 'logo', 'street',
                  'city', 'country', 'address', 'acronym', 'latitude', 'longitude',)
        read_only_fields = ('slug',)


class EquipmentCategorySerializer(DynamicFieldsModelSerializer):
    """
    Serializer class for list, create, update and delete Equipment Category
    """

    slug = serializers.ReadOnlyField()

    class Meta:
        model = EquipmentCategory
        fields = ('name', 'slug', 'type', 'created_at', 'modified_at', )

    def validate_name(self, name):
        if _validate_uniqueness(
                self=self,
                queryset=EquipmentCategory.objects.all(),
                fil={'name__iexact': name}
        ):
            raise ValidationError(
                "Equipment Category with this name already exists."
            )
        return name


class ExitInterviewAnswerPostSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    order = serializers.IntegerField(required=False)
    # given_rating = serializers.IntegerField()
    title = serializers.CharField(max_length=200)
    given_remarks = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True
    )
    weightage = serializers.CharField(max_length=200, allow_blank=True)
    question_type = serializers.CharField(max_length=200, allow_blank=True)
    answer_choices = serializers.CharField(max_length=200, allow_blank=True)
    answers = serializers.ListField(
        child=serializers.JSONField(required=False),
        required=False,
        allow_empty=True
    )
    # category = serializers.CharField(max_length=200, allow_blank=True)
    description = serializers.CharField(max_length=1000, allow_blank=True)
    is_open_ended = serializers.BooleanField(default=False)
    # answer = serializers.CharField(max_length=1000, required=True)


class CountrySerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = Country
        fields = '__all__'


class ProvinceSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = Province
        fields = '__all__'


class DistrictSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = District
        fields = '__all__'
