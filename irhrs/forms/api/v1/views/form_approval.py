from irhrs.core.mixins.viewset_mixins import (
    OrganizationMixin,
    ListCreateViewSetMixin,
)
from irhrs.forms.api.v1.serializers.setting import (
    FormApprovalSettingLevelSerializer,
    ReadFormApprovalSettingLevelSerializer
)
from irhrs.forms.api.v1.permission import FormApprovalSettingPermission
from irhrs.forms.models import Form, FormApprovalSettingLevel


class FormApprovalSettingLevelViewSet(
    OrganizationMixin,
    ListCreateViewSetMixin
):

    serializer_class = FormApprovalSettingLevelSerializer
    permission_classes = [FormApprovalSettingPermission]
    queryset = FormApprovalSettingLevel.objects.all()

    def get_queryset(self):
        form_id = self.kwargs.get('form')
        if self.action == "list":
            return Form.objects.filter(id=int(form_id))

        return super().get_queryset().filter(
            form__organization=self.get_organization(),
            form=int(form_id)
        )

    def get_serializer_class(self):
        if self.action == "list":
            return ReadFormApprovalSettingLevelSerializer
        return super().get_serializer_class()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['form'] = self.kwargs.get('form')
        context['organization'] = self.get_organization()
        return context

    def list(self, request, *args, **kwargs):
        response = super().list(self, request, *args, **kwargs)
        response.data.update({
            "results": response.data.get('results')[0]["results"]
        })
        return response
