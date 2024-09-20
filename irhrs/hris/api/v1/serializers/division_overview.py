from rest_framework.fields import ReadOnlyField
from rest_framework.serializers import ModelSerializer

from irhrs.organization.models import OrganizationDivision


class DivisionOverviewSerializer(ModelSerializer):
    count = ReadOnlyField()
    
    class Meta:
        model = OrganizationDivision
        fields = ['slug', 'name', 'count']
