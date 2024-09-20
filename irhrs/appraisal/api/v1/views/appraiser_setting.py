import types
from collections import defaultdict

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Prefetch, Exists, OuterRef, Q, Count, Case, When, CharField, Value, F, \
    ExpressionWrapper, DurationField, Sum
from django.http import Http404, HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from irhrs.appraisal.api.v1.permissions import PerformanceAppraisalSettingPermission
from irhrs.appraisal.api.v1.serializers.appraiser_setting import (
    SupervisorAppraiserSettingListSerializer, AppraiserSettingBulkAssignSerializer,
    AppraiserSettingIndividualAssignSerializer, SupervisorAppraiserSettingActionSerializer,
    PeerToPeerFeedBackSettingCreateSerializer, PeerToPeerFeedBackSettingListSerializer,
    SubordinateAppraiserSettingListSerializer, SubordinateAppraiserSettingActionSerializer,
    SubordinateAppraiserSettingUpdateSerializer, AppraisalListSerializer,
    AppraisalQuestionSetSerializer, PerformanceAppraisalUserThinSerializer,
    SelfAppraisalSettingListSerializer, SelfAppraisalSettingSerializer,
    ApproveAllAppraisalSerializer, EditDeadlineOfAppraisalSerializer, RemoveAppraisalSerializer,
    ReviewerEvaluationSettingActionSerializer, ReviewerEvaluationSettingListSerializer,
    SupervisorAppraiserConfigSerializer, ReviewerAppraiserConfigBulkAssign,
    KAARSupervisorAppraiserListSerializer, SupervisorIndividualAssignSerializer,
    ReviewerIndividualAssignSerializer, SupervisorAppraiserConfigBulkAssign,
    KAARSupervisorImportSerializer, ReviewerImportSerializer
)
from irhrs.appraisal.api.v1.serializers.question_set import \
    ValidateQuestionSetSerializer
from irhrs.appraisal.api.v1.serializers.performance_appraisal import ResendPAFormSerializer
from irhrs.appraisal.api.v1.views.performance_appraisal import SubPerformanceAppraisalMixin
from irhrs.appraisal.constants import (
    SUBORDINATE_APPRAISAL, SELF_APPRAISAL, SUPERVISOR_APPRAISAL,
    PEER_TO_PEER_FEEDBACK, PERCENTAGE, REVIEWER_EVALUATION
)
from irhrs.appraisal.models.appraiser_setting import Appraisal
from irhrs.appraisal.models.key_achievement_and_rating_pa import KAARAppraiserConfig
from irhrs.appraisal.models.performance_appraisal import SubPerformanceAppraisalSlotMode, \
    SubPerformanceAppraisalSlotWeight, SubPerformanceAppraisalSlot, \
    SubPerformanceAppraisalYearWeight
from irhrs.appraisal.models.performance_appraisal_setting import FormReviewSetting, \
    DeadlineExceedScoreDeductionCondition
from irhrs.appraisal.utils.common import get_user_appraisal_score_for_year
from irhrs.appraisal.utils.printable_export import generate_printable_document
from irhrs.appraisal.utils.util import AppraisalSettingFilterMixin
from irhrs.appraisal.utils.generate_question_set import calculate_obtained_score
from irhrs.core.mixins.file_import_mixin import BackgroundFileImportMixin
from irhrs.core.mixins.serializers import DummySerializer
from irhrs.core.mixins.viewset_mixins import (
    ListViewSetMixin, ListCreateViewSetMixin, OrganizationMixin, CreateViewSetMixin
)
from irhrs.core.utils import get_system_admin
from irhrs.core.utils.common import validate_permissions, get_today
from irhrs.core.utils.filters import OrderingFilterMap
from irhrs.notification.utils import add_notification, notify_organization
from irhrs.permission.constants.permissions import PERFORMANCE_APPRAISAL_PERMISSION, \
    PERFORMANCE_APPRAISAL_SETTING_PERMISSION, HAS_PERMISSION_FROM_METHOD, HRIS_PERMISSION
from irhrs.permission.permission_classes import permission_factory
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from irhrs.users.models import UserSupervisor

User = get_user_model()


class SelfAppraiserSettingViewSet(AppraisalSettingFilterMixin, ListViewSetMixin):
    appraisal_type = SELF_APPRAISAL
    permission_classes = [PerformanceAppraisalSettingPermission]

    def get_serializer_class(self):
        if self.action == 'edit_user':
            return SelfAppraisalSettingSerializer
        elif self.action == 'assign_all':
            return DummySerializer
        return SelfAppraisalSettingListSerializer

    def get_queryset(self):
        return super().get_queryset(union=False).filter(
            detail__organization=self.organization
        ).annotate(
            is_selected=Exists(
                Appraisal.objects.filter(
                    sub_performance_appraisal_slot=self.performance_appraisal_slot,
                    appraisee=OuterRef('id'),
                    appraiser=OuterRef('id'),
                    appraisal_type=SELF_APPRAISAL
                )
            )
        )

    @action(
        detail=False,
        methods=['post'],
        url_path='edit-users'
    )
    def edit_user(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=self.request.data
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.data

        appraisers = set(data.get('users'))
        filtered_users = set(self.get_queryset().values_list('id', flat=True))

        if not appraisers.issubset(filtered_users):
            raise ValidationError({
                'users': ['Users doesn\'t satisfy filter within setting.']
            })

        self_appraisers = set(
            Appraisal.objects.filter(
                sub_performance_appraisal_slot=self.performance_appraisal_slot,
                appraisal_type=SELF_APPRAISAL
            ).values_list('appraiser', flat=True)
        )
        deleted_appraisers = self_appraisers - appraisers
        new_appraisers = appraisers - self_appraisers

        if deleted_appraisers:
            Appraisal.objects.filter(
                sub_performance_appraisal_slot=self.performance_appraisal_slot,
                appraiser_id__in=deleted_appraisers,
                appraisal_type=SELF_APPRAISAL
            ).delete()

        appraisals = []

        if new_appraisers:
            for appraiser in new_appraisers:
                appraisals.append(
                    Appraisal(
                        sub_performance_appraisal_slot=self.performance_appraisal_slot,
                        appraisee_id=appraiser,
                        appraiser_id=appraiser,
                        appraisal_type=SELF_APPRAISAL
                    )
                )

        if appraisals:
            Appraisal.objects.bulk_create(appraisals)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['post'],
        url_path='assign/all'
    )
    def assign_all(self, request, *args, **kwargs):
        users = self.get_queryset()

        self_appraisals = []
        for user in users:
            self_appraisals.append(
                Appraisal(
                    sub_performance_appraisal_slot=self.performance_appraisal_slot,
                    appraisee=user,
                    appraiser=user,
                    appraisal_type=SELF_APPRAISAL
                )
            )

        if self_appraisals:
            Appraisal.objects.bulk_create(self_appraisals)
        return Response(
            SelfAppraisalSettingListSerializer(
                users,
                fields=(
                    'id', 'full_name', 'profile_picture', 'job_title',
                    'is_online'
                ),
                many=True
            ).data,
            status=status.HTTP_200_OK
        )


