# Django imports
from django.utils.functional import cached_property
from django_filters.rest_framework import DjangoFilterBackend
# Rest_framework imports
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

# Project current app imports
from irhrs.common.api.serializers.notification_template import \
    NotificationTemplateSerializer, NotificationTemplateContentSerializer
from irhrs.core.constants.common import LATE_IN_EMAIL, ABSENT_EMAIL, WEEKLY_ATTENDANCE_REPORT_EMAIL,\
    OVERTIME_EMAIL, LEAVE_EMAIL, LATE_IN_EMAIL_HINTS, ABSENT_EMAIL_HINTS, OVERTIME_EMAIL_HINTS, \
    LEAVE_EMAIL_HINTS, WEEKLY_ATTENDANCE_REPORT_EMAIL_HINTS, EMAIL_TYPE_STATUS
from irhrs.core.mixins.viewset_mixins import ValidateUsedData
from irhrs.core.utils.common import validate_permissions
from irhrs.organization.models import NotificationTemplateMap
from irhrs.permission.constants.permissions import (
    ALL_COMMON_SETTINGS_PERMISSION,
    HAS_PERMISSION_FROM_METHOD,
    ORGANIZATION_PERMISSION,
    ORGANIZATION_SETTINGS_PERMISSION,
    EMAIL_TEMPLATE_PERMISSION,
    ORGANIZATION_TEMPLATE_PERMISSION)
from irhrs.permission.permission_classes import permission_factory
from ...models import NotificationTemplate
# Project other app imports
from ...models.notification_template import NotificationTemplateContent


class NotificationTemplateViewSet(ValidateUsedData, ModelViewSet):
    """
    create:
    ## Create a notification template with the following essentials.

    * name||--> Late In Email for regular shift
    * type||--> Late In Email
    * content||--> Dear {{user}}}, Thank You.
    * description||-->

    """
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter,
                       DjangoFilterBackend)
    lookup_field = 'slug'
    permission_classes = [
        permission_factory.build_permission(
            "IDCardSamplePermission",
            limit_write_to=[
                ALL_COMMON_SETTINGS_PERMISSION,
                EMAIL_TEMPLATE_PERMISSION
            ],
            limit_read_to=[
                ALL_COMMON_SETTINGS_PERMISSION,
                EMAIL_TEMPLATE_PERMISSION,
                HAS_PERMISSION_FROM_METHOD
            ]
        )
    ]

    filter_fields = (
        'type', 'created_at'
    )
    search_fields = (
        ('name'),
    )
    related_names = ['notificationtemplatemap_set']
    related_methods = ['delete']

    @action(methods=['GET'], detail=False, url_path='hints')
    def get_hints(self, request, *args, **kwargs):
        self.__class__.__doc__ = """
        Use the following types to filter the hints

        * Late In Email
        * Absent Email
        * Overtime Email
        * Leave Email
        * Weekly Attendance Report Email
        """
        hints = {
            LATE_IN_EMAIL: LATE_IN_EMAIL_HINTS,
            ABSENT_EMAIL: ABSENT_EMAIL_HINTS,
            OVERTIME_EMAIL: OVERTIME_EMAIL_HINTS,
            LEAVE_EMAIL: LEAVE_EMAIL_HINTS,
            WEEKLY_ATTENDANCE_REPORT_EMAIL: WEEKLY_ATTENDANCE_REPORT_EMAIL_HINTS,
        }
        response = {
            'hints': hints.get(
                request.query_params.get('type')
            ) or 'Please select a valid type for hints.',
            'status': EMAIL_TYPE_STATUS.get(
                request.query_params.get('type')
            ) or 'Please select a valid type for hints.'

        }
        return Response(response)

    def has_user_permission(self):
        user = self.request.user
        # guess which organization granted user to access this page.
        return validate_permissions(
            user.get_hrs_permissions(user.switchable_organizations_pks),
            ORGANIZATION_PERMISSION, ORGANIZATION_SETTINGS_PERMISSION,
            ORGANIZATION_TEMPLATE_PERMISSION
        )


class NotificationTemplateContentViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'delete', 'head', 'options', 'trace']
    queryset = NotificationTemplateContent.objects.all()
    serializer_class = NotificationTemplateContentSerializer
    permission_classes = [
        permission_factory.build_permission(
            "IDCardSamplePermission",
            limit_write_to=[
                ALL_COMMON_SETTINGS_PERMISSION,
                EMAIL_TEMPLATE_PERMISSION
            ],
            limit_read_to=[
                ALL_COMMON_SETTINGS_PERMISSION,
                EMAIL_TEMPLATE_PERMISSION,
                HAS_PERMISSION_FROM_METHOD
            ]
        )
    ]

    def has_user_permission(self):
        user = self.request.user
        # guess which organization granted user to access this page.
        return validate_permissions(
            user.get_hrs_permissions(user.switchable_organizations_pks),
            ORGANIZATION_PERMISSION, ORGANIZATION_SETTINGS_PERMISSION,
            ORGANIZATION_TEMPLATE_PERMISSION
        )

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(template__slug=self.kwargs.get('template_slug'))

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if NotificationTemplateMap.objects.filter(
            template=instance.template,
            active_status__contains=[instance.status]
        ).exists():
            raise ValidationError({
                'detail': 'Unable to delete active email template content.'
            })
        return super().destroy(request, *args, **kwargs)

    @cached_property
    def template(self):
        return NotificationTemplate.objects.filter(slug=self.kwargs.get('template_slug')).first()
