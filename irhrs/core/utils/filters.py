"""@irhrs_docs"""
import datetime
from collections import OrderedDict

import pytz
from django.db.models import F
from django.forms.utils import pretty_name
from django.template import loader
from django_filters import utils as dj_filters_utils
from django_filters.rest_framework import FilterSet
from rest_framework.filters import BaseFilterBackend, OrderingFilter, \
    SearchFilter


def inverse_mapping(mapping):
    """
    Inverse key -> value to value -> key
    # NOTE: make sure values are unique
    """
    return mapping.__class__(map(reversed, mapping.items()))


def get_applicable_filters(qp, filter_map):
    """
    get applicable filters from filter map,
    *WARNING* -->  Do not use this directly, use `apply_filters` instead

    :param qp: query params
    :type qp: dict
    :param filter_map: filter map
    :type filter_map: dict
    :return: dictionary ready to be passed in filter method
    """
    query_params = {k: v for k, v in qp.items()}
    start = query_params.pop('start_date', '')
    end = query_params.pop('end_date', '')

    # Quick fix , @Anurag remove this
    # used for : /api/v1/task/overview/?approved=false
    approved = query_params.pop('approved', ' ')
    if approved and approved in ['true', 'True', '1']:
        query_params.update({
            'approved': True
        })
    elif approved and approved in ['false', 'False', '0']:
        query_params.update({
            'approved': False
        })

    if start:
        if isinstance(start, datetime.date):
            query_params.update({
                'start_date': start
            })
        else:
            try:
                start_date = datetime.datetime.strptime(
                    start, '%Y-%m-%d'
                ).replace(tzinfo=pytz.utc)
                query_params.update({
                    'start_date': start_date
                })
            except ValueError:
                pass

    if end:
        if isinstance(end, datetime.date):
            query_params.update({
                'end_date': end
            })
        else:
            try:
                end_date = datetime.datetime.strptime(
                    end, '%Y-%m-%d'
                ).replace(tzinfo=pytz.utc)
                query_params.update({
                    'end_date': end_date
                })
            except ValueError:
                pass
    return {
        filter_map.get(k): v for k, v in query_params.items() if
        k in filter_map.keys() and v is not None and v != ''
    }


class FilterMapFilterSet(FilterSet):
    """
    FilterSet used in FilterMapBackend

    Nothing much here, just uses get_applicable_filters filter queryset instead of default one
    """

    class Meta:
        fil_map = {}

    def filter_queryset(self, queryset):
        """
        Override filter queryset to use our own get_applicable_filters
        """
        cleaned_data = self.form.cleaned_data
        return queryset.filter(**get_applicable_filters(cleaned_data, self.Meta.fil_map))


class FilterMapBackend(BaseFilterBackend):
    """
    Filter map backend

    Filter Map
    ----------

    Provide filter map in view

    .. code-block:: python

        filter_map = {'name' : 'filter_expression', ...}
        OR
        define get_filter_map

    Raise Exception
    ---------------

    Raise exception when validation of query_params fails
    default is True

    .. code-block:: python

        raise_filter_exception=True
        or
        define get_raise_filter_exception

    """
    template = 'django_filters/rest_framework/form.html'

    def get_raise_exception(self, view):
        if hasattr(view, "get_raise_filter_exception"):
            return view.get_raise_filter_exceptions()
        return getattr(view, "raise_filter_exception", True)

    def get_filterset(self, request, queryset, view):
        filterset_class = self.get_filterset_class(view, self.get_filter_map(view))
        if filterset_class is None:
            return None
        kwargs = self.get_filterset_kwargs(request, queryset, view)
        return filterset_class(**kwargs)

    def get_filterset_kwargs(self, request, queryset, view):
        return {
            'data': request.query_params,
            'queryset': queryset,
            'request': request,
        }

    def filter_queryset(self, request, queryset, view):
        filterset = self.get_filterset(request, queryset, view)
        if filterset is None:
            return queryset

        if not filterset.is_valid() and self.get_raise_exception(view):
            raise dj_filters_utils.translate_validation(filterset.errors)
        return filterset.qs

    @staticmethod
    def get_filter_map(view):
        filter_map_func = getattr(view, 'get_filter_map', None)
        filter_map_var = getattr(view, 'filter_map', None)

        if not (filter_map_func or filter_map_var):
            return None

        if filter_map_func:
            return filter_map_func()

        if filter_map_var:
            return filter_map_var

    def to_html(self, request, queryset, view):
        filter_map = self.get_filter_map(view)
        if filter_map:
            template = loader.get_template(self.template)
            return template.render({
                'filter': self.get_filterset_class(view, filter_map)(**self.get_filterset_kwargs(
                    request, queryset, view))
            })
        else:
            return ''

    @staticmethod
    def get_filterset_class(view, filter_map):
        # build own filterset class for the filter
        model_class = view.get_queryset().model
        filter_map = filter_map or dict()

        # plain filter map, no tuples
        plain_filter_map = {key: "__".join(val) if isinstance(val, tuple) else val for key, val in
                            filter_map.items()}

        class Filterset(FilterMapFilterSet):
            class Meta:
                model = model_class
                # clean filed map for proper fields with expressions
                fields = FilterMapBackend.clean_field_names(
                    filter_map.values())
                fil_map = plain_filter_map

            def get_form_class(self):
                val_to_name = inverse_mapping(plain_filter_map)
                fields = OrderedDict()

                for name, filter_ in self.filters.items():
                    f = filter_.field
                    f.label = pretty_name(val_to_name[name])

                    fields.update({val_to_name[name]: f})

                return type(str('%sForm' % self.__class__.__name__),
                            (self._meta.form,), fields)

        return Filterset

    @staticmethod
    def clean_field_names(field_names):
        """Clean field names from query string to (field_name, expression) form"""
        real_fields = set()
        map_ = dict()
        filters = dict()
        for field_name in field_names:
            real_name, op = FilterMapBackend.clean_field_name(field_name)
            map_.update({field_name: op})
            real_fields.add(real_name)

        for real_name in real_fields:
            ops = set()
            for field_name, op in map_.items():
                if real_name in field_name:
                    ops.update(op)

            filters.update({real_name: ops})
        return filters

    @staticmethod
    def clean_field_name(field_name):
        if isinstance(field_name, tuple):
            return field_name[0], [field_name[1]]
        # just these for now, add more when needed
        ops = ["date__gte", "date__lte", "gte", "lte", "gt", "lt"]
        for op in ops:
            if f"__{op}" in field_name:
                return field_name.replace(f"__{op}", ""), [op]
        return field_name, ['exact']


