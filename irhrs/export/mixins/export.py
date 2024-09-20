"""@irhrs_docs
Mixin to provide basic statistical report based on the queryset of the given
view. The format generated is returned in the form of json response.
"""
from logging import getLogger
import re

from django.conf import settings
from django.core.files.base import ContentFile
from django.forms.utils import pretty_name
from django_q.tasks import async_task
from openpyxl.writer.excel import save_virtual_workbook
from rest_framework import status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from irhrs.core.mixins.serializers import create_dummy_serializer, DummySerializer
from irhrs.core.utils import get_system_admin
from irhrs.core.utils.common import get_complete_url
from irhrs.export.constants import NORMAL_USER, ADMIN,SUPERVISOR, QUEUED, FAILED, COMPLETED, PROCESSING
from irhrs.export.models import Export
from irhrs.export.utils.export import PDFExport, ExcelExport, TableExport
from irhrs.export.utils.helpers import get_latest_export, has_pending_export
from irhrs.notification.utils import notify_organization, add_notification
from irhrs.permission.models import HRSPermission

logger = getLogger(__name__)


class ExportMixin:
    """
    Highly Generic PDF and statistics mixin for views.
    Generates PDF as:
        * takes input from self.filter_queryset(self.queryset())
        * takes fields from self.export_fields else model._meta.fields.name
    """

    def list(self, request, *args, **kwargs):
        export = request.query_params.get('export')
        if export and (export == 'xlsx' or export == 'pdf'):
            if hasattr(self, 'filter_queryset') and hasattr(self,
                                                            'get_queryset'):
                queryset = self.filter_queryset(self.get_queryset())
            else:
                queryset = None
            if hasattr(self, 'export_fields'):
                export_fields = self.export_fields
            else:
                export_fields = [f.name for f in queryset.model._meta.fields if
                                 f.name not in ('id', 'created_at', 'updated')]
            if export == 'pdf':
                return PDFExport.get_response(qs=queryset, columns=export_fields, )
            elif export == 'xlsx' and queryset:
                return ExcelExport.get_response(qs=queryset, columns=export_fields)
        return super().list(request, *args, **kwargs)


ExportNameSerializer = create_dummy_serializer({
    "export_name": serializers.CharField(max_length=150, allow_blank=True, allow_null=True,
                                         required=False)
})


