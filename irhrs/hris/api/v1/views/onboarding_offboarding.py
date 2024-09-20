import logging
import os
import re
import types
import uuid

from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.db.models import Count, Q, F, Case, When, FloatField, Prefetch, \
    Exists, OuterRef
from django.db.models.functions import Cast
from django.http import HttpResponse, Http404
from django.template.loader import render_to_string, get_template
from django.utils.functional import cached_property
from django.utils.timezone import now
from django_q.tasks import async_task
from lxml.html.clean import Cleaner
from rest_framework import filters, serializers
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, MethodNotAllowed, PermissionDenied
from rest_framework.fields import CharField
from rest_framework.generics import get_object_or_404 as drf_get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.status import HTTP_204_NO_CONTENT
from rest_framework.viewsets import ModelViewSet
from xhtml2pdf import pisa
from xhtml2pdf.document import pisaDocument

from irhrs.common.models import DocumentCategory
from irhrs.core.mixins.serializers import DummySerializer
from irhrs.core.mixins.viewset_mixins import OrganizationMixin, \
    OrganizationCommonsMixin, ListCreateDestroyViewSetMixin
from irhrs.core.utils import nested_getattr
from irhrs.core.utils.common import format_timezone, validate_permissions, get_today, \
    get_complete_url
from irhrs.core.utils.custom_mail import custom_mail as send_mail
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.export.utils.export import PDFExport
from irhrs.hris.api.v1.permissions import TaskTemplatesPermission, OnBoardingPermission, \
    LetterTemplatePermission, OnBoardingOffBoardingPermissionMixin, EmploymentReviewPermission, \
    ChangeTypePermission, \
    SeparationTypePermission, OffBoardingPermission
from irhrs.hris.api.v1.serializers.core_task import \
    UserResultAreaListSerializer, UserResultAreaSerializer
from irhrs.hris.api.v1.serializers.onboarding_offboarding import \
    TaskTemplateTitleSerializer, TaskFromTemplateSerializer, \
    PreEmploymentSerializer, LetterTemplateSerializer, \
    GeneratedLetterSerializer, \
    TaskTemplateMappingSerializer, ChangeTypeSerializer, \
    EmploymentReviewSerializer, GenerateLetterSerializer, \
    EmployeeChangeTypeDetailSerializer, LeaveChangeTypeSerializer, \
    EmployeeSeparationTypeSerializer, \
    EmployeeSeparationSerializer, TaskReportSerializer, \
    TaskTemplateTitleDownloadSerializer, LeaveReportSerializer, EmployeeSeparationEditSerializer, \
    TaskMultiAssignSerializer, TaskFromTemplateAttachmentSerializer, StatusHistorySerializer, \
    EmployeeSeparationLeaveEncashmentEditSerializer, \
    EmployeeSeparationLeaveEncashmentEditHistorySerializer
from irhrs.hris.constants import NOT_SENT, FAILED, SENT, \
    ONBOARDING, \
    OFFBOARDING, CHANGE_TYPE, ACCEPTED, DECLINED, OFFER_LETTER_LETTER_PARAMS, \
    CHANGE_TYPE_LETTER_PARAMS, ONBOARDING_LETTER_PARAMS, \
    OFFBOARDING_LETTER_PARAMS, STOPPED, HOLD, SAVED, DOWNLOADED, EXPIRED, ACTIVE, OFFER_LETTER, \
    CUSTOM_LETTER_PARAMS, CUSTOM, COMPLETED as HRIS_COMPLETED
from irhrs.hris.models import PreEmployment, LetterTemplate, UserResultArea, \
    CoreTask
from irhrs.hris.models.onboarding_offboarding import GeneratedLetter, \
    TaskTracking, ChangeType, EmploymentReview, EmployeeSeparationType, \
    EmployeeSeparation, TaskTemplateMapping, GeneratedLetterHistory, TaskFromTemplateAttachment, \
    LeaveEncashmentOnSeparationChangeHistory
from irhrs.hris.utils import generate_offer_letter, create_task_from_templates, \
    raise_if_hold, transaction,\
    annotate_proportionate_carry_forward_used_edited_on_leave_accounts,\
    generate_custom_letter_message
from irhrs.leave.models import LeaveAccount, MasterSetting
from irhrs.leave.tasks import get_active_master_setting
from irhrs.leave.utils.balance import get_fiscal_year_for_leave
from irhrs.organization.models import FiscalYear
from irhrs.permission.constants.permissions import HRIS_REPORTS_PERMISSION
from irhrs.task.api.v1.serializers.task import TaskSerializer
from irhrs.task.constants import COMPLETED, PENDING, IN_PROGRESS
from irhrs.task.models import Task
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from irhrs.users.models import UserExperience
from irhrs.users.models.other import UserDocument
from ....models import TaskTemplateTitle, TaskFromTemplate

cleaner = Cleaner()
# This will kill some of the Trumbowyg styles. Hence, disable `safe_attrs_only`
# Currently, images is not supported, and carry a potential bug. Remove all `img` tags.
cleaner.kill_tags = ['img']
cleaner.safe_attrs_only = False
logger = logging.getLogger(__name__)
fernet = Fernet(settings.FERNET_KEY)
INFO_EMAIL = getattr(settings, 'INFO_EMAIL', 'noreply@realhrsoft.com')


class LetterGenerateMixin:

    def generate_letter(self, request, obj=None, data=None, **extra_response_data):
        self.serializer_class = GenerateLetterSerializer
        obj = obj or self.get_object()
        ctx = self.get_serializer_context()
        tracker_type = {
            PreEmployment: 'pre_employment',
            EmploymentReview: 'employment_review',
            EmployeeSeparation: 'separation'
        }
        letter_type = {
            PreEmployment: ONBOARDING,
            EmploymentReview: CHANGE_TYPE,
            EmployeeSeparation: OFFBOARDING,
        }
        ctx.update({
            tracker_type.get(type(obj)): obj,
            'letter_type': letter_type.get(type(obj))
        })
        if request.method == 'GET':
            action_performed = GeneratedLetterHistory.objects.filter(
                letter=OuterRef('pk')
            ).only('pk')
            letters = GeneratedLetter.objects.filter(
                **{tracker_type.get(type(obj)): obj}
            ).annotate(
                is_sent=Exists(
                    action_performed.filter(status=SENT)
                ),
                is_downloaded=Exists(
                    action_performed.filter(status=DOWNLOADED)
                ),
                is_saved=Exists(
                    action_performed.filter(status=SAVED)
                )
            )
            page = self.paginate_queryset(letters)
            return self.get_paginated_response(
                GenerateLetterSerializer(
                    page, many=True,
                    context=self.get_serializer_context()
                ).data
            )
        else:
            if obj.status in [HOLD, STOPPED]:
                raise ValidationError(
                    f"Cannot create letters this "
                    f"{obj.__class__.__name__.lower()} because it is in "
                    f"{obj.get_status_display().lower()} state."
                )
            ser = GenerateLetterSerializer(
                data=data or request.data,
                context=ctx
            )
            ser.is_valid(raise_exception=True)
            ser.save()
            return Response({**ser.data, **extra_response_data})


