from django.db.models import ProtectedError
from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.viewset_mixins import ListCreateRetrieveUpdateViewSetMixin, \
    OrganizationMixin, GetStatisticsMixin
from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.hris.api.v1.serializers.exit_interview import ExitInterviewSerializer, \
    ExitInterViewQuestionSetSerializer
from irhrs.hris.constants import STOPPED, HOLD, COMPLETED
from irhrs.hris.models.exit_interview import ExitInterview, ExitInterviewQuestionSet
from irhrs.permission.constants.permissions import HAS_PERMISSION_FROM_METHOD, \
    EXIT_INTERVIEW_PERMISSION
from irhrs.permission.permission_classes import permission_factory


class ExitInterviewViewSet(
    OrganizationMixin,
    ListCreateRetrieveUpdateViewSetMixin,
    GetStatisticsMixin
):
    """

    ## Create exit interview as below:

    To Set Exit Interview for an employee follow the steps:

    URL: /api/v1/hris/{organization_slug}/exit-interview/

    Method: POST

    Data:

        {
            "separation": "employee separation id",
            "scheduled_at": "date time i.e. 2020-02-20T00:00",
            "location": "Text",
            "question_set": "Exit interview question set id",
            "interviewer": "user id as interviewer"
        }

    ## To View Detail of employee we must follow these steps:

    URL:

    Method: Get

    Data:

        {
            "id": 4,
            "separation": {
                "id": 40,
                "employee": {userthinserializer},
            "scheduled_at": "2020-08-09T00:00:00+05:45",
            "location": "Kathmandu",
            "question_set": {
                "id": 1,
                "name": "Question set 1",
                "description": "Question set"
            },
            "interviewer": {userthinserializer},
            "status": "Pending",
            "data": {
                "status": "Pending",
                "questions": [
                    {
                        "id": 28,
                        "order": 1,
                        "title": "What are your strength and weaknesses?",
                        "answers": [],
                        "category": {
                            "slug": "interview-question",
                            "title": "Interview Question"
                        },
                        "weightage": 0,
                        "description": "",
                        "is_open_ended": true,
                        "question_type": "interview_evaluation",
                        "answer_choices": "short-text"
                    }
                ]
            }
        }

    Here, 'separation.employee' gives data for user whose interview is going to be taken.
    'data' holds all information about questions related to this exit interview.

    """
    lookup_field = 'separation_id'
    queryset = ExitInterview.objects.all()
    serializer_class = ExitInterviewSerializer
    permission_classes = [
        permission_factory.build_permission(
            'ExitInterViewPermission',
            allowed_to=[HAS_PERMISSION_FROM_METHOD]
        )
    ]
    http_method_names = ['get', 'post', 'patch', 'options']
    filter_backends = [FilterMapBackend, OrderingFilterMap]
    filter_map = {
        'status': 'status',
        'candidate_name': 'separation__employee',
        'schedule_date': 'scheduled_at'
    }
    ordering_fields_map = {
        'scheduled_date': 'scheduled_at',
        'candidate_name': 'separation__employee__first_name',
        'interviewer': 'interviewer__first_name',
        'location': 'location'
    }
    statistics_field = 'status'

    @property
    def mode(self):
        mode = self.request.query_params.get('as')
        if mode not in ['hr', 'interviewer']:
            return 'user'
        return mode

    def has_user_permission(self):
        if self.mode == 'hr' and validate_permissions(
            self.request.user.get_hrs_permissions(self.organization),
            EXIT_INTERVIEW_PERMISSION
        ):
            return True
        elif self.request.method.lower() != 'post' and self.mode == 'interviewer':
            return True
        return False

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.mode == 'interviewer':
            queryset = queryset.filter(
                interviewer=self.request.user
            ).exclude(
                separation__status__in=[STOPPED, HOLD, COMPLETED]
            )
        return queryset.select_related(
            'question_set', 'interviewer', 'interviewer__detail',
            'interviewer__detail__job_title', 'separation', 'separation__employee',
            'separation__employee__detail', 'separation__employee__detail__job_title',
        )

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            exclude_fields = ['question_set', 'data']
            if self.mode != 'hr':
                exclude_fields.append('interviewer')

            kwargs.update({
                'exclude_fields': exclude_fields
            })
        if self.action == 'partial_update':
            kwargs.update({
                'fields': ['data']
            })
        if self.action == 'create':
            kwargs.update({
                'exclude_fields': ['data']
            })
        return super().get_serializer(*args, **kwargs)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data.update({
            'stats': self.statistics
        })
        return response


class ExitInterviewQuestionSetViewSet(OrganizationMixin, ModelViewSet):
    queryset = ExitInterviewQuestionSet.objects.all()
    serializer_class = ExitInterViewQuestionSetSerializer
    permission_classes = [
        permission_factory.build_permission(
            'ExitInterviewPermission',
            allowed_to=[EXIT_INTERVIEW_PERMISSION]
        )
    ]

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            raise ValidationError({'error': 'Can not delete used exit interview question set.'})

