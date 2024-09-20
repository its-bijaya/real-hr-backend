from datetime import timedelta

from django.db import transaction
from django.db.models import Count, F, Exists, OuterRef
from django.http import Http404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from django_q.models import Schedule
from django_q.tasks import async_task
from rest_framework import filters, serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from irhrs.assessment.api.v1.serializers.assessment import (AssessmentSetSerializer,
                                                            AssignAssessmentToUserSerializer,
                                                            AssessmentSectionSerializer,
                                                            AssessmentQuestionsSerializer,
                                                            QuestionResponseSerializer,
                                                            UserAssessmentSerializer,
                                                            UserAssessmentRateSerializer,
                                                            AssessmentSetWithSectionSerializer)
from irhrs.assessment.models.assessment import (AssessmentSet, AssessmentSection,
                                                AssessmentQuestions, UserAssessment,
                                                QuestionResponse)
from irhrs.assessment.models.helpers import IN_PROGRESS, COMPLETED, CANCELLED, PENDING, HOLD
from irhrs.assessment.utils import calculate_total_weight, add_weightage_for_assessment_set
from irhrs.assessment.utils.background_tasks import unlock_assessment_questions, score_assessment
from irhrs.assessment.tasks import send_unassign_assessment_email
from irhrs.core.mixins.serializers import DummySerializer
from irhrs.core.mixins.viewset_mixins import (OrganizationMixin, OrganizationCommonsMixin,
                                              IStartsWithIContainsSearchFilter, ListViewSetMixin)
from irhrs.core.utils.common import validate_permissions, humanize_interval
from irhrs.core.utils.common_utils import get_users_list_from_permissions
from irhrs.core.utils.email import send_notification_email
from irhrs.notification.utils import notify_organization
from irhrs.permission.constants.permissions.assessment_questionnaire_training import \
    (ASSESSMENT_SET_PERMISSION, ASSESSMENT_ASSIGN_PERMISSION,
     ASSESSMENT_ATTACH_QUESTIONS_PERMISSION,
     ASSESSMENT_REVIEW_PERMISSION, FULL_ASSESSMENT_PERMISSION)
from irhrs.core.constants.organization import ASSESSMENT_COMPLETED_BY_USER_EMAIL
from irhrs.core.utils import email
from irhrs.permission.permission_classes import permission_factory


