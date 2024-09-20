from django.apps import apps as django_apps
from rest_framework import filters
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.viewset_mixins import (OrganizationCommonsMixin,
                                              OrganizationMixin, ListViewSetMixin)
from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.filters import FilterMapBackend
from irhrs.organization.api.v1.permissions import OrganizationSettingsPermission
from irhrs.permission.constants.permissions import (HAS_PERMISSION_FROM_METHOD,
                                                    ATTENDANCE_PERMISSION,
                                                    ATTENDANCE_INDIVIDUAL_ATTENDANCE_SETTINGS_PERMISSION,
                                                    ORGANIZATION_PERMISSION,
                                                    ORGANIZATION_TEMPLATE_PERMISSION,
                                                    ORGANIZATION_SETTINGS_PERMISSION,
                                                    ORGANIZATION_SETTINGS_VIEW_PERMISSION)
from irhrs.permission.permission_classes import permission_factory
from ..serializers.other import NotificationTemplateMapSerializer
from ....models.other import NotificationTemplateMap


class NotificationTemplateMapViewSet(
    OrganizationCommonsMixin, OrganizationMixin, ModelViewSet
):
    queryset = NotificationTemplateMap.objects.all()
    serializer_class = NotificationTemplateMapSerializer
    filter_backends = (
        filters.SearchFilter, filters.OrderingFilter,
        FilterMapBackend
    )
    permission_classes = [
        permission_factory.build_permission(
            "NotificationTemplateMapPermission",
            limit_write_to=[
                ORGANIZATION_PERMISSION,
                ORGANIZATION_SETTINGS_PERMISSION,
                ORGANIZATION_TEMPLATE_PERMISSION
            ],
            limit_read_to=[
                ORGANIZATION_PERMISSION,
                ORGANIZATION_SETTINGS_VIEW_PERMISSION,
                ORGANIZATION_SETTINGS_PERMISSION,
                ORGANIZATION_TEMPLATE_PERMISSION,
                HAS_PERMISSION_FROM_METHOD
            ]
        )
    ]
    search_fields = (
        'template__name',
    )

    filter_map = {
        'is_active': 'is_active',
        'template_type': 'template__type'
    }

    def has_user_permission(self):
        user = self.request.user
        # guess which organization granted user to access this page.
        return validate_permissions(
            user.get_hrs_permissions(self.get_organization()),
            ATTENDANCE_PERMISSION,
            ATTENDANCE_INDIVIDUAL_ATTENDANCE_SETTINGS_PERMISSION,
        )


class OrganizationSetupInfo(OrganizationMixin, ListViewSetMixin):
    permission_classes = [OrganizationSettingsPermission]

    def organization_specific(self):
        models = {
            'Asset': django_apps.get_model(
                'organization', 'organizationequipment'
            ),
            'Bank': django_apps.get_model(
                'organization', 'organizationbank'
            ),
            'Division': django_apps.get_model(
                'organization', 'organizationdivision'
            ),
            'Branch': django_apps.get_model(
                'organization', 'organizationbranch'
            ),
            'Document': django_apps.get_model(
                'organization', 'organizationdocument'
            ),
            'Employment Status': django_apps.get_model(
                'organization', 'employmentstatus'
            ),
            'Employment Level': django_apps.get_model(
                'organization', 'employmentlevel'
            ),
            'Organization Ethics': django_apps.get_model(
                'organization', 'organizationethics'
            ),
            'Job Title': django_apps.get_model(
                'organization', 'employmentjobtitle'
            ),
            'Holiday': django_apps.get_model(
                'organization', 'holiday'
            ),
            'Change Type': django_apps.get_model(
                'hris', 'changetype'
            ),
            'Vision & Mission': django_apps.get_model(
                'organization', 'organizationvision'
            ),
            'Template Mapping': django_apps.get_model(
                'organization', 'notificationtemplatemap'
            ),
            'Fiscal Year': django_apps.get_model(
                'organization', 'fiscalyear'
            ),
            'Application Setting': django_apps.get_model(
                'organization', 'applicationsettings'
            ),
        }
        return {
            model_display: (
                current_model.objects.filter(
                    organization=self.organization, enabled=False
                ).count() if model_display == "Application Setting" else
                current_model.objects.filter(
                    organization=self.organization
                ).count()
            ) for model_display, current_model in models.items()
        }

    @staticmethod
    def commons(self):
        # disabled for now as common settings has been moved out to switchable
        # organization space.
        return {}
        # religion_ethnicity_qs = ReligionAndEthnicity.objects.all()
        # models = {
        #     'Ethnicity': religion_ethnicity_qs.filter(
        #         category=ETHNICITY
        #     ),
        #     'Document Category': DocumentCategory.objects.all(),
        #     'Commons Bank': Bank.objects.all(),
        #     'Holiday Category': HolidayCategory.objects.all(),
        #     'Religion': religion_ethnicity_qs.filter(
        #         category=RELIGION
        #     ),
        #     'Email Template': NotificationTemplate.objects.all(),
        #     'Manager Message': MessageToUser.objects.all()
        # }
        # return {
        #     model_display: queryset.count() for model_display, queryset in
        #     models.items()
        # }

    def list(self, request, *args, **kwargs):
        return Response(
            {
                'org_specific': self.organization_specific(),
                # 'commons': self.commons()
            }
        )
