from django.contrib.contenttypes.models import ContentType

from irhrs.builder.utils import get_relation_fields_from_model, \
    get_direct_fields_from_model, get_properties_from_model


class ModelFieldsPropertyRelation:
    @staticmethod
    def get_direct_fields(model_class):
        fields = get_direct_fields_from_model(model_class)
        app_label = model_class._meta.app_label
        model = model_class

        return {
            'fields': fields,
            'app_label': app_label,
            'model': model,
        }

    @staticmethod
    def get_properties(model_class):
        properties = get_properties_from_model(model_class)
        app_label = model_class._meta.app_label
        model = model_class

        return {
            'fields': properties,
            'app_label': app_label,
            'model': model,
        }

    @staticmethod
    def get_related_fields(model_class):
        new_fields = get_relation_fields_from_model(model_class)
        return {
            'fields': new_fields,
            'model': model_class
        }
