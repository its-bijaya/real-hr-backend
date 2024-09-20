import types

import dateutil.parser as date_parser
from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.db.models import (
    Q, Count, Prefetch,
    F, FloatField, Sum, Avg, Exists, OuterRef)
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from django_q.tasks import async_task
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import get_object_or_404 as drf_get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.viewset_mixins import (
    ListViewSetMixin,
    OrganizationMixin)
from irhrs.core.utils.common import get_today, validate_permissions
from irhrs.core.utils.filters import FilterMapBackend
from irhrs.hris.models import CoreTask, ResultArea
from irhrs.permission.constants.permissions import (
    TASK_PERMISSION,
    TASK_APPROVALS_PERMISSION,
    TASK_REPORT_PERMISSION,
    TASK_PROJECT_PERMISSION, TASK_READ_ONLY_PERMISSION)
from irhrs.permission.utils.base import ApplicationSettingsPermission
from irhrs.permission.permission_classes import permission_factory
from irhrs.task.api.v1.filters import TaskScoresAndCycleFilterSet
from irhrs.task.utils.task import recalculate_efficiency
from ..serializers.activity import TaskActivitySerializer
from ..serializers.association import (
    TaskAssociationSerializer,
    TaskVerificationScoreSerializer)
from ..serializers.most_efficient_taskers import MostEfficientTaskers
from ..serializers.most_unverified_task import MostUnverifiedTaskSerializer
from ..serializers.task import TaskSerializer, TaskApprovalSerializer, StopRecurringTaskSerializer
from ..serializers.task_leaderboard import TaskLeaderBoardSerializer
from ..serializers.top_assignee_assigners import TopAssigneeAssignerSerializer
from ..serializers.top_result_areas import (
    TopResultAreasForTask,
    ResultAreaWithCurrentExperienceSerializer)
from ....constants import (
    RESPONSIBLE_PERSON, COMPLETED, OBSERVER,
    PENDING, IN_PROGRESS, CLOSED, ON_HOLD, CRITICAL,
    MAJOR, MINOR, APPROVAL_PENDING,
    ACKNOWLEDGE_PENDING, NOT_ACKNOWLEDGED, ACKNOWLEDGED,
    APPROVED_BY_HR, FORWARDED_TO_HR, SCORE_NOT_PROVIDED)
from ....models import Task
from ....models.task import (
    TaskCheckList, TaskActivity, TaskAssociation,
    TaskVerificationScore, MAX_LIMIT_OF_TASK_SCORING_CYCLE)
from ....utils.clone import task_disassociate
from ....utils.dates import dates_for_efficiency_report


# TODO @Ravi: (Old To-Do: @shrawan Change this soon .)
# .copy() was accepted for django but for drf due to _request
# this way of implementation doesn't seem good
# The whole idea is to set default setting for Task as 'R'(Responsible).
# Enforce this from frontend, this util is longer required.
# Or, Evaluate things from view's property and not directly from self.request.query_params.
def modify_request_params(self, **kwargs):
    self.request._request.GET = self.request._request.GET.copy()
    for k, v in kwargs.items():
        self.request._request.GET[k] = v


class TaskSummaryViewSet(ListViewSetMixin):
    queryset = TaskAssociation.objects.all()

    @property
    def user(self):
        user = self.request.query_params.get('user')
        if not user:
            return self.request.user
        return drf_get_object_or_404(get_user_model(), pk=user)

    def list(self, request, *args, **kwargs):
        today = get_today()
        agg = Task.objects.base().aggregate(
            assigned_by_me=Count(
                'id',
                filter=Q(created_by=self.request.user),
                distinct=True
            ),
            assigned_by_me_recently=Count(
                'id',
                filter=Q(
                    created_by=self.request.user
                ) & Q(
                    created_at__date=today
                ),
                distinct=True
            ),
            observed_by_me=Count(
                'id',
                filter=Q(
                    task_associations__user=self.request.user
                ) & Q(
                    task_associations__association=OBSERVER
                )
            ),
            observed_by_me_recently=Count(
                'id',
                filter=Q(
                    task_associations__user=self.request.user
                ) & Q(
                    task_associations__association=OBSERVER
                ) & Q(
                    created_at__date=today
                )
            ),
            assigned_to_me=Count(
                'id',
                filter=Q(
                    task_associations__user=self.request.user
                ) & Q(
                    task_associations__association=RESPONSIBLE_PERSON
                )
            ),
            assigned_to_me_recently=Count(
                'id',
                filter=Q(
                    task_associations__user=self.request.user
                ) & Q(
                    task_associations__association=RESPONSIBLE_PERSON
                ) & Q(
                    created_at__date=today
                )
            ),
            efficiency=Avg('task_associations__efficiency',
                           filter=Q(
                               task_associations__efficiency__isnull=False
                           ) & Q(
                               task_associations__user=self.request.user
                           ) & Q(
                               task_associations__association=RESPONSIBLE_PERSON
                           ),
                           output_field=FloatField()
                           )
        )
        return Response(agg)