class AssessmentSetViewSet(OrganizationCommonsMixin, OrganizationMixin, ModelViewSet):
    """

    """
    queryset = AssessmentSet.objects.all()
    serializer_class = AssessmentSetSerializer
    filter_backends = (
        filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend
    )
    permission_classes = [
        permission_factory.build_permission(
            'AssessmentPermission',
            limit_write_to=[
                ASSESSMENT_SET_PERMISSION,
                ASSESSMENT_ASSIGN_PERMISSION,
            ],
            actions={
                'assign_assessment': [ASSESSMENT_ASSIGN_PERMISSION]
            }
        )
    ]
    # filter_map = {
    #     'status': 'assessments__status'
    # }

    def get_queryset(self):
        is_authority = validate_permissions(
            self.request.user.get_hrs_permissions(self.organization),
            ASSESSMENT_SET_PERMISSION
        )  # or self.request.user.is_audit_user
        only_my = self.request.query_params.get('my') == 'true'
        status = self.request.query_params.get('status')
        fil = dict()

        if status:
            fil.update({
                'assessments__status': status
            })

        if not is_authority:
            only_my = True

        base_qs = super().get_queryset()

        if only_my:
            fil.update({
                'assessments__user': self.request.user
            })

        base_qs = base_qs.filter(**fil).annotate(
            assigned_count=Count('assessments'),
            appeared=Exists(
                UserAssessment.objects.filter(
                    user=self.request.user,
                    assessment_set=OuterRef('pk')
                )
            ),
        ).prefetch_related(
            'sections__questions'
        )

        # TODO @Shital, with Frontend, handle this & only my through `?as=hr`.
        if self.request.query_params.get('appeared') == 'true':
            return base_qs.filter(appeared=True)
        elif self.request.query_params.get('appeared') == 'false':
            return base_qs.filter(appeared=False)
        return base_qs.order_by('-created_at')

    def get_serializer_class(self):
        if self.action.lower() == "create":
            return AssessmentSetWithSectionSerializer
        return super().get_serializer_class()

    def update(self, request, *args, **kwargs):
        if not self.get_object().assessments.exists():
            update = super().update(request, *args, **kwargs)
            add_weightage_for_assessment_set(self.get_object())
            return update
        return Response(
            {'detail': ['Unable to update this assessment. '
                        'Assessment has been assigned to user.']},
            status=status.HTTP_400_BAD_REQUEST
        )

    def destroy(self, request, *args, **kwargs):
        if not self.get_object().assessments.exists():
            return super().destroy(request, *args, **kwargs)
        return Response(
            {'detail': ['Unable to delete this assessment. '
                        'Assessment has been assigned to user.']},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=True,
        methods=['POST'],
        serializer_class=AssignAssessmentToUserSerializer,
        url_path='assign-assessment'
    )
    def assign_assessment(self, request, *args, **kwargs):
        assessment_set = self.get_object()
        assessment_questions = AssessmentQuestions.objects.filter(
            assessment_section__assessment_set=assessment_set
        )
        _assessment_section_exists = assessment_set.sections.filter(
            section_questions__isnull=True
        ).exists()

        if not _assessment_section_exists and assessment_questions.exists():
            serializer = AssignAssessmentToUserSerializer(
                data=request.data,
                context={
                    **self.get_serializer_context(),
                    'assessment': assessment_set,
                    'request': self.request
                }
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        if _assessment_section_exists and assessment_questions.exists():
            return Response(
                {
                    'detail': ['There are no any questions associated to'
                               ' section of this assessment.']
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                'detail': ['There are no any questions associated to this assessment.']
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=True,
        methods=['DELETE'],
        url_path=r'assign-assessment/(?P<assigned_user_id>\d+)'
    )
    def remove_assigned_user(self, request, *args, **kwargs):
        assessment_set = self.get_object()
        assigned_user_id = self.kwargs.get('assigned_user_id')
        assigned_user = assessment_set.assessments.filter(id=assigned_user_id).first()

        if not assigned_user:
            return Response(
                {'detail': 'Data not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        if assigned_user.status == PENDING:
            # async_task(
            #     send_unassign_assessment_email,
            #     assigned_user
            # )
            send_unassign_assessment_email(assigned_user)
            assigned_user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        status_text = {
            IN_PROGRESS: 'Assessment for user is in progress.',
            COMPLETED: 'Assessment for user has been completed.',
            HOLD: 'Assessment for user has been hold.',
            CANCELLED: 'Assessment for user has been cancelled'
        }

        return Response(
            {
                'detail': [f'Unable to remove user from assessment. '
                           f'{status_text.get(assigned_user.status)}']
            },
            status=status.HTTP_400_BAD_REQUEST
        )


class AssessmentSectionViewSet(OrganizationMixin, ModelViewSet):
    queryset = AssessmentSection.objects.all()
    serializer_class = AssessmentSectionSerializer
    filter_backends = (
        filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend
    )
    filter_fields = ['assessment_set', ]
    permission_classes = [
        permission_factory.build_permission(
            'AssessmentPermission',
            allowed_to=[ASSESSMENT_SET_PERMISSION],
            limit_read_to=[
                ASSESSMENT_ATTACH_QUESTIONS_PERMISSION,
                ASSESSMENT_SET_PERMISSION
            ]
        )
    ]

    def get_serializer(self, *args, **kwargs):
        if self.action != 'retrieve':
            kwargs['exclude_fields'] = ('assessment_questions',)
        return super().get_serializer(*args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().annotate(
            questions_count=Count('questions')
        )

    def destroy(self, request, *args, **kwargs):
        assessment_set = self.get_object().assessment_set
        if not assessment_set.assessments.exists():
            return super().destroy(request, *args, **kwargs)
        return Response(
            {'detail': ['Unable to delete this section. Assessment has been assigned to user.']},
            status=status.HTTP_400_BAD_REQUEST
        )


class AssessmentSectionQuestionsView(OrganizationMixin, ModelViewSet):
    queryset = AssessmentQuestions.objects.all()
    serializer_class = AssessmentQuestionsSerializer
    filter_backends = (
        IStartsWithIContainsSearchFilter, DjangoFilterBackend
    )
    permission_classes = [
        permission_factory.build_permission(
            'AssessmentPermission',
            allowed_to=[
                ASSESSMENT_ATTACH_QUESTIONS_PERMISSION
            ],
        )
    ]
    search_fields = 'question__title',
    # TODO: @Shital Remove commented code given below
    # pagination_class = type(
    #     'AssessmentSectionPagination',
    #     (PageNumberPagination,),
    #     {
    #         'page_size': 10,
    #         'page_size_query_param': 'page_size'
    #     }
    # )

    def __init__(self, *args, **kwargs):
        self.assessment_object = None
        super().__init__(*args, **kwargs)

    def initial(self, *args, **kwargs):
        super().initial(*args, **kwargs)
        self.assessment_object = get_object_or_404(
            AssessmentSection.objects.filter(
                assessment_set__organization=self.organization
            ), pk=self.kwargs.get('assessment_section_id')
        )
        if self.request.method.lower() != 'get':
            assessment_set = self.assessment_object.assessment_set
            if assessment_set.assessments.exists():
                raise ValidationError(
                    {
                        'detail': ['Unable to perform this action.'
                                   ' Assessment has been assigned to user.']
                    }
                )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['assessment_section'] = self.assessment_object
        return ctx

    def get_serializer(self, *args, **kwargs):
        if isinstance(kwargs.get('data', {}), list):
            kwargs['many'] = True
        return super().get_serializer(*args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(
            assessment_section=self.assessment_object
        ).select_related(
            'question', 'question__category', 'assessment_section'
        ).order_by('order')

    def filter_queryset(self, queryset):
        return super().filter_queryset(queryset).order_by('order')

    # to rollback create if validation error occurs
    @transaction.atomic()
    def create(self, request, *args, **kwargs):
        if bool(request.data):
            AssessmentQuestions.objects.filter(
                assessment_section=self.assessment_object
            ).delete()
            _created_questions = super().create(request, *args, **kwargs)
            add_weightage_for_assessment_set(self.assessment_object.assessment_set)
            return _created_questions

        return Response(
            {
                'non_field_errors': [
                    'At least one question need to be added for assessment section.']
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    def destroy(self, request, *args, **kwargs):
        deleted = super().destroy(request, *args, **kwargs)
        add_weightage_for_assessment_set(self.assessment_object.assessment_set)
        self.recalculate_question_order(self.assessment_object)
        return deleted

    def recalculate_question_order(self, section):
        questions = section.section_questions.all()
        for index, question in enumerate(questions):
            question.order = index + 1
            question.save()


class TakeAssessmentView(OrganizationMixin, ModelViewSet):
    """
    This is users' API.
    Only Take Assessment is Done Here.

    # List API shall return the current question and available answers
    """
    serializer_class = AssessmentSectionSerializer

    @property
    def is_authority(self):
        return validate_permissions(
            self.request.user.get_hrs_permissions(self.organization),
            ASSESSMENT_REVIEW_PERMISSION
        ) and self.request.query_params.get('as') == 'hr'

    def get_queryset(self):
        assessment_set = self.assessment_set
        if not assessment_set and not self.is_authority:
            raise Http404
        return AssessmentSection.objects.filter(
            assessment_set=self.assessment_set.assessment_set,
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['user_assessment'] = self.assessment_set
        ctx['hide_answer'] = True

        # This is To hide is_correct field from answer while giving assessment
        # TODO: @Shital If any other possible solution please implement it

        if not self.is_authority:
            ctx['exclude_field'] = dict(exclude_fields=('is_correct',))
        return ctx

    @property
    def assessment_set(self):
        if not self.is_authority:
            assessment = UserAssessment.objects.filter(
                status__in=[PENDING, IN_PROGRESS],
                assessment_set=self.kwargs.get('assessment_id'),
                user=self.request.user
            ).first()
            return assessment
        else:
            user = self.request.query_params.get('user')
            if user:
                return UserAssessment.objects.filter(
                    assessment_set=self.kwargs.get('assessment_id'),
                    user_id=user
                ).first()
            return UserAssessment.objects.none()

    def list(self, request, *args, **kwargs):
        user_assessment_set = self.assessment_set
        if not user_assessment_set:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        self._validate_in_progress_assessment(user_assessment_set)

        if user_assessment_set and user_assessment_set.status == PENDING:
            if user_assessment_set.expiry_date <= timezone.now():
                user_assessment_set.expired = True
            user_assessment_set.save()
            if not user_assessment_set.question_responses.exists():
                unlock_assessment_questions(user_assessment_set)

        remaining_duration = self.calculate_remaining_duration()
        if not self.is_authority:
            self.validate_expired_assessment(user_assessment=user_assessment_set)

        response = super().list(request, *args, **kwargs)
        if remaining_duration:
            response.data.update({
                'remaining_duration': remaining_duration,
                'status': user_assessment_set.status
            })
        else:
            response.data.update({
                'remaining_duration': '00:00:00',
                'status': PENDING,
            })
        if user_assessment_set.status == COMPLETED:
            response.data['obtained_score'] = user_assessment_set.score
        else:
            response.data['obtained_score'] = 0

        response.data.update({
            'total_weightage': user_assessment_set.assessment_set.total_weightage,
            'marginal_weightage': user_assessment_set.assessment_set.marginal_weightage,
            'remarks': user_assessment_set.remarks,
            'expired': user_assessment_set.expired
        })
        return response

    def _validate_in_progress_assessment(self, user_assessment_set):
        if self.request and self.request.user == user_assessment_set.user:
            in_progress_assessment = self.request.user.assessments.filter(
                status=IN_PROGRESS
            ).exclude(id=self.assessment_set.id)
            if in_progress_assessment.exists():
                raise ValidationError(
                    {
                        "detail": f"You must complete "
                                  f"'{in_progress_assessment.first().assessment_set.title}'"
                                  " before starting this assessment."
                    }
                )

    @staticmethod
    def validate_expired_assessment(user_assessment):
        if user_assessment and user_assessment.expired:
            user_assessment.status = COMPLETED
            user_assessment.ended_at = timezone.now().astimezone()
            user_assessment.remarks = f"Assessment expired on " \
                                      f"{user_assessment.expiry_date.strftime('%Y-%m-%d %I:%M %p')}."
            user_assessment.save()
            user_assessment.refresh_from_db()

            # Remove listener for optimization.

            async_task(
                score_assessment,
                user_assessment
            )
            raise ValidationError(
                f'Assessment expired on '
                f'{user_assessment.expiry_date.strftime("%Y-%m-%d %I:%M %p")}.'
            )

    def calculate_remaining_duration(self):
        user_assessment = self.assessment_set
        if user_assessment and user_assessment.status == IN_PROGRESS \
                and not user_assessment.started_at and not user_assessment.expired:
            if user_assessment.user == self.request.user:
                user_assessment.started_at = timezone.now().astimezone()
                user_assessment.save()
                Schedule.objects.create(
                    func='irhrs.assessment.utils.background_tasks.terminate_ongoing_assessment',
                    args=(user_assessment.id,),
                    next_run=user_assessment.started_at + user_assessment.assessment_set.duration
                )

        if user_assessment and user_assessment.started_at:
            _elapsed_duration = timezone.now() - user_assessment.started_at
            _remaining_duration = user_assessment.assessment_set.duration - _elapsed_duration
            if _remaining_duration < timedelta(0):
                _remaining_duration = timedelta(0)
            return humanize_interval(_remaining_duration)
        return humanize_interval(user_assessment.assessment_set.duration)

    @action(
        methods=['POST'],
        detail=False,
        url_path='start',
        serializer_class=DummySerializer
    )
    @transaction.atomic()
    def start_assessment(self, *args, **kwargs):
        # only if not started.
        assessment_set = self.assessment_set
        if not assessment_set:
            raise Http404
        if assessment_set.status != PENDING:
            if assessment_set.expired:
                raise ValidationError(
                    'Assessment has been expired.'
                )
            raise ValidationError(
                'No Test in Progress'
            )

        if assessment_set.expiry_date <= timezone.now():
            assessment_set.expired = True
            response = {'detail': 'Assessment has been expired.'}, status.HTTP_400_BAD_REQUEST
        else:
            response = 'Assessment will begin shortly.'

        # Create all questions, update assessment status to in-progress.
        if assessment_set and not assessment_set.question_responses.exists():
            unlock_assessment_questions(assessment_set)

        self._validate_in_progress_assessment(assessment_set)

        assessment_set.status = IN_PROGRESS
        assessment_set.save()

        return Response(response)

    @action(
        methods=['GET', 'PUT'],
        detail=False,
        url_path=r'respond/(?P<response_id>\d+)',
        serializer_class=QuestionResponseSerializer
    )
    def respond(self, *args, **kwargs):
        if self.assessment_set.expired:
            raise ValidationError('Assessment has been expired.')

        response_id = self.kwargs.get('response_id')
        response_object = get_object_or_404(
            QuestionResponse.objects.filter(
                user_assessment=self.assessment_set,
            ),
            id=response_id
        )
        if self.request.method == 'GET':
            return Response(
                QuestionResponseSerializer(
                    instance=response_object
                ).data
            )
        # if response_object.status in [COMPLETED, CANCELLED]:
        #     raise ValidationError({
        #         'error': 'Can not update solutions.'
        #     })
        serializer = QuestionResponseSerializer(
            instance=response_object,
            data=self.request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response_object.status = COMPLETED
        response_object.save()
        return Response(serializer.data)

    @action(
        methods=['POST'],
        detail=False,
        url_path='exit-assessment',
        serializer_class=type(
            'AssessmentQuitSerializer',
            (DummySerializer,),
            {
                'remarks': serializers.CharField(max_length=255)
            }
        )
    )
    def exit_assessment(self, request, *args, **kwargs):
        """
        For pre mature evacuation
        """
        serializer = self.serializer_class(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        user_assessment = self.assessment_set
        recipients = []
        if user_assessment:
            user = user_assessment.user
            user_assessment.status = COMPLETED
            user_assessment.ended_at = timezone.now().astimezone()
            user_assessment.remarks = serializer.validated_data.get('remarks')
            user_assessment.save()
            user_assessment.refresh_from_db()

            # Remove listener for optimization.

            async_task(
                score_assessment,
                user_assessment
            )
            # send mail
            recipients = []
            subject = f"Assessment completed by {user.full_name}"
            email_text=(
                f"'{user_assessment.assessment_set.title}' assigned to"
                f" '{user_assessment.user.full_name}' has been completed."
            )
            mail_to_permisisons = [
                FULL_ASSESSMENT_PERMISSION,
                ASSESSMENT_ASSIGN_PERMISSION,
                ASSESSMENT_REVIEW_PERMISSION,
            ]
            mail_list = get_users_list_from_permissions(
                mail_to_permisisons,
                user_assessment.assessment_set.organization
            )

            for user in mail_list:
                # add to recipient list if not already sent
                email_already_sent =  email.has_sent_email(
                    recipient=user,
                    notification_text=email_text,
                    subject=subject
                )
                can_send_email = email.can_send_email(
                    user,
                    ASSESSMENT_COMPLETED_BY_USER_EMAIL
                )
                if can_send_email and not email_already_sent:
                    recipients.append(user.email)

            if recipients:
                send_notification_email(
                    recipients=recipients,
                    subject=subject,
                    notification_text=email_text
                )

            notify_organization(
                text=f"'{user_assessment.assessment_set.title}' assigned to"
                     f" '{user_assessment.user.full_name}' has been completed.",
                url=f'/admin/{user_assessment.assessment_set.organization}/'
                    f'assessment/enrolled-users',
                action=user_assessment,
                permissions=[
                    FULL_ASSESSMENT_PERMISSION,
                    ASSESSMENT_REVIEW_PERMISSION
                ],
                organization=user_assessment.assessment_set.organization,
            )
            return Response(
                "Assessment Completed Successfully."
                "Results will be notified soon"
            )
        return Response(
            "There is no any assessment assigned to user."
        )


class PastAssessmentView(OrganizationMixin, ListViewSetMixin):
    """
    # Retrieve assessment detail with
    * ../<id>/detail

    # Rate User's assessment (FOR Long & Short Texts)
    * ../<id>/detail/<response_id>/
    """
    queryset = UserAssessment.objects.all().filter(
        status__in=[COMPLETED, CANCELLED]
    )
    serializer_class = UserAssessmentSerializer
    permission_classes = [
        permission_factory.build_permission(
            'AssessmentReviewPermission',
            actions={
                'rate_assessment_answers': [ASSESSMENT_REVIEW_PERMISSION]
            }
        )
    ]
    filter_backends = [SearchFilter]
    search_fields = ['assessment_set__title', 'user__first_name',
                     'user__middle_name', 'user__last_name']

    def filter_queryset(self, queryset):
        is_authority = validate_permissions(
            self.request.user.get_hrs_permissions(self.organization),
            ASSESSMENT_REVIEW_PERMISSION
        ) and self.request.query_params.get('as') == 'hr'

        margin = self.request.query_params.get('margin')
        base_qs = super().filter_queryset(queryset)
        if not is_authority:
            base_qs = base_qs.filter(user=self.request.user)
        if margin == 'above':
            base_qs = base_qs.filter(
                score__gte=F('assessment_set__marginal_weightage')
            )
        elif margin == 'below':
            base_qs = base_qs.filter(
                score__lt=F('assessment_set__marginal_weightage')
            )
        return base_qs.select_related(
            'user', 'user__detail', 'user__detail__employment_level', 'user__detail__job_title',
            'user__detail__organization', 'user__detail__division',
            'created_by', 'created_by__detail', 'created_by__detail__employment_level',
            'created_by__detail__job_title', 'created_by__detail__organization',
            'created_by__detail__division', 'assessment_set',
        )

    @action(
        detail=True,
        url_path='detail'
    )
    def assessment_detail(self, *args, **kwargs):
        instance = self.get_object()
        ser = AssessmentSectionSerializer(
            instance=instance.assessment_set.sections.all(),
            many=True,
            context={
                **self.get_serializer_context(),
                'user_assessment': instance
            }
        )
        return Response(ser.data)

    @action(
        detail=True,
        methods=['POST'],
        url_path=r'detail/(?P<response_id>\d+)',
        serializer_class=UserAssessmentRateSerializer
    )
    def rate_assessment_answers(self, *args, **kwargs):
        question_response_map = get_object_or_404(
            self.filter_queryset(
                self.get_queryset()
            ),
            pk=self.kwargs.get('response_id')
        )
        serializer = UserAssessmentRateSerializer(
            data=self.request.data,
            instance=question_response_map,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
