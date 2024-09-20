from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.change_request import NoCreateChangeRequestMixin
from irhrs.core.mixins.viewset_mixins import RetrieveUpdateViewSetMixin
from irhrs.core.mixins.file_import_mixin import BackgroundFileImportMixin
from irhrs.core.mixins.viewset_mixins import OrganizationMixin
from irhrs.users.api.v1.permissions import UserLegalInfoImportPermission
from ..serializers.legal_info import UserLegalInfoSerializer, UserLegalInfoImportSerializer
from ....models import UserLegalInfo


class UserLegalInfoView(NoCreateChangeRequestMixin, RetrieveUpdateViewSetMixin):
    """
    create:
    ## Create User Legal Info:

    * Data
    ```javascript
    {
        "pan_number": "987987-984984-56",
        "cit_number": "67098-789-78",
        "citizenship_number": "A069-01-23-7894",
        "passport_number": "684698-65448-645"
    }
    ```

    retrieve:

    ## Displays User Legal Info.

    ```javascript
    {
        "pan_number": "123-45-79",
        "cit_number": "889898-89",
        "citizenship_number": "8989898-8989",
        "passport_number": "A8989-89898"
    }
    ```
    update:

    Update User Legal Info:

    Data
    ```javascript
    {
        "pan_number": "987987-984984-56",
        "cit_number": "67098-789-78",
        "citizenship_number": "P1212-1212",
        "passport_number": "684698-65448-645",
    }
    ```

    partial_update:

    Updates User Legal Info Details partially.

    Accepts the same parameters as ```.update()``` but not all fields required.

    """
    queryset = UserLegalInfo.objects.all()
    serializer_class = UserLegalInfoSerializer

    def get_object(self):
        return self.get_queryset().first()


class UserLegalInfoImportView(OrganizationMixin, BackgroundFileImportMixin, ModelViewSet):

    # Import Fields Start
    permission_classes = [UserLegalInfoImportPermission]
    queryset = UserLegalInfo.objects.all()
    serializer_class = UserLegalInfoSerializer
    import_serializer_class = UserLegalInfoImportSerializer
    import_fields = [
        "User",
        "Pan Number",
        "Citizenship Number",
        "Citizenship Issue Place",
        "Citizenship Issue Date",
        "CIT Number",
        "Passport Number",
        "Passport Issue Place",
        "Passport Issue Date",
        "PF Number",
        "SSFID",
    ]
    values = [
        "info@example.com",
        "15458213465",
        "2074-845-45",
        "Bhaktapur",
        "2023-05-25",
        "147845892358",
        "9874578",
        "Kathmandu",
        "2023-05-25",
        "4784515285",
        "145122656"
    ]
    background_task_name = 'legal_info'
    sample_file_name = 'legal-info-import'
    non_mandatory_field_value = {
        "Citizenship Issue Place": "",
        "Citizenship Issue Date": None,
        "CIT Number": "",
        "Passport Number": "",
        "Passport Issue Place": "",
        "Passport Issue Date": None,
        "PF Number": "",
        "SSFID": "",
    }

    def get_success_url(self):
        success_url = f'/admin/{self.organization.slug}/hris/employees/import/legal-information/'
        return success_url

    def get_failed_url(self):
        failed_url = f'/admin/{self.organization.slug}/hris/employees/import/legal-information/?status=failed'
        return failed_url

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['organization'] = self.get_organization()
        return context

