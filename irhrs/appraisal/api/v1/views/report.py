import types

from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Case, When, F, BooleanField, Avg, Value,\
    Subquery, Func, FloatField
from django.db.models.expressions import OuterRef
from django.utils.functional import cached_property
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from irhrs.appraisal.api.v1.serializers.report import SummaryReportSerializer, \
    SummaryReportDetailSerializer, YearlyReportSerializer
from irhrs.appraisal.constants import (
    SELF_APPRAISAL,
    SUPERVISOR_APPRAISAL,
    SUBORDINATE_APPRAISAL,
    PEER_TO_PEER_FEEDBACK
)
from irhrs.appraisal.models.appraiser_setting import Appraisal
from irhrs.appraisal.models.performance_appraisal import SubPerformanceAppraisalSlot, \
    SubPerformanceAppraisalSlotWeight, SubPerformanceAppraisalYearWeight
from irhrs.appraisal.utils.common import (
    get_user_appraisal_score_for_slot,
    get_user_appraisal_score_for_year
)
from irhrs.core.mixins.viewset_mixins import ListViewSetMixin, OrganizationMixin
from irhrs.core.utils.common import get_today
from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.filters import FilterMapBackend, NullsAlwaysLastOrderingFilter
from irhrs.export.mixins.export import BackgroundExcelExportMixin
from irhrs.permission.constants.permissions import PERFORMANCE_APPRAISAL_READ_ONLY_PERMISSION, \
    PERFORMANCE_APPRAISAL_PERMISSION
from irhrs.permission.constants.permissions.performance_appraisal import (
    PERFORMANCE_APPRAISAL_REPORT_PERMISSION
)
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer

User = get_user_model()