class SupervisorAppraiserSettingViewSet(AppraisalSettingFilterMixin, ListViewSetMixin):
    appraisal_type = SUPERVISOR_APPRAISAL
    serializer_class = SupervisorAppraiserSettingListSerializer
    permission_classes = [PerformanceAppraisalSettingPermission]

    def get_serializer_class(self):
        if self.action == 'assign_action':
            if self.kwargs.get('action_type') == 'bulk':
                return AppraiserSettingBulkAssignSerializer
            return AppraiserSettingIndividualAssignSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        queryset = super().get_queryset(union=False)
        return queryset.filter(
            detail__organization=self.organization,
            supervisors__isnull=False
        ).prefetch_related(
            Prefetch(
                'supervisors',
                queryset=UserSupervisor.objects.exclude(
                    supervisor=get_system_admin()
                ).annotate(
                    is_selected=Exists(
                        Appraisal.objects.filter(
                            sub_performance_appraisal_slot=self.performance_appraisal_slot,
                            appraisee=OuterRef('user'),
                            appraiser=OuterRef('supervisor')
                        )
                    )
                ).select_related(
                    'supervisor__detail', 'supervisor__detail__job_title'
                ),
                to_attr='user_supervisors'
            )
        ).select_related('detail', 'detail__job_title').order_by('first_name')

    @action(
        methods=['POST'],
        detail=False,
        url_path=r'(?P<action>(assign|unassign))/(?P<action_type>(bulk|individual))'
    )
    def assign_action(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        context = self.get_serializer_context()
        authority_level = data.get('authority_level')
        context.update({
            'authority_level': authority_level,
            'action': kwargs.get('action')
        })
        if kwargs.get('action_type') == 'bulk':
            users = self.filter_queryset(self.get_queryset()).filter(
                supervisors__isnull=False,
                supervisors__authority_order=authority_level
            )
            serializer_data = dict(
                many=True,
                data=[{'user': user.id} for user in users],
                context=context
            )
        else:
            user = data.get('user')
            if not user.supervisors.filter(authority_order=authority_level).exists():
                raise ValidationError({
                    'authority_level': ['User doesn\'t have supervisor with this authority order.']
                })
            serializer_data = dict(
                data={'user': user.id},
                context=context
            )
        multiple_serializer = SupervisorAppraiserSettingActionSerializer(
            **serializer_data)
        multiple_serializer.is_valid(raise_exception=True)
        multiple_serializer.save()
        return Response(multiple_serializer.data, status=status.HTTP_200_OK)


class SupervisorAppraiserConfigViewSet(
    AppraisalSettingFilterMixin,
    BackgroundFileImportMixin,
    ListViewSetMixin
):
    appraisal_type = SUPERVISOR_APPRAISAL
    serializer_class = KAARSupervisorAppraiserListSerializer
    permission_classes = [PerformanceAppraisalSettingPermission]
    import_serializer_class = KAARSupervisorImportSerializer
    sample_file_name = 'Supervisor Import'
    background_task_name = 'kaar_supervisor_import'
    import_fields = ['User', 'Supervisor']
    values = ['Username/Email', 'Username/Email']

    def get_success_url(self):
        success_url = f'/admin/pa/settings/frequency-and-mode/{self.performance_appraisal_slot.id}/kaar-appraiser'
        return success_url

    def get_failed_url(self):
        failed_url = f'/admin/pa/settings/frequency-and-mode/{self.performance_appraisal_slot.id}/kaar-appraiser'
        return failed_url

    def get_serializer_class(self):
        if self.action == 'assign_action':
            if self.kwargs.get('action_type') == 'bulk':
                return SupervisorAppraiserConfigBulkAssign
            return SupervisorIndividualAssignSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        queryset = super().get_queryset(union=False)
        return queryset.filter(
            detail__organization=self.organization,
            supervisors__isnull=False
        ).prefetch_related(
            Prefetch(
                'supervisors',
                queryset=UserSupervisor.objects.exclude(
                    supervisor=get_system_admin()
                ).annotate(
                    is_selected=Exists(
                        KAARAppraiserConfig.objects.filter(
                            kaar_appraisal__sub_performance_appraisal_slot=self.performance_appraisal_slot,
                            kaar_appraisal__appraisee=OuterRef('user'),
                            appraiser=OuterRef('supervisor'),
                            appraiser_type=SUPERVISOR_APPRAISAL
                        )
                    )
                ).select_related(
                    'supervisor__detail', 'supervisor__detail__job_title'
                ),
                to_attr='user_supervisors'
            )
        ).select_related('detail', 'detail__job_title').order_by('first_name')

    @action(
        methods=['POST'],
        detail=False,
        url_path=r'(?P<action>(assign|unassign))/(?P<action_type>(bulk|individual))'
    )
    def assign_action(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        context = self.get_serializer_context()
        authority_level = data.get('authority_level')
        supervisor = data.get('supervisor')
        context.update({
            'authority_level': authority_level,
            'supervisor': supervisor,
            'action': kwargs.get('action')
        })
        if kwargs.get('action_type') == 'bulk':
            fil = {}
            exclude_fil = {}
            if authority_level:
                fil = {
                    'supervisors__isnull': False,
                    'supervisors__authority_order': authority_level
                }
                exclude_fil = {'supervisors__supervisor': get_system_admin()}
            users = self.filter_queryset(self.get_queryset()).filter(
                **fil
            ).exclude(**exclude_fil)
            serializer_data = dict(
                many=True,
                data=[{'user': user.id} for user in users],
                context=context
            )
        else:
            user = data.get('user')
            supervisors = user.supervisors.exclude(
                supervisor=get_system_admin()
            ).filter(authority_order=authority_level)
            if authority_level and not supervisors.exists():
                raise ValidationError({
                    'authority_level': ['User doesn\'t have supervisor with this authority order.']
                })
            serializer_data = dict(
                data={'user': user.id},
                context=context
            )
        multiple_serializer = SupervisorAppraiserConfigSerializer(
            **serializer_data)
        multiple_serializer.is_valid(raise_exception=True)
        multiple_serializer.save()
        return Response(multiple_serializer.data, status=status.HTTP_200_OK)


class ReviewerEvaluationSettingViewSet(
    AppraisalSettingFilterMixin,
    BackgroundFileImportMixin,
    ListViewSetMixin
):
    appraisal_type = REVIEWER_EVALUATION
    serializer_class = ReviewerEvaluationSettingListSerializer
    permission_classes = [PerformanceAppraisalSettingPermission]

    import_serializer_class = ReviewerImportSerializer
    sample_file_name = 'Supervisor Import'
    background_task_name = 'kaar_supervisor_import'
    import_fields = ['User', 'Reviewer']
    values = ['Username/Email', 'Username/Email']

    def get_success_url(self):
        success_url = f'/admin/pa/settings/frequency-and-mode/{self.performance_appraisal_slot.id}/kaar-appraiser'
        return success_url

    def get_failed_url(self):
        failed_url = f'/admin/pa/settings/frequency-and-mode/{self.performance_appraisal_slot.id}/kaar-appraiser'
        return failed_url

    def get_serializer_class(self):
        if self.action == 'assign_action':
            if self.kwargs.get('action_type') == 'bulk':
                return ReviewerAppraiserConfigBulkAssign
            return ReviewerIndividualAssignSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        queryset = super().get_queryset(union=False)
        return queryset.filter(
            detail__organization=self.organization,
            supervisors__isnull=False
        ).prefetch_related(
            Prefetch(
                'supervisors',
                queryset=UserSupervisor.objects.exclude(
                    supervisor=get_system_admin()
                ).select_related(
                    'supervisor__detail', 'supervisor__detail__job_title'
                ),
                to_attr='user_supervisors'
            )
        ).select_related('detail', 'detail__job_title').order_by('first_name')

    @action(
        methods=['POST'],
        detail=False,
        url_path=r'(?P<action>(assign|unassign))/(?P<action_type>(bulk|individual))'
    )
    def assign_action(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        context = self.get_serializer_context()
        authority_level = data.get('authority_level')
        reviewer = data.get('reviewer')
        context.update({
            'action': kwargs.get('action')
        })
        if reviewer:
            context['reviewer'] = reviewer
        if authority_level:
            context['authority_level'] = authority_level
        if kwargs.get('action_type') == 'bulk':
            fil = {'supervisors__isnull': False}
            exclude_fil = {}
            if authority_level:
                fil['supervisors__authority_order'] = authority_level
                exclude_fil = {'supervisors__supervisor': get_system_admin()}
            users = self.filter_queryset(self.get_queryset()).exclude(
                **exclude_fil
            ).filter(
                **fil
            )
            serializer_data = dict(
                many=True,
                data=[{'user': user.id} for user in users],
                context=context
            )
        else:
            user = data.get('user')
            supervisors = user.supervisors.filter(
                authority_order=authority_level
            ).exclude(supervisor=get_system_admin())
            if authority_level and not supervisors.exists():
                raise ValidationError({
                    'authority_level': ['User doesn\'t have supervisor with this authority order.']
                })
            serializer_data = dict(
                data={'user': user.id},
                context=context
            )
        multiple_serializer = ReviewerEvaluationSettingActionSerializer(
            **serializer_data)
        multiple_serializer.is_valid(raise_exception=True)
        multiple_serializer.save()
        return Response(multiple_serializer.data, status=status.HTTP_200_OK)


class PeerToPeerFeedBackSettingViewSet(AppraisalSettingFilterMixin, ListCreateViewSetMixin):
    """
    #List:

        URL: api/v1/appraisal/{org_slug}/year/slot/{sub_pa_id}/setting/peer-to-peer--appraiser/

        Method: Get

        Data:

            {
                "count": 2,
                "next": null,
                "previous": null,
                "results": [
                    {
                        "id": 282,
                        "full_name": "Ishan Subedi",
                        "profile_picture": "http://localhost:8000/media/cache/d0/0f/d00f.png",
                        "job_title": "Senior Software Engineer",
                        "is_online": false
                        "no_of_appraisers": 1,
                        "appraisers": [
                            {
                                "id": 1,
                                "full_name": "Rajesh Shrestha",
                                "profile_picture": "http://localhost:8000/media/cache/6a/da/c7.png",
                                "job_title": "jobs titles 1",
                                "is_online": false
                            }
                        ]
                    },
                    {

                        "id": 1,
                        "full_name": "Rajesh Shrestha",
                        "profile_picture": "http://localhost:8000/media/cache/6a/da/4c0c7.png",
                        "job_title": "jobs titles 1",
                        "is_online": false
                        "no_of_appraisers": 1,
                        "appraisers": [
                            {
                                "id": 282,
                                "full_name": "Ishan Subedi",
                                "profile_picture": "http://localhost:8000/media/cache/d0/f/108.png",
                                "job_title": "Senior Software Engineer",
                                "is_online": false
                            }
                        ]
                    }
                ]
            }

    # Create or update Peer to peer appraisee

        URL:/api/v1/appraisal/{org_slug}/year/slot/{sub_pa_id}/setting/peer-to-peer–appraiser/

        Method: Post

        Data:

            {
                "add_default": false,
                "appraisee": 'user id',
                "appraisers": [user ids],
                "remarks": ""
            }


    """
    appraisal_type = PEER_TO_PEER_FEEDBACK
    permission_classes = [PerformanceAppraisalSettingPermission]

    def get_serializer_class(self):
        if self.request.method.lower() == 'get':
            return PeerToPeerFeedBackSettingListSerializer
        return PeerToPeerFeedBackSettingCreateSerializer

    def get_queryset(self):
        queryset = super().get_queryset(union=False)
        return queryset.filter(
            detail__organization=self.organization,
        ).prefetch_related(
            'as_appraisees'
        ).select_related(
            'detail', 'detail__job_title',
        ).order_by('first_name')

    def add_appraisee_within_appraiser(self, validated_data):
        if validated_data.get('add_default'):
            appraisee = validated_data.get('appraisee')
            appraisers = validated_data.get('appraisers')

            for appraiser in appraisers:
                _ = Appraisal.objects.get_or_create(
                    sub_performance_appraisal_slot=self.performance_appraisal_slot,
                    appraisee=appraiser,
                    appraiser=appraisee,
                    appraisal_type=PEER_TO_PEER_FEEDBACK
                )

    @transaction.atomic()
    def perform_create(self, serializer):
        instance = super().perform_create(serializer)
        self.add_appraisee_within_appraiser(serializer.validated_data)
        return instance


class SubordinateAppraiserSettingViewSet(AppraisalSettingFilterMixin, ListViewSetMixin):
    serializer_class = SubordinateAppraiserSettingListSerializer
    appraisal_type = SUBORDINATE_APPRAISAL
    permission_classes = [PerformanceAppraisalSettingPermission]

    def get_queryset(self):
        return super().get_queryset(union=False).filter(
            detail__organization=self.organization,
            as_supervisor__isnull=False,
            as_supervisor__user__is_active=True
        ).select_related(
            'detail', 'detail__organization', 'detail__branch', 'detail__division',
            'detail__employment_status', 'detail__employment_level'
        )

    def get_serializer_class(self):
        if self.action == 'assign_action':
            if self.kwargs.get('action_type') == 'bulk':
                return AppraiserSettingBulkAssignSerializer
            return AppraiserSettingIndividualAssignSerializer
        return super().get_serializer_class()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.action == 'edit_users':
            context['evaluatee'] = self.kwargs.get('user_id')
        return context

    @action(
        detail=False,
        methods=['POST'],
        url_path=r'(?P<action>(assign|unassign))/(?P<action_type>(bulk|individual))'
    )
    def assign_action(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        context = self.get_serializer_context()
        authority_level = data.get('authority_level')
        context.update({
            'authority_level': authority_level,
            'action': kwargs.get('action')
        })
        if kwargs.get('action_type') == 'bulk':
            users = self.filter_queryset(self.get_queryset()).filter(
                as_supervisor__authority_order=authority_level
            )
            if not users:
                raise Http404
            serializer_data = dict(
                many=True,
                data=[{'user': user.id} for user in users],
                context=context
            )
        else:
            user = data.get('user')
            if not user.as_supervisor.filter(authority_order=authority_level).exists():
                raise ValidationError({
                    'authority_level': [
                        'User doesn\'t have subordinate with this authority order.']
                })
            if not user:
                raise Http404
            serializer_data = dict(
                data={'user': user.id},
                context=context
            )

        multiple_serializer = SubordinateAppraiserSettingActionSerializer(
            **serializer_data)
        multiple_serializer.is_valid(raise_exception=True)
        multiple_serializer.save()
        return Response(multiple_serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['post'],
        detail=False,
        serializer_class=SubordinateAppraiserSettingUpdateSerializer,
        url_path=r'(?P<user_id>\d+)'
    )
    def edit_users(self, request, *args, **kwargs):
        context = self.get_serializer_context()
        context['appraisee'] = kwargs.get('user_id')
        serializer = self.get_serializer(
            data=request.data,
            context=context
        )

        serializer.is_valid(raise_exception=True)
        data = serializer.data

        authority_level = data.get("authority_level")
        new_subordinates = set(data.get('users'))

        authority_level_subordinates = set(
            User.objects.filter(
                supervisors__supervisor_id=kwargs.get('user_id'),
                supervisors__authority_order=data.get('authority_level')
            ).values_list('id', flat=True)
        )

        if not new_subordinates.issubset(authority_level_subordinates):
            level = {1: 'st', 2: 'nd', 3: 'rd'}
            raise ValidationError({
                'users': [
                    f'Users must be an subordinate of authority'
                    f' level {authority_level}{level.get(authority_level)}.'
                ]
            })

        assigned_subordinates = set(
            Appraisal.objects.filter(
                sub_performance_appraisal_slot=self.performance_appraisal_slot,
                appraisee=kwargs.get('user_id'),
                appraisal_type=SUBORDINATE_APPRAISAL
            ).values_list('appraiser', flat=True)
        )
        deleted_subordinates = authority_level_subordinates - new_subordinates

        if deleted_subordinates:
            Appraisal.objects.filter(
                sub_performance_appraisal_slot=self.performance_appraisal_slot,
                appraisee=kwargs.get('user_id'),
                appraiser_id__in=deleted_subordinates,
                appraisal_type=SUBORDINATE_APPRAISAL
            ).delete()

        subordinates = new_subordinates - assigned_subordinates
        if subordinates:
            subordinate_object = []
            for subordinate in subordinates:
                subordinate_object.append(
                    Appraisal(
                        sub_performance_appraisal_slot=self.performance_appraisal_slot,
                        appraisee_id=kwargs.get('user_id'),
                        appraiser_id=subordinate,
                        appraisal_type=SUBORDINATE_APPRAISAL
                    )
                )

            if subordinate_object:
                Appraisal.objects.bulk_create(subordinate_object)
        return Response(serializer.data)

    @action(
        methods=['get'],
        detail=False,
        url_path='selected-subordinates',
        serializer_class=AppraiserSettingIndividualAssignSerializer
    )
    def subordinate_list(self, request, *args, **kwargs):
        user = request.query_params.get('user')
        authority_order = request.query_params.get('authority_level')

        if not user:
            raise ValidationError({
                'user': 'User filter is required.'
            })

        if not authority_order:
            raise ValidationError({
                'authority_order': 'Authority order filter is required.'
            })

        if not str(authority_order) in ['1', '2', '3']:
            raise ValidationError({
                'authority_level': 'Authority level must be 1, 2 or 3.'
            })

        subordinate_serializer = PerformanceAppraisalUserThinSerializer(
            User.objects.filter(
                supervisors__supervisor=user,
                supervisors__authority_order=authority_order
            ).current().annotate(
                is_selected=Exists(
                    Appraisal.objects.filter(
                        sub_performance_appraisal_slot=self.performance_appraisal_slot,
                        appraisee=user,
                        appraiser=OuterRef('id')
                    )
                )
            ).select_related(
                'detail', 'detail__job_title'
            ),
            fields=(
                'id', 'full_name', 'profile_picture', 'job_title',
                'is_online', 'is_selected'
            ),
            many=True
        )
        return Response(subordinate_serializer.data, status=status.HTTP_200_OK)


class ListOfAppraiserWithRespectToAppraiseeViewSet(OrganizationMixin, SubPerformanceAppraisalMixin,
                                                   ListViewSetMixin):
    serializer_class = AppraisalListSerializer
    queryset = Appraisal.objects.all()
    filter_backends = (SearchFilter, OrderingFilterMap)
    ordering_fields_map = {
        'appraiser': ('appraiser__first_name', 'appraiser__middle_name', 'appraiser__last_name'),
        'sent_at': 'start_date',
        'deadline': 'deadline',
        'committed_at': 'committed_at',
        'approved_at': 'approved_at'
    }
    search_fields = (
        'appraiser__first_name', 'appraiser__middle_name', 'appraiser__last_name'
    )

    permission_classes = [
        permission_factory.build_permission(
            'ListOfAppraiserWithRespectToAppraiseePermission',
            allowed_to=[HAS_PERMISSION_FROM_METHOD]
        )
    ]

    def has_user_permission(self):
        if self.request.query_params.get('as') == 'hr':
            return validate_permissions(
                self.request.user.get_hrs_permissions(self.get_organization()),
                PERFORMANCE_APPRAISAL_PERMISSION,
                PERFORMANCE_APPRAISAL_SETTING_PERMISSION
            )
        if self.action == 'question_set':
            appraisal_type = self.request.query_params.get(
                'appraisal_type'
            )
            if not appraisal_type:
                return False
            return Appraisal.objects.filter(
                appraisee=self.kwargs.get('appraisee_id'),
                sub_performance_appraisal_slot=self.kwargs.get(
                    'sub_performance_appraisal_slot_id'),
                appraisal_type=appraisal_type.replace('_', ' ').title(),
                appraiser=self.request.user
            ).exists()

        if str(self.kwargs.get(
            'appraisee_id'
        )) == str(self.request.user.id):
            return True

        return False

    def get_queryset(self):
        appraisal_type = self.request.query_params.get('appraisal_type')
        if not appraisal_type:
            raise ValidationError(
                {
                    'detail': 'Appraisal Type must be supplied.'
                }
            )
        else:
            appraisal_type = appraisal_type.replace('_', ' ').title()

        return super().get_queryset().filter(
            appraisee=self.kwargs.get('appraisee_id'),
            sub_performance_appraisal_slot=self.performance_appraisal_slot,
            appraisal_type=appraisal_type
        ).annotate(
            status=Case(
                When(
                    condition=Q(
                        answer_committed=True,
                        approved=True
                    ),
                    then=Value('approved')
                ),
                When(
                    condition=Q(
                        answer_committed=True,
                        approved=False
                    ),
                    then=Value('received')
                ),
                When(
                    condition=Q(
                        answer_committed=False,
                        approved=False,
                        is_draft=True,
                    ),
                    then=Value('saved')
                ),
                default=Value('sent'),
                output_field=CharField()
            )
        )

    def filter_queryset(self, queryset):
        status = self.request.query_params.get('status')

        fil = {}
        if status:
            fil = dict(status=status)
        return super().filter_queryset(queryset).filter(**fil)

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            kwargs.update({
                'exclude_fields': ['appraisee']
            })
        return super().get_serializer(*args, **kwargs)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data['appraisee'] = UserThinSerializer(
            User.objects.filter(id=self.kwargs.get('appraisee_id')).first(),
            fields=(
                'id', 'full_name', 'profile_picture', 'job_title',
                'is_online', 'is_current', 'organization',
            )
        ).data

        stats = self.get_queryset().aggregate(
            total=Count('id'),
            sent=Count(
                'id',
                Q(
                    answer_committed=False,
                    approved=False,
                    is_draft=False
                )
            ),
            saved=Count(
                'id',
                Q(
                    answer_committed=False,
                    approved=False,
                    is_draft=True
                )
            ),
            approved_count=Count(
                'id',
                Q(
                    answer_committed=True,
                    approved=True
                )
            ),
            received=Count(
                'id',
                Q(
                    answer_committed=True,
                    approved=False
                )
            )
        )
        response.data['stats'] = dict(
            total=stats['total'],
            sent=stats['sent'],
            saved=stats['saved'],
            approved=stats['approved_count'],
            received=stats['received']
        )
        return response

    @property
    def appraisal(self):
        return self.get_queryset().filter(
            appraiser_id=self.kwargs.get('appraiser_id')
        ).first()

    @action(
        detail=False,
        methods=['get'],
        url_path=r'(?P<appraiser_id>\d+)/question-set',
        serializer_class=AppraisalQuestionSetSerializer
    )
    def question_set(self, request, *args, **kwargs):
        appraisal = self.appraisal
        if not appraisal:
            raise Http404
        return Response(
            self.get_serializer(
                appraisal
            ).data,
            status=status.HTTP_200_OK
        )

    def final_score_calculation_after_score_deduction(self, appraisal):
        instance = Appraisal.objects.filter(
            sub_performance_appraisal_slot=self.performance_appraisal_slot,
            committed_at__gt=F('deadline'),
            appraiser=appraisal.appraiser
        ).annotate(
            exceeded_by=ExpressionWrapper(
                F('committed_at') - F('deadline'),
                output_field=DurationField()
            )
        ).order_by('exceeded_by').last()

        if instance:
            exceed_days = instance.exceeded_by.days

            # if exceed_days crosses by some seconds, exceed_days is incremented by 1
            exceed_seconds = instance.exceeded_by.seconds
            if 0 < exceed_seconds < 86400:
                exceed_days += 1

            # if exceed_days go beyond the deadline rule, then max `total_exceed_days` is used
            get_exceed_days = DeadlineExceedScoreDeductionCondition.objects.values_list(
                'total_exceed_days_to', flat=True
            ).last()
            if get_exceed_days and (exceed_days > get_exceed_days):
                exceed_days = get_exceed_days

            deduction_condition = self.performance_appraisal_slot.deduction_condition.filter(
                total_exceed_days_from__lte=exceed_days,
                total_exceed_days_to__gte=exceed_days
            ).first()

            deduct_value = getattr(deduction_condition, 'deduct_value', 0)
            deduction_type = getattr(
                deduction_condition, 'deduction_type', PERCENTAGE)
            final_score = appraisal.final_score

            if deduction_type == PERCENTAGE:
                score_deduction_factor = final_score * deduct_value / 100
            else:
                score_deduction_factor = deduct_value

            final_score -= score_deduction_factor
            return final_score if final_score > 0 else 0, score_deduction_factor

        else:
            final_score = appraisal.final_score
            score_deduction_factor = 0
            return final_score, score_deduction_factor

    @action(
        detail=False,
        methods=['post'],
        url_path=r'(?P<appraiser_id>\d+)/approve',
        serializer_class=DummySerializer
    )
    def approve_given_answer(self, request, *args, **kwargs):
        appraisal = self.get_queryset().filter(
            appraiser_id=kwargs.get('appraiser_id')).first()
        # slot_id = kwargs.get('sub_performance_appraisal_slot_id')
        if not appraisal:
            raise Http404

        if not appraisal.answer_committed:
            raise ValidationError({
                'detail': ['Answers must be committed before attempting to approve.']
            })

        if appraisal.approved:
            raise ValidationError({
                'detail': ['This appraisal has already been approved.']
            })

        if not appraisal.question_set:
            raise ValidationError({
                'detail': ['There must be question set before attempting to approve']
            })

        appraisal.approved = True
        appraisal.approved_at = timezone.now()
        appraisal.final_score = calculate_obtained_score(
            appraisal.question_set)
        final_score, score_deduction_factor = self.final_score_calculation_after_score_deduction(
            appraisal)
        appraisal.final_score = final_score
        appraisal.score_deduction_factor = score_deduction_factor

        # Start: This section calculates approved appraiser's final score

        # calculates eligible employee for sub_performance_slot's type
        eligible_appraiser = Appraisal.objects.filter(
            appraisee=appraisal.appraisee,
            sub_performance_appraisal_slot=appraisal.sub_performance_appraisal_slot,
            question_set__isnull=False
        )
        # count of eligible appraisee
        question_set_count = len(eligible_appraiser)

        # count of approved performance appraisal mode
        approved_question_set_count = len(
            list(filter(
                lambda x: x.approved is True,
                eligible_appraiser
            ))
        )

        # Checks whether appraisee is eligible
        # Condition ensures that only one mode_of_appraisal is left for approval
        if question_set_count and (approved_question_set_count == (question_set_count - 1)):
            mode = SubPerformanceAppraisalSlotMode.objects.filter(
                sub_performance_appraisal_slot=appraisal.sub_performance_appraisal_slot
            )
            appraisal_types_and_weightages_of_pa_modes = mode.values(
                'appraisal_type', 'weightage')

            weightage_of_pa_modes = dict()

            unique_eligible_appraisal_type = {item.appraisal_type for item in eligible_appraiser}

            sum_of_weight_of_appraisal_types = mode.filter(
                    appraisal_type__in=unique_eligible_appraisal_type
                ).aggregate(total_weightage=Sum("weightage")).get('total_weightage')

            '''
            calculates distributable_weightage

            Example:
                if appraisee is eligible only for self_appraisal and peer_to_peer_feedback having
                respective weightage of 20 and 40 then, distributable_weightage will be:

                    (100 - (20+40))/2 = 20

                Now, 20 score will be added to self_appraisal and peer_to_peer_feedback each so,
                the final score will be:
                    self_appraisal_weightage = 20 + 20 =40
                    peer_to_peer_feedback_weightage = 40 + 20 = 60
            '''
            distributable_weightage = (
                100 - sum_of_weight_of_appraisal_types) / len(unique_eligible_appraisal_type)

            # distribute weightage equally among eligible appraisal_types
            for item in appraisal_types_and_weightages_of_pa_modes:
                name = item['appraisal_type']
                weightage_of_pa_modes[name] = item['weightage'] + \
                    distributable_weightage
            percentage_of_slot = 0
            appraisal_list = list()
            appraisal_list.append(appraisal)

            # list all appraisal to calculate percentage
            appraisal_list += list(eligible_appraiser.filter(approved=True))

            '''
                REFERENCE: https://howchoo.com/python/nested-defaultdict-python

                we can easily populate our data structure without having to initialize each value
                For example:
                    appraisal_type_score_and_count['abc']['def'] = 0
            '''

            appraisal_type_score_and_count = defaultdict(
                lambda: defaultdict(dict))

            for item in appraisal_list:
                appraisal_type_weightage = weightage_of_pa_modes.get(
                    item.appraisal_type)
                appraisal_type = item.appraisal_type

                # Initializing default value
                if not appraisal_type_score_and_count[appraisal_type]['percentage']:
                    appraisal_type_score_and_count[appraisal_type]['percentage'] = 0

                if not appraisal_type_score_and_count[appraisal_type]['count']:
                    appraisal_type_score_and_count[appraisal_type]['count'] = 0

                if item.total_score == 0:
                    raise ValidationError(
                        f"Total score for {appraisal_type} cannot be zero")

                appraisal_type_score_and_count[appraisal_type]['percentage'] += \
                    item.final_score / item.total_score * appraisal_type_weightage
                appraisal_type_score_and_count[appraisal_type]['count'] += 1

            for values in appraisal_type_score_and_count.values():
                percentage_of_slot += values.get('percentage') / \
                    values.get('count')

            # save percentage of user of selected sub_performance_appraisal_slot
            slot_weight = SubPerformanceAppraisalSlotWeight()
            slot_weight.appraiser = appraisal.appraisee
            slot_weight.sub_performance_appraisal_slot = appraisal.sub_performance_appraisal_slot
            slot_weight.percentage = float(
                format(percentage_of_slot, '0.2f')) or 0
            slot_weight.save()

            # calculate and save yearly percentage for a appraiser
            self.save_yearly_performance_appraisal_percentage(appraisal)

        # End
        appraisal.save()

        return Response(
            {
                'detail': 'Successfully approved question set.'
            },
            status=status.HTTP_200_OK
        )

    @staticmethod
    def save_yearly_performance_appraisal_percentage(appraisal: Appraisal) -> None:
        """Saves total percentage of user for a performance appraisal year

        :param appraisal: Appraisal instance
        :returns : None
        """
        sub_performance_appraisal_slot = appraisal.sub_performance_appraisal_slot
        performance_appraisal_year = sub_performance_appraisal_slot.performance_appraisal_year
        appraiser = appraisal.appraisee

        # check if every slot in given performance appraisal year have average score calculated
        slots = SubPerformanceAppraisalSlot.objects.filter(
            performance_appraisal_year=performance_appraisal_year)
        slots_weight_count = slots.filter(
            weight__appraiser=appraiser,
            weight__isnull=False
        ).count()
        if slots.count() == slots_weight_count:
            SubPerformanceAppraisalYearWeight.objects.create(
                appraiser=appraiser,
                performance_appraisal_year=performance_appraisal_year,
                percentage=get_user_appraisal_score_for_year(
                    appraiser, performance_appraisal_year.id
                ).get('total_average_score', 0)
            )

    @action(
        detail=False,
        methods=['post'],
        url_path=r'(?P<appraiser_id>\d+)/resend',
        serializer_class=DummySerializer
    )
    def resend_form(self, request, *args, **kwargs):
        appraisal = self.get_queryset().filter(
            appraiser_id=kwargs.get('appraiser_id')).first()
        if not appraisal:
            raise Http404
        _reason = request.data.get("reason")
        # if not _reason:
        #     raise ValidationError({"reason":"This field cannot be empty."})
        resend = ResendPAFormSerializer(data={"reason": _reason})
        if resend.is_valid(raise_exception=True):
            resend = resend.save()
        appraisal.resend = resend
        appraisal.answer_committed = False
        appraisal.committed_at = None
        appraisal.save()

        add_notification(
            text=f'Performance Appraisal Review Form of {appraisal.appraisee.full_name}'
                 f' has been resent.',
            recipient=appraisal.appraiser,
            action=appraisal,
            actor=request.user,
            url=f'/user/pa/appraisal/{appraisal.sub_performance_appraisal_slot.id}/forms'
        )

        return Response(
            {
                'detail': 'Form resent.'
            },
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=['get', 'post'],
        url_path=r'(?P<appraiser_id>\d+)/question-set/printable-export',
        serializer_class=DummySerializer
    )
    def printable_export(self, request, *args, **kwargs):
        appraisal = self.appraisal
        if not appraisal:
            raise Http404

        document = generate_printable_document(appraisal)
        return self.get_http_word_application_response(document)

    @staticmethod
    def get_http_word_application_response(document):
        # ref: https://stackoverflow.com/a/31904512
        content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        response = HttpResponse(content_type=content_type)
        response['Content-Disposition'] = 'attachment; filename=performance-appraisal.docx'
        document.save(response)
        return response


class ListOfAppraiseeWithRespectToAppraiserViewSet(
    OrganizationMixin, SubPerformanceAppraisalMixin,
    ListViewSetMixin
):
    serializer_class = AppraisalListSerializer
    queryset = Appraisal.objects.all()
    filter_backends = (SearchFilter,)
    search_fields = (
        'appraisee__first_name', 'appraisee__middle_name', 'appraisee__last_name'
    )
    permission_classes = [
        permission_factory.build_permission(
            'ListOfAppraiseeWithRespectToAppraiserPermission',
            allowed_to=[HAS_PERMISSION_FROM_METHOD]
        )
    ]

    def has_user_permission(self):
        if self.request.query_params.get('as') == 'hr':
            can_hr_download_form = FormReviewSetting.objects.filter(
                sub_performance_appraisal_slot__id=self.kwargs.get(
                    'sub_performance_appraisal_slot_id'),
                can_hr_download_form=True
            ).exists()
            return validate_permissions(
                self.request.user.get_hrs_permissions(self.get_organization()),
                PERFORMANCE_APPRAISAL_PERMISSION,
                PERFORMANCE_APPRAISAL_SETTING_PERMISSION
            ) and bool(can_hr_download_form)

        # for normal user, must be appraiser
        if str(self.kwargs.get('appraiser_id')) != str(self.request.user.id):
            return False

        return Appraisal.objects.filter(
                appraiser=self.request.user,
                sub_performance_appraisal_slot_id=self.kwargs.get(
                    'sub_performance_appraisal_slot_id')
            ).exists()

    @property
    def appraisal(self):
        return self.filter_queryset(
            self.get_queryset()
        ).filter(
            appraisee_id=self.kwargs.get('appraisee_id')
        ).first()

    def get_queryset(self):
        return super().get_queryset().filter(
            appraiser=self.kwargs.get('appraiser_id'),
            sub_performance_appraisal_slot=self.performance_appraisal_slot,
            start_date__isnull=False
        ).annotate(
            status=Case(
                When(
                    condition=Q(
                        answer_committed=True,
                        approved=True
                    ),
                    then=Value('approved')
                ),
                When(
                    condition=Q(
                        answer_committed=True,
                        approved=False
                    ),
                    then=Value('received')
                ),
                When(
                    condition=Q(
                        answer_committed=False,
                        approved=False,
                        is_draft=True,
                    ),
                    then=Value('saved')
                ),
                default=Value('sent'),
                output_field=CharField()
            )
        )

    def filter_queryset(self, queryset):
        status = self.request.query_params.get('status')

        appraisal_type = self.request.query_params.get('appraisal_type')
        if not appraisal_type:
            raise ValidationError(
                {
                    'detail': 'Appraisal Type must be supplied.'
                }
            )
        else:
            appraisal_type = appraisal_type.replace('_', ' ').title()

        fil = {}
        if status:
            fil = dict(status=status)
        return super().filter_queryset(queryset).filter(
            appraisal_type=appraisal_type,
            **fil
        )

    def get_serializer(self, *args, **kwargs):
        if self.action == 'answer':
            kwargs.update(
                {'fields': ['question_set', 'answer_committed', 'final_score']})
        else:
            kwargs.update({
                'exclude_fields': ['appraiser']
            })
        return super().get_serializer(*args, **kwargs)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data['appraiser'] = UserThinSerializer(
            User.objects.filter(id=self.kwargs.get('appraiser_id')).first(),
            fields=(
                'id', 'full_name', 'profile_picture', 'job_title',
                'is_online', 'is_current', 'organization',
            )
        ).data

        response.data['stats'] = self.get_queryset().aggregate(
            self_appraisal=Count(
                'id',
                Q(appraisal_type=SELF_APPRAISAL)
            ),
            supervisor_appraisal=Count(
                'id',
                Q(appraisal_type=SUPERVISOR_APPRAISAL)
            ),
            subordinate_appraisal=Count(
                'id',
                Q(appraisal_type=SUBORDINATE_APPRAISAL)
            ),
            peer_to_peer_feedback=Count(
                'id',
                Q(appraisal_type=PEER_TO_PEER_FEEDBACK)
            )
        )
        return response

    @action(
        detail=False,
        methods=['post'],
        url_path=r'(?P<appraisee_id>\d+)/answer',
        serializer_class=AppraisalQuestionSetSerializer
    )
    def answer(self, request, *args, **kwargs):
        appraisal = self.appraisal

        if kwargs.get('as') == 'hr' and appraisal.deadline < get_today(with_time=True):
            raise ValidationError({
                'non_field_errors': ['Unable to answer those appraisal whose'
                                     ' deadline has crossed.']
            })

        def get_serializer_context(s):
            return {
                'request': s.request,
                'format': s.format_kwarg,
                'view': s,
                'organization': s.organization,
                'sub_performance_appraisal_slot': s.performance_appraisal_slot,
                'appraisal': appraisal,
                'is_draft': s.request.query_params.get('draft')
            }

        self.get_serializer_context = types.MethodType(
            get_serializer_context, self)
        if not appraisal:
            raise Http404

        if appraisal.answer_committed:
            raise ValidationError({
                'detail': 'Answer for this appraisal has already been committed.'
            })

        question_set = request.data.get('question_set')

        validation_serializer = ValidateQuestionSetSerializer(
            data=question_set
        )
        validation_serializer.is_valid(raise_exception=True)

        serializer = self.get_serializer(
            data=request.data,
            instance=appraisal
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        appraisal.final_score = calculate_obtained_score(appraisal.question_set)
        appraisal.save()
        # send notification to hr
        organization = appraisal.sub_performance_appraisal_slot.\
            performance_appraisal_year.organization
        slot_id = kwargs.get('sub_performance_appraisal_slot_id')
        notify_organization(
            text=f"{appraisal.appraiser.full_name} has sent Performance Appraisal Form of "
                 f"{appraisal.appraisee.full_name}",
            organization=organization,
            action=appraisal,
            actor=self.request.user,
            permissions=[HRIS_PERMISSION],
            url=f'/admin/{organization.slug}/pa/settings/frequency-and-mode/'
                f'{slot_id}/pa-status'
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class AppraisalStatusChangeViewSet(
    OrganizationMixin, SubPerformanceAppraisalMixin,
    CreateViewSetMixin
):
    queryset = Appraisal.objects.all()
    permission_classes = [PerformanceAppraisalSettingPermission]

    def get_serializer_class(self):
        if self.kwargs.get('action_type') == 'approve-all':
            return ApproveAllAppraisalSerializer
        if self.kwargs.get('action_type') == 'remove-appraisers':
            return RemoveAppraisalSerializer
        return EditDeadlineOfAppraisalSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['user'] = self.request.user
        return ctx
