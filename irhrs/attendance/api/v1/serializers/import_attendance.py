from django.core.validators import FileExtensionValidator
from rest_framework.fields import FileField, CharField, JSONField
from rest_framework.serializers import Serializer

from irhrs.attendance.api.v1.serializers.call_export import import_attendance, save_file
from irhrs.core.utils.common import DummyObject


class AttendanceImportSerializer(Serializer):
    file = FileField(write_only=True, validators=[
        FileExtensionValidator(
            allowed_extensions=['xlsx'],
            message='Not a valid file format. Options are [.xlsx]',
            code='Invalid Format'
        )])
    message = CharField(read_only=True)
    imported = CharField(read_only=True)
    errors = JSONField(read_only=True)

    imported_records = 0
    total_records = 0
    successful_clocks = 0

    valid_input_fields = {
        'user',
        'timesheet_for',
        'punch_in',
        'punch_out'
    }

    def create(self, validated_data):

        # save uploaded file to memory and process it
        path = save_file(validated_data.get('file'))  # Save to disk.

        import_attendance(
            path,
            self.context.get(
                'request'
            ).user,
            self.context.get(
                'organization'
            )
        )
        return DummyObject(**{
            'message': 'The records are being processed. Please wait.',
        })

    def update(self, instance, validated_data):
        return instance
