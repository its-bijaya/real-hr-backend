# Django imports
import openpyxl
import types

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Sum, Value, Q, Count
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
# Rest_framework imports
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed, ValidationError
from rest_framework.fields import CharField
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.viewsets import ModelViewSet

from django_q.tasks import async_task

# Project current app imports
from irhrs.core.utils import email
from irhrs.core.mixins.viewset_mixins import (
    OrganizationMixin, OrganizationCommonsMixin,
    ListRetrieveUpdateViewSetMixin, GetStatisticsMixin,
    TrainingMixin, ListUpdateViewSetMixin,
    ListCreateViewSetMixin, ListViewSetMixin)
from irhrs.core.utils.common import validate_permissions, get_today, get_complete_url
from irhrs.core.utils.email import send_notification_email
from irhrs.core.utils.excel import ExcelList
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.core.utils.common_utils import get_users_list_from_permissions
from irhrs.core.utils.subordinates import find_immediate_subordinates
from irhrs.core.constants.organization import (
    TRAINING_CANCELLED_EMAIL,
    TRAINING_REQUESTED_EMAIL,
    TRAINING_UPDATED_EMAIL
)
from irhrs.core.utils.training import set_training_members
from irhrs.export.constants import ADMIN,FAILED
from irhrs.export.models.export import Export
from irhrs.export.utils.helpers import save_virtual_workbook
from irhrs.notification.utils import notify_organization
from irhrs.permission.constants.permissions import (
    ASSESSMENT_SCORE_PERMISSION,
    TRAINING_CREATE_PERMISSION,
    TRAINING_ASSIGN_PERMISSION,
    HAS_PERMISSION_FROM_METHOD,
    FULL_TRAINING_PERMISSION)
from irhrs.permission.permission_classes import permission_factory
from irhrs.training.api.v1.serializers import (
    TrainingTypeSerializer, TrainingSerializer,
    UserTrainingRequestSerializer, TrainerSerializer,
    TrainingAttachmentsSerializer,
    TrainingFeedbackSerializer,
    UserTrainingRequestMultiActionSerializer,
    TrainingAttendanceSerializer,
    TrainingMembersSerializer,
    UserTrainingImportSerializer)
from irhrs.training.models.helpers import (
    REQUESTED, PUBLIC, APPROVED, DECLINED, MEMBER, REQUEST,
    ONSITE, OFFSITE, IN_PROGRESS, COMPLETED)
from irhrs.training.utils import update_user_request_and_send_notification
from ....models import (
    TrainingType, Training, UserTrainingRequest, Trainer, UserTraining,
    TrainingFeedback, TrainingAttendance)
from ....utils.util import add_or_update_members_of_training, delete_members_from_training

TrainingPermission = permission_factory.build_permission(
    'TrainingPermission',
    allowed_to=[
        TRAINING_CREATE_PERMISSION
    ],
    limit_read_to=[
        ASSESSMENT_SCORE_PERMISSION,
        TRAINING_ASSIGN_PERMISSION,
    ]
)

USER = get_user_model()


class TrainingTypeViewSet(OrganizationCommonsMixin, OrganizationMixin, ModelViewSet):
    lookup_field = 'slug'
    queryset = TrainingType.objects.all()
    serializer_class = TrainingTypeSerializer
    filter_backends = (
        filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend
    )
    permission_classes = [TrainingPermission]
    search_fields = ['title']

    def get_queryset(self):
        return super().get_queryset().annotate(
            used_budget=Coalesce(
                Sum(
                    'trainings__budget_allocated'
                ),
                Value(0.0)
            )
        ).prefetch_related(
            'trainings'
        )

