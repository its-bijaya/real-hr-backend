from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.change_request import ChangeRequestMixin
from irhrs.core.mixins.file_import_mixin import BackgroundFileImportMixin
from irhrs.core.mixins.viewset_mixins import OrganizationMixin
from irhrs.common.models import Bank
from irhrs.users.api.v1.permissions import UserBankInfoImportPermission
from irhrs.users.api.v1.serializers.user_bank import UserBankSerializer, UserBankInfoImportSerializer
from irhrs.users.models.other import UserBank


class UserBankViewSet(ChangeRequestMixin, ModelViewSet):
    """
    View for Creating UserBank.

    create:

        {
            "bank": 1,
            "branch": "Baneshwor",
            "account_number": "12355105545411541",
            "contacts": {
                "Phone": "9809507803"
            },
            "email": "",
            "contact_person": {
                "person_list": [
                    {
                        "Name": "Anurag Regmi",
                        "Designation": "Manager",
                        "Contacts": {
                            "Phone": "9809507803"
                        }
                    }
                ]
            }
        }

    """
    queryset = UserBank.objects.all()
    serializer_class = UserBankSerializer
    ordering_fields = ('account_number',)
    search_fields = ('account_number',)
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter,
                       filters.SearchFilter)

    def get_object(self):
        return self.get_queryset().first()


class UserBankImportViewSet(BackgroundFileImportMixin, OrganizationMixin, ModelViewSet):
    permission_classes = [UserBankInfoImportPermission]
    queryset = UserBank.objects.all()
    serializer_class = UserBankSerializer
    import_serializer_class = UserBankInfoImportSerializer
    import_fields = [
        "User",
        "Bank",
        "Account Number",
        "Branch",
    ]
    values = [
        "info@example.com",
        "Bank Name",
        "140000040056124",
        "Baneshwor",
    ]
    background_task_name = 'bank-info'
    sample_file_name = 'bank-info-import'
    non_mandatory_field_value = {
        "Branch": "",
    }

    def get_success_url(self):
        success_url = f'/admin/{self.organization.slug}/hris/employees/import/bank-information/'
        return success_url

    def get_failed_url(self):
        failed_url = f'/admin/{self.organization.slug}/hris/employees/import/bank-information/?status=failed'
        return failed_url

    def get_queryset_fields_map(self):
        return {
            'bank': Bank.objects.all(),
        }
