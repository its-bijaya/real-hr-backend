from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError

from irhrs.attendance.constants import EXTERNAL_SERVER
from irhrs.attendance.models import AttendanceSource, TimeSheetEntry, AttendanceUserMap, TimeSheet
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.mixins.viewset_mixins import CreateViewSetMixin
from irhrs.core.utils.common import DummyObject


class AttendanceServerImportSerializer(DynamicFieldsModelSerializer):
    serial_number = serializers.CharField(
        max_length=250, trim_whitespace=False, write_only=True
    )
    bio_id = serializers.CharField(max_length=11, write_only=True)
    status = serializers.ReadOnlyField()

    class Meta:
        model = TimeSheetEntry
        exclude = ['timesheet']

    @staticmethod
    def validate_serial_number(serial_number):
        device = AttendanceSource.objects.filter(
            serial_number=serial_number,
            sync_method=EXTERNAL_SERVER
        ).first()
        if not device:
            raise ValidationError(
                "The serial number is not identified as any registered device."
            )
        return device, serial_number

    def validate(self, attrs):
        device, sn = attrs.get('serial_number')
        bio_id = attrs.get('bio_id')
        user_map = AttendanceUserMap.objects.filter(
            source=device,
            bio_user_id=bio_id
        ).first()
        if user_map:
            attrs.update({
                'bio_id': user_map
            })
            return super().validate(attrs)
        raise ValidationError({
            'bio_id': f'The bio id is not registered with device SN:{sn}'
        })

    def create(self, validated_data):
        user_map = validated_data.pop('bio_id', None)
        validated_data.pop('serial_number', None)
        TimeSheet.objects.clock(
            user_map.setting.user,
            validated_data.get('timestamp'),
            entry_method=validated_data.get('entry_method'),
            entry_type=validated_data.get('entry_type'),
            remarks=validated_data.get('remarks'),
            remark_category=validated_data.get('remark_category'),
            latitude=validated_data.get('latitude'),
            longitude=validated_data.get('longitude')
        )
        validated_data.update({
            'status': 'OK'
        })
        return DummyObject(**validated_data)


class AttendanceServerImportViewSet(CreateViewSetMixin):
    """
    Accepts Attendance Data from any attendance server in the given format.
    The same parser will be used to work data from pulled attendance data from
    ADMS Server

    Sample Input:
    ```
        {
            "serial_number": "ONP7010057010800013",
            "bio_id": "6",
            "timestamp": "2019-11-07T09:00:00+05:45",
            "entry_method": null,
            "entry_type": null,
            "category": "Uncategorized",
            "remark_category": "Others",
            "remarks": "",
            "latitude": null,
            "longitude": null
        }
    ```
    """
    serializer_class = AttendanceServerImportSerializer
    permission_classes = []

    def check_permissions(self, request):
        api_key = self.request.POST.get('ATTENDANCE_API_KEY')
        return api_key == settings.ATTENDANCE_API_KEY
