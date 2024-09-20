from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Exists, OuterRef
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from irhrs.appraisal.api.v1.permissions import PerformanceAppraisalSettingPermission, \
    PerformanceAppraisalFormSubmissionActionPermission
from irhrs.appraisal.api.v1.serializers.form_design import \
    PerformanceAppraisalFormDesignSerializer, AppraiseeQuestionSetCountBySerializer, \
    AppraiseeAppraiserQuestionSetCountSerializer, SendQuestionSetSerializer, \
    KAARFormDesignSerializer, KeyAchievementAndRatingAppraisalQuestionSetCount, \
    KAARAppraiserQuestionSetCountBySerializer, SendKAARQuestionSetSerializer
from irhrs.appraisal.api.v1.views.performance_appraisal import SubPerformanceAppraisalMixin
from irhrs.appraisal.constants import SUBORDINATE_APPRAISAL, SUPERVISOR_APPRAISAL, \
    PEER_TO_PEER_FEEDBACK, SELF_APPRAISAL, KEY_ACHIEVEMENTS_AND_RATING, REVIEWER_EVALUATION, \
    GENERATED, SUBMITTED, RECEIVED, NOT_GENERATED
from irhrs.appraisal.models.KAAR_question import KAARQuestionSet
from irhrs.appraisal.models.appraiser_setting import Appraisal
from irhrs.appraisal.models.form_design import PerformanceAppraisalFormDesign, KAARFormDesign
from irhrs.appraisal.models.key_achievement_and_rating_pa import KeyAchievementAndRatingAppraisal, \
    KAARAppraiserConfig
from irhrs.appraisal.utils.generate_question_set import GenerateQuestionSet
from irhrs.appraisal.utils.util import AppraisalSettingFilterMixin
from irhrs.core.mixins.serializers import DummySerializer
from irhrs.core.mixins.viewset_mixins import OrganizationMixin, \
    ListViewSetMixin, ListCreateViewSetMixin
from irhrs.core.utils.filters import FilterMapBackend
from irhrs.export.mixins.export import BackgroundExcelExportMixin
from irhrs.notification.utils import add_notification
from irhrs.permission.constants.permissions import PERFORMANCE_APPRAISAL_PERMISSION

User = get_user_model()