class BackgroundExportMixin(APIView):
    """
    Background Export Mixin
    =======================

    Export files in background.
    Before using this please look at BackgroundExcelExportMixin and BackgroundTableExportMixin

    :cvar export_fields:
        fields to export

        type -->  list or dict

        list of fields that will be fetched from object,
        use dot to separate nested attributes eg. "attr1.attr2.attr3"

        dict (Mapping) of header to field name

        set this value or override get_export_fields

    :cvar export_type:
        category of export, will be used to separate exports types

        type --> str

        set this value or override get_export_type

    :cvar heading_map:
        for custom heading that need to be displayed in export

        type --> dict

        set this value or override get_heading_map

    :cvar export_description:
        Description of export. Will be added in the file exported before result rows


    **Basic Flow**

    First the request is dispatched to export method and then flow goes to _export_post
    and _export_get

    *_export_get* returns previously exported file if found

    *_export_post* collects export fields, type, description, exported_as and extra data
    and calls *prepare_export* asynchronously

    *prepare_export* then calls *get_exported_file_content* and *save_file_content*

    """

    export_fields = None
    export_type = None

    export_description = None
    heading_map = None
    footer_data = None
    frontend_redirect_url = None
    notification_permissions = []

    def get_frontend_redirect_url(self):
        """Notification Redirect URL"""
        return self.frontend_redirect_url

    def get_notification_permissions(self):
        """Notification Permissions"""
        return self.notification_permissions

    def get_export_description(self):
        """Description lines to be added before data"""
        return self.export_description

    def get_export_type(self):
        assert self.export_type is not None, f"{self.__class__} must define  `export_type`"
        return self.export_type

    def get_export_fields(self):
        assert self.export_fields is not None, f"{self.__class__} must define  `export_fields`"
        return self.export_fields

    def get_exported_as(self):
        mode = self.request.query_params.get('as')
        return {
            "hr": ADMIN,
            "supervisor": SUPERVISOR
        }.get(mode, NORMAL_USER)

    def get_export_name(self):
        serializer = ExportNameSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        return serializer.data.get('export_name') or self.get_export_type()

    def get_extra_export_data(self):
        return dict(
            organization=self.get_organization() if hasattr(self, 'get_organization') else None,
            redirect_url=self.get_frontend_redirect_url(),
            exported_as=self.get_exported_as(),
            notification_permissions=self.get_notification_permissions()
        )

    def get_export_data(self):
        if hasattr(self, 'get_queryset'):
            queryset = self.get_queryset()

            if hasattr(self, 'filter_queryset'):
                queryset = self.filter_queryset(queryset)
            return queryset
        return []

    def get_heading_map(self):
        return self.heading_map

    def _export_get(self):
        """
        Get all task in xlsx
        returns previously exported file if found
        """
        if hasattr(self, 'get_organization'):
            organization = self.get_organization()
        else:
            organization = None
        latest_export = get_latest_export(
            export_type=self.get_export_type(),
            user=self.request.user,
            exported_as=self.get_exported_as(),
            organization=organization
        )

        if latest_export:
            return Response({
                'url': get_complete_url(latest_export.export_file.url),
                'created_on': latest_export.modified_at
            })
        else:
            return Response({
                'message': 'Previous Export file couldn\'t be found.',
                'url': ''
            }, status=status.HTTP_200_OK
            )

    @classmethod
    def get_exported_file_content(cls, queryset, title, columns, extra_content,
                                  description=None, heading_map=None, footer_data=None
                                  ):
        """Return contents of exported file of type ContentFile"""
        raise NotImplementedError

    @classmethod
    def save_file_content(cls, export_instance, file_content):
        """Save file_content and set export_instance.export_file and export_instance.status to Successful"""
        raise NotImplementedError

    def get_footer_data(self):
        return self.footer_data

    @staticmethod
    def prepare_export(cls, queryset, export_fields, export_instance, extra_content,
                       description=None, heading_map=None, footer_data=None):
        try:

            export_instance.status = PROCESSING
            export_instance.associated_permissions.add(
                *HRSPermission.objects.filter(
                    code__in=[
                        x.get('code') for x in
                        (extra_content.get('notification_permissions') or [])]
                )
            )
            export_instance.save()
            logger.info(f"Preparing export for {export_instance.__str__()}")
            file_content = cls.get_exported_file_content(
                queryset,
                title=export_instance.title[:30],
                columns=export_fields,
                extra_content=extra_content,
                description=description,
                heading_map=heading_map,
                footer_data=footer_data,
            )
            cls.save_file_content(export_instance, file_content)
            cls.send_success_notification(
                obj=export_instance,
                url=extra_content.get('redirect_url'),
                exported_as=extra_content.get('exported_as'),
                permissions=extra_content.get('notification_permissions')
            )
        except Exception as e:
            import traceback

            export_instance.remarks = str(e)[:255]
            export_instance.traceback = str(traceback.format_exc())
            export_instance.status = FAILED

            logger.error(f"Could not complete export for {export_instance.__str__()}",
                         exc_info=True)
            cls.send_failed_notification(
                obj=export_instance,
                url=extra_content.get('redirect_url'),
                exported_as=extra_content.get('exported_as'),
                permissions=extra_content.get('notification_permissions')
            )
            export_instance.save()

    @classmethod
    def send_success_notification(cls, obj, url, exported_as, permissions):
        if exported_as == ADMIN:
            notify_organization(
                permissions=permissions,
                text=f"{pretty_name(obj.name).replace('report', ' ')} report has been generated.",
                action=obj,
                organization=obj.organization,
                actor=get_system_admin(),
                url=url+f"/?export={obj.id}" if url else ''
            )
        else:
            name = obj.name or ""
            word_list=re.findall('[A-Z][^A-Z]*', name)
            seprated_word_name=" ".join(word_list)
            add_notification(
                text=f"{pretty_name(seprated_word_name).replace('report', ' ')} report has been generated.",
                action=obj,
                recipient=obj.user,
                actor=get_system_admin(),
                url=url+f"/?export={obj.id}" if url else ''
            )

    @classmethod
    def send_failed_notification(cls, obj, url, exported_as, permissions):
        if exported_as == ADMIN:
            notify_organization(
                permissions=permissions,
                text=f"Failed to generate {pretty_name(obj.name).replace('report', '')} report",
                action=obj,
                organization=obj.organization,
                actor=get_system_admin(),
                url=url+f"/?export={obj.id}" if url else ''
            )
        else:
            add_notification(
                text=f"Failed to generate {pretty_name(obj.name).replace('report', '')} report",
                action=obj,
                recipient=obj.user,
                actor=get_system_admin(),
                url=url+f"/?export={obj.id}" if url else ''
            )

    @action(methods=['GET', 'POST'], detail=False, serializer_class=ExportNameSerializer)
    def export(self, *args, **kwargs):
        if self.request.method.upper() == 'GET':
            return self._export_get()
        else:
            return self._export_post()

    def _export_post(self):
        """
        Start task export process in background
        """
        if hasattr(self, 'get_organization'):
            organization = self.get_organization()
        else:
            organization = None

        if has_pending_export(
            export_type=self.get_export_type(),
            user=self.request.user,
            exported_as=self.get_exported_as(),
            organization=organization
        ):
            return Response({
                'message': 'Previous request for generating report is being '
                           'currently processed, Please try back later'},
                status=status.HTTP_202_ACCEPTED)

        data = self.get_export_data()

        export = Export.objects.create(
            user=self.request.user,
            name=self.get_export_name(),
            exported_as=self.get_exported_as(),
            export_type=self.get_export_type(),
            organization=organization,
            status=QUEUED,
            remarks=''
        )

        try:
            export_extra_data = self.get_extra_export_data()
            _ = async_task(
                BackgroundExportMixin.prepare_export,
                self.__class__,
                data,
                self.get_export_fields(),
                export,
                export_extra_data,
                description=self.get_export_description(),
                heading_map=self.get_heading_map(),
                footer_data=self.get_footer_data()
            )
        except Exception as e:
            import traceback

            logger.error(e, exc_info=True)

            export.status = FAILED
            export.message = "Could not start export."
            export.traceback = str(traceback.format_exc())
            export.save()
            if getattr(settings, 'DEBUG', False):
                raise e
            return Response({
                'message': 'The export could not be completed.'
            }, status=400)

        return Response({
            'message': 'Your request is being processed in the background . Please check back later'})