class PerformanceAppraisalOverviewViewSet(
    OrganizationMixin, ListViewSetMixin
):
    queryset = Appraisal.objects.all()

    @property
    def pa_slot(self):
        slot_id = self.request.query_params.get('slot')

        if not slot_id:
            instance = SubPerformanceAppraisalSlot.objects.filter(
                performance_appraisal_year__organization=self.organization,
                from_date__lte=get_today(),
                to_date__gte=get_today()
            ).first()
            if not instance:
                instance = SubPerformanceAppraisalSlot.objects.filter(
                    performance_appraisal_year__organization=self.organization,
                    to_date__lte=get_today(),
                ).order_by('from_date').last()
        else:
            try:
                instance = SubPerformanceAppraisalSlot.objects.filter(
                    performance_appraisal_year__organization=self.organization,
                    id=slot_id
                ).first()

            except ValueError:
                instance = SubPerformanceAppraisalSlot.objects.filter(
                    performance_appraisal_year__organization=self.organization
                ).first()

        return instance

    def get_queryset(self):
        fil = {
            'sub_performance_appraisal_slot': self.pa_slot
        }
        is_hr = validate_permissions(
            self.request.user.get_hrs_permissions(self.organization),
            PERFORMANCE_APPRAISAL_PERMISSION,
            PERFORMANCE_APPRAISAL_READ_ONLY_PERMISSION
        ) and self.request.query_params.get('as') == 'hr'
        if not is_hr:
            fil.update({
                'appraiser': self.request.user
            })
        return super().get_queryset().filter(**fil)

    def list(self, request, *args, **kwargs):
        overall_stats = self.get_queryset().aggregate(
            self_appraisal_total=Count(
                'id',
                Q(
                    appraisal_type=SELF_APPRAISAL
                )
            ),
            self_appraisal_remaining=Count(
                'id',
                Q(
                    appraisal_type=SELF_APPRAISAL,
                    answer_committed=False,
                    committed_at__isnull=True
                )
            ),

            supervisor_appraisal_total=Count(
                'id',
                Q(
                    appraisal_type=SUPERVISOR_APPRAISAL
                )
            ),
            supervisor_appraisal_remaining=Count(
                'id',
                Q(
                    appraisal_type=SUPERVISOR_APPRAISAL,
                    answer_committed=False,
                    committed_at__isnull=True
                )
            ),

            subordinate_appraisal_total=Count(
                'id',
                Q(
                    appraisal_type=SUBORDINATE_APPRAISAL
                )
            ),
            subordinate_appraisal_remaining=Count(
                'id',
                Q(
                    appraisal_type=SUBORDINATE_APPRAISAL,
                    answer_committed=False,
                    committed_at__isnull=True
                )
            ),

            peer_to_peer_feedback_total=Count(
                'id',
                Q(
                    appraisal_type=PEER_TO_PEER_FEEDBACK
                )
            ),
            peer_to_peer_feedback_remaining=Count(
                'id',
                Q(
                    appraisal_type=PEER_TO_PEER_FEEDBACK,
                    answer_committed=False,
                    committed_at__isnull=True
                )
            ),
        )

        total_users = User.objects.filter(
            detail__organization=self.organization
        ).current().count()

        appraisal_type_queryset = self.get_queryset().annotate(
            on_time=Case(
                When(
                    condition=Q(deadline__gte=F('committed_at')),
                    then=True
                ),
                default=False,
                output_field=BooleanField()
            )
        ).values('appraisal_type').annotate(
            eligible_employees=Count(
                'appraisee',
                distinct=True
            ),
        ).annotate(
            non_eligible_employees=Value(total_users) - F('eligible_employees'),
            saved=Count(
                'id',
                Q(
                    approved=False,
                    answer_committed=False,
                    is_draft=True
                )
            ),
            pending=Count(
                'id',
                Q(
                    answer_committed=False
                )
            ),
            approved=Count(
                'id',
                Q(
                    approved=True
                )
            ),
            submitted_on_time=Count(
                'id',
                Q(
                    answer_committed=True,
                    on_time=True
                )
            ),
            submitted_after_deadline=Count(
                'id',
                Q(
                    answer_committed=True,
                    on_time=False
                )
            ),
        ).order_by('appraisal_type')

        def generate_appraisal_type_stats(stats):
            if self.request.query_params.get('as') != 'hr':
                _ = stats.pop('eligible_employees')
                _ = stats.pop('non_eligible_employees')
            return {
                stats.pop('appraisal_type'): stats
            }

        stats_dict = {
            'overall_stats': {
                'self_appraisal': {
                    'total': overall_stats.get('self_appraisal_total'),
                    'remaining': overall_stats.get('self_appraisal_remaining')
                },
                'supervisor_appraisal': {
                    'total': overall_stats.get('supervisor_appraisal_total'),
                    'remaining': overall_stats.get('supervisor_appraisal_remaining')
                },
                'subordinate_appraisal': {
                    'total': overall_stats.get('subordinate_appraisal_total'),
                    'remaining': overall_stats.get('subordinate_appraisal_remaining')
                },
                'peer_to_peer_feedback': {
                    'total': overall_stats.get('peer_to_peer_feedback_total'),
                    'remaining': overall_stats.get('peer_to_peer_feedback_remaining')
                }
            },
            'appraisal_type_stats': list(
                map(
                    generate_appraisal_type_stats,
                    appraisal_type_queryset
                )
            )
        }

        return Response(
            stats_dict,
            status=status.HTTP_200_OK
        )


# round an average to 2 decimal points
class Round(Func):
    function = 'ROUND'
    arity = 2
    # Only works as the arity is 2
    arg_joiner = '::numeric, '


