from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from rest_framework import serializers

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer

from ....models import ReportFilterField, ReportDisplayField, Report, \
    ReportFilter, ReportRelatedFieldsInfo
from ....utils import get_field_type_as_valid_type, \
    get_field_type_from_path_string


class ReportRelatedFieldsInfoSerializer(DynamicFieldsModelSerializer):
    class Meta:
        fields = 'url', 'field_verbose', 'field_path',
        model = ReportRelatedFieldsInfo


class ReportDisplayFieldSerializer(DynamicFieldsModelSerializer):
    class Meta:
        fields = ('field_name', 'field_path', 'field_type', 'display',
                  'aggregate', 'ordering')
        model = ReportDisplayField
        read_only_fields = ('field_type',)


class ReportFilterFieldSerializer(DynamicFieldsModelSerializer):
    class Meta:
        fields = ('field_name', 'field_path', 'field_type', 'display',
                  'filter_type', 'filter_value', 'filter_value2', 'apply_not')
        model = ReportFilterField
        read_only_fields = ('field_type',)


class ReportSerializer(DynamicFieldsModelSerializer):
    # filter_operation = serializers.CharField(max_length=200, required=True,
    #                    allow_null=False, write_only=True)
    _filter_operation = serializers.SerializerMethodField()
    display_fields = serializers.ListField(
        child=ReportDisplayFieldSerializer(), required=True,
        allow_null=False, allow_empty=False, write_only=True)
    filter_fields = serializers.ListField(child=ReportFilterFieldSerializer(),
                                          required=True,
                                          allow_null=False, allow_empty=True,
                                          write_only=True)
    related_info = serializers.ListField(
        child=ReportRelatedFieldsInfoSerializer(),
        allow_null=True, allow_empty=True,
        write_only=True)
    generated_report = serializers.SerializerMethodField()

    class Meta:
        _REPORT_FIELDS = 'id', 'name', 'description', 'app', 'model', 'model_url',
        _RELATED_TABLE = (
            'display_fields', 'filter_fields', '_filter_operation',
            'related_info')
        _EXTRA_FIELDS = 'generated_report',
        fields = _REPORT_FIELDS + _RELATED_TABLE + _EXTRA_FIELDS
        model = Report

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == 'get':
            fields['display_fields'] = ReportDisplayFieldSerializer(
                source='reportdisplayfield', many=True, read_only=True
            )
            fields['filter_fields'] = ReportFilterFieldSerializer(
                source='report_filter_fields', many=True,
                read_only=True,
            )
            fields['related_info'] = ReportRelatedFieldsInfoSerializer(
                source='reportrelatedfieldsinfo', many=True,
                read_only=True
            )
            # fields['filter_operation'] = serializers.CharField(
            #     source='reportfilter.operation', read_only=True
            # )
        return fields

    @staticmethod
    def get_generated_report(obj):
        message = cache.get(f'report_export_{obj.id}') or {
            'message': 'Previous Task Export file couldn\'t be found.',
            'url': ''
        }
        return message

    @staticmethod
    def get__filter_operation(obj):
        if hasattr(obj, 'reportfilter'):
            return obj.reportfilter.operation
        return None

    def validate(self, attrs):
        content_type = ContentType.objects.filter(
            app_label=attrs.get('app'),
            model=attrs.get('model')
        ).first()
        if not content_type:
            raise serializers.ValidationError(
                'Invalid app and model combination')
        if not content_type.model_class():
            raise serializers.ValidationError('Model Class doesn\'t exist')
        display_fields = attrs.get('display_fields')
        filter_fields = attrs.get('filter_fields')
        for i in display_fields:
            f_type, f_class = get_field_type_from_path_string(
                content_type.model_class(),
                i['field_path'],
                i['field_name']
            )
            if not f_type:
                raise serializers.ValidationError(
                    f"Invalid Field {i['field_name']}"
                )
            i['field_type'] = get_field_type_as_valid_type(f_class)

        for j in filter_fields:
            f_type, f_class = get_field_type_from_path_string(
                content_type.model_class(),
                j['field_path'],
                j['field_name']
            )
            if not f_type:
                raise serializers.ValidationError(
                    f"Invalid Field {j['field_name']}"
                )
            if f_type == property:
                pass
            else:
                try:
                    _ = f_type.to_python(j['filter_value'])
                    if j.get('filter_value2'):
                        _ = f_type.to_python(j['filter_value2'])
                except Exception as e:
                    raise e
            j['field_type'] = get_field_type_as_valid_type(f_class)

        attrs['display_fields'] = display_fields
        attrs['filter_fields'] = filter_fields
        return attrs

    def create(self, validated_data):
        display_fields = validated_data.pop('display_fields')
        # filter_operation = validated_data.pop('filter_operation')
        filter_fields = validated_data.pop('filter_fields')
        related_info = validated_data.pop('related_info')

        report = super().create(validated_data)
        related_info_obj = [
            ReportRelatedFieldsInfo(
                report=report,
                **i
            ) for i in related_info
        ]
        ReportRelatedFieldsInfo.objects.bulk_create(related_info_obj)

        if len(filter_fields) != 0:
            filter_operation = "&".join(
                [i.get('field_path') for i in filter_fields]
            )
            filter_operation_obj = ReportFilter.objects.create(
                report=report,
                operation=filter_operation
            )
            filter_fields_obj = [
                ReportFilterField(
                    report_filter=filter_operation_obj,
                    **i
                ) for i in filter_fields
            ]
            ReportFilterField.objects.bulk_create(filter_fields_obj)

        display_fields_obj = [ReportDisplayField(
            report=report,
            **i
        ) for i in display_fields]

        ReportDisplayField.objects.bulk_create(display_fields_obj)

        self.fields['display_fields'] = ReportDisplayFieldSerializer(
            source='reportdisplayfield', many=True
        )
        self.fields['filter_fields'] = ReportFilterFieldSerializer(
            source='report_filter_fields', many=True
        )

        return report

    def update(self, instance, validated_data):
        display_fields = validated_data.pop('display_fields')
        # filter_operation = validated_data.pop('filter_operation')
        filter_fields = validated_data.pop('filter_fields')
        related_info = validated_data.pop('related_info')

        report = super().update(instance, validated_data)

        report.reportrelatedfieldsinfo.all().delete()
        report.reportdisplayfield.all().delete()
        if hasattr(report,'reportfilter'):
            report.reportfilter.delete()

        related_info_obj = [
            ReportRelatedFieldsInfo(
                report=report,
                **i
            ) for i in related_info
        ]
        ReportRelatedFieldsInfo.objects.bulk_create(related_info_obj)
        if len(filter_fields) != 0:
            filter_operation = "&".join(
                [i.get('field_path') for i in filter_fields]
            )

            filter_operation_obj = ReportFilter.objects.create(
                report=report,
                operation=filter_operation
            )
            filter_fields_obj = [
                ReportFilterField(
                    report_filter=filter_operation_obj,
                    **i
                ) for i in filter_fields
            ]
            ReportFilterField.objects.bulk_create(filter_fields_obj)

        display_fields_obj = [ReportDisplayField(
            report=report,
            **i
        ) for i in display_fields]

        ReportDisplayField.objects.bulk_create(display_fields_obj)

        self.fields['display_fields'] = ReportDisplayFieldSerializer(
            source='reportdisplayfield', many=True
        )
        self.fields['filter_fields'] = ReportFilterFieldSerializer(
            source='report_filter_fields', many=True
        )

        return instance