class OrderingFilterMap(OrderingFilter):

    def get_ordering(self, request, queryset, view):
        params = request.query_params.get(self.ordering_param)
        if params:
            ascending = self.get_fields_map(view)
            if not ascending:
                return self.get_default_ordering(view)

            descending = dict()
            for order, value in ascending.items():
                if isinstance(value, str):
                    descending.update({f"-{order}": f"-{value}"})
                elif isinstance(value, (list, tuple)):
                    descending.update({
                        f"-{order}": [f"-{v}" for v in value]
                    })

            ordering_map = {
                **ascending,
                **descending
            }
            query_order = view.request.query_params.get('ordering', '')
            order_by = [
                v for k, v in ordering_map.items() if
                k in query_order.split(',')
            ]

            ord_by = []
            for order in order_by:
                if isinstance(order, str):
                    ord_by.append(order)
                elif isinstance(order, (list, tuple)):
                    order_by.extend(order)

            if ord_by:
                return ord_by
        else:
            return self.get_default_ordering(view)

    def get_valid_fields(self, queryset, view, context=None):
        valid_fields_ = self.get_fields_map(view) or {}
        valid_fields = valid_fields_.keys() or self.ordering_fields
        fields_labels = [
            (name, name.replace("_", " ").title())
            for name in valid_fields
        ] if valid_fields else []

        if valid_fields is None:
            # Default to allowing filtering on serializer fields
            return []
        return fields_labels

    @staticmethod
    def get_fields_map(view):
        ordering_map_func = getattr(view, 'get_ordering_fields_map', None)
        ordering_map_var = getattr(view, 'ordering_fields_map', None)

        if not (ordering_map_func or ordering_map_var):
            return None

        if ordering_map_func:
            return ordering_map_func()

        if ordering_map_var:
            return ordering_map_var


class DynamicSearchFilter(SearchFilter):
    """Dynamic search filters, which gets mapping from variable as well as method"""

    def get_search_fields(self, view, request):
        """
        Search fields are obtained from the view, but the request is always
        passed to this method. Sub-classes can override this method to
        dynamically change the search fields based on request content.
        """

        search_func = getattr(view, 'get_search_fields', None)
        search_var = getattr(view, 'search_fields', None)

        if not (search_func or search_var):
            return None

        if search_func:
            return search_func()

        if search_func:
            return search_var


# see : https://stackoverflow.com/questions/42899552
class NullsAlwaysLastOrderingFilter(OrderingFilterMap):
    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)

        if ordering:
            f_ordering = []
            for o in ordering:
                if not o:
                    continue
                if o[0] == '-':
                    f_ordering.append(F(o[1:]).desc(nulls_last=True))
                else:
                    f_ordering.append(F(o).asc(nulls_last=True))

            return queryset.order_by(*f_ordering)

        return queryset


