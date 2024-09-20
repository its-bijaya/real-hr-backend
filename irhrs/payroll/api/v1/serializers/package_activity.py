from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.fields import ReadOnlyField

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.organization.api.v1.serializers.organization import OrganizationSerializer
from irhrs.payroll.models import PayrollPackageActivity
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer

Employee = get_user_model()


class PayrollPackageActivitySerializer(
        DynamicFieldsModelSerializer):
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = PayrollPackageActivity
        fields = ('title', 'assigned_to', 'action', 'package', 'organization', 'created_at')


    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method == 'GET':
            fields['assigned_to'] = UserThinSerializer(fields=('id', 'full_name', 'profile_picture',
                                                               'cover_picture', 'division',
                                                               'job_title', 'email', 'employee_level',
                                                               'organization', ))
            fields['organization'] = OrganizationSerializer(fields=['name', 'slug'])
            fields['package'] = ReadOnlyField(
                    source='package.name', allow_null=True)
        return fields

