from django.db.models import Count, Sum, Q, \
    Avg, Min, Max, FloatField

from rest_framework.response import Response
from rest_framework.views import APIView

from irhrs.core.mixins.viewset_mixins import UserMixin, UserCommonsMixin
from irhrs.hris.models import ResultArea
from irhrs.organization.models import FiscalYear
from irhrs.task.constants import RESPONSIBLE_PERSON, PENDING, IN_PROGRESS, \
    COMPLETED, ON_HOLD, CLOSED
from irhrs.task.models.ra_and_core_tasks import UserResultArea

from ....models.task import TaskAssociation, Task


class EfficiencyView(APIView):
    """
    list:
    My Efficiency
    """

    def get(self, request, format=None):
        task_verified_score_filter = {
            'taskverificationscore__ack': True
        }

        agg_data = TaskAssociation.objects.filter(
            user=self.request.user, association=RESPONSIBLE_PERSON
        ).aggregate(
            assigned_task=Count('id', distinct=True),
            scored=Count('id', filter=Q(
                **task_verified_score_filter
            ), distinct=True),
            acknowledged=Count(
                'id', filter=Q(
                    **task_verified_score_filter
                ),
                distinct=True),
            average_efficiency=Avg(
                'efficiency',
                filter=Q(efficiency__isnull=False, **task_verified_score_filter),
                output_field=FloatField()
            ),
            min_efficiency=Min(
                'efficiency',
                filter=Q(efficiency__isnull=False, **task_verified_score_filter)
            ),
            max_efficiency=Max(
                'efficiency',
                filter=Q(efficiency__isnull=False, **task_verified_score_filter)
            ),
            total_score=Sum(
                'taskverificationscore__score',
                filter=Q(**task_verified_score_filter),
                output_field=FloatField()
            ),
            average_score=Avg(
                'taskverificationscore__score',
                filter=Q(**task_verified_score_filter),
                output_field=FloatField()
            ),
            min_score=Min(
                'taskverificationscore__score',
                filter=Q(**task_verified_score_filter)
            ),
            max_score=Max(
                'taskverificationscore__score',
                filter=Q(**task_verified_score_filter)
            )
        )
        return Response(agg_data)


class UserProfileTaskDetailView(UserCommonsMixin, APIView):
    def get(self, request, user_id=None):
        fiscal_year = FiscalYear.objects.current(
            organization=self.user.detail.organization)
        if fiscal_year:
            agg_data = TaskAssociation.objects.filter(
                user=self.user, association=RESPONSIBLE_PERSON,
                task__starts_at__date__gte=fiscal_year.applicable_from,
                task__deadline__date__lte=fiscal_year.applicable_to
            ).aggregate(
                all_tasks=Count('id', distinct=True),

                pending=Count(
                    'id',
                    filter=Q(task__status=PENDING),
                    distinct=True
                ),
                in_progress=Count(
                    'id',
                    filter=Q(task__status=IN_PROGRESS),
                    distinct=True
                ),
                completed=Count(
                    'id',
                    filter=Q(task__status=COMPLETED),
                    distinct=True
                ),
                closed_and_hold=Count(
                    'id',
                    filter=Q(Q(task__status=CLOSED) | Q(task__status=ON_HOLD)),
                    distinct=True
                ),
                efficiency=Avg(
                    'efficiency',
                    filter=Q(
                        efficiency__isnull=False,
                        taskverificationscore__ack=True
                    ),
                    output_field=FloatField(),
                ),
                total_score=Sum(
                    'taskverificationscore__score',
                    filter=Q(taskverificationscore__ack=True),
                    output_field=FloatField(),
                ),
                average_score=Avg(
                    'taskverificationscore__score',
                    filter=Q(taskverificationscore__ack=True),
                    output_field=FloatField(),
                ),
            )
            user_ra = UserResultArea.objects.filter(
                user_experience__user=self.user).distinct().values_list(
                'result_area__title',
                flat=True)
            result_area = {}
            for _result_area in user_ra:
                task_association = TaskAssociation.objects.filter(
                    user=self.user, association=RESPONSIBLE_PERSON,
                    task__starts_at__date__gte=fiscal_year.applicable_from,
                    task__deadline__date__lte=fiscal_year.applicable_to,
                    efficiency__isnull=False
                ).aggregate(
                    avg_data=Avg(
                        'efficiency',
                        filter=Q(
                            core_tasks__result_area__title=_result_area,
                            taskverificationscore__ack=True
                        ),
                        output_field=FloatField()
                    ))
                if task_association['avg_data']:
                    result_area[_result_area] = task_association['avg_data']

            sorted_result_area = dict(
                sorted(result_area.items(), key=lambda x: x[1], reverse=True)[:5])

            agg_data['result_area_efficiency'] = sorted_result_area
        else:
            agg_data = {
                'detail': "Fiscal Year not associated with user's organization"
            }
        return Response(agg_data)