class PerformanceAppraisalFormDesignViewSet(
    OrganizationMixin,
    SubPerformanceAppraisalMixin,
    GenerateQuestionSet,
    ListCreateViewSetMixin
):
    serializer_class = PerformanceAppraisalFormDesignSerializer
    queryset = PerformanceAppraisalFormDesign.objects.all()
    permission_classes = [PerformanceAppraisalSettingPermission]

    def create(self, request, *args, **kwargs):
        self.performance_appraisal_slot.form_design.filter(
            appraisal_type=request.data.get('appraisal_type'),
        ).delete()
        return super().create(request, *args, **kwargs)

    @property
    def appraisal_type(self):
        return self.performance_appraisal_slot.performance_appraisal_year.performance_appraisal_type

    @property
    def is_key_achievement_and_rating_appraisal(self):
        return self.appraisal_type == KEY_ACHIEVEMENTS_AND_RATING

    def get_serializer(self, *args, **kwargs):
        """ if an array is passed, set serializer to many """
        if isinstance(kwargs.get('data', {}), list) and self.action == 'send_question_set':
            kwargs['many'] = True
        if self.is_key_achievement_and_rating_appraisal:
            return KAARFormDesignSerializer(*args, **kwargs, context=self.get_serializer_context())
        return super().get_serializer(*args, **kwargs)

    def get_queryset(self):
        if self.is_key_achievement_and_rating_appraisal:
            return KAARFormDesign.objects.all()
        return super().get_queryset()

    @action(
        detail=False,
        methods=['post'],
        serializer_class=DummySerializer,
        url_path='send/question-set'
    )
    def send_question_set(self, request, *args, **kwargs):
        context = self.get_serializer_context()
        context['sub_performance_appraisal_slot'] = self.performance_appraisal_slot
        modes = self.performance_appraisal_slot.modes.filter(
            start_date__isnull=False,
            deadline__isnull=False
        )
        data = modes.values(
            'appraisal_type', 'start_date', 'deadline'
        )

        if not data:
            raise ValidationError({'non_field_errors': 'Set start date and deadline first.'})

        serializer = SendQuestionSetSerializer(
            data=list(data),
            context=context,
            many=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        appraisals = Appraisal.objects.filter(
            sub_performance_appraisal_slot=self.performance_appraisal_slot
        )

        recipient_list = list()
        for appraisal in appraisals:
            if appraisal.appraiser not in recipient_list:
                add_notification(
                    text=f"Performance Appraisal Review Forms has been assigned to you.",
                    action=appraisal,
                    recipient=appraisal.appraiser,
                    actor=self.request.user,
                    url=f'/user/pa/appraisal/{self.performance_appraisal_slot.id}/forms'
                )
                recipient_list.append(appraisal.appraiser)

        return Response(serializer.data, status=status.HTTP_200_OK)


class AppraiseeQuestionSetCountByTypeViewSet(
    AppraisalSettingFilterMixin,
    OrganizationMixin,
    SubPerformanceAppraisalMixin,
    ListViewSetMixin
):
    serializer_class = AppraiseeQuestionSetCountBySerializer
    filter_backends = [FilterMapBackend, SearchFilter]
    filter_map = {
        'branch': 'detail__branch__slug',
        'division': 'detail__division__slug',
        'job_title': 'detail__job_title__slug',
        'employment_level': 'detail__employment_level__slug',
        'employment_type': 'detail__employment_status__slug',
    }
    search_fields = ['first_name', 'middle_name', 'last_name']
    permission_classes = [PerformanceAppraisalFormSubmissionActionPermission]
    appraisal_type = SELF_APPRAISAL

    def get_serializer_class(self):
        if self.kwargs.get('action_type') == 'count':
            return AppraiseeAppraiserQuestionSetCountSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        queryset = super().get_queryset(union=False).filter(
            detail__organization=self.organization,
            as_appraisees__isnull=False,
            as_appraisees__sub_performance_appraisal_slot=self.performance_appraisal_slot
        ).current()

        fil = {}
        if self.kwargs.get('action_type') == 'count':
            fil = dict(as_appraisees__question_set__isnull=False)

        return queryset.select_related(
            'detail', 'detail__job_title', 'detail__organization'
        ).annotate(
            saved_subordinate_appraisal=Count(
                'as_appraisees__appraiser',
                Q(
                    as_appraisees__appraisal_type=SUBORDINATE_APPRAISAL,
                    as_appraisees__answer_committed=False,
                    as_appraisees__approved=False,
                    as_appraisees__is_draft=True,
                    **fil
                )
            ),
            sent_subordinate_appraisal=Count(
                'as_appraisees__appraiser',
                Q(
                    as_appraisees__appraisal_type=SUBORDINATE_APPRAISAL,
                    as_appraisees__answer_committed=False,
                    as_appraisees__approved=False,
                    as_appraisees__is_draft=False,
                    **fil
                )
            ),
            received_subordinate_appraisal=Count(
                'as_appraisees__appraiser',
                Q(
                    as_appraisees__appraisal_type=SUBORDINATE_APPRAISAL,
                    as_appraisees__answer_committed=True,
                    as_appraisees__approved=False
                )
            ),
            approved_subordinate_appraisal=Count(
                'as_appraisees__appraiser',
                Q(
                    as_appraisees__appraisal_type=SUBORDINATE_APPRAISAL,
                    as_appraisees__answer_committed=True,
                    as_appraisees__approved=True
                )
            ),

            saved_supervisor_appraisal=Count(
                'as_appraisees__appraiser',
                Q(
                    as_appraisees__appraisal_type=SUPERVISOR_APPRAISAL,
                    as_appraisees__answer_committed=False,
                    as_appraisees__approved=False,
                    as_appraisees__is_draft=True,
                    **fil
                )
            ),
            sent_supervisor_appraisal=Count(
                'as_appraisees__appraiser',
                Q(
                    as_appraisees__appraisal_type=SUPERVISOR_APPRAISAL,
                    as_appraisees__answer_committed=False,
                    as_appraisees__approved=False,
                    as_appraisees__is_draft=False,
                    **fil
                )
            ),
            received_supervisor_appraisal=Count(
                'as_appraisees__appraiser',
                Q(
                    as_appraisees__appraisal_type=SUPERVISOR_APPRAISAL,
                    as_appraisees__answer_committed=True,
                    as_appraisees__approved=False
                )
            ),
            approved_supervisor_appraisal=Count(
                'as_appraisees__appraiser',
                Q(
                    as_appraisees__appraisal_type=SUPERVISOR_APPRAISAL,
                    as_appraisees__answer_committed=True,
                    as_appraisees__approved=True
                )
            ),

            saved_peer_to_peer_feedback=Count(
                'as_appraisees__appraiser',
                Q(
                    as_appraisees__appraisal_type=PEER_TO_PEER_FEEDBACK,
                    as_appraisees__answer_committed=False,
                    as_appraisees__approved=False,
                    as_appraisees__is_draft=True,
                    **fil
                )
            ),
            sent_peer_to_peer_feedback=Count(
                'as_appraisees__appraiser',
                Q(
                    as_appraisees__appraisal_type=PEER_TO_PEER_FEEDBACK,
                    as_appraisees__answer_committed=False,
                    as_appraisees__approved=False,
                    as_appraisees__is_draft=False,
                    **fil
                )
            ),
            received_peer_to_peer_feedback=Count(
                'as_appraisees__appraiser',
                Q(
                    as_appraisees__appraisal_type=PEER_TO_PEER_FEEDBACK,
                    as_appraisees__answer_committed=True,
                    as_appraisees__approved=False
                )
            ),
            approved_peer_to_peer_feedback=Count(
                'as_appraisees__appraiser',
                Q(
                    as_appraisees__appraisal_type=PEER_TO_PEER_FEEDBACK,
                    as_appraisees__answer_committed=True,
                    as_appraisees__approved=True
                )
            ),

            saved_self_appraisal=Count(
                'as_appraisees__appraiser',
                Q(
                    as_appraisees__appraisal_type=SELF_APPRAISAL,
                    as_appraisees__answer_committed=False,
                    as_appraisees__approved=False,
                    as_appraisees__is_draft=True,
                    **fil
                )
            ),
            sent_self_appraisal=Count(
                'as_appraisees__appraiser',
                Q(
                    as_appraisees__appraisal_type=SELF_APPRAISAL,
                    as_appraisees__answer_committed=False,
                    as_appraisees__approved=False,
                    as_appraisees__is_draft=False,
                    **fil
                )
            ),
            received_self_appraisal=Count(
                'as_appraisees__appraiser',
                Q(
                    as_appraisees__appraisal_type=SELF_APPRAISAL,
                    as_appraisees__answer_committed=True,
                    as_appraisees__approved=False
                )
            ),
            approved_self_appraisal=Count(
                'as_appraisees__appraiser',
                Q(
                    as_appraisees__appraisal_type=SELF_APPRAISAL,
                    as_appraisees__answer_committed=True,
                    as_appraisees__approved=True
                )
            )
        )


class KAARAppraiseeQuestionSetCountByTypeViewSet(
    OrganizationMixin,
    SubPerformanceAppraisalMixin,
    ListViewSetMixin,
    BackgroundExcelExportMixin
):
    queryset = KeyAchievementAndRatingAppraisal.objects.all()
    serializer_class = KAARAppraiserQuestionSetCountBySerializer
    filter_backends = [FilterMapBackend, SearchFilter]
    filter_map = {
        'branch': 'appraisee__detail__branch__slug',
        'division': 'appraisee__detail__division__slug',
        'job_title': 'appraisee__detail__job_title__slug',
        'employment_level': 'appraisee__detail__employment_level__slug',
        'employment_type': 'appraisee__detail__employment_status__slug',
    }
    search_fields = ['appraisee__first_name', 'appraisee__middle_name', 'appraisee__last_name']
    permission_classes = [PerformanceAppraisalFormSubmissionActionPermission]
    notification_permissions = [PERFORMANCE_APPRAISAL_PERMISSION]

    def get_export_type(self):
        return "Key Achievements and Rating Form Submission Status"

    def get_export_description(self):
        return self.get_export_type()

    def get_export_fields(self):
        export_fields = {
            "Username": "username",
            "Appraisee": "appraisee",
            "Self Appraisal": "Self Appraisal",
            "Supervisor Appraisal": "Supervisor Appraisal",
            "Reviewer Evaluation": "Reviewer Evaluation"
        }
        return export_fields

    @staticmethod
    def prepare_export_object(obj, **kwargs):
        data_dict = {'username': obj.appraisee.username, 'appraisee': obj.appraisee}
        data = KAARAppraiserQuestionSetCountBySerializer(obj, context={
            'organization': kwargs.get('organization')}).data
        temp_dict = {}
        for appraisal_type, report_status in data['question_set_count'].items():
            for state, value in report_status.items():
                if value != 0:
                    temp_dict.update({appraisal_type: state})
        data_dict.update(temp_dict)
        return data_dict

    def get_frontend_redirect_url(self):
        slot_id = self.performance_appraisal_slot.id
        return f'/admin/{self.organization.slug}/pa/settings/frequency-and-mode/{slot_id}/kaar-status'

    def get_serializer_class(self):
        if self.kwargs.get('action_type') == 'count':
            return KeyAchievementAndRatingAppraisalQuestionSetCount
        return super().get_serializer_class()

    @staticmethod
    def get_appraiser_count(queryset, fil):
        return queryset.annotate(
            self_appraiser_question_count=Count(
                'appraiser_configs',
                Q(
                    appraiser_configs__appraiser_type=SELF_APPRAISAL,
                    **fil
                )
            ),
            supervisor_appraiser_question_count=Count(
                'appraiser_configs',
                Q(
                    appraiser_configs__appraiser_type=SUPERVISOR_APPRAISAL,
                    **fil
                )
            ),
            reviewer_appraiser_question_count=Count(
                'appraiser_configs',
                Q(
                    appraiser_configs__appraiser_type=REVIEWER_EVALUATION,
                    **fil
                )
            )
        )

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            sub_performance_appraisal_slot=self.performance_appraisal_slot
        ).annotate(
            has_quesiton_sets=Exists(
                KAARQuestionSet.objects.filter(kaar_appraisal_id=OuterRef('pk'))
            )
        ).select_related(
            'appraisee__detail',
            'appraisee__detail__job_title',
            'appraisee__detail__organization'
        )
        fil = {}
        if self.kwargs.get('action_type') == 'count':
            fil = dict(has_quesiton_sets=True)
            return self.get_appraiser_count(queryset, fil)
        return queryset.annotate(
            generated_self_appraisal=Count(
                'appraiser_configs',
                Q(
                    appraiser_configs__appraiser_type=SELF_APPRAISAL,
                    appraiser_configs__question_status=GENERATED,
                    **fil
                )
            ),
            received_self_appraisal=Count(
                'appraiser_configs',
                Q(
                    appraiser_configs__appraiser_type=SELF_APPRAISAL,
                    appraiser_configs__question_status=RECEIVED,
                    **fil
                )
            ),
            submitted_self_appraisal=Count(
                'appraiser_configs',
                Q(
                    appraiser_configs__appraiser_type=SELF_APPRAISAL,
                    appraiser_configs__question_status=SUBMITTED,
                    **fil
                )
            ),
            generated_supervisor_appraisal=Count(
                'appraiser_configs',
                Q(
                    appraiser_configs__appraiser_type=SUPERVISOR_APPRAISAL,
                    appraiser_configs__question_status=GENERATED,
                    **fil
                )
            ),
            received_supervisor_appraisal=Count(
                'appraiser_configs',
                Q(
                    appraiser_configs__appraiser_type=SUPERVISOR_APPRAISAL,
                    appraiser_configs__question_status=RECEIVED,
                    **fil
                )
            ),
            submitted_supervisor_appraisal=Count(
                'appraiser_configs',
                Q(
                    appraiser_configs__appraiser_type=SUPERVISOR_APPRAISAL,
                    appraiser_configs__question_status=SUBMITTED,
                    **fil
                )
            ),
            generated_reviewer_appraisal=Count(
                'appraiser_configs',
                Q(
                    appraiser_configs__appraiser_type=REVIEWER_EVALUATION,
                    appraiser_configs__question_status=GENERATED,
                    **fil
                )
            ),
            received_reviewer_appraisal=Count(
                'appraiser_configs',
                Q(
                    appraiser_configs__appraiser_type=REVIEWER_EVALUATION,
                    appraiser_configs__question_status=RECEIVED,
                    **fil
                )
            ),
            submitted_reviewer_appraisal=Count(
                'appraiser_configs',
                Q(
                    appraiser_configs__appraiser_type=REVIEWER_EVALUATION,
                    appraiser_configs__question_status=SUBMITTED,
                    **fil
                )
            ),
        )

    def list(self, request, *args, **kwargs):
        serialized_data = super().list(request, *args, **kwargs)
        serialized_data.data.update(
            {'question_status': self.performance_appraisal_slot.question_set_status}
        )
        return serialized_data


