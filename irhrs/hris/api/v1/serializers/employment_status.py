from rest_framework.fields import ReadOnlyField, IntegerField, \
    SerializerMethodField

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.organization.models import EmploymentStatus


class EmploymentStatusOverviewSerializer(DynamicFieldsModelSerializer):
    male = IntegerField(default=0)
    female = IntegerField(default=0)
    other = IntegerField(default=0)
    total = SerializerMethodField()

    class Meta:
        model = EmploymentStatus
        fields = ["title", "male", "female", "other", "total"]

    @staticmethod
    def get_total(obj):
        return obj.male + obj.female + obj.other