class PerformanceAppraisalSummaryReportViewSet(
    OrganizationMixin,
    ListViewSetMixin,
    BackgroundExcelExportMixin
):
    """

        Example,

        Total average score = (Score obtained from self/100)*weightage +
                              (Score obtained from supervisor/100)*weightage +
                              (Score obtained from subordinate/100)*weightage +
                              (Score obtained from peer to peer/100)*weightage

        Scenario for scoring criteria and weightage

            1. If there are four PA mode they are Self, Peer To Peer, Supervisor,
            and subordinate and each weightage is 25% then

                1. If an employee is eligible for all four modes then scoring criteria is the same
                as above defined. There is no change in weightage.

                2. If an employee is eligible for only one mode of appraisal then weightage for
                that PA mode will be by default 100%

                3. If an employee is eligible for only two mode of appraisal then weightage can be
                calculated as
                    1. Unused weightage =50%
                    2. Used mode = 2
                    3. Average weightage = 50/2 = 25%
                    4. Now add 25% in each eligible mode of appraisal.
                    5. Now use new weight for average calculation.

                4. If an employee is eligible for only three modes of appraisal then weightage can
                be calculated as
                    1. Unused weightage =25%
                    2. Used mode = 3
                    3. Average weightage = 25/3 = 8.33%
                    4. Now add 8.33% in each eligible mode of appraisal.
                    5. Now use new weight for average calculation
    """

    serializer_class = SummaryReportSerializer
    filter_backends = (FilterMapBackend, SearchFilter, NullsAlwaysLastOrderingFilter)
    filter_map = {
        'branch': 'detail__branch__slug',
        'division': 'detail__division__slug',
        'employment_level': 'detail__employment_level__slug',
        'employment_type': 'detail__employment_status__slug'
    }
    search_fields = (
        'first_name', 'middle_name', 'last_name'
    )
    ordering_fields_map = {
        'full_name': ('first_name', 'middle_name', 'last_name'),
        'score': 'total_average',
        'self_appraisal': 'self_appraisal',
        'supervisor_appraisal': 'supervisor_appraisal',
        'subordinate_appraisal': 'subordinate_appraisal',
        'peer_to_peer_feedback': 'peer_to_peer_feedback'
    }
    permission_for_hr = [PERFORMANCE_APPRAISAL_REPORT_PERMISSION]

    @property
    def mode(self):
        mode = self.request.query_params.get('as', 'user')
        if mode not in ['user', 'hr', 'approver']:
            return 'user'
        elif mode == 'hr':
            if not validate_permissions(
                self.request.user.get_hrs_permissions(self.get_organization()),
                *self.permission_for_hr
            ):
                raise PermissionDenied
        return mode

    def get_queryset(self):
        slot_id = self.kwargs.get('sub_performance_appraisal_slot_id')
        filters = dict(
            detail__organization=self.organization,
            as_appraisees__isnull=False,
            as_appraisees__sub_performance_appraisal_slot__id=slot_id
        )
        if self.mode == "user":
            filters.update(
                id=self.request.user.id
            )
        queryset = User.objects.filter(**filters).current()

        def get_appraisal_type_percentage(appraisal_type: str):
            """
            - calculates ratio of final_score by total_score when total_score is not zero else
               return 0
            - Queryset is obtained from slot_id and appraisal_type

            :param appraisal_type: Self Appraisal | Subordinate Appraisal | Supervisor Appraisal
            | Peer To Peer Feedback
            :return: Round object
            """
            return Round(
                Avg(
                    Case(
                        When(as_appraisees__total_score=0, then=0),
                        default=F('as_appraisees__final_score') / F('as_appraisees__total_score'),
                        output_field=FloatField()
                    ),
                    filter=Q(
                        as_appraisees__sub_performance_appraisal_slot__id=slot_id,
                        as_appraisees__appraisal_type=appraisal_type
                    )
                ), 4,
                output_field=FloatField()
            ) * 100

        queryset = queryset.annotate(
            self_appraisal=get_appraisal_type_percentage(SELF_APPRAISAL),
            supervisor_appraisal=get_appraisal_type_percentage(SUPERVISOR_APPRAISAL),
            subordinate_appraisal=get_appraisal_type_percentage(SUBORDINATE_APPRAISAL),
            peer_to_peer_feedback=get_appraisal_type_percentage(PEER_TO_PEER_FEEDBACK)
        ).select_related(
            'detail', 'detail__job_title'
        )
        # total_average is used while ordering
        if self.action != "export":
            queryset = queryset.annotate(
                total_average=Subquery(
                    SubPerformanceAppraisalSlotWeight.objects.filter(
                        appraiser=OuterRef('id'),
                        sub_performance_appraisal_slot_id=slot_id
                    ).values('percentage')[:1]
                )
            )
        return queryset

    def get_export_type(self):
        return 'Export summary report of appraisal'

    def get_export_fields(self):
        fields = {
            'Employee Name': 'full_name',
            'Self appraisal score': 'self_appraisal_percent_score',
            'Supervisor Avg. score': 'supervisor_appraisal_percent_score',
            'Subordinate Avg. score': 'subordinate_appraisal_percent_score',
            'Peer to peer Avg. score': 'peer_to_peer_appraisal_percent_score',
            'Total percent Avg. score': 'total_average_percent_score',
        }
        return fields

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['slot_id'] = self.kwargs.get('sub_performance_appraisal_slot_id')
        return ctx

    def get_extra_export_data(self):
        ctx = super().get_extra_export_data()
        ctx['prepare_export_object_context'] = {
            'slot_id': self.kwargs.get('sub_performance_appraisal_slot_id')
        }
        return ctx

    @staticmethod
    def prepare_export_object(user, **kwargs):
        """
        this is a method that will prepare export object. It will get object instance as its
        first parameter and should return object or dict.
        :param obj: Instance (A row) that will be exported
        :return: prepared object
        """
        slot_id = kwargs.get('slot_id')
        scores = get_user_appraisal_score_for_slot(user, slot_id)
        user.self_appraisal_percent_score = scores.get('self_appraisal')
        user.supervisor_appraisal_percent_score = scores.get('supervisor_appraisal')
        user.subordinate_appraisal_percent_score = scores.get('subordinate_appraisal')
        user.peer_to_peer_appraisal_percent_score = scores.get('peer_to_peer_feedback')
        user.total_average_percent_score = scores.get('total_average')
        return user

    @action(
        detail=False,
        methods=['get'],
        url_path=r'appraisee/(?P<appraisee_id>\d+)/(?P<appraisal_type>'
                 r'(self_appraisal|supervisor_appraisal|subordinate_appraisal'
                 r'|peer_to_peer_feedback))',
        serializer_class=SummaryReportDetailSerializer
    )
    def report_for_appraisee(self, request, *args, **kwargs):
        slot_id = self.kwargs.get('sub_performance_appraisal_slot_id')
        appraisal_type = self.kwargs.get('appraisal_type')
        appraisee_id = kwargs.get('appraisee_id')
        appraisee = self.get_queryset().filter(id=appraisee_id).first()

        def get_queryset(s):
            return User.objects.filter(
                as_appraisers__isnull=False,
                as_appraisers__appraisee=appraisee_id,
                as_appraisers__sub_performance_appraisal_slot__id=slot_id,
                as_appraisers__appraisal_type=appraisal_type.replace('_', ' ').title()
            ).current().annotate(
                score=Avg(
                    'as_appraisers__final_score',
                    filter=Q(
                        as_appraisers__sub_performance_appraisal_slot__id=slot_id,
                        as_appraisers__appraisee_id=appraisee_id,
                        as_appraisers__appraisal_type=appraisal_type.replace('_', ' ').title()
                    ),
                    output_field=FloatField()
                ),
                total_score=Avg(
                    'as_appraisers__total_score',
                    filter=Q(
                        as_appraisers__sub_performance_appraisal_slot__id=slot_id,
                        as_appraisers__appraisee_id=appraisee_id,
                        as_appraisers__appraisal_type=appraisal_type.replace('_', ' ').title()
                    ),
                    output_field=FloatField()
                )
            ).select_related(
                'detail', 'detail__job_title'
            )

        self.get_queryset = types.MethodType(get_queryset, self)

        response = super().list(self, request, *args, **kwargs)

        response.data.update({
            'appraisee': UserThinSerializer(
                appraisee,
                fields=('id', 'full_name', 'profile_picture', 'cover_picture', 'is_current', 'organization', 'job_title',)
            ).data,
            'average': get_user_appraisal_score_for_slot(appraisee, slot_id).get(appraisal_type, 0)
        })
        return response