class BackgroundExcelExportMixin(BackgroundExportMixin):
    """
    Export excel file in background

    export_fields:
        fields to export
        type -->  list or dict

        refer to BackgroundExportMixin.export_fields

    export_type:
        category of export, will be used to separate exports types
        type --> str

        refer to BackgroundExportMixin.export_fields

    export_description:
        Description of export. Will be added in the file exported before result rows

    prepare_export_object:
        This is a method that will prepare export object. It will get object instance as its
        first parameter and should return object or dict.

        Pass `prepare_export_object_context` in extra_content(value returned from get_extra_data)
        for context to be unpacked
        while calling prepare_export_object

    export_freeze_first_column:
        Boolean to freeze first column of export

    """

    export_freeze_first_column = False

    @staticmethod
    def prepare_export_object(obj, **kwargs):
        """
        this is a method that will prepare export object. It will get object instance as its
        first parameter and should return object or dict.
        :param obj: Instance (A row) that will be exported
        :return: prepared object
        """
        return obj

    @classmethod
    def get_exported_file_content(cls, data, title, columns, extra_content,
                                  description=None, **kwargs):
        organization = extra_content.get('organization')
        wb = ExcelExport.process(
            data,
            title=title,
            columns=columns,
            description=description,
            prepare_export_object=cls.prepare_export_object,
            prepare_export_object_context=extra_content.get('prepare_export_object_context'),
            freeze_first_column=cls.export_freeze_first_column,
            organization=organization
        )
        return ContentFile(save_virtual_workbook(wb))

    @classmethod
    def save_file_content(cls, export_instance, file_content):
        export_instance.export_file.save('random.xlsx', file_content)
        export_instance.status = COMPLETED
        export_instance.save()


class BackgroundTableExportMixin(BackgroundExportMixin):
    """
    Excel export for nested data using TableExport

    :export_fields:
        fields to export

        type --> list of dict

        format -->

        .. code-block:: python

            [{
                "name": "user",  # field name
                "title": "User Details",  # heading
                "fields": ({"name": "id", "title": "Id"}, {"name": "full_name", "title": "Full Name"}, ) # child fields
            }, ...]

    :get_serializer_class_for_export:
        method for dynamic serializer class for export defaults to view.serializer_class

    :get_serializer_class_params:
        Params for get_serializer_class_for_export

    :get_extra_export_data:
        Extra export data (like extra context for templates).
        Make sure to call super().get_extra_export_data()


    """

    @classmethod
    def get_serializer_class_for_export(cls, *args, **kwargs):
        """
        Serializer class used for export
        defaults to view.serializer_class
        :return: Serializer Class
        """
        if hasattr(cls, 'serializer_class'):
            return cls.serializer_class
        return DummySerializer

    def get_serializer_class_params(self):
        """
        Params for get_serializer_class_for_export
        """
        return {
            "args": [],
            "kwargs": dict()
        }

    def get_extra_export_data(self):
        """
        Extra export data
        type dict (like context for template)
        default --> {
            "serializer_class_params": self.get_serializer_class_params(),
        }
        :return:
        """
        extra = super().get_extra_export_data()
        extra.update({
            "serializer_class_params": self.get_serializer_class_params(),
        })
        return extra

    @classmethod
    def get_workbook_to_export_file_content(cls, data, title, columns, extra_content,
                                            description=None, **kwargs):
        serializer_class_params = extra_content.get('serializer_class_params', {})
        a = serializer_class_params.get('args', [])
        k = serializer_class_params.get('kwargs', {})

        serializer_class = cls.get_serializer_class_for_export(*a, **k)

        serializer_context = extra_content.get('serializer_context', {})
        serializer_kwargs = extra_content.get('serializer_kwargs', {})
        organization = extra_content.get('organization')

        export_data = serializer_class(instance=data, many=True, context=serializer_context,
                                       **serializer_kwargs).data
        return TableExport.process(
            export_data,
            export_format=columns,
            description=description,
            organization=organization
        )

    @classmethod
    def get_exported_file_content(cls, data, title, columns, extra_content,
                                  description=None, **kwargs):
        wb = cls.get_workbook_to_export_file_content(data, title, columns, extra_content,
                                                     description=None, **kwargs)
        return ContentFile(save_virtual_workbook(wb))

    @classmethod
    def save_file_content(cls, export_instance, file_content):
        export_instance.export_file.save('random.xlsx', file_content)
        export_instance.status = COMPLETED
        export_instance.save()
