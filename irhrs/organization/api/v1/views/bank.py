from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.viewset_mixins import OrganizationMixin, \
    OrganizationCommonsMixin
from ..permissions import (OrganizationPermission, OrganizationSettingsPermission,
                           OrganizationBankPermission)
from ..serializers.bank import OrganizationBankSerializer
from ....models import OrganizationBank


class OrganizationBankViewSet(OrganizationCommonsMixin,
                              OrganizationMixin, ModelViewSet):
    """
    list:
    Lists organization banks for the selected organization.

    create:
    Create new Bank for the given organization.

    ### Format

    ```javascript
        "person_list" : [{
                    "Name": "Walter White",
                    "Designation": "Executive",
                    "Contacts": {
                        "Phone": "015554920",
                        "Mobile": "9842875805",
                        "Work": "015554920",
                        "Fax": "015554920",
                    }
                }]
    ```

    retrieve:
    Get Bank detail of the organization.

    delete:
    Deletes the selected Bank of the organization.

    update:
    Updates the selected Bank details for the given organization.

    """
    queryset = OrganizationBank.objects.all()
    serializer_class = OrganizationBankSerializer
    ordering_fields = (
        'branch', 'account_number', 'contact_person', 'created_at', 'modified_at',
        'bank__name'
    )
    search_fields = (
        'bank__name',
    )
    filter_backends = (OrderingFilter, SearchFilter, DjangoFilterBackend)
    permission_classes = [OrganizationBankPermission]

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        try:
            response.data.update({
                "statistics": {
                    "total_banks": OrganizationBank.objects.filter(
                        organization=self.get_organization()
                    ).count(),
                }
            })
        except AttributeError:
            return response
        return response