class PrePostTaskMixin(LetterGenerateMixin):
    """
    Helper Class for providing `<pk>/pre-tasks`, `<pk>/post-tasks`,
    and `<pk>/letters` API. This Helper class will maintain consistency
    across the three major functions provided through on boarding / off boarding
    platform.
    """

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status in [STOPPED, HOLD]:
            raise ValidationError(
                f"Updating "
                f"{instance.get_status_display().lower()} "
                f"process is not permitted."
            )
        return super().update(request, *args, **kwargs)

    def raise_if_task_pending(self):
        obj = self.get_object()
        disallowed_status = ['In Progress', 'Completed']
        if (
            obj.pre_task_status in disallowed_status
            or obj.post_task_status in disallowed_status
        ):
            raise ValidationError(
                "Cannot delete as the tasks has been assigned."
            )

    def destroy(self, request, *args, **kwargs):
        self.raise_if_task_pending()
        return super().destroy(request, *args, **kwargs)

    @cached_property
    def step(self):
        allowed_kwargs = {
            'pre-tasks': 'pre_task',
            'post-tasks': 'post_task',
        }
        step = self.kwargs.get('step')
        if step in allowed_kwargs:
            return allowed_kwargs.get(step)
        raise Http404

    @property
    def pre_task(self):
        obj = self.get_object()
        tracker_type = {
            PreEmployment: 'pre_employment',
            EmploymentReview: 'employment_review',
            EmployeeSeparation: 'separation'
        }
        pre_task = obj.pre_task
        if not pre_task:
            raise ValidationError(
                "Please assign Pre Task."
            )
        tracker = TaskTracking.objects.filter(
            task_template=pre_task
        ).filter(
            **{
                tracker_type.get(type(obj)): obj
            }
        )
        if tracker.exists():
            instance = tracker.first()
        else:
            instance = TaskTracking.objects.create(
                task_template=pre_task,
                **{tracker_type.get(type(obj)): obj}
            )
            create_task_from_templates(instance)
        return instance

    @property
    def post_task(self):  # make generic with pre-task
        obj = self.get_object()
        post_task = obj.post_task
        if not post_task:
            raise ValidationError(
                "Please assign Post Task."
            )
        tracker_type = {
            PreEmployment: 'pre_employment',
            EmploymentReview: 'employment_review',
            EmployeeSeparation: 'separation'
        }
        tracker = TaskTracking.objects.filter(
            task_template=post_task,
            **{tracker_type.get(type(obj)): obj}
        )
        if tracker.exists():
            instance = tracker.first()
        else:
            instance = TaskTracking.objects.create(
                task_template=post_task,
                **{tracker_type.get(type(obj)): obj}
            )
            create_task_from_templates(instance)
        return instance

    @action(detail=True,
            url_path='(?P<step>(pre-tasks|post-tasks))',
            methods=['GET'],
            serializer_class=TaskTemplateMappingSerializer
            )
    def tasks(self, request, *args, **kwargs):
        self.__class__.__doc__ = """
        Filter task results with
        * status=pending for status in progress and pending
        * status=completed for completed status
        """

        # HAVE TO RESET THESE FOLLOWING FIELDS, BECAUSE self.get_object()
        # calls self.filter_queryset() and the result wont be found,
        # resulting 404
        self.search_fields = ()
        self.filter_map = {}
        step = self.step
        instance = getattr(self, step)
        self.filter_map = {}
        self.ordering_fields_map = {
            'title': 'task__title',
            'deadline': 'task__deadline',
        }
        self.search_fields = (
            'task__title',
        )

        qs = instance.tasks.all()

        search_param = self.request.query_params.get('search')
        if search_param:
            qs = qs.filter(Q(task__title__icontains=search_param)
                           | Q(template_detail__title__icontains=search_param))

        ordering = self.request.query_params.get('ordering')
        if ordering in ('title', '-title'):
            qs = qs.annotate(
                ordering_value=Case(
                    When(
                        task__isnull=True,
                        then=F('template_detail__title')
                    ),
                    default=F('task__title')
                )
            ).order_by(
                'ordering_value' if ordering == 'title' else '-ordering_value'
            )
        page = self.paginate_queryset(qs)
        ctx = self.get_serializer_context()
        return self.get_paginated_response(
            TaskTemplateMappingSerializer(
                page, many=True, context=ctx,
            ).data
        )

    @action(
        detail=True,
        url_path='letters',
        methods=['GET', 'POST'],
        serializer_class=GenerateLetterSerializer
    )
    def letters(self, request, **kwargs):
        return self.generate_letter(request)

    @action(
        detail=True,
        url_path='(?P<step>(pre-tasks|post-tasks))/multi-assign',
        methods=['POST'],
        serializer_class=TaskMultiAssignSerializer
    )
    def task_multiple_assign(self, request, *args, **kwargs):
        actual_object = self.get_object()
        if request.method == 'POST':
            raise_if_hold(actual_object)

        ser = TaskMultiAssignSerializer(
            data=request.data,
            context={
                'request': request,
                'actual_object': actual_object,
                **self.get_serializer_context()
            }
        )
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

    @action(detail=True,
            url_path=r'(?P<step>(pre-tasks|post-tasks))/(?P<task_id>\d+)',
            serializer_class=TaskTemplateMappingSerializer,
            methods=['GET', 'PUT'])
    def task_assign(self, request, **kwargs):
        actual_object = self.get_object()
        instance = getattr(self, self.step)
        if request.method == 'PUT':
            raise_if_hold(actual_object)
        mapping = drf_get_object_or_404(
            instance.tasks.all(),
            pk=kwargs.get('task_id')
        )
        context = self.get_serializer_context()
        if request.method == 'GET':
            ser = TaskTemplateMappingSerializer(mapping, context=context)
            return Response(ser.data)
        ser = TaskTemplateMappingSerializer(
            context=context,
            instance=mapping,
            data=request.data
        )
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

    @action(detail=False,
            url_path='tasks-summary',
            methods=['GET'])
    def tasks_report(self, request, **kwargs):
        self.ordering_fields_map = {}
        self.filter_map = {}
        self.__class__.__doc__ = """
        The task summary reports the following:

        * total_tasks: All tasks count
        * pending: Assigned tasks not in COMPLETED
        * completed: Assigned tasks in COMPLETED
        * percentage: completed/total
        """
        qs = TaskTracking.objects.filter()
        report_type = ''
        if isinstance(self, PreEmploymentView):
            report_type = 'pre_employment'
            qs = PreEmployment.objects.filter(
                organization=self.organization
            )
            self.ordering_fields_map = {
                'full_name': 'full_name'
            }
        elif isinstance(self, EmploymentReviewViewSet):
            report_type = 'employment_review'
            qs = EmploymentReview.objects.filter(
                employee__detail__organization=self.organization
            )
            self.ordering_fields_map = {
                'full_name': 'employee__first_name'
            }
        elif isinstance(self, EmployeeSeparationView):
            report_type = 'separation'
            qs = EmployeeSeparation.objects.filter(
                separation_type__organization=self.organization
            )
            self.ordering_fields_map = {
                'full_name': 'employee__first_name'
            }
        qs = qs.filter(
            task__isnull=False
        ).annotate(
            total_tasks=Count('task__tasks__task'),
            total_assigned=Count(
                'task__tasks__task', filter=Q(task__tasks__task__isnull=False)
            ),
            pending_tasks=Count(
                'task__tasks__task',
                filter=Q(
                    task__tasks__task__isnull=False
                ) & ~Q(
                    task__tasks__task__status=COMPLETED
                )),
            completed_tasks=Count(
                'task__tasks__task',
                filter=Q(task__tasks__task__status=COMPLETED)
            )
        ).annotate(
            percentage=Case(
                When(
                    total_assigned=0, then=0.0
                ),
                default=Cast(
                    F('completed_tasks'), FloatField()
                ) / Cast(
                    F('total_assigned'), FloatField()
                ) * 100.0,
                output_field=FloatField()
            )
        )
        page = self.paginate_queryset(self.filter_queryset(qs))
        ctx = self.get_serializer_context()
        ctx.update({
            'report_type': report_type
        })
        return self.get_paginated_response(
            TaskReportSerializer(
                page, many=True, context=ctx,
            ).data
        )

    @action(detail=False,
            url_path='(?P<identifier>(\d+))/tasks-list',
            methods=['GET'])
    def tasks_summary_list(self, request, **kwargs):
        self.search_fields = (
            'task__title',
        )
        self.ordering_fields_map = {
            'title': 'task__title',
            'deadline': 'task__deadline'
        }
        self.__class__.__doc__ = """
        """
        qs = TaskTracking.objects.filter()
        report_type = ''

        pre_employment = kwargs.get('identifier', '')
        employment_review = kwargs.get('identifier', '')
        separation = kwargs.get('identifier', '')

        if isinstance(self, PreEmploymentView):
            report_type = 'pre_employment'
            qs = qs.filter(
                pre_employment__isnull=False,
                pre_employment__organization=self.organization
            )
            if pre_employment:
                qs = qs.filter(pre_employment_id=pre_employment)
        elif isinstance(self, EmploymentReviewViewSet):
            report_type = 'employment_review'
            qs = qs.filter(
                employment_review__isnull=False,
                employment_review__employee__detail__organization=self.organization
            )
            if employment_review:
                qs = qs.filter(employment_review_id=employment_review)
        elif isinstance(self, EmployeeSeparationView):
            report_type = 'separation'
            qs = qs.filter(
                separation__isnull=False,
                separation__employee__detail__organization=self.organization
            )
            if separation:
                qs = qs.filter(separation_id=separation)
        template_mapping = TaskTemplateMapping.objects.filter(
            tasktracking__in=qs
        ).filter(
            task__isnull=False
        )
        status = request.query_params.get('status')
        if status:
            if status == 'pending':
                template_mapping = template_mapping.filter(
                    task__status__in=[PENDING, IN_PROGRESS]
                )
            elif status == 'completed':
                template_mapping = template_mapping.filter(
                    task__status=COMPLETED
                )
        queryset = self.filter_queryset(template_mapping)
        # Ordering in Pre/Post Task
        # (ordering by TaskTitle + Template Title (effect merged) )
        # Until a task is assigned, the task's title should be presumed to
        # Template's title and then ordering should be performed.
        ordering = self.request.query_params.get('ordering')
        if ordering in ('title', '-title'):
            queryset = queryset.annotate(
                ordering_value=Case(
                    When(
                        task__isnull=True,
                        then=F('template__title')
                    ),
                    default=F('task__title')
                )
            ).order_by(
                'ordering_value' if ordering == 'title' else '-ordering_value'
            ).exclude('ordering_value')
        page = self.paginate_queryset(queryset)
        ctx = self.get_serializer_context()
        ctx.update({
            'report_type': report_type
        })
        return self.get_paginated_response(
            TaskTemplateMappingSerializer(
                page, many=True, context=ctx,
            ).data
        )

    @action(
        methods=['POST'], detail=True,
        serializer_class=type(
            'UnHoldSerializer',
            (Serializer,),
            {
                'remarks': CharField(
                    max_length=600,
                    required=True
                )
            }
        )
    )
    def resume(
        self, request, *args, **kwargs,
    ):
        instance = self.get_object()
        if instance.status != HOLD:
            raise ValidationError({
                'error': 'Only hold status can be resumed.'
            })
        ser = self.serializer_class(data=request.data)
        ser.is_valid(raise_exception=True)
        last_history = instance.history.exclude(
            status=HOLD
        ).order_by(
            '-created_at'
        ).first()
        return_status_to = last_history.status if last_history else ACTIVE
        instance.history.create(
            status=return_status_to,
            remarks=ser.validated_data.get('remarks')
        )
        instance.status = return_status_to
        instance.save()
        return Response({
            'message': 'The resume was successful.'
        })

    def has_user_permission(self):
        if self.action == 'tasks_report' and validate_permissions(
            self.request.user.get_hrs_permissions(self.organization),
            HRIS_REPORTS_PERMISSION
        ):
            return True
        return False

    @action(
        methods=['GET'],
        detail=True
    )
    def history(self, request, *args, **kwargs):
        instance = self.get_object()
        return Response(
            StatusHistorySerializer(
                instance.history.filter(
                    remarks__isnull=False
                ).order_by('created_at').select_related(
                    'created_by', 'created_by__detail'
                ),
                many=True
            ).data
        )


