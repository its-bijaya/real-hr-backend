from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Prefetch
from django.http import HttpResponseForbidden
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from irhrs.organization.models import Organization
from irhrs.permission.utils.base import ApplicationSettingsPermission
from irhrs.core.mixins.viewset_mixins import \
    ListCreateRetrieveUpdateViewSetMixin, ModeFilterQuerysetMixin, \
    WorkLogPermissionMixin
from irhrs.core.utils.filters import FilterMapBackend
from irhrs.users.models import UserDetail
from irhrs.worklog.api.v1.serializers.worklog import WorkLogSerializer, \
    WorkLogAttachmentSerializer, WorkLogCommentsSerializer
from irhrs.worklog.models import WorkLog
from rest_framework import status

from irhrs.worklog.models.worklog import WorkLogAttachment, WorkLogComment


class WorkLogOrganizationMixin:

    def organization_queryset(self):
        organization_base = Organization.objects.all()
        if self.user_mode == 'hr':
            return organization_base.filter(
                id__in=self.request.user.switchable_organizations_pks
            )
        if self.user_mode == 'supervisor':
            return organization_base.filter(
                id__in=UserDetail.objects.filter(
                    user_id__in={*self.request.user.subordinates_pks, self.request.user.id}
                ).values_list('organization_id', flat=True)
            )
        # Umm, we dont require organization for normal user mode.
        return organization_base.none()

    @property
    def user_mode(self):
        _as = self.request.query_params.get('as')
        return _as if _as in ['hr', 'supervisor'] else ''

    @property
    def organization_get_filter(self):
        return {
            'slug': self.request.query_params.get('organization')
        }

    @property
    def organization(self):
        return self.organization_queryset().filter(
            **self.organization_get_filter
        ).first()

    def get_organization(self):
        return self.organization


