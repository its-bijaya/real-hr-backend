import copy
import inspect
from collections import namedtuple

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.utils.functional import cached_property

from irhrs.builder.valid_apps import VALID_APPS
from .valid_fields import VALID_MODEL_FIELDS


def get_valid_fields_for_model(model_class):
    try:
        return (
            VALID_MODEL_FIELDS[model_class]['valid_direct_fields'],
            VALID_MODEL_FIELDS[model_class]['valid_related_fields'],
        )
    except (KeyError, AttributeError):
        raise AttributeError


def get_models(label):
    # this will be the right place to validate and return allowed models
    content_types = ContentType.objects.filter(
        app_label=label
    )
    models = []
    for c_type in content_types:
        if c_type.model_class() and c_type.model_class() in \
                VALID_MODEL_FIELDS.keys():
            models.append(c_type)
    return models


def get_all_apps():
    ValidApp = namedtuple(
        'ValidApp', ['name', 'verbose_name', 'label', 'icon']
    )

    return [ValidApp(**i) for i in VALID_APPS]


def is_property(v):
    return isinstance(v, property)


def get_all_valid_fields(model_class):
    return [field.name
            for field in model_class._meta.get_fields()
            if not (field.many_to_one and field.related_model is None)
            ]


def get_properties_from_model(model_class):
    properties = []
    attr_names = [name for (name, value) in
                  inspect.getmembers(model_class, is_property)]
    for attr_name in attr_names:
        if attr_name.endswith('pk'):
            attr_names.remove(attr_name)
        else:
            properties.append(dict(label=attr_name,
                                   name=attr_name.strip('_').replace('_',
                                                                     ' ')))
    return sorted(properties, key=lambda k: k['label'])


def get_relation_fields_from_model(model_class):
    relation_fields = []
    all_fields_names = get_all_valid_fields(model_class)
    for field_name in all_fields_names:
        field = copy.deepcopy(model_class._meta.get_field(field_name))
        direct = field.concrete
        m2m = field.many_to_many
        if field_name[-3:] == '_id' and field_name[:-3] in all_fields_names:
            continue
        if m2m or not direct or field.is_relation:
            relation_fields += [field]
    return relation_fields


def get_direct_fields_from_model(model_class):
    direct_fields = []
    all_fields_names = get_all_valid_fields(model_class)
    for field_name in all_fields_names:
        field = model_class._meta.get_field(field_name)
        direct = field.concrete
        m2m = field.many_to_many
        if direct and not m2m and not field.is_relation:
            direct_fields += [field]
    return direct_fields


def get_model_from_path_string(root_model, path):
    for path_section in path.split('__')[:-1]:  # since path=path+field
        if path_section:
            try:
                field = root_model._meta.get_field(path_section)
                direct = field.concrete
            except FieldDoesNotExist:
                return root_model
            if direct:
                if hasattr(field, 'related'):
                    try:
                        root_model = field.related.parent_model()
                    except AttributeError:
                        root_model = field.related.model

                elif hasattr(field, 'related_model') and field.related_model:
                    root_model = field.related_model

            else:
                if hasattr(field, 'related_model'):
                    root_model = field.related_model
                else:
                    root_model = field.model
    return root_model


def get_field_type_from_path_string(root_model, path, field_name):
    model = get_model_from_path_string(
        root_model, path)
    try:
        return model._meta.get_field(field_name), model._meta.get_field(
            field_name).get_internal_type()
    except FieldDoesNotExist:
        pass
    field_attr = getattr(model, field_name, None)
    if isinstance(field_attr, (property, cached_property)):
        return property, "Property"

    return None, "Invalid"


def get_field_type_as_valid_type(field_type):
    # We are using different custom fields in our model
    # so convert to something generic
    if field_type == 'CurrentUserField':
        return 'ForeignKey'
    return field_type
