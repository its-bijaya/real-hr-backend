from rest_framework.filters import SearchFilter
from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.change_request import ChangeRequestMixin
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.users.api.v1.serializers.user_document import UserDocumentSerializer
from irhrs.users.models.other import UserDocument


class UserDocumentViewSet(ChangeRequestMixin, ModelViewSet):
    """
    Store user documents
    create:

    post data =

        {
            'title': Document Title
            'document_type': Document Category Slug,
            'file': Document File
       }

    list:

    filters -

        search= <search by title>
        document_type = <document_category_slug>

    ordering -

        'created_by', title', document_type', created_at', updated_at',


    """
    serializer_class = UserDocumentSerializer
    queryset = UserDocument.objects.all().select_related(
        'document_type',
        'uploaded_by',
        'uploaded_by__detail',
        'uploaded_by__detail__organization',
        'uploaded_by__detail__job_title'
    )
    lookup_field = 'slug'
    filter_backends = (FilterMapBackend, SearchFilter, OrderingFilterMap)

    filter_map = {
        'document_type': 'document_type__slug'
    }
    search_fields = ('title',)
    ordering = '-created_at'
    ordering_fields_map = {
        'uploaded_by': ('uploaded_by__first_name', 'uploaded_by__middle_name', 'uploaded_by__last_name',),
        'title': 'title',
        'document_type': 'document_type__name',
        'created_at': 'created_at',
        'updated_at': 'updated_at',
    }

    def get_serializer(self, *args, **kwargs):
        kwargs.update({'exclude_fields': ['user']})
        return super().get_serializer(*args, **kwargs)