class WorkLogViewSet(
    WorkLogOrganizationMixin,
    ModeFilterQuerysetMixin,
    ListCreateRetrieveUpdateViewSetMixin
):
    """
        Create or Update:

              create work log for User [Can update until verified ]
                  {
                    date: TextField :Required
                    description :Required
                  }

              Review Work log for Supervisor [cannot update once set]
                  {
                    score: Integer :Required
                    score_remarks: TextField :Required
                  }

        Retrieve or List:

                Retrieve or List [attachments added on retrieve method]

                {
                    "id": 1,
                    "date": "1212-12-12",
                    "description": "hello world",
                    "score": 5,
                    "score_remarks": "5",
                    "verified_by": User Object,
                    "verified_at": "2019-07-03T19:28:47+05:45",
                    "attachments": [], :on retrieve only
                    "created_by": User Object,
                    "status": "pending" or "reviewed"
                }

        Create Attachments:

                Create a new attachments /work-log/:id/attachments/

                params:
                        attachment :file :required
                        description: TextField :required

        Create Comments:

                Create a new comment /work-log/:id/comments/

                params:
                        comment :TextField :required

        List Attachments:

                 Retrieve a work log to list attachments on work log

        Filter backends:

                Filter backend , Search backend , Ordering backend

                Filter_fields : [score,
                                date,
                                start_date,
                                end_date,
                                as :choices ["supervisor"]
                                created_by,
                                verified_by,
                                status :choices ["pending","reviewed"]]
                search_fields : [description]
                ordering_fields : [id,score,date]


    """
    serializer_class = WorkLogSerializer
    filter_backends = [FilterMapBackend, SearchFilter, OrderingFilter]
    permission_classes = [ApplicationSettingsPermission]
    queryset = WorkLog.objects.all()
    allow_supervisor_filter = True
    user_definition = 'created_by'
    search_fields = (
        "description",
        "created_by__first_name",
        "created_by__last_name",
        "date"
    )
    # To allow HR to view, place appropriate permission here.
    # permission_to_check = HRIS_PERMISSION
    ordering_fields = (
        'id',
        'date',
        'score',
    )
    filter_map = {
        'score': 'score',
        'date': 'date',
        'start_date': ('date', 'gte'),
        'end_date': ('date', 'lte'),
        'created_by': 'created_by',
        'verified_by': 'verified_by'
    }

    def get_queryset(self):
        active_users = set(
            get_user_model().objects.filter(
                user_experiences__is_current=True
            ).values_list('id', flat=True)
        )
        # filter active users only.
        return super().get_queryset().filter(
            created_by__in=active_users
        )

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        status = self.request.query_params.get('status')
        as_supervisor = self.request.query_params.get('as')
        organization = self.request.query_params.get('organization')
        if as_supervisor and organization:
            queryset = queryset.filter(created_by__detail__organization__slug=organization)
        if status == 'pending':
            queryset = queryset.filter(score__isnull=True)
        elif status == 'reviewed':
            queryset = queryset.filter(score__isnull=False)
        return queryset.select_related(
            'created_by',
            'created_by__detail',
            'created_by__detail__employment_level',
            'created_by__detail__job_title',
            'created_by__detail__organization',
            'created_by__detail__division',
            'verified_by',
            'verified_by__detail',
            'verified_by__detail__employment_level',
            'verified_by__detail__job_title',
            'verified_by__detail__organization',
            'verified_by__detail__division',
        ).prefetch_related(
            Prefetch(
                'worklog_attachments',
                queryset=WorkLogAttachment.objects.filter(),
                to_attr='_worklog_attachments'
            ),
            Prefetch(
                'worklog_comments',
                queryset=WorkLogComment.objects.filter(),
                to_attr='_worklog_comments'
            ),

        )

    def get_serializer(self, *args, **kwargs):
        if self.action in ['update', 'partial_update']:
            if self.request.query_params.get('as') == 'supervisor':
                allowed_fields = 'id', 'score', 'score_remarks',
            else:
                allowed_fields = 'id', 'date', 'description',
            kwargs['fields'] = allowed_fields
        elif self.action == 'list':
            kwargs['exclude_fields'] = 'attachments',
        elif self.action == 'create':
            allowed_fields = 'id', 'date', 'description',
            kwargs['fields'] = allowed_fields
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        serializer = self.serializer_class(page,
                                           many=True,
                                           context=self.get_serializer_context())
        resp = self.get_paginated_response(serializer.data)

        agg_data = self.get_queryset().aggregate(
            pending=Count('id', filter=Q(score__isnull=True)),
            reviewed=Count('id', filter=Q(score__isnull=False)),
            total_work_logs=Count('id')
        )
        resp.data.update({'statistics': agg_data})
        return resp

    def update(self, request, *args, **kwargs):
        log = self.get_object()
        if log.is_verified:
            return Response({'detail': 'You cannot update verified work logs'},
                            status=status.HTTP_400_BAD_REQUEST)
        if self.request.user not in (
                log.created_by.first_level_supervisor,
                log.created_by
        ):
            raise PermissionDenied(
                detail='You\'re not the immediate supervisor'
            )
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=['post'],
            serializer_class=WorkLogAttachmentSerializer)
    def attachments(self, request, pk):
        self.parser_classes = (MultiPartParser, FormParser,)
        work_log = self.get_object()
        if work_log.created_by != self.request.user:
            return Response(
                {'detail': 'You are not allowed to {} attachment'.format(
                    'post' if self.request.method.lower() == 'post' else 'delete')
                },
                status=status.HTTP_400_BAD_REQUEST)
        if work_log.is_verified:
            return Response(
                {'detail': 'Work log has already been verified'},
                status=status.HTTP_400_BAD_REQUEST
            )

        context = super().get_serializer_context()
        context['work_log'] = work_log
        serializer = self.serializer_class(data=self.request.data,
                                           context=context)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)
        return Response({'detail': 'Invalid Request'},
                        status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'],
            serializer_class=WorkLogCommentsSerializer)
    def comments(self, request, pk):
        work_log = self.get_object()
        context = super().get_serializer_context()
        context['work_log'] = work_log
        serializer = self.serializer_class(data=self.request.data,
                                           context=context)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)
        return Response({'detail': 'Invalid Request'},
                        status=status.HTTP_400_BAD_REQUEST)
