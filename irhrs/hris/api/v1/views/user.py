import logging
from datetime import time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjValidationError, ObjectDoesNotExist
from django.db import models
from django.db.models import Case, When, F, DateField, ExpressionWrapper, \
    DurationField, Value, Prefetch, Subquery, OuterRef, Q
from django.db.models.functions import Concat
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_q.models import Schedule
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework import serializers
from rest_framework.response import Response

from irhrs.core.constants.user import RESIGNED, TERMINATED
from irhrs.core.mixins.serializers import DummySerializer
from irhrs.core.mixins.viewset_mixins import ListViewSetMixin, \
    OrganizationMixin, HRSOrderingFilter, ListRetrieveViewSetMixin
from irhrs.core.utils import get_system_admin
from irhrs.core.utils.common import get_today, \
    apply_filters, validate_permissions, combine_aware
from irhrs.core.utils.filters import FilterMapBackend, DynamicSearchFilter, \
    NullsAlwaysLastOrderingFilter
from irhrs.export.utils.export import PDFExport, ExcelExport
from irhrs.hris.api.v1.serializers.user import UserEmploymentSerializer, \
    UserResignSerializer, HRPasswordChangeSerializer, UserDirectorySerializer, \
    UserDirectoryDetailSerializer, UserTerminateSerializer, PastUserSerializer, \
    UserActivationSerializer, \
    CreatePastUserSerializer
from irhrs.organization.models import Organization
from irhrs.permission.constants.permissions import HRIS_PERMISSION, HAS_PERMISSION_FROM_METHOD, \
    USER_PROFILE_PERMISSION, REPORT_VIEWERS
from irhrs.permission.permission_classes import permission_factory
from irhrs.users.models import UserExperience, UserSupervisor

USER = get_user_model()


