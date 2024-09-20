from collections import OrderedDict

from rest_framework.pagination import LimitOffsetPagination, _positive_int
from rest_framework.response import Response


class LimitZeroNoResultsPagination(LimitOffsetPagination):

    def get_limit(self, request):
        if self.limit_query_param:
            try:
                return _positive_int(
                    request.query_params[self.limit_query_param],
                    strict=False,
                    cutoff=self.max_limit
                )
            except (KeyError, ValueError):
                pass

        return self.default_limit


class NoCountLimitZeroNoResultsPagination(LimitZeroNoResultsPagination):

    def get_count(self, queryset):
        """
        rest_framework/pagination.py:332
        The value is set to 1:- because if its <=0, result is [].
        Setting 1 does not affect in any other way,

        if self.count > self.limit and self.template is not None: ...
            self.display_page_controls = True
        if self.count == 0 or self.offset > self.count:
            return []
        """
        return 1

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', None),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))
