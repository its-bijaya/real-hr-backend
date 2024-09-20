from rest_framework import serializers

from irhrs.core.mixins.serializers import DummySerializer, DynamicFieldsModelSerializer
from irhrs.hris.models import ResultArea
from irhrs.task.models.ra_and_core_tasks import UserResultArea


class TopResultAreasForTask(DummySerializer):
    result_area_id = serializers.IntegerField()
    result_area = serializers.CharField()
    total = serializers.IntegerField()
    critical = serializers.IntegerField()
    major = serializers.IntegerField()
    minor = serializers.IntegerField()


class ResultAreaWithCurrentExperienceSerializer(DynamicFieldsModelSerializer):
    result_area_id = serializers.ReadOnlyField(source='id')
    result_area = serializers.ReadOnlyField(source='title')

    class Meta:
        model = ResultArea
        fields = ['result_area_id', 'result_area']