class TaskTemplateTitleViewSet(PDFExport,
                               OrganizationMixin,
                               OrganizationCommonsMixin,
                               ModelViewSet):
    """
    Create Task Template Title with following data:

    ```js
    {
        "name": "Change Type",
        "template_type": "change"
    }
    ```
    """
    queryset = TaskTemplateTitle.objects.all()
    serializer_class = TaskTemplateTitleSerializer
    filter_backends = (
        filters.SearchFilter, OrderingFilterMap, FilterMapBackend
    )
    lookup_field = 'slug'
    permission_classes = [TaskTemplatesPermission]
    search_fields = (
        'name',
    )
    filter_map = {
        'type': 'template_type'
    }
    ordering_fields_map = {
        'name': 'name',
        'modified_at': 'modified_at',
        'template_type': 'template_type'
    }

    @action(
        methods=['GET'],
        url_path='download-checklists',
        detail=True
    )
    def download_checklists(self, request, *args, **kwargs):
        template = self.get_object()
        ser_context = self.get_serializer_context()
        ctx = TaskTemplateTitleDownloadSerializer(
            template,
            context=ser_context
        ).data
        html = render_to_string(
            'download_checklists.html',
            context=ctx,
            request=request,
        )
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(
            f'{uuid.uuid4().hex}.pdf'
        )
        pisa_status = pisa.CreatePDF(
            html, dest=response, link_callback=self.link_callback)
        if pisa_status.err:
            return HttpResponse(
                'We had some errors <pre>' + html + '</pre>')
        return response


class TaskFromTemplateViewSet(OrganizationMixin, ModelViewSet):
    """
    Create with following data:
    ```javascript
    {
        "template": "template-slug",
        "title": "Title",
        "description": "Description",
        "checklists": [
            {
                "title": "Checklist1"
            },
            {
                "title": "Checklist2"
            }
        ]
    }
    ```
    """
    permission_classes = [TaskTemplatesPermission]
    serializer_class = TaskFromTemplateSerializer
    filter_backends = (
        filters.SearchFilter, OrderingFilterMap, FilterMapBackend
    )
    filter_map = {
        'type': 'template__slug',
        'organization': 'template__organization__slug',
        'template_type': 'template__template_type',
    }
    search_fields = (
        'title',
    )
    ordering_fields_map = {
        'title': 'title',
        'modified_at': 'modified_at',
        'checklists_count': 'checklists_count'
    }
    ordering_fields = (
        'title',
    )

    def get_queryset(self):
        queryset = TaskFromTemplate.objects.filter(
            template__organization=self.organization
        ).select_related(
            'template'
        ).annotate(
            checklists_count=Count('checklists')
        )
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                'checklists'
            )
        return queryset

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx.update({
            'action': self.action,
            'organization': self.organization
        })
        return ctx


