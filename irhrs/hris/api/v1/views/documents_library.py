from rest_framework.filters import SearchFilter

from irhrs.core.mixins.viewset_mixins import ListRetrieveDestroyViewSetMixin, OrganizationMixin
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.hris.api.v1.permissions import HRISPermission
from irhrs.users.api.v1.serializers.user_document import UserDocumentSerializer
from irhrs.users.models.other import UserDocument


class UserDocumentsLibraryViewSet(OrganizationMixin, ListRetrieveDestroyViewSetMixin):
    """
    filters -

        search= <search by name>
        job_title= <job_title slug>
        employee_level = <employment_level_slug>
        division = <division_slug>
        document_type = <document_category_slug>

    ordering -

        'full_name', created_by', title', document_type', created_at', updated_at',

    """
    serializer_class = UserDocumentSerializer
    queryset = UserDocument.objects.all()
    permission_classes = [HRISPermission]
    filter_backends = (FilterMapBackend, SearchFilter, OrderingFilterMap)
    filter_map = {
        'job_title': 'user__detail__job_title__slug',
        'employee_level': 'user__detail__employment_level__slug',
        'division': 'user__detail__division__slug',
        'document_type': 'document_type__slug'
    }
    search_fields = (
        'user__first_name',
        'user__middle_name',
        'user__last_name',
        'title'
    )
    ordering = '-created_at'
    ordering_fields_map = {
        'full_name': ('user__first_name', 'user__middle_name', 'user__last_name'),
        'uploaded_by': ('uploaded_by__first_name', 'uploaded_by__middle_name', 'uploaded_by__last_name',),
        'title': 'title',
        'document_type': 'document_type__name',
        'created_at': 'created_at',
        'updated_at': 'updated_at',
    }
    lookup_field = 'slug'

    def get_queryset(self):
        select_related = [
            'document_type',
            'user',
            'user__detail',
            'user__detail__organization',
            'user__detail__job_title',
            'uploaded_by__detail',
            'uploaded_by__detail__organization',
            'uploaded_by__detail__job_title'
        ]
        return super().get_queryset().filter(
            user__detail__organization=self.get_organization()
        ).select_related(*select_related)