class TrainingViewSet(OrganizationMixin, ModelViewSet):
    """
    # VIew only my trainings with `?my=true`
    """
    lookup_field = 'slug'
    queryset = Training.objects.all()
    serializer_class = TrainingSerializer
    filter_backends = (
        filters.SearchFilter, filters.OrderingFilter, FilterMapBackend
    )
    search_fields = ('name',)
    filter_map = {
        'visibility': 'visibility',
        'status': 'status',
        'start_date': 'start__date__gte',
        'end_date': 'start__date__lte'
    }
    permission_classes = [
        permission_factory.build_permission(
            'TrainingPermission',
            actions={
                'create': [TRAINING_CREATE_PERMISSION],
                'list': [
                    ASSESSMENT_SCORE_PERMISSION, TRAINING_ASSIGN_PERMISSION,
                    TRAINING_CREATE_PERMISSION, HAS_PERMISSION_FROM_METHOD
                ],
                'retrieve': [
                    ASSESSMENT_SCORE_PERMISSION, TRAINING_ASSIGN_PERMISSION,
                    TRAINING_CREATE_PERMISSION, HAS_PERMISSION_FROM_METHOD
                ],
                'put': [TRAINING_CREATE_PERMISSION],
                'patch': [TRAINING_CREATE_PERMISSION],
                'delete': [TRAINING_CREATE_PERMISSION],
                'join': [HAS_PERMISSION_FROM_METHOD],
                'attachments': [HAS_PERMISSION_FROM_METHOD],
                'feedback': [HAS_PERMISSION_FROM_METHOD],
                'assign_members': [TRAINING_ASSIGN_PERMISSION]
            },
        )
    ]

    def get_serializer(self, *args, **kwargs):
        is_authority = self.organization and validate_permissions(
            self.request.user.get_hrs_permissions(self.organization),
            TRAINING_ASSIGN_PERMISSION, TRAINING_CREATE_PERMISSION,
            ASSESSMENT_SCORE_PERMISSION
        )
        if self.organization and not is_authority:
            kwargs.update({
                'exclude_fields': ['budget_allocated']
            })

        if self.action == 'update':
            kwargs.update({'exclude_fields': ['status']})

        return super().get_serializer(*args, **kwargs)

    def has_user_permission(self):
        if self.action in ['list', 'retrieve']:
            return True
        elif self.action == 'join':
            return True
        elif self.action in ['attachments', 'feedback']:
            # try:
            #     obj = self.filter_queryset(
            #         self.get_queryset()
            #     ).get(
            #         slug=self.kwargs.get('slug')
            #     )
            #     return self.request.user in obj.members_qs() or self.request.user == obj.created_by
            # except Training.DoesNotExist:
            #     return False
            return True
        return False

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['organization'] = self.organization
        return ctx

    def get_queryset(self):
        organization = self.kwargs.get('organization_slug')
        return super().get_queryset().filter(
            training_type__organization__slug=organization
        ).select_related(
            'training_type', 'coordinator', 'coordinator__detail',
            'coordinator__detail__employment_level', 'coordinator__detail__organization',
            'coordinator__detail__job_title', 'coordinator__detail__division',
            'created_by', 'created_by__detail', 'created_by__detail__organization',
            'created_by__detail__job_title', 'created_by__detail__division',
            'created_by__detail__employment_level'
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        only_my = self.request.query_params.get('participated', 'false')
        is_authority = validate_permissions(
            self.request.user.get_hrs_permissions(self.organization),
            TRAINING_ASSIGN_PERMISSION
        )
        if only_my == 'true':
            queryset = queryset.filter(user_trainings__user=self.request.user)

        if not is_authority and only_my == 'false':
            queryset = queryset.exclude(
                user_trainings__user=self.request.user
            ).filter(visibility=PUBLIC)
        page = self.paginate_queryset(queryset)
        serializer = TrainingSerializer(page, many=True, context=self.get_serializer_context())
        return self.get_paginated_response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        training = self.get_object()
        if training.status in [IN_PROGRESS, COMPLETED]:
            raise ValidationError({
                "training": ['Training with status ‘In Progress’ and ‘Completed’ cannot be deleted']
            })
        if training.meeting_room:
            training.meeting_room.delete()

        # send mail
        members = set(training.members.all())
        external_trainers = set(training.external_trainers.all())
        internal_trainers = set(training.internal_trainers.all())
        possible_recipients = (
            members.union(external_trainers).union(internal_trainers)
        )
        email_recipients = []
        email_body = f"Training '{training.name}' has been cancelled."
        email_subject = "Training cancelled."
        for user in possible_recipients:
            if isinstance(user, Trainer):
                can_send_mail = email.is_email_setting_enabled_in_org(
                    training.training_type.organization,
                    TRAINING_CANCELLED_EMAIL
                )
            else:
                can_send_mail = email.can_send_email(user, TRAINING_CANCELLED_EMAIL)
            if can_send_mail:
                email_recipients.append(user.email)

        if email_recipients:
            async_task(
                send_notification_email,
                recipients=email_recipients,
                subject=email_subject,
                notification_text=email_body
            )
        return super().destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        training = self.get_object()
        resp = super().update(request, *args, **kwargs)
        training.refresh_from_db()

        # send email
        members = set(training.members.all())
        external_trainers = set(training.external_trainers.all())
        internal_trainers = set(training.internal_trainers.all())
        possible_recipients = (
            members.union(external_trainers).union(internal_trainers)
        )
        email_recipients = []
        email_subject = "Training updated."
        email_body = f"Some details on training '{training.name}' have been updated."
        for user in possible_recipients:
            if isinstance(user, Trainer):
                can_send_mail = email.is_email_setting_enabled_in_org(
                    training.training_type.organization,
                    TRAINING_CANCELLED_EMAIL
                )
            else:
                can_send_mail = email.can_send_email(user, TRAINING_CANCELLED_EMAIL)
            if can_send_mail:
                email_recipients.append(user.email)
        if email_recipients:
            async_task(
                send_notification_email,
                recipients=email_recipients,
                subject=email_subject,
                notification_text=email_body
            )
        return resp

    @action(
        methods=['POST'],
        detail=True,
        serializer_class=type(
            'RequestSerializer',
            (Serializer,),
            {
                'remarks': CharField(max_length=255)
            }
        )
    )
    def join(self, request, *args, **kwargs):
        training = self.get_object()
        serializer = UserTrainingRequestSerializer(
            data={
                'training': training.id,
                'status': REQUESTED,
                'request_remarks': request.data.get('remarks')
            },
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        recipients = []
        email_subject = f"New training request from {request.user.full_name}"
        email_text=(
            f"{self.request.user.full_name} has requested for training '{training.name}'."
        )
        email_permissions = [
            FULL_TRAINING_PERMISSION
        ]
        hrs_list = get_users_list_from_permissions(
            email_permissions,
            self.organization
        )

        for user in hrs_list:
            # add to recipient list if not already sent
            can_send_email = email.can_send_email(
                user,
                TRAINING_REQUESTED_EMAIL
            )
            if can_send_email:
                recipients.append(user.email)

        if recipients:
            async_task(
                send_notification_email,
                recipients=recipients,
                subject=email_subject,
                notification_text=email_text
            )

        notify_organization(
            text=f'Training \'{training.name}\' has been '
                 f'requested by {self.request.user.full_name}',
            organization=training.training_type.organization,
            actor=self.request.user,
            url=f'/admin/{training.training_type.organization.slug}/training/training-need-analysis',
            action=training,
            permissions=[
                FULL_TRAINING_PERMISSION,
                TRAINING_CREATE_PERMISSION
            ]
        )
        return Response(serializer.data)

    @action(
        methods=['GET'],
        detail=True,
        serializer_class=TrainingAttachmentsSerializer,
    )
    def attachments(self, *args, **kwargs):
        training = self.get_object()
        page = self.paginate_queryset(
            training.attachments.all().select_related(
                'created_by', 'created_by__detail',
                'created_by__detail__organization',
                'created_by__detail__job_title'
            ).prefetch_related(
                'files'
            )
        )
        return self.get_paginated_response(
            TrainingAttachmentsSerializer(
                many=True,
                instance=page,
                context=self.get_serializer_context()
            ).data
        )

    @attachments.mapping.post
    def attachments_post(self, *args, **kwargs):
        training = self.get_object()
        ser = TrainingAttachmentsSerializer(
            data=self.request.data,
            context={
                **self.get_serializer_context(),
                'training': training
            }
        )
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

    @action(
        detail=True,
        methods=['POST'],
        serializer_class=TrainingMembersSerializer,
        url_path='assign-member'
    )
    def assign_members(self, request, *args, **kwargs):
        training = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        users = serializer.data.get('user')
        add_or_update_members_of_training(self, training, users)
        return Response(serializer.data)

    @transaction.atomic
    @action(
        detail=True,
        methods=['POST'],
        serializer_class = UserTrainingImportSerializer,
        url_path='import-member'
    )
    def bulk_import_training(self, request, *args, **kwargs):
        training = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        excel_update_file = serializer.validated_data['excel_file']
        workbook = openpyxl.load_workbook(excel_update_file)
        excel_list = ExcelList(workbook)
        excel_data = excel_list[1:]
        error_exists = False
        valid_user = set()
        duplicated_data = set()
        users_in_training = training.user_trainings.all().select_related('user').values_list('user__username', flat=True)

        for index,row in enumerate(excel_data, 1):
            row = row[0]
            errors = {}
            user = USER.objects.filter(
                Q(username=row)|Q(email=row)
            ).distinct().first()
            if not user:
                errors['user'] = 'Username/Email doesnot exists.'
            elif user and row in duplicated_data:
                errors['user'] = 'Given user credentials already exist in excel sheet.'
            elif user and row in users_in_training:
                errors['user'] = 'User is already assigned the same training.'
            else:
                valid_user.add(user.id)
            if errors:
                error_exists = True
                excel_list[index].append(",".join(errors.values()))
                continue
            duplicated_data.add((row))

        if error_exists:
            excel_list[0].append('Remarks')
            error_wb = excel_list.generate_workbook()
            export = Export.objects.filter(export_type='Bulk Assign Training').first()

            if not export:
                export=Export.objects.create(
                    user=self.request.user,
                    name="Bulk Assign Training",
                    exported_as=ADMIN,
                    export_type='Bulk Assign Training',
                    organization=self.organization,
                    status=FAILED,
                    remarks='Bulk Assign Training Failed.'
                )
            export.export_file.save(
                "bulk_assign_training.xlsx",
                ContentFile(save_virtual_workbook(error_wb))
            )
            export.save()
            export_url = get_complete_url(export.export_file.url)

            return Response(
                {'file': {'error_file': export_url }},
                status=status.HTTP_400_BAD_REQUEST
            )
        add_or_update_members_of_training(self,training,users=valid_user)
        return Response(
            {'msg': 'Bulk Assign Training completed successfully'},
            status=status.HTTP_200_OK
        )

    @action(
        methods=['GET'],
        detail=True,
        url_path='sample'
    )
    def get_sample(self, request, *args, **kwargs):
        workbook = openpyxl.Workbook()
        ws = workbook.active
        fields = ['Employee']
        values = ['Username/Email']
        ws.append(fields)
        ws.append(values)
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = "attachment; filename=Bulk_Assign_Training_Sample.xlsx"
        workbook.save(response)
        return response

    @action(
        detail=True,
        methods=['POST'],
        serializer_class=TrainingMembersSerializer,
        url_path='delete-member'
    )
    def deleted_members(self, request, *args, **kwargs):
        training = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        users = serializer.data.get('user')
        delete_members_from_training(self, training, users)
        set_training_members()
        return Response("Member is deleted from training.")

class TrainingFeedbackViewSet(TrainingMixin, OrganizationMixin, ListCreateViewSetMixin):
    queryset = TrainingFeedback.objects.all()
    serializer_class = TrainingFeedbackSerializer
    permission_classes = [
        permission_factory.build_permission(
            'TrainingPermission',
            allowed_to=[HAS_PERMISSION_FROM_METHOD],
        )
    ]

    def has_user_permission(self):
        user = self.request.user
        if self.request.method.lower() == 'post':
            return self.training and (
                user == self.training.coordinator or
                self.training.internal_trainers.filter(id=user.id).exists() or
                self.training.members.filter(id=user.id).exists()
            )
        return True

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['organization'] = self.organization
        context['training'] = self.training
        return context

    def get_queryset(self):
        training = self.kwargs.get('training_slug')
        return super().get_queryset().filter(training__slug=training).select_related(
            'user', 'user__detail',
            'user__detail__organization'
        )

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data['responded'] = self.get_queryset().filter(
            user=self.request.user
        ).exists()
        return response

    # def perform_destroy(self, instance):
    #     super().perform_destroy(instance)
    #     calibrate_average_rating(instance)


class UserTrainingRequestViewSet(
    GetStatisticsMixin,
    OrganizationMixin,
    ListRetrieveUpdateViewSetMixin
):
    queryset = UserTrainingRequest.objects.all()
    serializer_class = UserTrainingRequestSerializer
    filter_backends = (
        filters.SearchFilter, OrderingFilterMap, FilterMapBackend
    )
    filter_map = {
        'status': 'status',
        'training': 'training__slug'
    }
    ordering_fields_map = {
        'request_by': (
            'user__first_name', 'user__middle_name', 'user__last_name',
        ),
        'assessment_set': 'training__name',
        'modified_at': 'modified_at'
    }
    statistics_field = 'status'
    search_fields = (
        'user__first_name', 'user__middle_name', 'user__last_name',
        'training__name'
    )
    _training = None

    def get_queryset(self):
        base_qs = super().get_queryset().filter(
            user__detail__organization=self.organization
        )
        only_my = self.request.query_params.get('my') == 'true'
        if not only_my:
            is_authority = validate_permissions(
                self.request.user.get_hrs_permissions(self.organization),
                TRAINING_ASSIGN_PERMISSION
            )
            if not is_authority:
                only_my = True
        if only_my:
            base_qs = base_qs.filter(
                user=self.request.user
            )
        return base_qs

    def get_serializer(self, *args, **kwargs):
        if self.request.method in ['PUT', 'PATCH']:
            kwargs.update({
                'fields': (
                    'action_remarks',
                    'status'
                )
            })
        return super().get_serializer(*args, **kwargs)

    def get_training(self):
        if not self._training:
            slug = self.kwargs.get('training_slug')
            if slug is not None:
                self._training = get_object_or_404(
                    Training, slug=slug
                )
        return self._training

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if 'training_slug' in self.kwargs:
            training = self.get_training()
            context['training'] = training
            user_requests = training.training_requests.filter(
                status=REQUESTED
            ).values_list('user', flat=True)
            context['users'] = user_requests

        return context

    def get_serializer_class(self):
        if self.action.lower() == 'multi_action_post':
            return UserTrainingRequestMultiActionSerializer
        return super().get_serializer_class()

    def list(self, request, *args, **kwargs):
        ret = super().list(request, *args, **kwargs)
        ret.data.update({
            'statistics': self.statistics
        })
        return ret

    @action(
        methods=['get'],
        detail=False,
        url_path=r'training/(?P<training_slug>[\w\-]+)'
    )
    def multi_action(self, request, *args, **kwargs):
        def get_queryset(self):
            request_data = UserTrainingRequest.objects.filter(
                status=REQUESTED,
                training__slug=self.kwargs.get('training_slug')
            )
            return request_data

        self.get_queryset = types.MethodType(get_queryset, self)
        return super().list(request, *args, **kwargs)

    @multi_action.mapping.post
    def multi_action_post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request_data = serializer.data
        users = request_data.get('user')
        _status = request_data.get('status')
        if not _status in [APPROVED, DECLINED]:
            return Response({
                'status': [f'Status for requested training can\'t be {_status}. '
                           f'It must be either {APPROVED} or {DECLINED}']
            })

        training_slug = self.kwargs.get('training_slug')
        user_training_requests = UserTrainingRequest.objects.filter(
            training__slug=training_slug,
            user_id__in=users
        )
        training_user = UserTraining.objects.filter(
            training__slug=training_slug
        ).values_list('user', flat=True)

        def filter_user(user):
            if user.id in training_user:
                return False
            return True

        if user_training_requests:
            update_user_request_and_send_notification(
                self,
                user_training_requests,
                **request_data
            )
            if _status == APPROVED:
                training_attendance = []
                user_trainings = []
                for user_request in user_training_requests:
                    user_trainings.append(
                        UserTraining(
                            user=user_request.user,
                            training=user_request.training,
                            start=timezone.now(),
                            training_need=REQUEST
                        )
                    )

                    training_attendance.append(
                        TrainingAttendance(
                            member=user_request.user,
                            training=user_request.training,
                            position=MEMBER
                        )
                    )
                UserTraining.objects.bulk_create(user_trainings)
                TrainingAttendance.objects.bulk_create(training_attendance)

                set_training_members()
            return Response(request_data)
        return Response({
            'non_field_errors': ['User didn\'t requested for these trainings.']
        })


class TrainersViewSet(OrganizationCommonsMixin, OrganizationMixin, ModelViewSet):
    """
    Create Format:

        full_name:ABC XYZ
        email:abc@xyz.com
        description:Description
        expertise:
        contact_info:{}
        attachment0.file:<File>
        attachment1.file:<File>
        attachment2.file:<File>
        // attachment0.attachment_type: // Not Required for Now
        // attachment1.attachment_type: // Not Required for Now
    """
    queryset = Trainer.objects.all()
    serializer_class = TrainerSerializer
    filter_backends = (
        filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend
    )
    permission_classes = [
        permission_factory.build_permission(
            'TrainersPermission',
            allowed_to=[TRAINING_ASSIGN_PERMISSION]
        )
    ]
    search_fields = 'full_name',

    def destroy(self, request, *args, **kwargs):
        trainer = self.get_object()
        if trainer.external_trainers.exists():
            return Response(
                {
                    'message': [f'{trainer.full_name} has been added as trainer for trainings.']
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)


class TrainingAttendanceViewSet(OrganizationMixin, TrainingMixin, ListUpdateViewSetMixin):
    """
    This viewset is used for recording attendance time of member and trainer of the training.

    To get data for attendance following information are needed
        Url: /api/v1/training/{org_slug}/training/{training_slug}/attendance
        method: 'get'

    To post data for recording attendance following information are needed:
        Url: /api/v1/training/{org_slug}/training/{training_slug}/attendance/{attendance_id}
        method: 'patch'
        data:
            {
                'arrival_time': DateTime,
                'remarks': CharField
            }
    """
    serializer_class = TrainingAttendanceSerializer
    queryset = TrainingAttendance.objects.all()
    permission_classes = [
        permission_factory.build_permission(
            'TrainingAttendancePermission',
            allowed_to=[
                FULL_TRAINING_PERMISSION,
                TRAINING_CREATE_PERMISSION,
                TRAINING_ASSIGN_PERMISSION,
                HAS_PERMISSION_FROM_METHOD
            ]
        )
    ]

    def get_queryset(self):
        return super().get_queryset().filter(
            training=self.training
        ).select_related(
            'member', 'member__detail', 'member__detail__organization',
            'member__detail__job_title', 'external_trainer'
        )

    def has_user_permission(self):
        return self.training and self.training.coordinator == self.request.user


class TrainingStatsMixin:
    @property
    def training(self):
        return Training.objects.filter(training_type__organization=self.organization)

    @property
    def training_type(self):
        return TrainingType.objects.filter(organization=self.organization)

    def get_training_count(self):
        today = get_today(with_time=True)
        return self.training.aggregate(
            upcoming=Count(
                'id',
                filter=Q(start__gt=today)
            ),
            completed=Count(
                'id',
                filter=Q(end__lt=today)
            ),
            ongoing=Count(
                'id',
                filter=Q(
                    start__lte=today,
                    end__gte=today
                )
            ),
            onsite=Count(
                'id',
                filter=Q(nature=ONSITE)
            ),
            offsite=Count(
                'id',
                filter=Q(nature=OFFSITE)
            )
        )

    def get_upcoming_training(self, involved=False, fields=None):
        fil = {'start__gt': get_today(with_time=True)}
        if involved:
            fil.update({
                'user_trainings__user': self.request.user
            })

        if not fields:
            fields = ['name', 'start', 'end', 'members', 'slug']

        trainings = self.training.filter(**fil).order_by('start')[:5]
        return TrainingSerializer(
            trainings, many=True,
            context=self.get_serializer_context(),
            fields=fields,
        ).data

    def get_completed_training(self):
        trainings = self.training.filter(end__lt=get_today(with_time=True)).order_by('-end')[:5]
        return TrainingSerializer(
            trainings, many=True,
            context=self.get_serializer_context(),
            fields=['name', 'start', 'end', 'members', 'slug'],
        ).data


class TrainingStatsViewSet(
    OrganizationMixin,
    TrainingStatsMixin,
    ListViewSetMixin
):
    filter_map = {}

    def get_queryset(self):
        if self.action == 'noticeboard':
            fil = {}
            if self.request.query_params.get('as') == 'supervisor':
                subordinates = find_immediate_subordinates(self.request.user.id)
                fil.update({
                    'user_training__user_id__in': subordinates
                })
            else:
                fil.update({
                    'user_trainings__user': self.request.user
                })
            return self.training.filter(
                user_trainings__user=self.request.user
            ).order_by('start').distinct()
        return self.training_type.order_by('-budget_limit')

    def filter_queryset(self, queryset):
        if self.action == "noticeboard":
            start_date = self.request.query_params.get('start_date')
            end_date = self.request.query_params.get('end_date')
            if not start_date and not end_date:
                start_date = get_today()
                end_date = start_date + relativedelta(month=1)
            return queryset.filter(
                Q(Q(start__date__gt=start_date) | Q(end__date__gt=start_date)),
                Q(end__date__lte=end_date)
            )
        return super().filter_queryset(queryset)

    def get_serializer(self, *args, **kwargs):
        if self.action == 'noticeboard':
            kwargs.update({
                'fields': ['name', 'start', 'end', 'slug']
            })
        else:
            kwargs.update({
                'fields': ['title', 'budget_limit', 'slug', 'amount_type']
            })
        return super().get_serializer(*args, **kwargs)

    def get_serializer_class(self):
        if self.action == 'noticeboard':
            return TrainingSerializer
        return TrainingTypeSerializer

    def list(self, request, *args, **kwargs):
        raise MethodNotAllowed(method=request.method)

    @action(methods=['GET'], detail=False)
    def budget(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(methods=['GET'], detail=False)
    def stats(self, request, *args, **kwargs):
        training_counts = self.get_training_count()
        upcoming_training = self.get_upcoming_training()
        completed_training = self.get_completed_training()

        response = dict(
            upcoming_training=upcoming_training,
            completed_training=completed_training,
            stats=training_counts
        )
        return Response(response)

    @action(
        methods=['GET'],
        detail=False,
        filter_backends=[FilterMapBackend],
        url_path='upcoming'
    )
    def noticeboard(self, request, *args, **kwargs):
        return super().list(self, request, *args, **kwargs)
