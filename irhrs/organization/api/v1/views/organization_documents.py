import types

from django.contrib.auth import get_user_model
from django.db.models import Exists
from django_filters.rest_framework import DjangoFilterBackend
from django_q.tasks import async_task
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST

from irhrs.core.mixins.viewset_mixins import OrganizationMixin
from rest_framework import filters, status
from rest_framework.viewsets import ModelViewSet

from irhrs.core.utils.common import validate_permissions
from irhrs.organization.api.v1.permissions import OrganizationPermission, OrganizationWritePermission, \
    OrganizationDocumentPermission
from irhrs.organization.api.v1.serializers.organization import (
    OrganizationDocumentSerializer)
from irhrs.permission.constants.permissions import ORGANIZATION_PERMISSION, ORGANIZATION_DOCUMENTS_PERMISSION
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from ....models import OrganizationDocument
from ....utils.organization_documents import send_notification_for_acknowledge_document, \
    send_notification_when_user_acknowledges_document

USER = get_user_model()


class OrganizationDocumentView(OrganizationMixin, ModelViewSet):
    """
    list:
    Lists the Document for the selected organization.

    ### Filtering Results
    Results can be filtered with two query parameters. ```?category=&name=```
    matches document category and name of the organization document, with
    matching initials

    ```javascript
    {
            "title": "VAT PAN Document",
            "category": "legal-document",
            "description": "Essential Document",
            "attachment": "http://localhost:8000/media/organization/documents/
                attachments/test_v5Q8HEs.png",
            "slug": "vat-pan-document"
    }
    ```

    create:
    Create new Document for the given organization.
    ## Note: Organization, Title and Document must be unique together.

    ```javascript
    {
            "title": "VAT PAN Document",
            "category": "document_category.slug",
            "description": "Essential Document",
            "attachment": "http://localhost:8000/media/organization/documents/
                attachments/test_v5Q8HEs.png"
    }
    ```

    retrieve:
    Get the Document detail for the organization.
    ```javascript
    {
            "title": "VAT PAN Document",
            "category": "Legal Document",
            "description": "Essential Document",
            "attachment": "http://localhost:8000/media/organization/documents/
                attachments/test_v5Q8HEs.png",
            "slug": "vat-pan-document"
    }
    ```

    delete:
    Deletes the selected document for an organization.

    update:
    Updates the selected document details for the given organization.
    ```javascript
    {
            "title": "VAT PAN Document",
            "category": "legal-document",
            "description": "Essential Document",
            "attachment": "http://localhost:8000/media/organization/documents/
                attachments/test_v5Q8HEs.png"
    }
    ```

    partial_update:
    Update only selected fields of a document given the organization.

    Accepts the same parameters as ```.update()```.
    However, not all fields are required.

    """
    queryset = OrganizationDocument.objects.all()
    lookup_field = 'slug'
    ordering_fields = ('created_at', 'title', 'modified_at', 'category__name')
    filter_backends = (filters.OrderingFilter, filters.SearchFilter,
                       DjangoFilterBackend)
    filter_fields = ('title', 'category__slug', 'description', 'is_archived', 'is_public')
    search_fields = ('title',)
    serializer_class = OrganizationDocumentSerializer
    permission_classes = [OrganizationDocumentPermission]

    def get_queryset(self):
        queryset = super().get_queryset().filter(organization=self.organization)
        is_admin = validate_permissions(
            self.request.user.get_hrs_permissions(self.organization),
            ORGANIZATION_PERMISSION,
            ORGANIZATION_DOCUMENTS_PERMISSION
        )
        if is_admin:
            return queryset
        return queryset.filter(is_archived=False, is_public=True)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx.update({'organization': self.get_organization()})
        return ctx

    def filter_queryset(self, queryset):
        qs = super().filter_queryset(queryset)
        if self.request.query_params.get('resignation') == "true":
            return qs.filter(for_resignation=True)
        elif self.request.query_params.get('resignation') == 'false':
            return qs.exclude(for_resignation=True)
        return qs

    def has_user_permission(self):
        if self.action == 'acknowledge':
            return True
        return False

    @action(
        methods=['POST'],
        detail=True,
        url_path='notify-users'
    )
    def notify_users(self, *args, **kwargs):
        ack_document = self.get_object()
        if not ack_document.require_acknowledgement:
            return Response({
                "errors": ["Only documents that require acknowledgement can be notified."]
            }, status=HTTP_400_BAD_REQUEST)
        acknowledged_users = ack_document.acknowledgements.all()
        users_in_org = USER.objects.filter(
            detail__organization=ack_document.organization
        ).exclude(
            id__in=acknowledged_users
        )
        async_task(
            send_notification_for_acknowledge_document,
            ack_document,
            users_in_org
        )

        return Response({
            "message": "Users will be notified"
        }, status=HTTP_201_CREATED)

    @action(
        methods=['POST'],
        detail=True
    )
    def acknowledge(self, *args, **kwargs):
        ack_document = self.get_object()
        if not ack_document.require_acknowledgement:
            raise ValidationError({
                'error': 'Acknowledgement is not available for this document.'
            })
        if ack_document.acknowledgements.filter(id=self.request.user.id).exists():
            raise ValidationError(
                "%s has already acknowledged the document %s" % (
                    self.request.user.full_name, ack_document.title
                )
            )
        ack_document.acknowledgements.add(self.request.user)
        send_notification_when_user_acknowledges_document(self.request.user, ack_document)
        return Response(
            {
                'message': 'Acknowledged Successfully.'
            }, status=status.HTTP_201_CREATED
        )

    @action(
        methods=['GET'],
        detail=True,
        serializer_class=UserThinSerializer,
        url_path='acknowledgements'
    )
    def list_acknowledged_users(self, *args, **kwargs):
        ack_document = self.get_object()
        if not ack_document.require_acknowledgement:
            raise self.permission_denied(self.request)
        if not validate_permissions(
            self.request.user.get_hrs_permissions(self.get_organization()),
            ORGANIZATION_DOCUMENTS_PERMISSION
        ):
            raise self.permission_denied(self.request)

        def get_acknowledged_users(slf):
            to_select_related = [
                'detail',
                'detail__employment_level',
                'detail__job_title',
                'detail__organization',
                'detail__division',
            ]
            if slf.request.query_params.get('acknowledged') == 'false':
                return USER.objects.filter(
                    detail__organization=ack_document.organization
                ).exclude(
                    id__in=ack_document.acknowledgements.all()
                ).current().select_related(*to_select_related)
            return ack_document.acknowledgements.all().select_related(*to_select_related)

        self.get_queryset = types.MethodType(get_acknowledged_users, self)

        # override filter, search, ordering
        self.filter_fields = []
        self.ordering_fields = []
        self.search_fields = []

        return super().list(*args, **kwargs)