class TaskViewSet(ModelViewSet):
    """
    create:

        Create work shifts

            {
              "project": 0,             //ProjectID -> PrimaryKey
              "title": "First Task",        //Title of tasks
              "description": "description",
              "parent": 0,              // if is sub task ,parent is the taskID of parent
              "priority": "string",     //Default MINOR: ['TRIVIAL','MINOR','MAJOR','CRITICAL']
              "status": "string",       // [1,2,3,4,5] ==>[PENDING,IN PROGRESS,COMPLETED,CLOSED,ON HOLD]
              "deadline": "string[TS]",     //Deadline of task
              "starts_at": "string[TS]",     //starts_at of task
              "start": "string",        //start Time: Read Only
              "finish": "string",       //Finish Time: Read Only
              "changeable_deadline": true, //Responsible Person can change deadline
              "approve_required": true,    //Approve Task When Completed
              "check_lists": ['first','second',.....] //Works on POST only : lists of checklists
              "recurring": {'recurring_first_run':.., 'recurring_rule':...},
              "responsible_persons": [
                    {"user":ID,"core_tasks":[1,2,3,4]}, .......
              ],
              "observers": [
                    {"user":ID,"core_tasks":[1,2,3,4]}, .......
              ]
            }

    retrieve:

        Retrieve task from ID

    list:

        List All of mine tasks
        ```
        Available Filters :
            'status': [1,2,3,4,5] eg: status=1
            'priority': ['MINOR','MAJOR','CRITICAL'] eg: status=MINOR
            'assignee': members ID comma separated eg : assignee=UserID
            'approved': filters the completed tasks eg: approved=true
            'created_by': UserID eg:created_by = 1
            'only' : either parent or sub ie:only=parent
            'delayed': returns the delayed tasks
            'as' : ['all', 'creator', 'responsible', 'observer']
            'start_date':Date
            'end_date':Date
        ```
    """
    serializer_class = TaskSerializer
    http_method_names = [u'get', u'post', u'patch', u'delete', u'options']
    filter_backends = [SearchFilter, OrderingFilter, FilterMapBackend]
    search_fields = (
        "title",
        "description",
    )

    ordering_fields = (
        'id',
        'deadline',
    )
    filter_map = {
        'status': 'status',
        'priority': 'priority',
        'created_by': 'created_by',
        'created_at': 'created_at',
        'start_date': 'created_at__date__gte',
        'end_date': 'created_at__date__lte'
    }
    permission_classes = [permission_factory.build_permission(
        "TaskViewSetPermissions",
        actions={
            'overview': [
                TASK_PERMISSION,
                TASK_REPORT_PERMISSION
            ]
        }
    )]

    base_qs = Task.objects.base()

    def get_queryset(self):
        if self.action in ['retrieve', 'sub_tasks', 'activity',
                           'partial_update']:
            if validate_permissions(
                self.request.user.get_hrs_permissions(),
                TASK_APPROVALS_PERMISSION,
                TASK_REPORT_PERMISSION,
                TASK_APPROVALS_PERMISSION,
                TASK_PROJECT_PERMISSION,
            ):
                qs = Task.objects.base() | Task.objects.recurring(
                    self.request.user)
                if self.action == 'partial_update' and not validate_permissions(
                    self.request.user.get_hrs_permissions(),
                    TASK_APPROVALS_PERMISSION
                ):
                    return qs.none()
                return qs

            my_task = (Task.objects.my_tasks(
                self.request.user
            ) | Task.objects.recurring(self.request.user).distinct())
            my_subordinate_task = Task.objects.as_supervisor(
                self.request.user
            ).distinct()

            my_project_task = Task.objects.base().filter(
                project__user_activity_projects__user=self.request.user
            ).distinct()

            return (
                my_task | my_subordinate_task | my_project_task
            ).select_related(
                'created_by',
                'created_by__detail',
                'created_by__detail__division',
                'created_by__detail__organization',
            ).prefetch_related(
                Prefetch('task_checklists',
                         queryset=TaskCheckList.objects.select_related(
                             'created_by'))
            )

        _allowed = ['all', 'creator', 'responsible', 'observer']
        task_view = self.request.query_params.get('as', 'all')
        if task_view in _allowed:
            if task_view == 'all':
                return Task.objects.my_tasks(self.request.user)
            elif task_view == 'creator':
                return Task.objects.as_creator(self.request.user)
            elif task_view == 'responsible':
                return Task.objects.as_responsible(self.request.user)
            elif task_view == 'observer':
                return Task.objects.as_observer(self.request.user)
        else:
            return Task.objects.none()

    @property
    def task(self):
        return Task.objects.filter(
            deleted_at__isnull=True,
            created_by=self.request.user,
            id=self.kwargs.get('pk')
        ).first()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.action == 'stop_recurring_task' or self.request.method.lower() in ['put', 'patch']:
            context['task'] = self.task
        return context

    def filter_queryset(self, queryset):
        assignee = self.request.query_params.get("assignee")
        only = self.request.query_params.get("only")
        delayed = self.request.query_params.get("delayed")
        queryset = super().filter_queryset(queryset)
        if only:
            if only.lower() == 'parent':
                queryset = queryset.filter(parent__isnull=True)
            if only.lower() == 'sub':
                queryset = queryset.filter(parent__isnull=False)
        if assignee:
            try:
                assignee = int(assignee)
            except ValueError:
                pass
            else:
                queryset = queryset.filter(
                    task_associations__user_id=assignee,
                    task_associations__association=RESPONSIBLE_PERSON
                )
        if delayed:
            queryset = queryset.filter(approved=False,
                                       deadline__lte=timezone.now())
        return queryset

    def update(self, request, *args, **kwargs):
        """
        Update a task
            Responsible Person can update deadline and status if is allowed in task setting
            else only can update status
        """
        obj = self.get_object()
        if obj.freeze:
            return Response({'detail': 'Is undergoing background process'},
                            status=status.HTTP_400_BAD_REQUEST)
        if obj.approved:
            return Response({'detail': 'Cannot update approved task'},
                            status=status.HTTP_400_BAD_REQUEST)

        if obj.status not in [PENDING, IN_PROGRESS]:
            if obj.created_by == self.request.user:
                serializer = TaskSerializer(instance=obj, fields=['status'],
                                            data=request.data,
                                            context=self.get_serializer_context(),
                                            partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data)
            return Response({
                'detail': 'Can only edit when Task in Pending or In Progress'},
                status=status.HTTP_400_BAD_REQUEST)

        if obj.created_by == self.request.user:
            if obj.is_recurring:
                serializer = TaskSerializer(instance=obj,
                                            exclude_fields=['status'],
                                            data=request.data,
                                            context=self.get_serializer_context(),
                                            partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data)
            if obj.starts_at > timezone.now():
                serializer = TaskSerializer(instance=obj,
                                            exclude_fields=['status'],
                                            data=request.data,
                                            context=self.get_serializer_context(),
                                            partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data)
            return super().update(request, *args, **kwargs)

        if obj.task_associations.filter(user=self.request.user,
                                        association=RESPONSIBLE_PERSON
                                        ).exists() and not obj.is_recurring:

            if obj.starts_at > timezone.now():
                return Response({'detail': 'Task has not been started'},
                                status=status.HTTP_400_BAD_REQUEST)

            _allowed_fields = ['deadline',
                               'status'] if obj.changeable_deadline else [
                'status']
            serializer = TaskSerializer(instance=obj, fields=_allowed_fields,
                                        data=request.data,
                                        context=self.get_serializer_context(),
                                        partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        return Response(
            {'detail': 'You are not authorized to perform this action'},
            status=status.HTTP_403_FORBIDDEN)

    def perform_destroy(self, instance):
        # Soft delete the task
        # as Task as required for overall efficiency for the company
        instance.deleted_at = timezone.now()
        instance.save()

    def destroy(self, request, *args, **kwargs):
        # FOR NOW BLOCK THE REQUESTS
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        # """
        # Delete a task created by me
        # """
        # obj = self.get_object()
        # if obj.created_by == self.request.user:
        #     return super().destroy(request, *args, **kwargs)
        # # Probably raising the 404 error would be good if someone is not
        # # authorized here but 403 would be fine for now
        # return Response(
        #     {'detail': 'You are not authorized to perform this action'},
        #     status=status.HTTP_403_FORBIDDEN)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        agg_data = self.get_queryset().aggregate(
            all_tasks=Count('id'),
            pending=Count('id', filter=Q(status=PENDING)),
            in_progress=Count('id', filter=Q(status=IN_PROGRESS)),
            closed=Count('id', filter=Q(status=CLOSED)),
            on_hold=Count('id', filter=Q(status=ON_HOLD)),
            completed=Count('id', filter=Q(status=COMPLETED)),
            delayed=Count('id', filter=Q(approved=False) & Q(
                deadline__lte=timezone.now())),
        )
        independent_agg_data = self.base_qs.aggregate(
            created=Count('id',
                          filter=Q(created_by=self.request.user),
                          distinct=True
                          ),
            observed=Count('id', filter=Q(
                task_associations__user=self.request.user
            ) & Q(
                task_associations__association=OBSERVER)
                           ),
            responsible=Count('id', filter=Q(
                task_associations__user=self.request.user) & Q(
                task_associations__association=RESPONSIBLE_PERSON))
        )
        page = self.paginate_queryset(queryset)
        _context = self.get_serializer_context()
        _context.update({'force_thin_view': True})
        fields = (
            'id', 'title', 'deadline', 'created_by',
            'responsible_persons', 'status', 'priority',
            'parent', 'is_delayed', 'can_view_parent_task'
        )
        serializer = TaskSerializer(page, many=True,
                                    fields=fields, context=_context)
        resp = self.get_paginated_response(serializer.data)
        resp.data.update({'summary': agg_data})
        resp.data['summary'].update(independent_agg_data)
        return resp

    @action(
        detail=False,
        url_path='approvals',
        filter_backends=[DjangoFilterBackend, SearchFilter],
        get_queryset=(lambda *x, **y: Task.objects.base()),
        search_fields=('title',),
        serializer_class=TaskApprovalSerializer
    )
    def pending_approvals(self, request):
        """
            list

                Lists all approval as filters [responsible, creator]
        """
        self.filterset_class = TaskScoresAndCycleFilterSet

        queryset = self.get_queryset()
        queryset = DjangoFilterBackend().filter_queryset(self.request, queryset, self)

        _allowed = ['creator', 'responsible']
        task_view = self.request.query_params.get('as')
        if task_view not in _allowed:
            return Response(
                {"detail": f"invalid filter field , as={task_view}"},
                status=status.HTTP_400_BAD_REQUEST)
        cycle_status = request.query_params.get('cycle_status')
        fil_status = dict()
        if cycle_status:
            fil_status.update({'task_associations__cycle_status': cycle_status})

        fil = dict(
            status=COMPLETED,
            task_associations__association=RESPONSIBLE_PERSON
        )
        _fields = ['id', 'title', 'responsible_persons',
                   'approved']
        if task_view == 'responsible':
            _fields.append('created_by')
            fil.update({
                'task_associations__user': self.request.user,
            })
        else:
            fil.update({
                'created_by': self.request.user
            })

        qs = queryset.filter(
            **fil, **fil_status
        ).select_related(
            'created_by', 'created_by__detail',
            'created_by__detail__organization',
            'created_by__detail__job_title'
        ).order_by('-modified_at')
        # Patch request params
        modify_request_params(self, associations='R')
        stats = Task.objects.base().filter(
            **fil
        ).distinct().aggregate(
            all=Count(
                'id',
                distinct=True
            ),
            approval_pending=Count(
                'id',
                filter=Q(task_associations__cycle_status=APPROVAL_PENDING),
                distinct=True
            ),
            acknowledge_pending=Count(
                'id',
                filter=Q(task_associations__cycle_status=ACKNOWLEDGE_PENDING),
                distinct=True
            ),
            not_acknowledged=Count(
                'id',
                filter=Q(task_associations__cycle_status=NOT_ACKNOWLEDGED),
                distinct=True
            ),
            acknowledged=Count(
                'id',
                filter=Q(task_associations__cycle_status=ACKNOWLEDGED),
                distinct=True
            ),
            approved_by_hr=Count(
                'id',
                filter=Q(task_associations__cycle_status=APPROVED_BY_HR),
                distinct=True
            ),
            forwarded_to_hr=Count(
                'id',
                filter=Q(task_associations__cycle_status=FORWARDED_TO_HR),
                distinct=True
            ),
            score_not_provided=Count(
                'id',
                filter=Q(task_associations__cycle_status=SCORE_NOT_PROVIDED),
                distinct=True
            )
        )
        qs = qs.distinct()
        page = self.paginate_queryset(qs)
        serializer = self.serializer_class(
            page, many=True, fields=_fields,
            context=self.get_serializer_context()
        )
        _resp = self.get_paginated_response(serializer.data)
        _resp.data['_MAX_TASK_SCORING_CYCLE'] = MAX_LIMIT_OF_TASK_SCORING_CYCLE
        _resp.data['stats'] = {
            'All': stats['all'],
            APPROVAL_PENDING: stats['approval_pending'],
            ACKNOWLEDGE_PENDING: stats['acknowledge_pending'],
            NOT_ACKNOWLEDGED: stats['not_acknowledged'],
            ACKNOWLEDGED: stats['acknowledged'],
            APPROVED_BY_HR: stats['approved_by_hr'],
            FORWARDED_TO_HR: stats['forwarded_to_hr'],
            SCORE_NOT_PROVIDED: stats['score_not_provided'],
        }
        return _resp

    @action(detail=True, url_path=r'approvals/(?P<user_id>[\d]+)',
            serializer_class=TaskVerificationScoreSerializer)
    def pending_approvals_details(self, request, pk, user_id):
        task = self.get_object()
        if not (task.created_by == self.request.user or
                (task.task_associations.filter(
                    user=self.request.user, association=RESPONSIBLE_PERSON
                ).exists() and
                 self.request.user.id == int(user_id)
                )
        ):
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            qs = task.task_associations.get(user_id=user_id)
        except TaskAssociation.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = TaskAssociationSerializer(
            instance=qs, context=self.get_serializer_context()
        )
        data = serializer.data
        data.update(
            {'_MAX_TASK_SCORING_CYCLE': MAX_LIMIT_OF_TASK_SCORING_CYCLE}
        )
        return Response(data)

    @pending_approvals_details.mapping.post
    def pending_approval_verification(self, request, pk, user_id):
        # implement ways to send notification to the user
        task = self.get_object()
        if task.freeze:
            return Response({'detail': 'Is undergoing background process'},
                            status=status.HTTP_400_BAD_REQUEST)

        if not task.status == COMPLETED:
            return Response({'detail': 'Task has not been completed yet'},
                            status=status.HTTP_400_BAD_REQUEST)

        if task.created_by == self.request.user:
            if not task.task_associations.filter(
                user_id=user_id, association=RESPONSIBLE_PERSON
            ).exists():
                return Response(
                    {'detail': 'Invalid User as Responsible Person '},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if TaskVerificationScore.objects.filter(
                association__task=task, association__user_id=user_id,
                ack=True).exists():
                return Response(
                    {'detail': 'Previous Score has already been acknowledged'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if TaskVerificationScore.objects.filter(
                association__task=task, association__user_id=user_id
            ).count() >= MAX_LIMIT_OF_TASK_SCORING_CYCLE:
                return Response(
                    {'detail': 'Maximum cycle limit reached'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if TaskVerificationScore.objects.filter(
                association__task=task, association__user_id=user_id,
                ack__isnull=True).exists():
                return Response(
                    {'detail': 'Previous Score has not been acknowledged'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = self.serializer_class(data=self.request.data,
                                               fields=('score', 'remarks'))
            if serializer.is_valid(raise_exception=True):
                TaskVerificationScore.objects.create(
                    association=task.task_associations.get(user_id=user_id),
                    score=serializer.data.get('score'),
                    remarks=serializer.data.get('remarks'),
                )

                # maybe we need to refactor this
                # currently if creator scores to any responsible person
                # then we are assuming the task has been approved
                if not task.approved:
                    task.approved = True
                    task.approved_at = timezone.now()
                    task.save(update_fields=['approved', 'approved_at'])

                return Response(serializer.data)

        elif task.task_associations.filter(
            user=self.request.user, association=RESPONSIBLE_PERSON
        ).exists():
            if not TaskVerificationScore.objects.filter(
                association__task=task,
                association__user=self.request.user,
                ack__isnull=True).exists():
                return Response(
                    {'detail': 'Doesn\'t have any pending acknowledgement'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = self.serializer_class(data=self.request.data,
                                               fields=('ack', 'ack_remarks'))
            if serializer.is_valid(raise_exception=True):
                _instance = TaskVerificationScore.objects.get(
                    association__task=task,
                    association__user=self.request.user,
                    ack__isnull=True
                )
                _instance.ack = serializer.data.get('ack')
                _instance.ack_remarks = serializer.data.get('ack_remarks')
                _instance.ack_at = timezone.now()
                _instance.save()

                if _instance.ack:
                    recalculate_efficiency(task, self.request.user, _instance)

                return Response(serializer.data)

        return Response(status=status.HTTP_404_NOT_FOUND)

    @action(detail=False)
    def thin(self, request):
        """
        Returns /api/v1/tasks/thin with limited fields useful for Kanban Board without pagination
        """
        qs = Task.objects.base().filter(
            task_associations__user=self.request.user,
            status__in=[PENDING, IN_PROGRESS, COMPLETED],
            task_associations__association__in=[
                RESPONSIBLE_PERSON],
            approved=False)
        # Its fine to send the delayed task to the kanban board .
        #     .exclude(
        #     deadline__lte=timezone.now()
        # )
        _context = self.get_serializer_context()
        _context.update({'force_thin_view': True})
        serializer = TaskSerializer(
            fields=(
                'id', 'title', 'status', 'priority', 'responsible_persons',
                'task_completion_percentage',
                'deadline', 'parent', 'created_by', 'is_delayed', 'created_at'),
            instance=qs,
            many=True, context=_context)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='sub-tasks')
    def sub_tasks(self, request, pk=None):
        """
        Sub-tasks for the given taskID
        """
        obj = drf_get_object_or_404(self.get_queryset(), **{'pk': pk})
        qs = self.get_queryset().filter(parent=obj)
        qs = self.filter_queryset(qs)
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['get'])
    def activity(self, request, pk=None):
        """
        Status change activity log for task
        """
        obj = self.get_object()
        qs = obj.histories.all()
        page = self.paginate_queryset(qs)
        serializer = TaskActivitySerializer(instance=page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=['get'])
    def recurring(self, request, *args, **kwargs):
        """
        List of my recurring tasks
        """

        queryset = Task.objects.recurring(self.request.user)
        queryset = self.filter_queryset(queryset)
        fields = (
            'id', 'title', 'responsible_persons', 'priority',
            'recurring_task_queue', 'attachments_count', 'created_at'
        )
        page = self.paginate_queryset(queryset)
        _context = self.get_serializer_context()
        _context.update({'force_thin_view': True})
        serializer = TaskSerializer(page, many=True,
                                    fields=fields, context=_context)
        return self.get_paginated_response(serializer.data)

    @action(detail=False)
    def overview(self, request, *args, **kwargs):
        """
        Returns All Task independent of created_by and association
        """

        # Permission checked at :
        # irhrs/task/api/v1/permissions.py:4

        qs = self.base_qs

        def get_queryset(self):
            return qs

        self.get_queryset = types.MethodType(get_queryset, self)

        return self.list(request, request, *args, **kwargs)

    @action(detail=False)
    def subordinate(self, request, *args, **kwargs):
        """
        Returns All Task of the subordinate
        """
        qs = Task.objects.as_supervisor(self.request.user)
        select_related = [
            'created_by',
            'created_by__detail',
            'created_by__detail__division',
            'created_by__detail__organization',
        ]

        assigned_by_subordinates = Task.objects.base().filter(
            created_by_id__in=self.request.user.subordinates_pks
        ).select_related(*select_related)
        assigned_to_subordinates = Task.objects.base().filter(
            task_associations__user__in=self.request.user.subordinates_pks,
            task_associations__association=RESPONSIBLE_PERSON
        ).distinct().select_related(*select_related)
        subordinate_qs = {
            'assigned': assigned_by_subordinates,
            'assignee': assigned_to_subordinates
        }.get(
            self.request.query_params.get('subordinates'),
            qs
        )

        def get_queryset(self):
            return subordinate_qs

        self.get_queryset = types.MethodType(get_queryset, self)

        return self.list(request, request, *args, **kwargs)

    @action(detail=False, url_path='recent-activities', filter_backends=[])
    def recent_activities(self, request, pk=None):
        """
        Recent Activities for my task
        """
        task_list = list(self.get_queryset().values_list('id', flat=True))
        task_recent_activities = TaskActivity.objects.filter(
            task_id__in=task_list
        ).select_related('task', 'created_by', 'created_by__detail')
        page = self.paginate_queryset(task_recent_activities)
        serializer = TaskActivitySerializer(instance=page,
                                            many=True,
                                            fields=['key', 'description',
                                                    'created_by', 'created_at',
                                                    'task'])
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['POST'])
    def disassociate(self, request, pk):
        task = self.get_object()
        if task.created_by != self.request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if task.freeze:
            return Response({'detail': 'Is undergoing background process'},
                            status=status.HTTP_400_BAD_REQUEST)
        if task.approved:
            return Response({'detail': 'Approved Task cannot be disassociate'},
                            status=status.HTTP_400_BAD_REQUEST)
        if task.task_associations.filter(
            association=RESPONSIBLE_PERSON).count() <= 1:
            return Response({'detail': 'Multiple Responsible person is '
                                       'required for Disassociate Process'},
                            status=status.HTTP_400_BAD_REQUEST)
        async_task(task_disassociate, task)

        return Response(
            {'detail': 'Your request is being Processed in Background'})

    @action(
        detail=True,
        methods=['POST'],
        serializer_class=StopRecurringTaskSerializer,
        url_path='stop/recurring'
    )
    def stop_recurring_task(self, request, *args, **kwargs):
        serializer = StopRecurringTaskSerializer(
            data=request.data,
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        self.task.recurring_task_queue.filter(
            id__in=serializer.data.get('queued_task', [])
        ).delete()
        return Response(
            {
                'detail': 'Some of the recurring task has been removed from the queue.'
            },
            status=status.HTTP_204_NO_CONTENT
        )


class TaskListViewSetV2(ListViewSetMixin):
    """
        list:

            List All of mine tasks
            ```
            Available Filters :
                'status': [1,2,3,4,5] eg: status=1
                'priority': ['MINOR','MAJOR','CRITICAL'] eg: priority=MINOR
                'approved': filters the completed verified tasks eg: approved=true
                'created_at': date filter eg :2018-12-12
                'assignee': UserID eg:assignee = 1
                'assigner': UserID eg:assigner = 1
                'created' : date range ['year','month','week','yesterday','today']
                'pre_condition': ['pending','in_progress','completed','all','closed','on_hold']
                'post_condition': ['delayed','all','on_time']
                'as' : ['all', 'creator', 'responsible', 'observer']
                'recent': Boolean , returns the recent tasks within 7
                'start_date_from': date filter eg :2018-12-12
                'start_date_to': date filter eg :2018-12-12
                'finish_date_from': date filter eg :2018-12-12
                'finish_date_to': date filter eg :2018-12-12
            ```

    """
    serializer_class = TaskSerializer
    filter_backends = [FilterMapBackend, SearchFilter,
                       OrderingFilter]
    search_fields = (
        "title",
        "description",
    )

    ordering_fields = (
        'id',
        'title',
        'deadline',
        'created_at'
    )

    filter_map = {
        'status': 'status',
        'priority': 'priority',
        'created_by': 'created_by',
        'approved': 'approved',
        'created_at': 'created_at',
        'start_date_from': 'created_at__date__gte',
        'start_date_to': 'created_at__date__lte',
        'finish_date_from': 'finish__date__gte',
        'finish_date_to': 'finish__date__lte'
    }
    raise_filter_exception = True

    @staticmethod
    def _get_independent_agg_data(queryset):
        return queryset.aggregate(
            recent=Count('id',
                         filter=Q(created_at__date=timezone.now().date())),
            critical=Count('id', filter=Q(priority=CRITICAL)),
            major=Count('id', filter=Q(priority=MAJOR)),
            minor=Count('id', filter=Q(priority=MINOR)),
            all=Count('id'),
        )

    @staticmethod
    def _get_dependent_agg_data(queryset, q_deadline_condition):
        agg_data = queryset.aggregate(
            pending=Count('id', filter=Q(status=PENDING)),
            pending_delayed=Count('id', filter=(
                Q(status=PENDING) & q_deadline_condition)),
            in_progress=Count('id', filter=Q(status=IN_PROGRESS)),
            in_progress_delayed=Count('id',
                                      filter=(Q(
                                          status=IN_PROGRESS
                                      ) & q_deadline_condition)),
            completed=Count('id', filter=Q(status=COMPLETED)),
            completed_delayed=Count('id',
                                    filter=(Q(status=COMPLETED) & Q(
                                        deadline__lt=F('finish')))),
            closed=Count('id', filter=Q(status=CLOSED)),
            on_hold=Count('id', filter=Q(status=ON_HOLD)),
            all=Count('id'),
            all_delayed=Count('id', filter=q_deadline_condition),
        )
        summary_data = {}
        for summary_status in ['all', 'pending', 'in_progress', 'completed']:
            summary_data.update(
                {summary_status: {
                    'all': agg_data.get(summary_status),
                    'delayed': agg_data.get(f"{summary_status}_delayed"),
                    'on_time': agg_data.get(summary_status) - agg_data.get(
                        f"{summary_status}_delayed")
                }}
            )
        summary_data['closed'] = {
            'all': agg_data.get('closed'),
            'delayed': None,
            'on_time': None
        }
        summary_data['on_hold'] = {
            'all': agg_data.get('on_hold'),
            'delayed': None,
            'on_time': None
        }
        return summary_data

    def _get_task_results(self, queryset):
        page = self.paginate_queryset(queryset)
        _context = self.get_serializer_context()
        _context.update({'force_thin_view': True})
        fields = (
            'id', 'title', 'deadline', 'created_by', 'responsible_persons',
            'status', 'priority', 'parent', 'is_delayed', 'approved',
            'created_at', 'attachments_count', 'comments_count')

        serializer = TaskSerializer(page, many=True,
                                    fields=fields, context=_context)
        return serializer.data

    def _get_closed_and_hold_data(self, queryset):
        _STATUS_IN = Q(status__in=[CLOSED, ON_HOLD])
        agg_data = queryset.aggregate(
            created=Count('id',
                          filter=_STATUS_IN & Q(created_by=self.request.user),
                          distinct=True),
            created_closed=Count('id',
                                 filter=Q(created_by=self.request.user) &
                                        Q(status=CLOSED), distinct=True),
            responsible=Count('id', filter=_STATUS_IN & Q(
                task_associations__association=RESPONSIBLE_PERSON) & Q(
                task_associations__user=self.request.user),
                              distinct=True),
            responsible_closed=Count('id', filter=Q(status=CLOSED) & Q(
                task_associations__association=RESPONSIBLE_PERSON) & Q(
                task_associations__user=self.request.user),
                                     distinct=True
                                     ),
            observed=Count('id', filter=_STATUS_IN & Q(
                task_associations__association=OBSERVER) & Q(
                task_associations__user=self.request.user),
                           distinct=True),
            observed_closed=Count('id', filter=Q(status=CLOSED) & Q(
                task_associations__association=OBSERVER) & Q(
                task_associations__user=self.request.user),
                                  distinct=True
                                  )
        )
        closed_hold_data = {}
        for _status in ['created', 'responsible', 'observed']:
            closed_hold_data.update(
                {_status: {
                    'all': agg_data.get(_status),
                    'closed': agg_data.get(f"{_status}_closed"),
                    'on_hold': agg_data.get(_status) - agg_data.get(
                        f"{_status}_closed")
                }}
            )
        return closed_hold_data

    def _get_queryset_for_task_activities(self):
        task_list = list(self.get_queryset().values_list('id', flat=True))
        return TaskActivity.objects.filter(
            task_id__in=task_list
        ).select_related('task', 'created_by', 'created_by__detail')

    def _get_queryset_for_result_area_by_priority(self):
        if self.request.query_params.get('current_experience', 'false') == 'true':
            user_result_area = self.request.user.current_experience.user_result_areas \
                .all().values_list('result_area_id', flat=True)
            return ResultArea.objects.filter(id__in=user_result_area)

        return Task.objects.base().filter(
            task_associations__user=self.request.user,
            task_associations__association=RESPONSIBLE_PERSON
        ).values('task_associations__core_tasks__result_area'
                 ).annotate(
            result_area=F('task_associations__core_tasks__result_area__title'),
            result_area_id=F('task_associations__core_tasks__result_area'),
            total=Count('id', distinct=True),
            critical=Count('id', filter=Q(priority=CRITICAL), distinct=True),
            major=Count('id', filter=Q(priority=MAJOR), distinct=True),
            minor=Count('id', filter=Q(priority=MINOR), distinct=True)
        ).order_by('-critical')

    def _get_queryset_for_top_task_assignee(self):
        return TaskAssociation.objects.filter(
            created_by=self.request.user,
            association=RESPONSIBLE_PERSON
        ).values('user').annotate(
            total_assigned=Count('task', distinct=True)).order_by(
            '-total_assigned')

    def _get_queryset_got_top_task_assigner(self):
        _allowed = ['responsible', 'observer']
        viewing_as = self.request.query_params.get('as', '')
        _filter = {
            'association': RESPONSIBLE_PERSON if
            viewing_as[0] == 'r' else
            OBSERVER
        } if viewing_as in _allowed else {}
        return TaskAssociation.objects.filter(
            user=self.request.user,
            **_filter
        ).values('created_by').annotate(
            total_assigned=Count('task', distinct=True),
            user=F('created_by')
        ).order_by('-total_assigned')

    def get_queryset(self):
        mode = self.request.query_params.get('as', 'all')
        user = self.request.user

        if mode == 'hr' and validate_permissions(
            user.get_hrs_permissions(),
            TASK_PERMISSION
        ):
            return Task.objects.base()

        queryset_method = {
            'all': Task.objects.my_tasks,
            'creator': Task.objects.as_creator,
            'responsible': Task.objects.as_responsible,
            'observer': Task.objects.as_observer
        }.get(mode)
        return queryset_method(user) if queryset_method else Task.objects.none()
 
    def filter_queryset(self, queryset):
        recent = self.request.query_params.get("recent")
        assignee = self.request.query_params.get("assignee")
        assigner = self.request.query_params.get("assigner")
        result_area = self.request.query_params.getlist("result_area")
        queryset = super().filter_queryset(queryset)
        if recent in ['true', 'True', 'TRUE']:
            queryset = queryset.filter(created_at__date=timezone.now().date())
        if assignee or assigner:
            try:
                assignee = int(assignee) if assignee else None
                assigner = int(assigner) if assigner else None
            except ValueError:
                assigner = None
                assignee = None
        if assignee:
            queryset = queryset.filter(
                task_associations__user_id=assignee,
                task_associations__association=RESPONSIBLE_PERSON
            )
        if assigner:
            queryset = queryset.filter(created_by_id=assigner)

        if result_area:
            try:
                core_tasks = CoreTask.objects.filter(
                    result_area_id__in=result_area)
                queryset = queryset.filter(
                    task_associations__core_tasks__in=core_tasks)
            except (TypeError, ValueError):
                pass
        return queryset.distinct()

    def list(self, request, *args, **kwargs):
        show_info = kwargs.get('show_info', True)
        show_summary = kwargs.get('show_summary', True)
        show_results = kwargs.get('show_results', True)
        show_closed_and_hold = kwargs.get('show_closed_and_hold', False)

        # ALERT : This may reveal sensitive data
        show_closed_and_hold_hr = kwargs.get('hr_view', False)
        show_closed_and_hold_supervisor = kwargs.get('supervisor_view', False)
        _Q_DEADLINE_CONDITION = Q(deadline__lte=timezone.now())

        queryset = self.filter_queryset(self.get_queryset())

        independent_agg_data = {}
        if show_info:
            independent_agg_data = self._get_independent_agg_data(
                self.get_queryset()
            )
        closed_and_hold_data = {}
        if show_closed_and_hold:
            start_date = self.request.query_params.get('start_date')
            end_date = self.request.query_params.get('end_date')
            fil = {}
            if start_date and end_date:
                fil.update(
                    {
                        'created_at__date__gte': start_date,
                        'created_at__date__lte': end_date
                    }
                )
            if show_closed_and_hold_hr:
                closed_and_hold_data = Task.objects.base().filter(
                    **fil
                ).aggregate(
                    closed=Count('id', filter=Q(status=CLOSED)),
                    on_hold=Count('id', filter=Q(status=ON_HOLD)),
                )
            elif show_closed_and_hold_supervisor:
                closed_and_hold_data = Task.objects.as_supervisor(
                    self.request.user).filter(
                    **fil
                ).aggregate(
                    closed=Count('id', filter=Q(status=CLOSED)),
                    on_hold=Count('id', filter=Q(status=ON_HOLD)),
                )
            else:
                closed_and_hold_data = self._get_closed_and_hold_data(
                    Task.objects.my_tasks(self.request.user)
                )

        summary_data = {}
        if show_summary:
            summary_data = self._get_dependent_agg_data(queryset,
                                                        _Q_DEADLINE_CONDITION)

        ser_data = []
        if show_results:
            # Filters are placed here since required a/c to requirement
            if not show_closed_and_hold:
                pre_condition = self.request.query_params.get("pre_condition",
                                                              'all')
                post_condition = self.request.query_params.get(
                    "post_condition",
                    'all')
                if pre_condition in ['pending', 'in_progress', 'completed',
                                     'all']:
                    if pre_condition == 'pending':
                        queryset = queryset.filter(status=PENDING)
                    elif pre_condition == 'in_progress':
                        queryset = queryset.filter(status=IN_PROGRESS)
                    elif pre_condition == 'completed':
                        queryset = queryset.filter(status=COMPLETED)
                    # else:
                    #     queryset = queryset
                if post_condition in ['delayed', 'on_time', 'all']:
                    if post_condition == 'delayed':
                        if pre_condition == 'completed':
                            queryset = queryset.filter(
                                deadline__lt=F('finish'))
                        else:
                            queryset = queryset.filter(
                                deadline__lte=timezone.now())
                    elif post_condition == 'on_time':
                        if pre_condition == 'completed':
                            queryset = queryset.filter(
                                deadline__gt=F('finish'))
                        else:
                            queryset = queryset.filter(
                                deadline__gte=timezone.now())
                    # else:
                    #     queryset = queryset
            else:
                queryset = queryset.filter(status__in=[CLOSED, ON_HOLD])
            ser_data = self._get_task_results(queryset)

        resp = self.get_paginated_response(
            ser_data) if show_results else Response()
        if not resp.data:
            resp.data = {}
        resp.data.update({'info': independent_agg_data}) if \
            independent_agg_data else None
        resp.data.update({'summary': summary_data}) if summary_data else None
        resp.data.update(
            {'closed_and_hold': closed_and_hold_data}
        ) if closed_and_hold_data else None
        return resp

    def modified_list(self, distinct=False):
        queryset = super().filter_queryset(self.get_queryset())
        if distinct:
            queryset = queryset.distinct()
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False,
            filter_backends=[OrderingFilter, FilterMapBackend],
            serializer_class=TaskActivitySerializer,
            filter_map={
                'start_date': 'task__created_at__date__gte',
                'end_date': 'task__created_at__date__lte'
            })
    def activities(self, request):
        """
            get:

                List of activities from Task
                filters:
                       start_date : Date
                       end_date: Date

        """
        task_recent_activities = self._get_queryset_for_task_activities()

        def get_queryset(self):
            return task_recent_activities

        self.get_queryset = types.MethodType(get_queryset, self)
        return self.modified_list()

    @action(detail=False, url_path='top-assignee',
            filter_backends=[OrderingFilter, FilterMapBackend],
            serializer_class=TopAssigneeAssignerSerializer,
            ordering_fields=('total_assigned',),
            filter_map={
                'start_date': 'task__created_at__date__gte',
                'end_date': 'task__created_at__date__lte'
            })
    def top_assignee(self, request):
        """
            get:

                List of Top Assignee
                filters:
                       start_date : Date
                       end_date: Date
                ordering:
                       total_assigned

        """

        def get_queryset(self):
            return self._get_queryset_for_top_task_assignee() if \
                self.request.query_params.get('start_date') and \
                self.request.query_params.get('end_date') else \
                TaskAssociation.objects.none()

        self.get_queryset = types.MethodType(get_queryset, self)
        return self.modified_list()

    @action(detail=False, url_path='top-assigner',
            filter_backends=[OrderingFilter, FilterMapBackend],
            ordering_fields=('total_assigned',),
            serializer_class=TopAssigneeAssignerSerializer,
            filter_map={
                'start_date': 'task__created_at__date__gte',
                'end_date': 'task__created_at__date__lte'
            })
    def top_assigner(self, request):
        """
            get:

                List of top assigner
                filters:
                       start_date : Date
                       end_date: Date
                ordering:
                       total_assigned

        """

        def get_queryset(self):
            return self._get_queryset_got_top_task_assigner() if \
                self.request.query_params.get('start_date') and \
                self.request.query_params.get('end_date') else \
                TaskAssociation.objects.none()

        self.get_queryset = types.MethodType(get_queryset, self)
        return self.modified_list()

    @action(detail=False, url_path='result-areas',
            ordering_fields=('total', 'critical', 'major', 'minor'),
            search_fields=("result_area",),
            serializer_class=TopResultAreasForTask)
    def result_area(self, request):
        # TODO @Ravi: Find and Resolve.
        # (Old TO-DO: @shrawan
        # A quick hack to filter data whose result area is null
        # need to find a cause and refactor this)
        ra_by_priority = self._get_queryset_for_result_area_by_priority()
        if self.request.query_params.get('current_experience', 'false') == 'true':
            page = self.paginate_queryset(ra_by_priority)
            serializer = ResultAreaWithCurrentExperienceSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        ra_by_priority = ra_by_priority.filter(
            result_area_id__isnull=False
        )
        task_according_to_result_areas = super().filter_queryset(
            ra_by_priority)
        page = self.paginate_queryset(task_according_to_result_areas)
        serializer = self.serializer_class(instance=page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False)
    def stat(self, request):
        """

        """
        current_date = timezone.now().date()
        start_of_current_month = current_date.replace(day=1)
        _STATUS__NOT_IN = ~Q(status__in=[CLOSED, ON_HOLD])
        agg_data = Task.objects.base().filter(
            starts_at__date__gte=start_of_current_month
        ).aggregate(
            assigned_by_me=Count('id', filter=(
                Q(created_by=self.request.user) & _STATUS__NOT_IN),
                                 distinct=True),
            assigned_to_me=Count('id', filter=(
                Q(task_associations__user=self.request.user) &
                Q(task_associations__association=RESPONSIBLE_PERSON) &
                _STATUS__NOT_IN
            ), distinct=True),
            observed=Count('id',
                           filter=(Q(
                               task_associations__user=self.request.user) &
                                   Q(
                                       task_associations__association=OBSERVER
                                   ) & _STATUS__NOT_IN
                                   ), distinct=True),
            recurring=Count('id', filter=Q(created_by=self.request.user,
                                           recurring_rule__isnull=False),
                            distinct=True),
            pending_approvals=Count('id',
                                    filter=Q(created_by=self.request.user,
                                             status=COMPLETED, approved=False),
                                    distinct=True)
        )
        agg_data.update(
            {
                '_condition': 'Task starts_at greater than or '
                              f'equals to {start_of_current_month}'
            }
        )
        return Response(agg_data)

    @action(detail=False, url_path='closed-hold')
    def extra_tasks(self, request):
        """
            get:

                List of closed and hold tasks
        """
        return self.list(request, show_info=False, show_summary=False,
                         show_closed_and_hold=True)

    @action(detail=False)
    def efficiency(self, request):
        """
            get:

                Available Filters
                start_date: Date: eg 2019-01-01
                end_date: Date: eg 2019-10-10
                condition: [yearly, daily, monthly]
        """
        condition = self.request.query_params.get('condition', 'daily')
        if condition not in ['daily', 'monthly', 'yearly']:
            return Response({'detail': 'Condition is required'})
        try:
            start = date_parser.parse(
                self.request.query_params.get('start_date')
            )
            end = date_parser.parse(
                self.request.query_params.get('end_date')
            )
        except (TypeError, ValueError):
            days_deduction = relativedelta(
                days=6) if condition == 'daily' else relativedelta(months=11) \
                if condition == 'monthly' else relativedelta(years=5)
            start = timezone.now() - days_deduction
            end = timezone.now()
        # lets not raise the validation everywhere
        if start > end:
            start, end = end, start
        data = dates_for_efficiency_report(start, end, condition)
        qs = TaskAssociation.objects.filter(
            task__approved_at__date__gte=start.date(),
            task__approved_at__date__lte=end.date(),
            association=RESPONSIBLE_PERSON,
            user=self.request.user
        ).aggregate(**{
            i['var'].__str__(): Avg('efficiency', filter=Q(
                task__approved_at__date__gte=i['start_date'],
                task__approved_at__date__lte=i['end_date']),
                                    output_field=FloatField())
            for i in data
        }, avg_efficiency=Avg(
            'efficiency',
            output_field=FloatField()
        ))
        for _d in data:
            _d['efficiency'] = qs.get(_d['var'].__str__())
        _data = dict(
            remarks=dict(
                condition=condition,
                start=start.date(),
                end=end.date()
            ),
            average_efficiency=qs.get('avg_efficiency'),
            highest_efficiency=max(
                filter(lambda x: bool(x['efficiency']), data),
                key=lambda x: x['efficiency']
            ) if list(filter(lambda x: bool(x['efficiency']), data)) else None,
            lowest_efficiency=min(
                filter(lambda x: bool(x['efficiency']), data),
                key=lambda x: x['efficiency']
            ) if len(list(
                filter(lambda x: bool(x['efficiency']), data))) else None,
            results=sorted(data, key=lambda x: x['start_date']),
        )

        return Response(_data)


class TaskOverview(OrganizationMixin, TaskListViewSetV2):
    """"""

    def _get_verified_role(self):
        role = self.request.query_params.get("as", "HR")
        if role not in ['HR', 'supervisor']:
            role = 'HR'

        if role == 'HR' and validate_permissions(
            self.request.user.get_hrs_permissions(),
            TASK_PERMISSION,
            TASK_REPORT_PERMISSION,
            TASK_APPROVALS_PERMISSION
        ):
            return 'VHR'
        elif role == 'supervisor':
            return 'Vsupervisor'
        raise PermissionDenied

    def _get_role_view_(self):
        role = self._get_verified_role()
        if role == 'VHR':
            return {'hr_view': True}
        return {'supervisor_view': True}

    def _get_task_queryset(self):
        actor = self._get_verified_role()
        if actor == 'VHR':
            return Task.objects.base()
        qs = Task.objects.as_supervisor(self.request.user)
        return qs

    def _get_task_association_queryset(self):
        actor = self._get_verified_role()
        if actor == 'VHR':
            return TaskAssociation.objects.filter(
                task__deleted_at__isnull=True)
        return TaskAssociation.objects.filter(
            task__deleted_at__isnull=True,
            user_id__in=self.request.user.subordinates_pks
        )

    def _get_task_activity_queryset(self):
        actor = self._get_verified_role()
        if actor == 'VHR':
            return TaskActivity.objects.filter(
                task__deleted_at__isnull=True
            )
        return TaskActivity.objects.filter(
            task_id__in=list(self.get_queryset().values_list('id', flat=True))
        )

    def _get_queryset_for_task_activities(self):
        return self._get_task_activity_queryset().select_related(
            'task', 'created_by', 'created_by__detail'
        )

    def _get_queryset_for_top_task_assignee(self):
        return self._get_task_association_queryset().filter(
            task__deleted_at__isnull=True,
            association=RESPONSIBLE_PERSON
        ).values('user').annotate(
            total_assigned=Count('task', distinct=True)
        ).order_by('-total_assigned')

    def _get_queryset_got_top_task_assigner(self):
        return self._get_task_association_queryset().filter(
            association=RESPONSIBLE_PERSON
        ).values('created_by').annotate(
            total_assigned=Count('task', distinct=True),
            user=F('created_by')
        ).order_by('-total_assigned')

    def _get_queryset_for_result_area_by_priority(self):
        return self._get_task_queryset().filter(
            task_associations__association=RESPONSIBLE_PERSON
        ).values('task_associations__core_tasks__result_area'
                 ).annotate(
            result_area=F('task_associations__core_tasks__result_area__title'),
            result_area_id=F('task_associations__core_tasks__result_area'),
            total=Count('id', distinct=True),
            critical=Count('id', filter=Q(priority=CRITICAL), distinct=True),
            major=Count('id', filter=Q(priority=MAJOR), distinct=True),
            minor=Count('id', filter=Q(priority=MINOR), distinct=True)
        ).order_by('-critical')

    def get_queryset(self):
        return self._get_task_queryset()

    def list(self, request, *args, **kwargs):
        return super().list(request)

    @action(detail=False)
    def stat(self, request):
        """"""
        return Response({
            'detail': '/api/v1/task/overview/stat/ is deprecated ,'
                      'use /api/v1/task/overview/'},
            status=status.HTTP_410_GONE)

    @action(detail=False, url_path='leader-board',
            filter_backends=[OrderingFilter, FilterMapBackend],
            ordering_fields=('points',),
            serializer_class=TaskLeaderBoardSerializer,
            filter_map={
                'start_date': 'task__created_at__date__gte',
                'end_date': 'task__created_at__date__lte'
            })
    def task_leader_board(self, request):
        """"""
        task_leader_qs = self._get_task_association_queryset().filter(
            taskverificationscore__ack=True,
            association=RESPONSIBLE_PERSON,
            task__status=COMPLETED
        ).values('user').annotate(
            points=Sum(
                'taskverificationscore__score',
                filter=Q(taskverificationscore__ack=True)
            )
        ).order_by('-points')

        def get_queryset(self):
            return task_leader_qs if \
                self.request.query_params.get('start_date') and \
                self.request.query_params.get('end_date') else \
                TaskAssociation.objects.none()

        self.get_queryset = types.MethodType(get_queryset, self)
        return self.modified_list()

    # according to efficiency
    @action(detail=False, url_path='most-efficient',
            filter_backends=[OrderingFilter, FilterMapBackend],
            serializer_class=MostEfficientTaskers,
            ordering_fields=('total_efficiency',),
            filter_map={
                'start_date': 'task__created_at__date__gte',
                'end_date': 'task__created_at__date__lte'
            })
    def most_efficient(self, request):
        """"""
        most_efficient_qs = self._get_task_association_queryset().filter(
            taskverificationscore__ack=True,
            association=RESPONSIBLE_PERSON,
            task__status=COMPLETED,
            efficiency__isnull=False
        ).values('user').annotate(
            total_efficiency=Avg('efficiency')
        ).order_by('-total_efficiency')

        def get_queryset(self):
            return most_efficient_qs if \
                self.request.query_params.get('start_date') and \
                self.request.query_params.get('end_date') else \
                TaskAssociation.objects.none()

        self.get_queryset = types.MethodType(get_queryset, self)
        return self.modified_list()

    @action(
        detail=False,
        url_path='most-efficient/detail',
        filter_backends=[FilterMapBackend],
        filter_map={
            'start_date': 'created_at__date__gte',
            'end_date': 'created_at__date__lte',
            'assignee': 'user'
        },
        serializer_class=TaskAssociationSerializer
    )
    def most_efficient_detail(self, request, *args, **kwargs):
        def get_queryset(self):
            if self.request.query_params.get('assignee'):
                return self._get_task_association_queryset().filter(
                    taskverificationscore__ack=True,
                    association=RESPONSIBLE_PERSON,
                    task__status=COMPLETED,
                    user=self.request.query_params.get('assignee'),
                    efficiency__isnull=False
                ).distinct()
            return self._get_task_association_queryset().none()

        def get_serializer(self, *args, **kwargs):
            kwargs.update(
                {'fields': ['task', 'cycle_status', 'efficiency']}
            )
            serializer_class = self.get_serializer_class()
            kwargs['context'] = self.get_serializer_context()
            return serializer_class(*args, **kwargs)

        self.get_queryset = types.MethodType(get_queryset, self)
        self.get_serializer = types.MethodType(get_serializer, self)

        return self.modified_list()

    @action(
        detail=False,
        url_path='leader-board/detail',
        filter_backends=[FilterMapBackend],
        filter_map={
            'start_date': 'created_at__date__gte',
            'end_date': 'created_at__date__lte',
            'assignee': 'user'
        },
        serializer_class=TaskAssociationSerializer
    )
    def leader_board_detail(self, request, *args, **kwargs):
        def get_queryset(self):
            if self.request.query_params.get('assignee'):
                return self._get_task_association_queryset().filter(
                    taskverificationscore__ack=True,
                    association=RESPONSIBLE_PERSON,
                    task__status=COMPLETED,
                    user=self.request.query_params.get('assignee'),
                ).distinct()
            return self._get_task_association_queryset().none()

        def get_serializer(self, *args, **kwargs):
            kwargs.update(
                {'fields': ['task', 'cycle_status', 'current_score']}
            )
            serializer_class = self.get_serializer_class()
            kwargs['context'] = self.get_serializer_context()
            return serializer_class(*args, **kwargs)

        self.get_queryset = types.MethodType(get_queryset, self)
        self.get_serializer = types.MethodType(get_serializer, self)

        return self.modified_list()

    @action(detail=False, url_path='most-unverified',
            filter_backends=[OrderingFilter, FilterMapBackend],
            ordering_fields=('total_tasks',),
            serializer_class=MostUnverifiedTaskSerializer,
            filter_map={
                'start_date': 'created_at__date__gte',
                'end_date': 'created_at__date__lte'
            })
    def most_unverified_tasks(self, request):
        """"""
        most_unverified_qs = self._get_task_queryset().filter(
            approved=False, status=COMPLETED
        ).values('created_by').annotate(
            total_tasks=Count('id')
        ).order_by('-total_tasks')

        def get_queryset(self):
            return most_unverified_qs if \
                self.request.query_params.get('start_date') and \
                self.request.query_params.get('end_date') else \
                Task.objects.none()

        self.get_queryset = types.MethodType(get_queryset, self)

        return self.modified_list()

    @action(detail=False, url_path='closed-hold')
    def extra_tasks(self, request):
        """"""
        return super().list(request, show_info=False, show_summary=False,
                            show_closed_and_hold=True,
                            **self._get_role_view_())

    @action(detail=False, url_path='approvals',
            filter_backends=[FilterMapBackend, SearchFilter],
            filter_map={
                'start_date': 'created_at__date__gte',
                'end_date': 'created_at__date__lte',
                'assignee': 'task_associations__user',
                'associations': 'task_associations__association',
                'assigner': 'created_by',
            },
            search_fields=('title',),
            serializer_class=TaskSerializer)
    def approvals(self, request):
        """
            list

                Lists all approval
                filters :
                    assignee: UserID
                    start_date: Date
                    end_date: Date
        """

        def get_queryset(self):
            return self._get_task_queryset().filter(
                status=COMPLETED
            ).annotate(
                valid_display=Exists(
                    TaskAssociation.objects.exclude(
                        Q(taskverificationscore__ack=True) |
                        Q(taskverificationscore__ack__isnull=True)
                    ).filter(
                        task_id=OuterRef('pk')
                    ).annotate(
                        cycle_count=Count(
                            'taskverificationscore',
                        )
                    ).exclude(
                        cycle_count__lt=MAX_LIMIT_OF_TASK_SCORING_CYCLE
                    )
                )
            ).filter(valid_display=True)

        def get_serializer(self, *args, **kwargs):
            kwargs.update(
                {'fields': ('id', 'title', 'responsible_persons', 'approved',
                            'created_by')}
            )
            serializer_class = self.get_serializer_class()
            kwargs['context'] = self.get_serializer_context()
            return serializer_class(*args, **kwargs)

        self.get_queryset = types.MethodType(get_queryset, self)
        self.get_serializer = types.MethodType(get_serializer, self)

        # Patch request params
        modify_request_params(self, associations=RESPONSIBLE_PERSON)

        resp = self.modified_list(distinct=True)
        resp.data['_MAX_TASK_SCORING_CYCLE'] = MAX_LIMIT_OF_TASK_SCORING_CYCLE
        return resp

    @action(detail=True, url_path=r'approvals/(?P<user_id>[\d]+)',
            serializer_class=TaskVerificationScoreSerializer)
    def pending_approvals_details(self, request, pk, user_id):
        task = self.get_object()
        if task.status != COMPLETED:
            return Response({'detail': 'This Task has not been completed yet'})
        if not task.task_associations.filter(
            user_id=user_id, association=RESPONSIBLE_PERSON).exists():
            return Response(status=status.HTTP_404_NOT_FOUND)
        qs = task.task_associations.get(user_id=user_id)
        serializer = TaskAssociationSerializer(
            instance=qs, context=self.get_serializer_context()
        )
        data = serializer.data
        data.update(
            {'_MAX_TASK_SCORING_CYCLE': MAX_LIMIT_OF_TASK_SCORING_CYCLE}
        )
        return Response(data)

    @pending_approvals_details.mapping.post
    def pending_approval_verification(self, request, pk, user_id):
        if not validate_permissions(
            self.request.user.get_hrs_permissions(),
            TASK_APPROVALS_PERMISSION,
            TASK_PERMISSION
        ):
            return Response(status=status.HTTP_403_FORBIDDEN)
        task = self.get_object()
        if task.freeze:
            return Response({'detail': 'Is undergoing background process'},
                            status=status.HTTP_400_BAD_REQUEST)

        if not task.status == COMPLETED:
            return Response({'detail': 'Task has not been completed yet'},
                            status=status.HTTP_400_BAD_REQUEST)

        if not task.task_associations.filter(
            user_id=user_id, association=RESPONSIBLE_PERSON
        ).exists():
            return Response(
                {'detail': 'Invalid User as Responsible Person '},
                status=status.HTTP_400_BAD_REQUEST
            )
        if TaskVerificationScore.objects.filter(
            association__task=task, association__user_id=user_id,
            ack=True).exists():
            return Response(
                {'detail': 'Previous Score has already been acknowledged'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if TaskVerificationScore.objects.filter(
            association__task=task, association__user_id=user_id
        ).count() < MAX_LIMIT_OF_TASK_SCORING_CYCLE:
            return Response(
                {'detail': 'Scoring Cycle has not exceeded maximum limit'},
                status=status.HTTP_400_BAD_REQUEST
            )
        _iteration_count = TaskVerificationScore.objects.filter(
            association__task=task, association__user_id=user_id
        ).count()
        if _iteration_count == MAX_LIMIT_OF_TASK_SCORING_CYCLE and \
            TaskVerificationScore.objects.filter(
                association__task=task, association__user_id=user_id,
                ack__isnull=True).exists():
            return Response(
                {'detail': 'Previous score has not been '
                           'responded by Responsible Person '},
                status=status.HTTP_400_BAD_REQUEST
            )

        if _iteration_count > MAX_LIMIT_OF_TASK_SCORING_CYCLE:
            # if its true , the code will never reach this block because
            # its handled above
            # so , this block will never execute
            return Response(
                {'detail': 'Has Already been verified'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.serializer_class(data=self.request.data,
                                           fields=('score', 'remarks'))
        if serializer.is_valid(raise_exception=True):
            _instance = TaskVerificationScore.objects.create(
                association=task.task_associations.get(user_id=user_id),
                score=serializer.data.get('score'),
                remarks=serializer.data.get('remarks'),
                ack=True,
                ack_at=timezone.now()
            )
            recalculate_efficiency(task, user_id, _instance)
            return Response(serializer.data)

        return Response(status=status.HTTP_404_NOT_FOUND)

    @action(detail=False)
    def efficiency(self, request):
        return Response(status=status.HTTP_404_NOT_FOUND)

