import os
import uuid

from django.http import HttpResponse
from django.utils import timezone
from django_q.tasks import async_task
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from django.conf import settings
from django.conf import settings
from irhrs.builder.api.v1.serializers.report import ReportSerializer
from irhrs.builder.api.v1.views.report_util import export_report
from irhrs.builder.models import Report
from django.core.cache import cache

from irhrs.builder.permissions import ReportBuilderPermission
from irhrs.core.mixins.serializers import DummySerializer
from irhrs.export.utils.helpers import save_workbook

MEDIA_ROOT = settings.MEDIA_ROOT
BACKEND_URL = settings.BACKEND_URL


#    "filter_operation": "CharField",  //define a operation eg ((A&B)|C)
class ReportViewSet(viewsets.ModelViewSet):
    """


        create:

                 REFER: /api/v1/builder/

                {
                  "display_fields": [
                    {
                      "field_name": CharField, //field name eg:id
                      "field_path": CharField, //field full path eg:id
                      "display": CharField //field display eg:ID
                      "aggregate": AggFunc //REFER: /api/v1/builder/constants/
                      "ordering":Asc or Desc ////REFER: /api/v1/builder/constants/
                    }
                  ],
                  "filter_fields": [
                    {
                      "field_path": "id",
                      "field_name": "id",
                      "display": "ID Filter",
                      "apply_not":Boolean,  //will apply not ~ on this field
                      "filter_value": "1" //will query (field_path=filter_value)
                      "filter_type": "Lookup" //eg: exact, REFER:/api/v1/builder/constants/
                      "filter_value2": CharField //incase of __range filter
                    }
                  ],
                  "name": CharField, //Name
                  "description": TextField, //Description
                  "app": CharField,   //App label
                  "model": CharField  // Model Name
                }

    """
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = [ReportBuilderPermission]
    serializer_class = ReportSerializer
    queryset = Report.objects.all()
    filter_backends = [SearchFilter]
    search_fields = (
        'name',
    )

    @action(detail=True, serializer_class=DummySerializer)
    def generate(self, request, pk):
        message = cache.get(f'report_export_{pk}') or {
            'message': 'Previous Task Export file couldn\'t be found.',
            'url': ''
        }
        return Response(message)

    # @staticmethod
    # def prepare_export(report_object):
    #     cache.delete(f'report_export_{report_object.id}')
    #     file_name = report_object.name[:15].replace(' ',
    #                                                 '') + '-' + uuid.uuid4().hex + '.xlsx'
    #     base_path = 'report-exports'
    #     if not os.path.exists(base_path):
    #         os.mkdir(base_path)
    #     file_path = os.path.join(base_path, file_name)
    #     try:
    #         wb = report_object.export_result_wb()
    #         file_path = save_workbook(wb, file_path)
    #         _prepare_cache = {  # key will be used in future
    #             'url': BACKEND_URL + '/media/' + file_path + '?key=' + uuid.uuid4().hex + '&public=' + uuid.uuid4().hex,
    #             'created_on': timezone.now().astimezone()
    #         }
    #         cache.set(f'report_export_{report_object.id}',
    #                   _prepare_cache,
    #                   timeout=None)
    #         cache.delete(f'report_export_on_progress_{report_object.id}')
    #     except Exception as e:
    #         print(e)
    #         cache.delete(f'report_export_on_progress_{report_object.id}')

    @generate.mapping.post
    def prepare_report(self, request, pk):
        if cache.get(f'report_export_on_progress_{pk}'):
            return Response({
                'message': 'Previous request for generating report is being'
                           'currently processed, Please try back later'},
                status=status.HTTP_202_ACCEPTED)
        cache.set(f'report_export_on_progress_{pk}', True, timeout=None)
        _ = async_task(export_report, self.get_object())
        return Response({
            'message': 'Your request is being processed in the background,'
                       'Please check back later'})

    if getattr(settings, 'DEBUG', False):
        @action(detail=True, serializer_class=DummySerializer)
        def check(self, request, pk):
            report_obj = self.get_object()
            try:
                _query_select, _display_obj_map, base_query = report_obj.get_report_queryset()
            except Exception as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
            return Response({
                '_query_select': _query_select,
                '_display_objects': _display_obj_map.__str__(),
                'base_query': base_query.query.__str__().replace('"', "'")
            })

        @action(detail=True, serializer_class=DummySerializer)
        def gen(self, request, pk):
            report_obj = self.get_object()
            wb = report_obj.export_result_wb()
            from openpyxl.writer.excel import save_virtual_workbook
            response = HttpResponse(content=save_virtual_workbook(wb),
                                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response[
                'Content-Disposition'] = 'attachment; filename=myexport.xlsx'
            return response