class TaskFromTemplateAttachmentViewSet(OrganizationMixin, ListCreateDestroyViewSetMixin):
    serializer_class = TaskFromTemplateAttachmentSerializer
    queryset = TaskFromTemplateAttachment.objects.all()
    permission_classes = [TaskTemplatesPermission]
    parser_classes = (MultiPartParser, FormParser,)

    @staticmethod
    def _get_template(template_id):
        try:
            task = TaskFromTemplate.objects.get(id=template_id)
        except (Task.DoesNotExist, ValueError):
            raise Http404
        return task

    def get_queryset(self):
        template = self._get_template(self.kwargs.get('template_id'))
        return template.attachments.all()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # temp :HACK
        try:
            template = self._get_template(self.kwargs.get('template_id'))
        except Exception as e:
            template = None
        context['template'] = template
        return context


class PreEmploymentView(PrePostTaskMixin,
                        OrganizationMixin,
                        OrganizationCommonsMixin,
                        PDFExport, ModelViewSet):
    """
    Create Pre employment here.

    ## Use `generate` API to generate offer email. It will re-generate every
    time.
    ## Use `send-offer` to send email to respective client. It is deprecated
    as `send` API is available from Letters API.
    ## Use `download` API to download the email in pdf format. It is
    deprecated as `download` is available in letters API.
    """
    queryset = PreEmployment.objects.all()
    serializer_class = PreEmploymentSerializer
    filter_backends = (
        filters.SearchFilter, OrderingFilterMap, FilterMapBackend
    )
    permission_classes = [OnBoardingPermission]
    ordering_fields_map = dict(
        full_name='full_name',
        email='email',
        date_of_join='date_of_join',
        deadline='deadline',
        status='template_letter__status',
        modified_at='modified_at',
    )
    search_fields = (
        'full_name',
    )

    filter_map = {
        'deleted': 'is_deleted'
    }

    def filter_queryset(self, queryset):
        deleted = self.request.query_params.get('deleted') or False
        is_deleted = True if deleted == 'true' else False
        fil = {
            PreEmployment: {
                'is_deleted': is_deleted
            },
            TaskTemplateMapping: {
            },
        }.get(queryset.model)
        return super().filter_queryset(queryset).filter(**fil)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx.update({
            'letter_type': ONBOARDING
        })
        return ctx

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        letter_status = nested_getattr(
            obj,
            'generated_letter.status'
        )
        if letter_status not in [None, NOT_SENT, EXPIRED]:
            # The trouble is checked for a proper validation message.
            if letter_status == ACCEPTED:
                pre_employment_status = 'Accepted'
                pre_status = obj.pre_task_status
                if pre_status == 'Completed':
                    post_status = obj.post_task_status
                    if post_status == 'Completed':
                        pre_employment_status = 'Completed'
                    else:
                        pre_employment_status = 'In Progress'
            else:
                pre_employment_status = obj.generated_letter.get_status_display(
                )
            raise ValidationError({
                'error': [
                    f'The '
                    f'{pre_employment_status.lower()} '
                    f'pre-employment cannot be deleted'
                ]
            })
        obj.is_deleted = True
        obj.save()
        return Response({
            'message': 'Pre Employment has been successfully deleted.'
        }, status=HTTP_204_NO_CONTENT)

    @action(methods=['GET', 'POST'], detail=True, serializer_class=DummySerializer)
    def generate(self, request, *args, **kwargs):
        instance = self.get_object()
        template = instance.template_letter
        if not template:
            raise ValidationError({
                "message": "The user is not assigned a template. Please assign."
            })
        generated_letter = instance.generated_letter
        if request.method == 'GET':
            if generated_letter:
                return Response(
                    GeneratedLetterSerializer(
                        instance=generated_letter
                    ).data
                )
            else:
                raise ValidationError({
                    "message": "The letter has not been generated."
                })
        else:
            raise_if_hold(instance)
            if generated_letter:
                raise ValidationError({
                    "message": "The letter has already been generated."
                })
            uri = uuid.uuid4().hex + uuid.uuid4().hex[::-1]
            generated_letter = GeneratedLetter.objects.create(
                pre_employment=instance,
                letter_template=template,
                email=instance.email,
                message='EMPTY',
                # create with empty, and fill the message later
                uri=uri
            )
            message_content = generate_offer_letter(
                instance, template, uri, generated_instance=generated_letter
            )
            generated_letter.message = message_content
            generated_letter.save(update_fields=['message'])
            instance.generated_letter = generated_letter
            instance.save()
            return Response(
                GeneratedLetterSerializer(
                    instance=generated_letter
                ).data
            )

    @action(methods=['POST'], detail=True, url_path='send-offer')
    def send_offer(self, request, *args, **kwargs):
        pre_employment = self.get_object()
        raise_if_hold(pre_employment)
        generated_letter = pre_employment.generated_letter
        if pre_employment.deadline < now():
            raise ValidationError({
                'message': 'The offer has expired.'
            })
        if generated_letter:
            if not pre_employment.email:
                raise ValidationError({
                    'error': 'The on boarding does not have an assigned email.'
                })
            if generated_letter.status in [NOT_SENT, FAILED, SENT]:
                async_task(
                    send_mail,
                    'Offer Letter',
                    pre_employment.generated_letter.message,
                    INFO_EMAIL,
                    [pre_employment.email],
                    html_message=pre_employment.generated_letter.message,
                )
                generated_letter.status = SENT
                generated_letter.history.create(status=SENT)
                generated_letter.save()
            else:
                raise ValidationError({
                    'message': f'{generated_letter.get_status_display()} '
                               f'offer letter cannot be sent.'
                })
        else:
            raise ValidationError({
                'message': 'Please generate the letter before sending.'
            })
        return Response({
            'message': 'Email was sent successfully.'
        })

    @action(methods=['POST'], detail=True)
    def download(self, request, *args, **kwargs):
        # Create a Django response object, and specify content_type as pdf
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = (
            'attachment; '
            + 'filename="{}"'.format(uuid.uuid4().hex + '.pdf')
        )
        # Render the template.
        instance = self.get_object().generated_letter
        if not instance:
            return HttpResponse(
                'The offer letter has not yet been generated.',
                status=400
            )
        html = instance.message  # html from WYSIWYG

        # [HRIS-1446] #6 [500 Error during Letter Download]
        # TypeError: int() argument must be a string, a bytes-like object or a number, not 'tuple'
        # The issue is caused by 'letter-spacing' kept by Trumbowyg.
        # For now, removing letter-spacing before the message is converted into PDF.
        clean_html = cleaner.clean_html(
            re.sub(r'letter-spacing: [0-9.(px);]+', '', html)
        )

        # PDF Creation
        pisa_status = pisa.CreatePDF(
            clean_html,
            dest=response,
            link_callback=super().link_callback
        )
        if pisa_status.err:
            return HttpResponse(
                'We had some errors <pre>' + html + '</pre>')
        instance.history.create(status=DOWNLOADED)
        return response

    @action(methods=['POST'], detail=True,
            url_path=r'letter/(?P<action>(accept|decline))',
            serializer_class=DummySerializer)
    def perform_letter(self, *args, **kwargs):
        pre_employment = self.get_object()
        raise_if_hold(pre_employment)
        if pre_employment.deadline < now():
            raise ValidationError({
                'message': 'The offer has expired.'
            })
        generated_letter = pre_employment.generated_letter
        if generated_letter:
            new_status = {
                'accept': ACCEPTED,
                'decline': DECLINED,
            }.get(kwargs.get('action').lower())
            if generated_letter.status == new_status:
                raise ValidationError({
                    'message': f'This offer has already been {new_status}'
                })
            generated_letter.status = new_status
            generated_letter.save(update_fields=['status'])
            generated_letter.history.create(status=new_status)
            return Response({
                'message': f'This offer has successfully been {new_status}'
            })
        raise ValidationError({
            'message': 'Please generate the letter before performing action.'
        })

    @action(
        detail=True,
        url_path='letters',
        methods=['GET', 'POST'],
        serializer_class=GenerateLetterSerializer
    )
    def letters(self, request, **kwargs):
        obj = self.get_object()
        if request.method == 'POST':
            raise_if_hold(obj)
            if not obj.employee:
                raise ValidationError(
                    "Please assign a user before generating letters."
                )
        return super().letters(request, **kwargs)


