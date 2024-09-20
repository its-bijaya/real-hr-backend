"""@irhrs_docs"""


class PermissionWithFilterMixin:
    """
    Creates a get_queryset method that returns
    queryset filtered according to `filter` method
    in permission.

    Permission should have filter method with given
    signature.

    .. code-block::python

       filter_queryset(self, request, view, queryset)
    """
    def get_queryset(self):
        qs = super().get_queryset()
        permissions = self.get_permissions()

        for permission in permissions:
            if hasattr(permission, 'filter_queryset'):
                qs = permission.filter_queryset(self.request, self, qs)
        return qs