class PerformanceAppraisalYearlyReportViewSet(
        OrganizationMixin,
        ListViewSetMixin,
        BackgroundExcelExportMixin
):
    """
    Total Average Score - Should display the average score. Average score should be calculated
    by using weightage defined in frequency settings.

        1. Example,

            Total average score = (Score obtained from first quarter/100) * weightage +
                                  (Score obtained from second quarter/100) * weightage +
                                  (Score obtained from third quarter/100) * weightage +
                                  (Score obtained from fourth quarter/100) * weightage

        2. Scenario for scoring criteria and weightage (scenario will be added later)
    """
    serializer_class = YearlyReportSerializer
    filter_backends = (FilterMapBackend, SearchFilter, NullsAlwaysLastOrderingFilter)
    filter_map = {
        'branch': 'detail__branch__slug',
        'division': 'detail__division__slug',
        'employment_level': 'detail__employment_level__slug',
        'employment_type': 'detail__employment_status__slug'
    }
    search_fields = (
        'first_name', 'middle_name', 'last_name'
    )
    ordering_fields_map = {
        'full_name': ('first_name', 'middle_name', 'last_name'),
        'score': 'total_average'
    }
    permission_for_hr = [PERFORMANCE_APPRAISAL_REPORT_PERMISSION]

    @cached_property
    def pa_slots(self):
        return SubPerformanceAppraisalSlot.objects.filter(
            performance_appraisal_year=self.kwargs.get('year_id')
        ).values('id', 'title', 'weightage')

    @property
    def mode(self):
        mode = self.request.query_params.get('as', 'user')
        if mode not in ['user', 'hr']:
            return 'user'
        elif mode == 'hr':
            if not validate_permissions(
                self.request.user.get_hrs_permissions(self.get_organization()),
                *self.permission_for_hr
            ):
                raise PermissionDenied
        return mode

    def get_queryset(self):
        fiscal_year_id = self.kwargs.get('year_id')
        filters = dict(
            as_appraisees__sub_performance_appraisal_slot__performance_appraisal_year__id=(
                fiscal_year_id
            ),
            as_appraisees__isnull=False
        )
        if self.mode == 'user':
            filters.update(
                id=self.request.user.id
            )
        queryset = User.objects.filter(**filters).select_related(
            'detail', 'detail__job_title'
        ).prefetch_related('sub_performance_appraisal_slot_weights').distinct()

        # total_average is used while ordering
        if self.action != "export":
            queryset = queryset.annotate(
                total_average=Subquery(
                    SubPerformanceAppraisalYearWeight.objects.filter(
                        appraiser=OuterRef('id'),
                        performance_appraisal_year_id=fiscal_year_id
                    ).values('percentage')[:1]
                )
            )
        return queryset

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['year_id'] = self.kwargs.get('year_id')
        return ctx

    def get_export_type(self):
        return 'Yearly report of appraisal'

    def get_slots_in_fy(self) -> dict:
        """Returns all the slot presented in given performance appraisal year for export purpose.

        :returns : dictionary of all the slots with same key and value
        """
        slots = SubPerformanceAppraisalSlot.objects.filter(
            performance_appraisal_year__id=self.kwargs.get('year_id')
        ).values_list('title', flat=True)
        return {slot + '(%)': slot for slot in slots}

    def get_export_fields(self):
        fields = {
            'Employee Name': 'full_name',
            **self.get_slots_in_fy(),
            'Total Avg. score (%)': 'total_average_score',
        }
        return fields

    def get_extra_export_data(self):
        ctx = super().get_extra_export_data()
        ctx['prepare_export_object_context'] = {
            'year_id': self.kwargs.get('year_id')
        }
        return ctx

    @staticmethod
    def prepare_export_object(user, **kwargs):
        """
        this is a method that will prepare export object. It will get object instance as its
        first parameter and should return object or dict.
        :param user: Instance (A row) that will be exported
        :return: prepared object
        """
        year_id = kwargs.get('year_id')
        scores = get_user_appraisal_score_for_year(user, year_id)
        for slot, percentage in scores.items():
            # setting percentage of corresponding slot for a user
            setattr(user, slot, percentage)
        user.total_average_score = scores.get('total_average_score')
        return user