class LetterTemplateView(
    LetterGenerateMixin,
    OrganizationCommonsMixin,
    OrganizationMixin,
    ModelViewSet
):
    queryset = LetterTemplate.objects.all()
    serializer_class = LetterTemplateSerializer
    permission_classes = [LetterTemplatePermission]
    filter_backends = (
        filters.SearchFilter, filters.OrderingFilter, FilterMapBackend
    )
    filter_map = {
        'type': 'type'
    }
    lookup_field = 'slug'
    ordering_fields = (
        'title', 'modified_at', 'type',
    )

    def get_queryset(self):
        if self.action == 'generate':
            return super().get_queryset().exclude(type=OFFER_LETTER)
        return super().get_queryset()

    @action(detail=False)
    def hints(self, request, **kwargs):
        hints = {
            'offer': OFFER_LETTER_LETTER_PARAMS,
            'on': ONBOARDING_LETTER_PARAMS,
            'off': OFFBOARDING_LETTER_PARAMS,
            'change': CHANGE_TYPE_LETTER_PARAMS,
            'custom': CUSTOM_LETTER_PARAMS,
        }
        return Response(hints.get(
            self.request.query_params.get('letter_type')
        ))

    @action(detail=True, methods=['post'])
    def generate(self, request, **kwargs):
        letter_template = self.get_object()

        user = request.data.get('user')
        user_experience = request.data.get('experience')

        if user and str(user).isdigit():
            user = drf_get_object_or_404(get_user_model(), id=user)
        else:
            raise ValidationError({'user': 'User must be provided'})

        user_organization = user.detail.organization
        if user_organization != self.organization:
            self.permission_denied(
                request,
                "User Latest Organization doesn't match with this organization"
            )

        if letter_template.type == CUSTOM:
            old_exists = GeneratedLetter.objects.filter(
                employee=user,
                letter_template=letter_template,
            ).first()
            if old_exists:
                raise ValidationError({
                    'errors': 'Letter from this template has already been generated for this user.'
                })
            letter = GeneratedLetter.objects.create(
                employee=user,
                letter_template=letter_template,
                email=user.email,
                message=generate_custom_letter_message(letter_template, user),
            )
            return Response(GeneratedLetterSerializer(instance=letter).data)

        if letter_template.type == CHANGE_TYPE:
            if user_experience:
                user_experience = drf_get_object_or_404(
                    UserExperience,
                    user=user,
                    id=user_experience
                )
            else:
                raise ValidationError({'experience': 'User Experience must be provided'})

        if letter_template.type == OFFBOARDING:
            obj = EmployeeSeparation.objects.exclude(status=STOPPED).filter(employee=user).first()
            if not obj:
                raise ValidationError(
                    {'message': 'Employee Separation has not been initialized or been Stopped for this User.'}
                )
        elif letter_template.type == ONBOARDING:
            obj = PreEmployment.objects.filter(employee=user).first()
            if not obj:
                raise ValidationError(
                    {'message': 'Pre-Employment has not been initialized or been Stopped for this User.'}
                )
        else:
            obj = EmploymentReview.objects.filter(
                employee=user, detail__new_experience=user_experience
            ).first()
            if not obj:
                raise ValidationError(
                    {'message': 'Employment Review has not been initialized or been Stopped for this User.'}
                )

        return self.generate_letter(
            request,
            obj=obj,
            data={'letter_template': letter_template.slug, 'employee': user.id},
            employee=UserThinSerializer(user).data
        )

    @action(
        detail=True, methods=['GET'], url_path='generated-letters',
        serializer_class=GeneratedLetterSerializer
    )
    def generated_letters(self, *args, **kwargs):
        letter_template = self.get_object()

        def get_qs(slf):
            return letter_template.generated_letters.all()

        self.get_queryset = types.MethodType(get_qs, self)
        self.filter_backends = []
        return super().list(*args, **kwargs)


