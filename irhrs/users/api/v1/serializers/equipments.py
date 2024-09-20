# from rest_framework import serializers
# from rest_framework.fields import ReadOnlyField
# from rest_framework.serializers import ModelSerializer

# from irhrs.common.models.commons import EquipmentCategory
# from irhrs.common.api.v1.serializers import EquipmentCategorySerializer
# from irhrs.organization.models import (
#     OrganizationEquipment,
#     OrganizationDivision,
#     OrganizationBranch
# )


# class OrganizationEquipmentSerializer(ModelSerializer):
#     category = EquipmentCategorySerializer()
#     equipment_picture_thumbnail = ReadOnlyField(
#         source='equipment_picture_thumb',
#         allow_null=True)
#     assigned_detail = serializers.SerializerMethodField(read_only=True)

#     class Meta:
#         model = OrganizationEquipment
#         fields = (
#             'id', 'category', 'name', 'brand_name', 'code', 'amount',
#             'purchased_date', 'service_order', 'bill_number',
#             'reference_number', 'assigned_to', 'status',
#             'specifications', 'equipment_picture',
#             'equipment_picture_thumbnail', 'remark', 'slug',
#             'assigned_detail',
#         )
#         read_only_fields = ('slug', 'organization')
#         extra_kwargs = {
#             'code': {
#                 'allow_blank': False
#             },
#             'equipment_picture': {
#                 'required': False
#             }
#         }