class UserEmploymentViewSet(OrganizationMixin,
                            ListViewSetMixin):
    """
    list:
    employee list

    For filters refer to drf browsable api
    for date range filters send 'start_date' and 'end_date'
    on `yyyy-mm-dd` format. It filters users on the basis of `joined_date`.

    pass `yos=2-4` for years of service range in query params

    pass `age_group=16-25` for age group filter

    filter by supervisor using supervisor=user_id

    """
    queryset = UserExperience.objects.all()
    serializer_class = UserEmploymentSerializer
    filter_backends = [FilterMapBackend,
                       DynamicSearchFilter, NullsAlwaysLastOrderingFilter]
    search_fields = ['user__first_name',
                     'user__middle_name',
                     'user__last_name','user__username']
    permission_classes = [
        permission_factory.build_permission(
            "UserOrganizationView",
            limit_write_to=[
                HRIS_PERMISSION
            ],
            limit_read_to=[
                HRIS_PERMISSION, HAS_PERMISSION_FROM_METHOD,
                USER_PROFILE_PERMISSION, *REPORT_VIEWERS
            ],
        )

    ]

    def has_user_permission(self):
        return self.request.query_params.get('supervisor') == str(self.request.user.id)

    def get_search_fields(self):
        if self.action == 'past_users':
            return ['first_name', 'middle_name', 'last_name']
        return self.search_fields

    def get_filter_map(self):
        if self.action == 'past_users':
            return {
                'division': 'detail__division__slug',
                'employment_status': 'detail__employment_status__slug',
                'employment_level': 'detail__employment_level__slug',
                'branch': 'detail__branch__slug',
                'gender': 'detail__gender',
                'code': 'detail__code',
                'username': 'username'
            }
        return {
            'division': 'division__slug',
            'employment_status': 'employment_status__slug',
            'employment_level': 'employee_level__slug',
            'branch': 'branch__slug',
            'date_of_join': 'user__detail__joined_date',
            'joined_after': 'user__detail__joined_date__gte',
            'gender': 'user__detail__gender',
            'code': 'user__detail__code',
            'username': 'user__username'
        }

    def get_ordering_fields_map(self):
        if self.action == 'past_users':
            return {
                'joined_date': 'detail__joined_date',
                'date_of_birth': 'detail__date_of_birth',
                'full_name': ('first_name', 'middle_name', 'last_name'),
                'branch': 'detail__branch__name',
                'parted_date': 'detail__last_working_date',
                'id': 'id',
                'contract_end_date': 'user_experiences__end_date'
            }
        return {
            'joined_date': 'user__detail__joined_date',
            'date_of_birth': 'user__detail__date_of_birth',
            'full_name': ('user__first_name', 'user__middle_name', 'user__last_name'),
            'supervisor_full_name': 'supervisor_full_name',
            'branch': 'branch__name',
            'created_at': 'created_at',
            'id': 'id'
        }

    def get_queryset(self):
        if self.action == "past_users":
            return self.get_past_user_queryset()

        queryset = super().get_queryset()

        supervisor_filter_activated = self.request.query_params.get('supervisor', None)
        if supervisor_filter_activated:
            supervisor = self._get_supervisor()
            if supervisor:
                queryset = queryset.filter(
                    user_id__in=supervisor.subordinates_pks)
            else:
                queryset = queryset.none()

        fil = dict(
            organization=self.get_organization(),
            is_current=True
        )
        if validate_permissions(
            self.request.user.get_hrs_permissions(),
            USER_PROFILE_PERMISSION,
            HRIS_PERMISSION
        ) and self.action in (
            'terminate_user'
            # Allow non-current users to be terminated.
        ):
            fil.pop('is_current', None)
        return queryset.filter(
            **fil
        ).annotate(
            # get supervisor full name in order to order it by supervisor
            supervisor_full_name=Subquery(
                UserSupervisor.objects.filter(
                    user_id=OuterRef('user_id'),
                    authority_order=1
                ).annotate(full_name=Concat(
                    'supervisor__first_name', Value(' '),
                    'supervisor__middle_name', Value(' '),
                    'supervisor__last_name', Value(' ')
                )).values(
                    'full_name')[:1],
                output_field=models.CharField()
            )
        )

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        if self.action == "past_users":
            queryset = apply_filters(
                self.request.query_params,
                {
                    'start_date': 'detail__last_working_date__gte',
                    'end_date': 'detail__last_working_date__lte'
                },
                queryset.past()
            )
            return queryset

        queryset = queryset.filter(
            is_current=True
        ).filter(Q(end_date__isnull=True) |
                 Q(end_date__gte=get_today()))
        queryset = apply_filters(
            self.request.query_params,
            {
                'start_date': 'user__detail__joined_date__gte',
                'end_date': 'user__detail__joined_date__lte'
            },
            queryset
        )
        yos = self.request.query_params.get('yos')
        age_group = self.request.query_params.get('age_group')

        if yos:
            start = None
            end = None
            try:
                yos = yos.split('-')
                if len(yos) == 2:
                    start = int(yos[0])
                    end = int(yos[1])
            except TypeError:
                pass

            if not (start is None and end is None):
                queryset = self.annotate_service_period(queryset).filter(
                    duration__gte=timezone.timedelta(days=365 * start),
                    duration__lte=timezone.timedelta(days=365 * end)
                )

        if age_group:
            today = get_today()
            start = None
            end = None

            try:
                age_group = age_group.split('-')
                if len(age_group) == 2:
                    start = int(age_group[0])
                    end = int(age_group[1])
            except TypeError:
                pass
            if not (start is None and end is None):
                queryset = queryset.filter(
                    user__detail__date_of_birth__lte=today - timezone.timedelta(
                        days=365 * start),
                    user__detail__date_of_birth__gt=today - timezone.timedelta(
                        days=365 * end)
                )

        if self.get_show_supervisor():
            prefetches = [Prefetch(
                    'user__supervisors',
                    queryset=UserSupervisor.objects.filter(
                        user__detail__organization=self.get_organization(),
                        authority_order=1
                    ).select_related('supervisor',
                                     'supervisor__detail',
                                     'supervisor__detail__job_title',
                                     'supervisor__detail__organization',
                                     'supervisor__detail__division',
                                     'supervisor__detail__employment_level',
                                     'supervisor__detail__employment_status'),
                    to_attr='user_supervisors'
            )]
        else:
            prefetches = []

        return queryset.select_related(
            'user',
            'user__detail',
            'user__detail__job_title',
            'user__detail__organization',
            'user__detail__division',
            'user__detail__employment_level',
            'user__detail__employment_status',
            'branch',
            'division',
            'employee_level',
            'employment_status',
            'job_title',
        ).prefetch_related(*prefetches)

    def get_show_supervisor(self):
        return self.request.query_params.get('no_supervisor', 'false') == 'false'

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            exclude = []
            if not (self.request.query_params.get(
                    'profile_completeness', 'false') == 'true'):
                exclude.append('profile_completeness')
            if not self.get_show_supervisor():
                exclude.append('supervisor')

            if exclude:
                kwargs.update({'exclude_fields': exclude})

        return super().get_serializer(*args, **kwargs)

    def get_serializer_class(self):
        if self.action == 'resign':
            return UserResignSerializer
        elif self.action == 'change_password':
            return HRPasswordChangeSerializer
        elif self.action == 'terminate_user':
            return UserTerminateSerializer
        elif self.action in ['block_user', 'unblock_user', 'enable_audit_user', 'disable_audit_user']:
            return DummySerializer
        elif self.action == 'activate_user':
            return UserActivationSerializer
        return super().get_serializer_class()

    def _schedule_termination(self, experience):
        func_name = 'irhrs.users.utils.terminate_user_for_date'
        params = {
            'experience_id': experience.id
        }
        next_run = combine_aware(
            experience.end_date + timezone.timedelta(days=1),
            time(0, 5)
        )
        data = {
            'name': f'Terminate {experience.user} on {experience.end_date}',
            'func': func_name,
            'kwargs': params,
            'next_run': next_run,
        }
        Schedule.objects.create(
            **data
        )

    def get_past_user_queryset(self):
        return USER.objects.all().past().filter(
            Q(detail__organization=self.get_organization()) | Q(
                detail__organization__isnull=True)
        ).exclude(user_experiences__isnull=True).select_related(
            'detail', 'detail__organization',
            'detail__job_title',
            'detail__organization',
            'detail__division',
            'detail__employment_level',
            'detail__employment_status',
        )

    def _get_supervisor(self):
        try:
            supervisor_id = self.request.query_params.get('supervisor')
            return USER.objects.get(id=supervisor_id)
        except (TypeError, ValueError, DjValidationError, ObjectDoesNotExist):
            return None

    # TODO @Ravi: All these actions need to go somewhere else, or,
    # TODO ****** Implement the actions using user_id instead of experience_id.

    @action(methods=['GET'], detail=False, url_path='past', url_name='past')
    def past_users(self, request, **kwargs):
        offboarded = self.request.query_params.get('offboarded', 'false')
        # users who do not have current experience
        queryset = self.filter_queryset(self.get_queryset())
        if offboarded == 'true':
            queryset = queryset.exclude(
                detail__parting_reason=''
            )
        else:
            queryset = queryset.filter(
                detail__parting_reason=''
            )
        page = self.paginate_queryset(queryset.distinct())
        return self.get_paginated_response(
            PastUserSerializer(
                page, many=True, context=self.get_serializer_context()).data
        )

    @action(methods=['POST'], detail=True, url_path='resign', url_name='resign')
    def resign(self, request, **kwargs):
        user = self.get_user()
        experience = user.current_experience
        if not experience:
            return Response(
                {'message': 'User has no current experience'},
                400
            )
        if user == request.user:
            return Response(
                {'message': 'Can not act on own user'},
                403
            )

        serializer = self.get_serializer(instance=experience,
                                         data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if experience.end_date == timezone.now().date():
            # deactivate user if resign date is today
            # add this to task if resign date is not today

            user.is_active = False
            user.is_blocked = True

            user.save()

            experience.is_current = False
        else:
            self._schedule_termination(experience)
        experience.save()

        userdetail = user.detail
        userdetail.last_working_date = experience.end_date
        userdetail.parting_reason = RESIGNED
        userdetail.save()

        return Response({'message': f'Resigned user on {experience.end_date}'})

    @action(methods=['GET'], detail=False, url_path='export', url_name='export')
    def export(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        export_format = request.query_params.get('export_format', 'xlsx')

        export_kwargs = {
            "qs": queryset,
            "columns": ["user.full_name",
                        "branch",
                        "division",
                        "employee_level",
                        "user.detail.joined_date",
                        "user.detail.date_of_birth",
                        "employment_status",
                        "supervisor_full_name"]
        }
        if export_format == 'pdf':
            return PDFExport.get_response(**export_kwargs)
        elif export_format == 'xlsx':
            return ExcelExport.get_response(**export_kwargs)

        return Response({}, status=400)

    @action(methods=['post'], detail=True, url_path='change-password',
            url_name='change-password')
    def change_password(self, request, *args, **kwargs):
        user = self.get_user()

        serializer_data = {
            'user': user.id,
            'password': request.data.get('password'),
            'repeat_password': request.data.get('repeat_password')
        }

        serializer_context = {'request': request}

        serializer = self.get_serializer(
            data=serializer_data,
            context=serializer_context
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(methods=['post'], detail=True, url_path='enable-audit-user',
            url_name='enable-audit-user')
    def enable_audit_user(self, request, *args, **kwargs):
        """change user to audit user"""
        user = get_object_or_404(
            USER.objects.filter(
                id__in=self.filter_queryset(self.get_queryset()).values('user'),
            ),
            id=self.kwargs.get('pk')
        )
        if user == request.user:
            return Response(
                {'message': 'Can not act on own user'},
                403
            )
        result = self._enable_audit_user(user)
        if result:
            return Response({"detail" : "The user was changed to audit user."})
        return Response({"detail": "Failed to change to audit user. Perhaps the user is already an audit user."
        }, 400)

    @action(methods=['post'], detail=True, url_path='disable-audit-user',
            url_name='disable-audit-user')
    def disable_audit_user(self, request, *args, **kwargs):
        """ change user to non audit user"""
        user = get_object_or_404(
            USER.objects.filter(
                id__in=self.filter_queryset(self.get_queryset()).values('user'),
            ),
            id=self.kwargs.get('pk')
        )
        if user == request.user:
            return Response(
                {'message': 'Can not act on own user'},
                403
            )
        result = self._disable_audit_user(user)
        if result:
            return Response({
                "detail" : "The user was changed to non audit user."
                })
        return Response({
            "detail": "Failed to change to non audit user. Perhaps the user is already a non audit user."
        }, 400)


    @action(methods=['post'], detail=True, url_path='block')
    def block_user(self, request, *args, **kwargs):
        """Block The User"""
        user = self.get_user()

        if user == request.user:
            return Response(
                {'message': 'Can not act on own user'},
                403
            )
        result = self._block_user(user)
        if result:
            return Response({
                "detail": "The user was blocked."
            })
        return Response({
                "detail": "Failed to block user. Perhaps the user is not active or already blocked."
        }, 400)

    @action(methods=['post'], detail=True, url_path='unblock')
    def unblock_user(self, request, *args, **kwargs):
        """Unblock The User"""
        if USER.objects.filter(is_active=True).count() >= settings.MAX_USERS_COUNT:
            raise serializers.ValidationError(
                f"Active user count cannot exceed {settings.MAX_USERS_COUNT}"
            )
        user = self.get_user()

        result = self._unblock_user(user)
        if result:
            return Response({
                "detail": "The user was unblocked."
            })

        return Response({
            "detail": "Failed to unblock user. Perhaps the user is not blocked."
        }, 400)

    @action(methods=['post'], detail=True, url_path='activate')
    def activate_user(self, request, *args, **kwargs):
        if USER.objects.filter(is_active=True).count() >= settings.MAX_USERS_COUNT:
            raise serializers.ValidationError(
                f"Active user count cannot exceed {settings.MAX_USERS_COUNT}"
            )
        user = self.get_user()

        serializer = self.get_serializer(instance=user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    @action(methods=['post'], detail=True, url_path='terminate',
            url_name='terminate')
    def terminate_user(self, request, *args, **kwargs):
        user = self.get_user()
        experience = user.current_experience
        if not experience:
            return Response(
                {'message': 'User has no current experience'},
                400
            )

        if user == request.user:
            return Response(
                {'message': 'Can not act on own user'},
                403
            )
        data = request.data
        remarks = data.get('reason_for_termination')
        serializer = self.get_serializer(instance=experience,
                                         data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger = logging.getLogger('irhrs.hris.api.v1.users')
        logger.warning(
            f'Terminated user {user} with remarks `{remarks}`. '
            f'Store properly.'
        )
        if experience.end_date == timezone.now().date():
            # deactivate user if resign date is today
            # add this to task if resign date is not today

            self._block_user(user)

            user.save()

            experience.is_current = False
        else:
            self._schedule_termination(experience)
        experience.save()

        userdetail = user.detail
        userdetail.last_working_date = experience.end_date
        userdetail.parting_reason = TERMINATED
        userdetail.save()

        return Response(
            {
                'message': f'Terminated user on {experience.end_date}'
            }
        )

    @property
    def detail_user(self):
        return get_object_or_404(
            USER.objects.all().filter(
                Q(detail__organization__isnull=True) |
                Q(detail__organization=self.get_organization())
            ), pk=self.kwargs.get('user_id')
        )

    @action(
        methods=['post'], detail=False,
        url_path=r'(?P<user_id>\d+)/terminate-inactive',
        serializer_class=CreatePastUserSerializer
    )
    def terminate_inactive(self, request, **kwargs):
        user = self.detail_user
        serializer = CreatePastUserSerializer(
            data=self.request.data,
            context={
                **self.get_serializer_context(),
                'user': user
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        self._block_user(user)
        return Response(
            serializer.data
        )

    @staticmethod
    def _block_user(user):
        if not user.is_active or user.is_blocked:
            return False
        user.is_active = False
        user.is_blocked = True
        user.save()
        return True

    @staticmethod
    def _unblock_user(user):
        if not user.is_blocked:
            return False
        user.is_active = True
        user.is_blocked = False
        user.save()
        return True

    @staticmethod
    def _enable_audit_user(user):
        if user.is_audit_user:
            return False
        user.is_audit_user = True
        user.save()
        return True

    @staticmethod
    def _disable_audit_user(user):
        if not user.is_audit_user:
            return False
        user.is_audit_user = False
        user.save()
        return True

    @staticmethod
    def annotate_service_period(queryset):
        qs = queryset.annotate(
            service_end_date=Case(
                When(user__detail__last_working_date__isnull=False, then=F(
                    'user__detail__last_working_date')),
                default=timezone.now().date(),
                output_field=DateField(),
            )
        ).annotate(
            duration=ExpressionWrapper(F('service_end_date') -
                                       F('user__detail__joined_date'),
                                       output_field=DurationField())
        )
        return qs

    def get_user(self):
        user = get_object_or_404(
            USER.objects.filter(
                id__in=self.filter_queryset(self.get_queryset()).values('user'),
            ),
            id=self.kwargs.get('pk')
        )
        return user


class UserDirectoryViewSet(HRSOrderingFilter, ListRetrieveViewSetMixin):
    """
    list:
    Returns the users whose experience has been defined.

    filter by supervisor using supervisor=user_id

    """

    filter_backends = (SearchFilter, OrderingFilter, FilterMapBackend)
    search_fields = (
        'first_name', 'middle_name', 'last_name', 'username'
    )
    ordering_fields_map = {
        'full_name': ('first_name',
                      'middle_name',
                      'last_name')
    }
    filter_map = {
        'organization': 'detail__organization__slug',
        'email' : 'email',
        'branch' : 'detail__branch'
    }
    ordering = '-detail__joined_date'

    def get_serializer_class(self):
        if self.action == 'list':
            return UserDirectorySerializer
        elif self.action == 'retrieve':
            return UserDirectoryDetailSerializer

    def get_queryset(self):
        system_admin = get_system_admin()
        if system_admin:
            exclude = {'pk': system_admin.pk}
        else:
            exclude = {}
        queryset = USER.objects.exclude(**exclude).current().filter(
            detail__joined_date__lte=get_today()
        ).select_related(
            'detail',
            'detail__organization',
            'detail__division',
            'detail__employment_level',
            'detail__job_title',
            'detail__branch'
        ).prefetch_related(
            Prefetch('supervisors',
                     queryset=UserSupervisor.objects.filter(authority_order=1)
                     .select_related('supervisor',
                                     'supervisor__detail',
                                     'supervisor__detail__organization',
                                     'supervisor__detail__job_title',
                                     'supervisor__detail__division',
                                     'supervisor__detail__employment_level'),
                     to_attr='user_supervisors')
        )
        # INFO irhrs.users.models.user.User#first_level_supervisor
        # irhrs.users.models.user.User#user_supervisors
        # to_attr='user_supervisors' will be used as in first_level_supervisor
        organization = self.request.query_params.get('organization')
        if organization:
            queryset = queryset.filter(
                detail__organization=get_object_or_404(
                    Organization, slug=organization
                )
            )

        supervisor_filter_activated = self.request.query_params.get('supervisor', None)
        if supervisor_filter_activated:
            supervisor = self._get_supervisor()
            if supervisor:
                queryset = queryset.filter(
                    id__in=supervisor.subordinates_pks)
            else:
                queryset = queryset.none()

        return queryset.distinct()

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        if settings.ORGANIZATION_SPECIFIC_EMPLOYEE_DIRECTORY:
            supervisor_filter_activated = self.request.query_params.get(
                'supervisor', None)
            supervisor = self._get_supervisor()
            if not hasattr(self.request.user, 'detail'):
                return queryset.none()
            if supervisor:
                queryset = queryset.filter(
                    id__in=supervisor.subordinates_pks)
            else:
                return queryset.filter(detail__organization=self.request.user.detail.organization)

        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data['organization_specific'] = settings.ORGANIZATION_SPECIFIC_EMPLOYEE_DIRECTORY
        return response

    def _get_supervisor(self):
        try:
            supervisor_id = self.request.query_params.get('supervisor')
            return USER.objects.get(id=supervisor_id)
        except (TypeError, ValueError, DjValidationError, ObjectDoesNotExist):
            return None
