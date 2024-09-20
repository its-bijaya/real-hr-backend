from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.export.models import Export
from irhrs.organization.api.v1.serializers.organization import OrganizationSerializer
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer


class ExportSerializer(DynamicFieldsModelSerializer):
    user = UserThinSerializer(
        fields=["id", "full_name", "profile_picture", "cover_picture", 'is_current', 'organization', "job_title", "is_online"]
    )
    organization = OrganizationSerializer(fields=["name", "slug"])

    class Meta:
        model = Export
        fields = [
            "name", "export_type", "user", "organization", "exported_as", "export_file",
            "status", "remarks", "id", "created_at"
        ]
