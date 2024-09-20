"""@irhrs_docs"""
from django.utils.functional import cached_property
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer, Serializer

from irhrs.core.constants.payroll import SUPERVISOR, EMPLOYEE
from irhrs.core.fields import JSONTextField
from irhrs.core.mixins.serializer_fields import JSONTextField as \
    JSONSerializerField
from irhrs.core.utils.common import DummyObject, get_random_class_name
from irhrs.core.validators import validate_phone_number


class DynamicFieldsSerializerMixin:
    def __init__(self, instance=None, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)
        exclude_fields = kwargs.pop('exclude_fields', None)

        # Instantiate the superclass normally
        super().__init__(
            instance, *args, **kwargs
        )

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)
        # exclude fields
        if exclude_fields is not None:
            # Drop any fields that are  specified in the `exclude_fields` argument.
            exclude_fields = set(exclude_fields)
            for field_name in exclude_fields:
                self.fields.pop(field_name)


class DummySerializer(DynamicFieldsSerializerMixin, Serializer):
    """
    Read only serializer for non model serializers
    Overrides create and update but does nothing in that
    """

    def create(self, validated_data):
        return DummyObject(**validated_data)

    def update(self, instance, validated_data):
        return instance


def create_dummy_serializer(fields, name=None):
    """return dummy serializer class having given fields"""
    name = name or get_random_class_name()
    return type(
        name,
        (DummySerializer,),
        fields
    )


def create_read_only_dummy_serializer(fields, name=None):
    """
    create dummy serializer class having given fields read only

    :param fields: list of read only fields
    :param name: name of serializer class
    """
    fields_ = dict()

    for field in fields:
        if isinstance(field, str):
            fields_.update({field: serializers.ReadOnlyField(allow_null=True)})
        else:
            field_name, source = field
            fields_.update({field_name: serializers.ReadOnlyField(source=source, allow_null=True)})

    return create_dummy_serializer(fields=fields_, name=name)


def add_fields_to_serializer_class(serializer_class, fields):
    """Add given fields to provided serializer class"""
    parent_meta = getattr(serializer_class, "Meta", None)
    attrs = dict()

    if parent_meta:
        meta_class = type("Meta", (parent_meta,),
                          {"fields": list(parent_meta.fields) + list(fields.keys())})
        attrs.update({"Meta": meta_class})

    attrs.update(fields)

    return type(
        get_random_class_name(),
        (serializer_class,),
        attrs
    )


class CustomModelSerializer(ModelSerializer):
    """
    Custom Model Serializer that contains field mapping of custom fields
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.serializer_field_mapping.update({
            JSONTextField: JSONSerializerField})


class DynamicFieldsModelSerializer(CustomModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` and 'exclude_fields'
    argument that controls which fields should be displayed and not to be
    displayed.
    """

    def __init__(self, instance=None, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)
        exclude_fields = kwargs.pop('exclude_fields', None)

        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(
            instance, *args, **kwargs
        )

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)
        # exclude fields
        if exclude_fields is not None:
            # Drop any fields that are  specified in the `exclude_fields` argument.
            exclude_fields = set(exclude_fields)
            for field_name in exclude_fields:
                self.fields.pop(field_name)

    def get_extra_kwargs(self):
        extra_kwargs = super().get_extra_kwargs()
        create_only_fields = getattr(self.Meta, 'create_only_fields', None)

        if self.instance and create_only_fields:
            for field_name in create_only_fields:
                kwargs = extra_kwargs.get(field_name, {})
                kwargs['read_only'] = True
                extra_kwargs[field_name] = kwargs

        return extra_kwargs

    @cached_property
    def request(self):
        return self.context.get("request")


class ContactsSerializer(DummySerializer):
    """
    Serializer for handling contacts info.
    # TODO @Ravi: require at least one.
    """
    Phone = serializers.CharField(
        required=False,
        validators=[validate_phone_number]
    )
    Fax = serializers.CharField(
        required=False,
        validators=[validate_phone_number]
    )
    Mobile = serializers.CharField(
        required=False,
        validators=[validate_phone_number]
    )
    Work = serializers.CharField(
        required=False,
        validators=[validate_phone_number]
    )


def require_remarks_serializer(max_length=255):
    return type(
        'WriteOnlySerializer',
        (serializers.Serializer,),
        {
            'remarks': serializers.CharField(max_length=max_length)
        }
    )


class ApprovalSettingValidationMixin:
    def validate(self, attrs):
        approve_by = attrs.get('approve_by')
        supervisor_level = attrs.pop('supervisor_level', None)
        employee = attrs.pop('employee', None)
        if not approve_by:
            raise ValidationError({
                'approved_by': ['This field is required.']
            })

        if approve_by == SUPERVISOR and not supervisor_level:
            raise ValidationError({
                'supervisor_level': 'This field is required if approve_by is set to supervisor.'
            })

        if approve_by == EMPLOYEE and not employee:
            raise ValidationError({
                'employee': 'This field is required if approve_by is set to employee.'
            })

        if approve_by == EMPLOYEE:
            attrs['employee'] = employee
        if approve_by == SUPERVISOR:
            attrs['supervisor_level'] = supervisor_level

        return super().validate(attrs)