class EmployeeLettersView(
    OnBoardingOffBoardingPermissionMixin,
    PDFExport, OrganizationMixin, ModelViewSet
):
    """
    All generated letters are available here.
    # Use `hints` API for what keywords will be translated.
    # Use `downloads` API for downloading the selected letter.
    # Use `send` API for sending the mail to respective recipient.
    # Use `save` API for saving the letter in `User's Document` section.

    """
    lookup_url_kwarg = 'pk'
    serializer_class = GeneratedLetterSerializer
    queryset = GeneratedLetter.objects.all()
    filter_backends = (FilterMapBackend, OrderingFilterMap)

    filter_map = {
        'letter_template': 'letter_template__slug',
        'status': 'status'
    }
    ordering_fields_map = {
        'created_at': 'created_at',
        'modified_at': 'modified_at',
        'employee': (
            'employee__first_name',
            'employee__middle_name',
            'employee__last_name'
        )
    }

    def get_queryset(self):
        return super().get_queryset().filter(
            letter_template__organization=self.organization
        )

    def filter_queryset(self, queryset):
        queryset = self.filter_queryset_by_permission(
            super().filter_queryset(queryset)
        )
        action_performed = GeneratedLetterHistory.objects.filter(
            letter=OuterRef('pk')
        ).only('pk')
        queryset = queryset.annotate(
            is_sent=Exists(
                action_performed.filter(status=SENT)
            ),
            is_downloaded=Exists(
                action_performed.filter(status=DOWNLOADED)
            ),
            is_saved=Exists(
                action_performed.filter(status=SAVED)
            )
        )

        employee = self.request.query_params.get('employee')
        if employee:
            queryset = queryset.filter(
                Q(employee=employee) |
                Q(pre_employment__employee=employee) |
                Q(employment_review__employee=employee) |
                Q(separation__employee=employee)
            )
        return queryset.select_related('letter_template', 'employee')

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed(method='post')

    def get_serializer(self, *args, **kwargs):
        if self.request.method.lower() in ['patch', 'put']:
            kwargs.update({
                'fields': ('message',)
            })
        return super().get_serializer(*args, **kwargs)

    @action(detail=True, methods=['POST'], serializer_class=DummySerializer)
    def regenerate(self, *args, **kwargs):
        letter_instance = self.get_object()
        letter_instance.regenerate()
        return Response(
            GeneratedLetterSerializer(
                letter_instance,
                context=self.get_serializer_context()
            ).data
        )

    @property
    def letter(self):
        return drf_get_object_or_404(self.get_queryset(), pk=self.kwargs.get('pk'))

    @action(methods=['GET'], detail=True, url_path='download')
    def download(self, request, *args, **kwargs):
        instance = self.letter
        template_path = "header_footer.html"
        # find the template and render it.
        template = get_template(template_path)

        organization = self.get_organization()
        # Cleaning the img tag
        clean_html_body = cleaner.clean_html(
            re.sub(r'letter-spacing: [0-9.(px);]+', '', instance.message)
        )
        default_logo = get_complete_url(
            'images/default/cover.png',
            att_type='static'
        )
        logo = nested_getattr(organization, 'appearance.logo')
        context = {
            "organization": organization,
            "logo": logo.url if logo else default_logo,
            "body": clean_html_body,
            "email": organization.email,
            "website": organization.website,
            "address": organization.address.address if hasattr(organization, 'address') else 'N/A',
            "contact": organization.contacts.get('Phone'),
            "created_at": get_today(with_time=True).strftime("%Y-%m-%d %I:%M:%S %p")
        }
        # html from template
        html = template.render(context)

        # Create a Django response object, and specify content_type as pdf
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = (
            'attachment; '
            + 'filename="{}"'.format(uuid.uuid4().hex + '.pdf')
        )
        # Render the template.
        if not instance:
            return HttpResponse(
                'The offer letter has not yet been generated.',
                status=400
            )

        # PDF Creation
        try:
            pisa.CreatePDF(
                html,
                dest=response,
                link_callback=super().link_callback
            )
        except Exception as e:
            logger.warning(
                'Create PDF failed as: ' + str(e)
            )
            raise ValidationError({
                'message': 'The letter could not be downloaded.'
            })
        if instance.status not in [ACCEPTED, DECLINED, EXPIRED]:
            instance.status = DOWNLOADED
            instance.save(update_fields=['status'])
        instance.history.create(
            status=DOWNLOADED
        )
        return response

    @action(methods=['POST'], detail=True)
    def send(self, request, *args, **kwargs):
        generated_letter = self.letter
        if generated_letter:
            title = 'Offer Letter' if getattr(
                generated_letter, 'preemployment', None
            ) else generated_letter.letter_template.title.title()
            if generated_letter.status not in [
                ACCEPTED, DECLINED
            ]:
                if not generated_letter.email:
                    raise ValidationError({
                        'email': 'The letter does not have an associated '
                                 'email.'
                    })
                async_task(
                    send_mail,
                    title,
                    generated_letter.message,
                    INFO_EMAIL,
                    [generated_letter.email],
                    html_message=generated_letter.message
                )
                generated_letter.status = SENT
                generated_letter.history.create(status=SENT)
                generated_letter.save()
            else:
                raise ValidationError({
                    'message':
                        f'{generated_letter.get_status_display().lower()} '
                        f'letter cannot be sent.'
                })
        else:
            raise ValidationError({
                'message': 'Please generate the letter before sending.'
            })
        return Response(
            "Email was sent successfully."
        )

    @transaction.atomic()
    @action(methods=['POST'], detail=True, serializer_class=DummySerializer)
    def save(self, request, *args, **kwargs):
        generated_letter = self.letter
        last_saved = generated_letter.history.filter(status=SAVED).first()
        if last_saved:
            raise ValidationError({
                'message': 'The letter has already been saved to user\'s '
                           f'document on '
                           f'{format_timezone(last_saved.created_at)}',
                'code': 'already-saved'
            })
        try:
            user = get_user_model().objects.get(
                email=generated_letter.email
            )
        except get_user_model().DoesNotExist:
            raise ValidationError(
                "The letter is not associated to any user."
            )
        file_root = f"uploads/{UserDocument.__name__.lower()}"
        directory = os.path.join(
            settings.MEDIA_ROOT,
            file_root
        )
        if not os.path.exists(directory):
            os.makedirs(directory)
        filename = uuid.uuid4().hex + '.pdf'
        file_path = os.path.join(
            directory,
            filename
        )
        file = default_storage.open(file_path, 'wb')
        try:
            clean_html = cleaner.clean_html(
                re.sub(r'letter-spacing: [0-9.(px);]+', '', generated_letter.message)
            )
            pisaDocument(
                clean_html.encode(),
                file
            )
        except:
            raise ValidationError(
                "Letter could not be saved."
            )
        file.close()
        doc_type, _ = DocumentCategory.objects.get_or_create(
            name=generated_letter.letter_template.get_type_display(),
        )
        UserDocument.objects.create(
            user=user,
            uploaded_by=request.user,
            title=generated_letter.letter_template.title,
            document_type=doc_type,
            file=os.path.join(file_root, filename)
        )
        generated_letter.status = SAVED
        generated_letter.save(update_fields=['status'])
        generated_letter.history.create(status=SAVED)
        return Response({
            'message': f'Document was saved to {user.full_name}\'s profile.'
        })

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        is_offer_letter = getattr(obj, 'preemployment', None)
        message = f"{obj.get_status_display().lower()} letter cannot be " \
                  f"deleted."
        if is_offer_letter:
            if obj.status in [ACCEPTED, DECLINED, EXPIRED]:
                raise ValidationError({
                    'error': message
                })
        else:
            if obj.history.filter(status=SAVED).exists():
                raise ValidationError({
                    'error': f'The saved document cannot be deleted.'
                })
        return super().destroy(request, *args, **kwargs)


class TaskAssignViewSet(
    OnBoardingOffBoardingPermissionMixin,
    OrganizationMixin,
    OrganizationCommonsMixin,
    ModelViewSet
):
    """
    Assign tasks to User here.
    Frontend will use the pre-populate the task assign page according to
    template.
    """
    serializer_class = TaskTemplateMappingSerializer

    def get_queryset(self):
        template_mapping = drf_get_object_or_404(
            self.filter_queryset_by_permission(TaskTracking.objects.all()),
            pk=self.kwargs.get('mapping_id')
        )
        return template_mapping.tasks.all()


class ChangeTypeView(OrganizationMixin,
                     OrganizationCommonsMixin,
                     ModelViewSet):
    """
    Create Change Type Title here.
    ## Example

    ```
        {
            "title": "Promotion of Programmer",
            "affects_experience": true,
            "affects_payroll": true,
            "affects_work_shift": true,
            "affects_core_tasks": true,
            "affects_leave_balance": true,
        }
    ```
    """
    permission_classes = [ChangeTypePermission]
    serializer_class = ChangeTypeSerializer
    queryset = ChangeType.objects.all()
    lookup_field = 'slug'
    filter_backends = (
        filters.SearchFilter, filters.OrderingFilter, FilterMapBackend
    )
    ordering_fields = (
        'title', 'modified_at', 'created_at'
    )
    search_fields = (
        'title',
    )

    def raise_if_assigned(self):
        obj = self.get_object()
        if obj.is_assigned:
            raise ValidationError(
                "This Change type is being used"
            )

    def update(self, request, *args, **kwargs):
        self.raise_if_assigned()
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self.raise_if_assigned()
        return super().destroy(request, *args, **kwargs)


