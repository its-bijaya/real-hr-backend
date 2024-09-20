from rest_framework import serializers
from rest_framework.relations import SlugRelatedField
from rest_framework.serializers import ModelSerializer

from irhrs.common.api.serializers.common import DisabilitySerializer
from irhrs.common.models import Disability
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils.change_request import create_add_change_request, \
    create_delete_change_request
from irhrs.core.validators import validate_height, validate_weight, \
    validate_chronic_disease
from irhrs.users.models.medical_and_legal import ChronicDisease, UserMedicalInfo, \
    RestrictedMedicine, AllergicHistory
from irhrs.users.utils.notification import send_change_notification_to_user


class ChronicDiseaseSerializer(ModelSerializer):
    class Meta:
        model = ChronicDisease
        fields = ('title',
                  'description',
                  'user',
                  'slug')
        read_only_fields = ('slug',)


class RestrictedMedicineSerializer(ModelSerializer):
    class Meta:
        model = RestrictedMedicine
        fields = ('title',
                  'description',
                  'user',
                  'slug')
        read_only_fields = ('slug',)


class AllergicHistorySerializer(ModelSerializer):
    class Meta:
        model = AllergicHistory
        fields = ('title',
                  'description',
                  'user',
                  'slug')
        read_only_fields = ('slug',)


class UserMedicalInfoSerializer(DynamicFieldsModelSerializer):
    # This serializer only supports put not patch, if patch request is sent all
    # chronic diseases will be cleared
    chronic_disease = ChronicDiseaseSerializer(
        required=False, many=True
    )
    restricted_medicine = RestrictedMedicineSerializer(
        required=False, many=True
    )
    allergic_history = AllergicHistorySerializer(
        required=False, many=True
    )
    disabilities = SlugRelatedField(queryset=Disability.objects.all(),
                                    slug_field='slug', many=True,
                                    required=False)

    class Meta:
        model = UserMedicalInfo
        fields = (
            'id', 'user', 'blood_group', 'height', 'height_unit', 'weight',
            'weight_unit', 'smoker', 'drinker', 'on_medication', 'chronic_disease',
            'disabilities', 'restricted_medicine', 'allergic_history'
        )
        read_only_fields = ('id',)

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if request and request.method.upper() == 'GET':
            fields['disabilities'] = DisabilitySerializer(many=True)
            fields['chronic_disease'] = serializers.SerializerMethodField()
            fields['restricted_medicine'] = serializers.SerializerMethodField()
            fields['allergic_history'] = serializers.SerializerMethodField()
        return fields

    @staticmethod
    def get_chronic_disease(obj):
        return ChronicDiseaseSerializer(
            ChronicDisease.objects.filter(user=obj.user),
            many=True
        ).data

    @staticmethod
    def get_restricted_medicine(obj):
        return RestrictedMedicineSerializer(
            RestrictedMedicine.objects.filter(user=obj.user),
            many=True
        ).data

    @staticmethod
    def get_allergic_history(obj):
        return AllergicHistorySerializer(
            AllergicHistory.objects.filter(user=obj.user),
            many=True
        ).data

    def before_create(self, validated_data, change_request=False):
        user = self.context.get('user')
        validated_data.update({
            'user': user
        })
        model_map = {
            'chronic_disease': ChronicDisease,
            'restricted_medicine': RestrictedMedicine,
            'allergic_history': AllergicHistory
        }
        info_categories = ['chronic_disease', 'restricted_medicine', 'allergic_history']
        for info_category in info_categories:
            model = model_map.get(info_category)
            extra_info_data = validated_data.pop(info_category, None)
            if extra_info_data:
                for datum in extra_info_data:
                    datum.update({'user': user})
                    if change_request:
                        create_add_change_request(
                            user,
                            model,
                            datum,
                            category=info_category.replace('_', ' ').title()
                        )

                    else:
                        model.objects.create(**datum)
        return validated_data

    def create(self, validated_data):
        validated_data = self.before_create(validated_data)
        instance = super().create(validated_data)
        send_change_notification_to_user(
            self, instance, instance.user,
            self.request.user, 'created'
        )
        return instance

    def before_update(self, instance, validated_data, change_request=False):

        user = self.context.get('user')
        model_map_with_relation = {
            'chronic_disease': (ChronicDisease, 'chronicdisease_set'),
            'restricted_medicine': (RestrictedMedicine, 'restrictedmedicine_set'),
            'allergic_history': (AllergicHistory, 'allergichistory_set'),
        }
        info_categories = ['chronic_disease', 'restricted_medicine', 'allergic_history']
        for info_category in info_categories:
            model, model_relation = model_map_with_relation.get(info_category)
            category_data = validated_data.pop(info_category, None)
            # since we only insert chronic disease name at the moment so,
            # for update, take title as reference
            existing_data = set(
                getattr(
                    user,
                    model_relation
                ).all().values_list('title', flat=True)
            )

            requested_data = set(
                map(
                    lambda x: x.get('title'),
                    category_data
                )
            ) if category_data else set()

            new_data = (requested_data - existing_data)
            deleted_data = (existing_data - requested_data)

            new_data_to_create = list(
                filter(
                    lambda x: x.get('title') in new_data,
                    category_data
                )
            )
            if change_request:
                if new_data:
                    for datum in new_data_to_create:
                        data = {
                            'user': user,
                            **datum
                        }
                        create_add_change_request(
                            user,
                            model,
                            data,
                            category=info_category.replace('_', ' ').title()
                        )

                if deleted_data:
                    deleted_instances = model.objects.filter(
                        user=user,
                        title__in=deleted_data
                    )
                    for cd in deleted_instances:
                        create_delete_change_request(
                            user=user, obj=cd,
                            category=info_category.replace('_', ' ').title()
                        )
            else:
                if new_data:
                    for title in new_data:
                        model.objects.create(
                            title=title,
                            description='',
                            user=user
                        )

                if deleted_data:
                    for title in deleted_data:
                        model.objects.filter(
                            user=user,
                            title=title
                        ).delete()

        return validated_data

    def update(self, instance, validated_data):
        validated_data = self.before_update(instance, validated_data)
        instance = super().update(instance, validated_data)
        send_change_notification_to_user(
            self, instance, instance.user,
            self.request.user, 'created'
        )
        return instance

    def validate(self, data):
        validate_height(obj=self.instance, input_data=data)
        validate_weight(obj=self.instance, input_data=data)
        data.update(user=self.context.get('user'))
        chronic_disease = data.get('chronic_disease')
        validate_chronic_disease(chronic_disease)
        return super().validate(data)
