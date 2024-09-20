import random

from django.contrib.contenttypes.models import ContentType
from rest_framework import viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.serializers import Serializer

from irhrs.builder.constants import FIELDS_FILTER_CHOICES, \
    FIELDS_ORDERING_CHOICES, FIELDS_AGGREGATE_CHOICES
from irhrs.builder.helpers import ModelFieldsPropertyRelation
from irhrs.builder.permissions import ReportBuilderPermission
from irhrs.builder.utils import get_models, get_all_apps, \
    get_field_type_as_valid_type, get_valid_fields_for_model
from irhrs.core.mixins.serializers import DummySerializer
from irhrs.core.utils.filters import inverse_mapping


class BuilderViewSet(viewsets.ViewSet):
    serializer_class = DummySerializer
    permission_classes = [ReportBuilderPermission]

    def list(self, request, *args, **kwargs):
        serializer_class = type(
            'InstalledAppsSerializer', (Serializer,),
            {
                'name': serializers.ReadOnlyField(source='verbose_name'),
                'description': serializers.SerializerMethodField(),
                'icon': serializers.ReadOnlyField(),
                'models_url': serializers.SerializerMethodField(),
                '_models_url': serializers.SerializerMethodField(),
                '_app_label': serializers.ReadOnlyField(source='label'),
                '_name': serializers.ReadOnlyField(source='name'),
                'get_models_url': (
                    lambda inner_self, x: reverse(
                        'api_v1:dj-report-builder-models',
                        kwargs={'app_label': x.label}
                    )
                ),
                'get__models_url': (
                    lambda inner_self, x: reverse(
                        'api_v1:dj-report-builder-models',
                        kwargs={'app_label': x.label},
                        request=inner_self.context.get('request')
                    )
                ),
                'get_description': lambda _,x: ", ".join(
                    [i.__str__().title() for i in get_models(x.label)[:3]]
                ).__add__(
                    ' and {} others'.format(
                        len(get_models(x.label)) - 3
                    ) if len(
                        get_models(x.label)
                    ) > 3 else ''
                )
            }
        )
        query = get_all_apps()
        return Response(
            serializer_class(
                query,
                many=True,
                context={'request': self.request}
            ).data
        )

    @action(detail=False, url_path=r'(?P<app_label>[\w]+)')
    def models(self, request, app_label, *args, **kwargs):
        serializer_class = type(
            'AllowedModelsSerializer', (Serializer,),
            {
                'model': serializers.ReadOnlyField(),
                'field': serializers.ReadOnlyField(source='model'),
                'field_path': serializers.ReadOnlyField(source='model'),
                'field_verbose': serializers.SerializerMethodField(
                    'get_v_name'),
                'app_label': serializers.ReadOnlyField(),
                'fields_url': serializers.SerializerMethodField(),
                '_fields_url': serializers.SerializerMethodField(),
                '_name': serializers.ReadOnlyField(source='name'),
                '_is_valid_model': serializers.SerializerMethodField(),
                'get_fields_url': lambda inner_self, x: reverse(
                    'api_v1:dj-report-builder-fields',
                    kwargs={
                        'app_label': inner_self.context.get('app_label'),
                        'model': x.model,
                    },
                ),
                'get__fields_url': lambda inner_self, x: reverse(
                    'api_v1:dj-report-builder-fields',
                    kwargs={
                        'app_label': inner_self.context.get('app_label'),
                        'model': x.model,
                    },
                    request=inner_self.context.get('request')
                ),
                'get__is_valid_model': staticmethod(
                    lambda x: bool(x.model_class())
                ),
                'get_v_name': staticmethod(
                    lambda x: x.name.title()
                )

            }
        )
        query = get_models(app_label)
        if not query:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(
            serializer_class(
                query, many=True,
                context={
                    'request': self.request,
                    'app_label': app_label
                }).data)

    @action(detail=False,
            url_path=r'(?P<app_label>[\w]+)/'
                     r'(?P<model>[\w]+)',
            url_name='fields')
    def field_details(self, request, app_label, model, *args,
                      **kwargs):
        try:
            content_type_obj = ContentType.objects.get(app_label=app_label,
                                                       model=model)
        except ContentType.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        fields_obj = ModelFieldsPropertyRelation()

        model_class = content_type_obj.model_class()
        root_path = self.request.query_params.get('path', '')
        exclude_model = self.request.query_params.get('exclude', '')
        if root_path:
            if root_path.count("__") > 3:
                return Response({'detail': 'Accessing child upto '
                                           'level 3 is only permitted'
                                 }, status=status.HTTP_400_BAD_REQUEST)

            root_path__ = root_path + '__'
        else:
            root_path__ = ''
        if not model_class:
            # Delete the content type that reflects the deleted model
            # [NOTE]: Leave this for now
            # Can deleting the content type can harm our system where
            # we are using GenericForeignKey ????
            # content_type_obj.delete()
            return Response({'error': 'Couldn\'t get Model class '
                                      'Did you Delete this model '
                                      'but the changes are not reflected on '
                                      'ContentType Framework'
                             }, status=status.HTTP_502_BAD_GATEWAY)

        try:
            valid_direct_fields_for_model, \
                valid_related_fields_for_model = get_valid_fields_for_model(
                    model_class)
        except AttributeError:
            return Response(
                {'detail': 'Invalid model'},
                status=status.HTTP_400_BAD_REQUEST
            )

        def get_fields_for_http_response():
            result = []
            direct_fields = fields_obj.get_direct_fields(model_class)

            # This method has been used for easiness in FE
            def _choices_conversion(choices):
                _choices = []
                for k, v in choices.items():
                    _choices.append({'name': k, 'value': v})
                return _choices

            for new_field in direct_fields['fields']:
                if new_field.name not in valid_direct_fields_for_model:
                    continue
                verbose_name = getattr(new_field, 'verbose_name', None)
                if not verbose_name:
                    verbose_name = " ".join(
                        new_field.name.split('_')
                    )
                result += [{
                    'field': new_field.name,
                    'field_path': root_path__ + new_field.name,
                    'field_verbose': verbose_name.title(),
                    'concrete': True,
                    'field_type': new_field.get_internal_type(),
                    'field_choices': _choices_conversion(
                        inverse_mapping(dict(new_field.choices))),
                    'help_text': new_field.help_text,
                    '_field_choices': new_field.choices,
                }]
            return result

        # def get_property_for_http_response():
        #     result = []
        #     property_fields = fields_obj.get_properties(model_class)
        #     for field in property_fields['fields']:
        #         result += [{
        #             'name': field['name'],
        #             'field': field['label'],
        #             'field_verbose': field['name'],
        #             'concrete': True,
        #             'field_type': 'Property',
        #             'field_choices': [],
        #             'help_text': ''
        #         }]
        #     return result

        def get_related_fields_for_http_response():
            related_fields = fields_obj.get_related_fields(model_class)
            result = []
            for new_field in related_fields['fields']:
                if new_field.name not in valid_related_fields_for_model:
                    continue
                verbose_name = getattr(new_field, 'verbose_name', None)
                if not verbose_name:
                    verbose_name = new_field.related_model._meta.verbose_name_plural
                c_type = ContentType.objects.get_for_model(
                    new_field.related_model
                )
                if exclude_model and exclude_model == c_type.model:
                    continue
                result += [{
                    'field': new_field.name,
                    'field_path': root_path__ + new_field.name,
                    'field_verbose': verbose_name.title(),
                    'field_type': 'Related',
                    'concrete': new_field.concrete,
                    'field_choices': [],
                    'help_text': getattr(new_field, 'help_text', ''),
                    'fields_url': "%s?path=%s&exclude=%s" % (reverse(
                        'api_v1:dj-report-builder-fields',
                        kwargs={
                            'app_label': c_type.app_label,
                            'model': c_type.model,
                        },
                    ), root_path__ + new_field.name, model
                    ),
                    '_fields_url': "%s?path=%s&exclude=%s" % (reverse(
                        'api_v1:dj-report-builder-fields',
                        kwargs={
                            'app_label': c_type.app_label,
                            'model': c_type.model,
                        },
                        request=self.request
                    ), root_path__ + new_field.name, model
                    ),
                    '__class': get_field_type_as_valid_type(
                        new_field.__class__.__name__
                    ),
                    '__model_name': c_type.model,
                    '__app_label': c_type.app_label,
                    '__root_field': root_path
                }]
            return result

        response = {
            'direct_fields': get_fields_for_http_response(),
            # 'property': get_property_for_http_response(),
            'related_fields': get_related_fields_for_http_response()
        }
        return Response(response)

    @action(detail=False)
    def constants(self, request):
        _f_choices = []  # filter choices
        _o_choices = []  # ordering choices
        _a_choices = []  # aggregate choices
        _filter_choices_description = {
            'exact': 'Equals',
            'iexact': 'Case-insensitive exact match',
            'contains': 'Case-sensitive containment test',
            'icontains': 'Case-insensitive containment test',
            'in': 'List of data to compare with (Comma separated)',
            'gt': 'Greater than',
            'gte': 'Greater than or equal to',
            'lt': 'Less than',
            'lte': 'Less than or equal to',
            'startswith': 'Case-sensitive starts-with',
            'istartswith': 'Case-insensitive starts-with',
            'endswith': 'Case-sensitive ends-with',
            'iendswith': 'Case-insensitive ends-with',
            'range': 'Range test (inclusive)',
            'isnull': 'Is Empty or Not'
        }

        _ordering_choices_description = {
            'Asc': 'Sorts in Ascending Order',
            'Desc': 'Sorts in Descending Order'
        }
        _aggregate_choices_description = {
            'Sum': 'Sum of all the values in the specified column',
            'Count': 'Total number of values in the specified field',
            'Avg': 'The average of the values in a specified column',
            'Max': 'The largest value from the specified table field',
            'Min': 'The smallest value in the specified table field'
        }

        for k, v in dict(FIELDS_FILTER_CHOICES).items():
            _f_choices.append({
                'value': k,
                'verbose': v,
                'description': _filter_choices_description.get(k),
                'params': 2 if k == 'range' else 1
            })
        for k, v in dict(FIELDS_ORDERING_CHOICES).items():
            _o_choices.append({
                'value': k,
                'verbose': v,
                'description': _ordering_choices_description.get(k)
            })
        for k, v in dict(FIELDS_AGGREGATE_CHOICES).items():
            _a_choices.append({
                'value': k,
                'verbose': v,
                'description': _aggregate_choices_description.get(k)
            })
        _constants = {
            'filter_choices': _f_choices,
            'ordering_choices': _o_choices,
            'aggregate_choices': _a_choices
        }
        return Response(_constants)