class EmploymentReviewViewSet(
    PrePostTaskMixin, OrganizationMixin, ModelViewSet
):
    """
    Create Employment Review here.

    # Details are visible on `<id>/detail` page.
    # To Update the leave balance visit to `<id>/update-leave` page.
    """
    permission_classes = [EmploymentReviewPermission]
    serializer_class = EmploymentReviewSerializer
    queryset = EmploymentReview.objects.all()
    filter_backends = (
        filters.SearchFilter, OrderingFilterMap, FilterMapBackend
    )
    ordering_fields_map = {
        'full_name': (
            'employee__first_name', 'employee__middle_name',
            'employee__last_name'
        ),
        'effective_date': 'detail__new_experience__start_at',
        'change_type': 'change_type__title',
    }
    search_fields = (
        'employee__first_name', 'employee__middle_name', 'employee__last_name'
    )
    filter_map = {
        'type': 'change_type__slug'
    }

    @staticmethod
    def raise_if_hold(instance):
        if instance.status in [HOLD, STOPPED]:
            raise PermissionDenied(
                'Cannot perform this action because Employment review '
                f'is in {instance.get_status_display().lower()} state.'
            )

    def get_object(self):
        obj = super().get_object()
        if self.request.method in ('PUT', 'PATCH'):
            self.raise_if_hold(obj)
        return obj

    def get_queryset(self):
        return super().get_queryset().filter(
            employee__detail__organization=self.organization
        ).select_related(
            'employee__detail', 'employee__detail__organization',
            'employee__detail__division', 'employee__detail__job_title',
            'employee__detail__employment_level',
            'employee__detail__employment_status',
            'change_type', 'detail'
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx.update({
            'letter_type': CHANGE_TYPE,
            'organization': self.organization
        })
        return ctx

    @action(methods=['GET', 'PATCH'], detail=True, url_path='detail',
            serializer_class=EmployeeChangeTypeDetailSerializer)
    def view_detail(self, request, *args, **kwargs):
        self.__class__.__doc__ = """
        list:
        View the employment update details here.
        These data are pre-populated during the object creation
        ```
            {
                ## Old Experience
                ## Old Leave Balance
                ## Old Work Shift
                ## Old Payroll
            }
        ```

        update:

        1. Firstly, assign a new experience.
        2. Secondly, assign work_shift, payroll package.
        3. Head over to <pk>/update-leave to assign the new leave balances.
        """
        review = self.get_object()
        detail = review.detail
        if request.method == 'GET':
            return Response(EmployeeChangeTypeDetailSerializer(
                detail,
                context=self.get_serializer_context(),
            ).data)
        self.raise_if_hold(review)
        ser = EmployeeChangeTypeDetailSerializer(
            detail,
            context=self.get_serializer_context(),
            data=request.data
        )
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

    @action(
        methods=['GET'],
        detail=True,
        url_path='leaves',
        serializer_class=LeaveChangeTypeSerializer
    )
    def list_leaves(self, request, *args, **kwargs):
        self.__class__.__doc__ = """
        Set the values for updating the leave balance
        """
        obj = self.get_object()
        page = self.paginate_queryset(obj.detail.leave_changes.all())
        return self.get_paginated_response(
            LeaveChangeTypeSerializer(
                page, many=True,
                context=self.get_serializer_context(),
            ).data
        )

    @action(
        methods=['PUT'],
        detail=True,
        url_path='leaves/(?P<change_type_pk>\d+)',
        serializer_class=LeaveChangeTypeSerializer
    )
    def update_leaves(self, request, *args, **kwargs):
        self.__class__.__doc__ = """
        Set the values for updating the leave balance

        Use the following data for update:
        Directly send the list without any wraps.
        ```javascript
        [
            {
                "leave_type": 31,
                "balance": 0.0,
                "update_balance": null,
                "id": 17
            },
            .
            .
            .

        ]
        ```

        """
        obj = self.get_object()
        leave_change_type = drf_get_object_or_404(
            obj.detail.leave_changes,
            pk=kwargs.get('change_type_pk')
        )
        self.raise_if_hold(obj)
        ser = LeaveChangeTypeSerializer(
            instance=leave_change_type,
            data=request.data
        )
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

    @action(
        methods=['POST'],
        detail=True,
        url_path='copy-core-tasks'
    )
    def copy_core_task_from_old_experience_to_new(
        self, request, *args, **kwargs
    ):
        self.__class__.__doc__ = """
        Copy Core tasks from old experience to new.
        Must be of same division to copy the core tasks.
        Or else, disallowed
        """
        review = self.get_object()
        self.raise_if_hold(review)
        new_experience = review.detail.new_experience
        old_experience = review.detail.old_experience
        if not old_experience:
            raise ValidationError(
                "The user does not have an old experience. Copying Failed."
            )
        if not new_experience:
            raise ValidationError(
                "Please assign new experience. Copying Failed"
            )
        if new_experience.division != old_experience.division:
            raise ValidationError(
                "Copying core tasks between divisions is not permitted. "
                "Copying Failed"
            )
        if new_experience.user_result_areas.exists():
            raise ValidationError(
                "The user result has already been added."
            )
        user_result_areas = old_experience.user_result_areas.all()
        if not user_result_areas:
            raise ValidationError(
                "The experience has no result areas. Copying Failed."
            )
        copied_ura = copied_core_tasks = 0
        for user_result_area in user_result_areas:
            core_tasks = user_result_area.core_tasks.all()
            user_result_area.id = None
            user_result_area.user_experience = new_experience
            user_result_area.save()
            for core_task in core_tasks:
                copied_core_tasks += 1
                user_result_area.core_tasks.add(core_task)
            copied_ura += 1
        return Response({
            'Copied User Result Areas': copied_ura,
            'Copied Core Tasks': copied_ura,
        })

    @action(
        detail=True,
        url_path='letters',
        methods=['GET', 'POST'],
        serializer_class=GenerateLetterSerializer
    )
    def letters(self, request, **kwargs):
        obj = self.get_object()
        if request.method == 'POST':
            self.raise_if_hold(obj)
            if not obj.detail.new_experience:
                raise ValidationError(
                    "Assign new experience before generating letters."
                )
        return super().letters(request, **kwargs)

    @action(
        detail=True,
        url_path='assign-core-task',
        methods=['GET', 'POST'],
        serializer_class=UserResultAreaSerializer
    )
    def assign_core_tasks(self, request, *args, **kwargs):
        self.filter_map = dict()
        review = self.get_object()
        if request.method == 'GET':
            qs = get_user_model().objects.filter(
                pk=review.employee.id,
                detail__organization__slug=self.kwargs['organization_slug']
            ).select_related(
                'detail', 'detail__organization', 'detail__division',
                'detail__job_title', 'detail__employment_level',
                'detail__employment_status'
            ).prefetch_related(
                Prefetch(
                    'user_experiences',
                    queryset=UserExperience.objects.include_upcoming(
                    ).select_related(
                        'organization', 'job_title'
                    ).prefetch_related(
                        Prefetch(
                            'user_result_areas',
                            queryset=UserResultArea.objects.order_by(
                                'result_area__title'
                            ).prefetch_related(
                                Prefetch(
                                    'core_tasks',
                                    queryset=CoreTask.objects.order_by(
                                        'order'
                                    )
                                )
                            )
                        )
                    )
                )
            )
            page = self.paginate_queryset(qs)
            return self.get_paginated_response(
                UserResultAreaListSerializer(
                    page,
                    context=self.get_serializer_context(),
                    many=True
                ).data
            )
        else:
            self.raise_if_hold(review)
            ctx = self.get_serializer_context()
            if isinstance(request.data, list):
                ser = UserResultAreaSerializer(
                    data=request.data,
                    context=ctx,
                    many=True
                )
            else:
                ser = UserResultAreaSerializer(
                    data=request.data,
                    context=ctx,
                )
            ser.is_valid(raise_exception=True)
            ser.save()
            return Response(ser.data)


class EmployeeSeparationTypeView(
    OrganizationCommonsMixin, OrganizationMixin, ModelViewSet
):
    """
    Create Employee Separation Title here.
    ## Example
     ```
        {
            "title": "Resigned"
        }
    ```
    """
    permission_classes = [SeparationTypePermission]
    serializer_class = EmployeeSeparationTypeSerializer
    queryset = EmployeeSeparationType.objects.all()
    filter_backends = (
        filters.SearchFilter, filters.OrderingFilter, FilterMapBackend
    )
    lookup_field = 'slug'
    filter_map = {
        'category': 'category'
    }
    search_fields = (
        'title',
    )
    ordering_fields = (
        'title', 'modified_at'
    )

    def update(self, request, *args, **kwargs):
        if self.get_object().is_assigned:
            raise ValidationError(
                "Cannot update this separation type because it is being used."
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        destroying_object = self.get_object()
        if destroying_object.is_assigned:
            raise ValidationError(
                "Cannot delete this separation type because it is being used."
            )
        return super().destroy(request, *args, **kwargs)


class EmployeeSeparationView(
    PrePostTaskMixin, OrganizationMixin, ModelViewSet
):
    """
    Create the Employee Separation.

    ## The employee separations are visible on this page.
    ## The leaves, attendance details are visible on detail page.
    ## The tasks of the user are visible on `<id>/tasks` page.
    ## Pre-task is available on `<id>/pre-tasks` page
    ## Post-task is available on `<id>/post-tasks` page
    ## Letters are available on `<id>/letters` page

    ### Leave:

    On leave, these items are visible:
        1. rule__leave_type__name: Example: Sick Leave
        2. consumed: Consumed in this fiscal year.
        3. consumable: How much user could consume? Reverse proportionate.
    """
    serializer_class = EmployeeSeparationSerializer
    permission_classes = [OffBoardingPermission]
    queryset = EmployeeSeparation.objects.all()
    filter_backends = (
        filters.SearchFilter, OrderingFilterMap, FilterMapBackend
    )
    search_fields = (
        'employee__first_name', 'employee__middle_name', 'employee__last_name',
        'employee__username'
    )
    ordering_fields_map = {
        'full_name': (
            'employee__first_name', 'employee__middle_name',
            'employee__last_name'
        ),
        'parted_date': 'parted_date',
        'release_date': 'release_date',
        'separation_type': 'separation_type__slug'
    }
    filter_map = {
        'type': 'separation_type__slug',
        'username': 'employee__username',
    }

    def get_queryset(self):
        return super().get_queryset().filter(
            employee__detail__organization=self.organization
        ).select_related(
            'employee',
            'employee__detail',
            'employee__detail__division',
            'employee__detail__employment_level',
            'employee__detail__organization',
            'separation_type',
        )

    @action(methods=['GET'], detail=True, url_path='tasks')
    def tasks_list(self, request, *args, **kwargs):
        separation_object = self.get_object()
        if not separation_object.separation_type.display_pending_tasks:
            raise ValidationError(
                "Pending tasks are not available for this separation type"
            )
        qs = Task.objects.as_responsible(
            separation_object.employee
        ).filter(
            status__in=[PENDING, IN_PROGRESS]
        )
        page = self.paginate_queryset(qs)
        response = self.get_paginated_response(
            TaskSerializer(
                page, fields=[
                    'title', 'priority', 'deadline', 'status', 'created_by',
                    'id'
                ], context=self.get_serializer_context(), many=True
            ).data
        )
        return response

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx.update({
            'letter_type': OFFBOARDING,
            'organization': self.organization,
        })
        return ctx


    # Because the validation in Serializer is complicated, and shall take longer,
    # New API is opened for edit. Only `last_working_date` is allowed to be edited.
    @action(
        methods=['PUT'],
        detail=True,
        serializer_class=EmployeeSeparationEditSerializer
    )
    def edit(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status in [HOLD, STOPPED, HRIS_COMPLETED]:
            raise serializers.ValidationError(
                f'Can not update Employment Separation while it is in {instance.status} state.'
            )
        serializer = self.serializer_class(
            instance=instance,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class EmployeeSeparationLeaveViewSet(
    OrganizationMixin,
    ModelViewSet
):
    permission_classes = [OffBoardingPermission]
    queryset = LeaveAccount.objects.all()
    serializer_class = LeaveReportSerializer

    def has_user_permission(self):
        return False

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        separation = self.get_separation()
        if request.method.upper() in ['PUT', 'PATCH', 'DELETE']:
            if separation.status in [HOLD, STOPPED, HRIS_COMPLETED]:
                raise ValidationError({
                    'non_field_errors':
                        ['Can not update encashment balance while Employment Separation '
                         f'is in {separation.status} state.']
                })
            elif separation.release_date and separation.release_date <= get_today() and not settings.ROUND_LEAVE_BALANCE:
                raise ValidationError({
                    'non_field_errors': [
                        'Can not update encashment when last working date is in past.'
                        ' Details has been sent to leave encashment for processing.'
                    ]
                })

    def get_serializer_class(self):
        if self.request.method.upper() in ['PUT', 'PATCH']:
            return EmployeeSeparationLeaveEncashmentEditSerializer
        return super().get_serializer_class()

    def partial_update(self, request, *args, **kwargs):
        # run full update even on PATCH request
        return self.update(request, *args, **kwargs)

    def get_separation(self):
        return drf_get_object_or_404(
            EmployeeSeparation.objects.all(),
            employee__detail__organization=self.organization,
            id=self.kwargs.get('separation_id')
        )

    def get_queryset(self):
        queryset = super().get_queryset()

        fiscal = get_fiscal_year_for_leave(self.organization)
        if not fiscal:
            return queryset.none()
        release_date = self.get_separation().release_date
        fy_for_release_date = FiscalYear.objects.active_for_date(self.organization, release_date)
        return annotate_proportionate_carry_forward_used_edited_on_leave_accounts(
            queryset.filter(
                user_id=self.get_separation().employee_id,
                rule__is_paid=True,
                rule__leave_type__master_setting__in=MasterSetting.objects.filter(
                    organization=self.organization,
                ).get_between(fy_for_release_date.start_at, fy_for_release_date.end_at)
            ),
            fiscal,
            self.get_separation()
        ).filter(
            # active leave account or Edited Encashment
            Q(is_archived=False) | Q(encashment_edit__isnull=False)
        ).annotate(
            renew_balance=Case(
                When(
                    rule__renewal_rule__isnull=True,
                    then=None
                ),
                default=F(
                    'rule__renewal_rule__initial_balance'
                )
            ),
        )

    def perform_destroy(self, instance):
        # destroy seperation edits
        instance.encashment_edits_on_separation.filter(separation=self.get_separation()).delete()

    @action(methods=['GET'], detail=True,
            serializer_class=EmployeeSeparationLeaveEncashmentEditHistorySerializer)
    def history(self, *args, **kwargs):
        instance = self.get_object().encashment_edits_on_separation.filter(
            separation=self.get_separation()).first()

        def get_queryset():
            if instance:
                return instance.history.all()
            else:
                return LeaveEncashmentOnSeparationChangeHistory.objects.none()

        self.get_queryset = get_queryset
        return self.list(*args, **kwargs)