class KAARPerformanceAppraisalFormDesignViewSet(
    OrganizationMixin,
    SubPerformanceAppraisalMixin,
    GenerateQuestionSet,
    ListCreateViewSetMixin
):
    serializer_class = KAARFormDesignSerializer
    queryset = KAARFormDesign.objects.all()
    permission_classes = [PerformanceAppraisalSettingPermission]

    @property
    def appraisal_type(self):
        return self.performance_appraisal_slot.performance_appraisal_year.performance_appraisal_type

    @property
    def is_key_achievement_and_rating_appraisal(self):
        return self.appraisal_type == KEY_ACHIEVEMENTS_AND_RATING

    def get_serializer(self, *args, **kwargs):
        """ if an array is passed, set serializer to many """
        if isinstance(kwargs.get('data', {}), list) and self.action == 'send_question_set':
            kwargs['many'] = True
        return super().get_serializer(*args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            sub_performance_appraisal_slot__performance_appraisal_year__performance_appraisal_type=KEY_ACHIEVEMENTS_AND_RATING
        )
        return queryset

    @action(
        detail=False,
        methods=['post'],
        serializer_class=DummySerializer,
        url_path='send/question-set'
    )
    def send_question_set(self, request, *args, **kwargs):
        context = self.get_serializer_context()
        context['sub_performance_appraisal_slot'] = self.performance_appraisal_slot
        all_modes = self.performance_appraisal_slot.modes
        modes = all_modes.filter(
            start_date__isnull=False,
            deadline__isnull=False
        )
        data = modes.values(
            'appraisal_type', 'start_date', 'deadline'
        )

        if not data:
            raise ValidationError({'non_field_errors': 'Set start date and deadline first.'})

        serializer = SendKAARQuestionSetSerializer(
            data=list(data),
            context=context,
            many=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
