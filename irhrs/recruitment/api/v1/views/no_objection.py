from django.db import transaction
from django.db.models import Q, Count, Subquery, OuterRef
from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from irhrs.core.mixins.viewset_mixins import (
    ListCreateRetrieveUpdateViewSetMixin)
from irhrs.notification.utils import add_notification
from irhrs.recruitment.api.v1.mixins import (
    DynamicFieldViewSetMixin, HrAdminOrSelfQuerysetMixin, RecruitmentPermissionMixin)
from irhrs.recruitment.api.v1.permissions import (
    RecruitmentPermission, RecruitmentAuditUserPermission
)
from irhrs.recruitment.api.v1.serializers.no_objection import (
    NoObjectionSerializer,
    MemorandumSerializer, MemorandumJobApplySerializer
)
from irhrs.recruitment.constants import (
    REFERENCE_VERIFIED, REJECTED, SELECTED, SHORTLISTED, COMPLETED,
    SCREENED, INTERVIEWED,
    PENDING, DENIED, APPROVED, SALARY_DECLARED
)
from irhrs.recruitment.models import (
    NoObjection,
    Job, JobApply, JobApplyStage,
    PreScreening, ReferenceCheck,
    PreScreeningInterview, ApplicantReference, ReferenceChecker, InterViewAnswer, Interview,
    SalaryDeclaration, PostScreening
)
from irhrs.recruitment.utils.email import replace_template_message
from irhrs.recruitment.utils.stages import (
    get_next_stage, class_mapper
)
from irhrs.recruitment.utils.util import raise_exception_if_job_apply_is_not_in_completed_step
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer


class NoObjectionViewSet(
    RecruitmentPermissionMixin,
    HrAdminOrSelfQuerysetMixin,
    DynamicFieldViewSetMixin,
    ListCreateRetrieveUpdateViewSetMixin
):
    queryset = NoObjection.objects.select_related(
        'email_template', 'report_template',
        'responsible_person'
    )
    serializer_class = NoObjectionSerializer
    user_field = 'responsible_person'
    serializer_exclude_fields = ['job', 'modified_template', ]
    permission_classes = [RecruitmentPermission]

    _job = None

    def get_permission_classes(self):
        if self.is_hr_admin and self.action == 'verify_no_objection':
            return [RecruitmentAuditUserPermission]
        return self.permission_classes

    def check_permissions(self, request):
        if self.action in ['update', 'partial_update']:
            self.permission_denied(request)
        super().check_permissions(request)

    def get_queryset(self):
        qs = super().get_queryset()
        if self.kwargs.get('job_slug'):
            qs = qs.filter(
                job__slug=self.kwargs.get('job_slug')
            )

        if self.action == 'verify_no_objection':
            qs = qs.filter(
                responsible_person=self.request.user,
                status=COMPLETED
            )
        if self.action == 'list':
            qs = qs.filter(
                Q(status=COMPLETED) |
                Q(status=DENIED) |
                Q(status=APPROVED)
            )
        return qs.order_by('-created_at', 'verified')

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['job'] = self.job
        return ctx

    @action(
        detail=True,
        methods=['POST'],
        url_name='verify',
        url_path='verify',
        permission_classes=[RecruitmentAuditUserPermission]
    )
    def verify_no_objection(self, request, *args, **kwargs):
        status = request.data.get('status')
        if status and status in [APPROVED, DENIED]:
            obj = self.get_object()
            with transaction.atomic():
                remarks = str(request.data.get('remarks', ''))[:200]
                obj.remarks = remarks

                if status == APPROVED:
                    self.process_post_no_objection(obj)
                    obj.verified = True

                obj.status = status
                obj.save()

                if status == DENIED and obj.job_apply:
                    job_apply = obj.job_apply

                    job_apply.status = REJECTED
                    job_apply.remarks = remarks
                    job_apply.save()

                    JobApplyStage.objects.create(
                        job_apply=job_apply,
                        status=REJECTED
                    )
            return Response({'status': 'Completed'})
        else:
            raise ValidationError(_('Invalid Status'))

    @action(
        detail=False,
        methods=['post'],
        url_name='multiple_candidate',
        url_path='multiple-candidate'
    )
    def multiple_candidate(self, request, *args, **kwargs):
        job_apply_ids = request.data.get('candidates')
        stage = request.data.get('stage')
        job_slug = kwargs['job_slug']
        if job_apply_ids and stage:
            invalid_ids = NoObjection.objects.filter(
                status__in=[PENDING, APPROVED],
                stage=stage
            ).values_list('id', flat=True)

            job_apply_ids = JobApply.objects.filter(
                job__slug=job_slug
            ).values_list("id", flat=True)

            valid_ids = set(job_apply_ids).difference(set(invalid_ids))
            if valid_ids:
                ser = NoObjectionSerializer(
                    data=request.data,
                    fields=[
                        'responsible_person',
                        'email_template',
                        'stage',
                        'title',
                        'report_template'
                    ],
                )
                ser.is_valid(raise_exception=True)
                NoObjection.objects.bulk_create([
                    NoObjection(
                        job_apply_id=apply_id,
                        job=self.job,
                        **ser.validated_data
                    ) for apply_id in valid_ids
                ])
        return Response(status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'], url_name='template_modify', url_path='modify-template')
    def modify_template(self, request, *args, **kwargs):
        obj = self.get_object()

        if obj.status == COMPLETED:
            raise ValidationError({
                'status': ['Completed no objection cannot be modified']
            })

        status = request.data.get('status')
        if status and status not in [COMPLETED, PENDING]:
            raise ValidationError({
                'status': ['Only completed and pending status is allowed']
            })

        self.pre_condition_for_no_objection(obj)

        with transaction.atomic():
            ser = self.serializer_class(
                instance=obj,
                data=request.data,
                fields=['modified_template'],
                partial=True
            )
            ser.is_valid(raise_exception=True)
            obj = ser.save(status=status)
            if status == COMPLETED:
                transaction.on_commit(lambda: obj.send_mail())
                add_notification(
                    f'You have been assigned for no-objection verification of {obj.title}',
                    obj.responsible_person,
                    obj,
                    url=obj.notification_link,
                )
        return Response({'status': 'Modified'})

    def pre_condition_for_no_objection(self, instance: NoObjection):
        job_apply_stage = instance.stage
        job_apply_stage_map = {
            SHORTLISTED: PostScreening,
            INTERVIEWED: Interview,
            SALARY_DECLARED: SalaryDeclaration
        }

        if job_apply_stage in job_apply_stage_map.keys():
            raise_exception_if_job_apply_is_not_in_completed_step(
                job_apply_stage_map[job_apply_stage], self.job)

    @action(detail=True, url_name='memorandum-report', url_path='memorandum-report')
    def memorandum_report(self, request, *args, **kwargs):

        obj = self.get_object()

        extra_data = {
            'responsible_person': UserThinSerializer(instance=obj.responsible_person).data
        }
        if obj.modified_template:
            return Response({'template': obj.modified_template, **extra_data})

        stat = {
            'total_applicants': Count('applications', distinct=True),
            'total_eliminated_initially': Count(
                'applications',
                filter=Q(applications__pre_screening__isnull=True),
                distinct=True
            ),
            'total_duplicate': Count(
                'applications',
                filter=Q(applications__data__duplicate=True),
                distinct=True
            ),
            'long_list_eligible_candidate': Count(
                'applications',
                filter=Q(applications__pre_screening__isnull=False),
                distinct=True
            ),
            'hr_shortlisted': Count(
                'applications',
                filter=Q(applications__apply_stages__status=SCREENED),
                distinct=True
            ),
            # hiring manager shortlisted is just step completed as shortlisted will be done on
            # the basis of score and category provided in no objection letter
            'hiring_manager_shortlisted': Count(
                'applications',
                filter=Q(applications__post_screening__verified=True) & Q(
                    applications__post_screening__score__gte=obj.score),
                distinct=True
            ),
            'interview_completed': Count(
                'applications',
                filter=Q(applications__interview__verified=True),
                distinct=True
            ),
            'interview_absent': Count(
                'applications',
                filter=Q(
                    Q(applications__pre_screening_interview__status=PENDING) |
                    Q(applications__assessment__status=PENDING) |
                    Q(applications__interview__status=PENDING)
                ),
                distinct=True
            ),
            'interview_total_score': Subquery(
                InterViewAnswer.objects.filter(
                    interview__job_apply__job=OuterRef('pk'),
                    status=COMPLETED
                ).values('data__total_score')[:1]
            ),
            'pre_screening_questions': Subquery(
                PreScreening.objects.filter(
                    job_apply__job=OuterRef('pk'),
                    status=COMPLETED
                ).values('data__questions')[:1]
            ),
        }

        message = obj.report_template.message

        import re
        used_keys = re.findall('\{\{[A-Za-z0-9 _]+\}\}', message)

        try:
            valid_keys = [
                key.replace('{{', '').replace('}}', '') for key in used_keys
            ]
        except AttributeError:
            valid_keys = []

        if not obj.job_apply:

            job = Job.objects.filter(
                slug=self.kwargs.get('job_slug')
            ).annotate(
                **stat
            ).prefetch_related('applications').get()

            serialized_data = MemorandumSerializer(instance=job, fields=valid_keys).data
        else:
            serialized_data = MemorandumJobApplySerializer(
                instance=obj.job_apply, fields=valid_keys,
                context={
                    **self.get_serializer_context(),
                    **{'no_objection': obj}
                }
            ).data

        replace_data = {
            '{{' + k + '}}': v for k, v in serialized_data.items()
        }
        return Response(
            {
                'template': replace_template_message(
                    replace_data,
                    message
                ),
                **extra_data
            }
        )

    def process_post_no_objection(self, no_objection):
        """
            current_process:
                Forward candidates to next step using previous process's score and categories
                if score and categories both are not provided all candidates are forwarded to next
                status
            current_status:
                Move candidate to this step using apply status and further more rejecting all
                candidates who doesn't fall under this status
            next_step_class:
                Forward to next step by initializing next step
            extra_process:
                Extra Process that is to be carried out after next step initialization
            letter_template_key
                Template use to send email to candidate key are mapped in hiring info of job
        """
        next_stage = get_next_stage(self.job, no_objection.stage)
        next_class = class_mapper.get(next_stage)
        interview_hook = None
        if (
            no_objection.stage == INTERVIEWED and
            next_stage == REFERENCE_VERIFIED
        ):
            interview_hook = self.populate_reference_checkers

        mapper = {
            # Current Step: [current process, next_step_class, extra_process, letter_template_key]
            SHORTLISTED: [
                'post_screening',
                next_class,
                None,
                'pre_screening_interview_letter'
            ],
            INTERVIEWED: [
                'interview',
                next_class,
                interview_hook,
                'reference_check_letter'
            ],
            SALARY_DECLARED: [
                None,
                None,
                None,
                None
            ]
        }

        if mapper.get(no_objection.stage):
            new_stage = no_objection.stage
            current_process, next_step_class, extra_process, letter_template_key = mapper.get(
                no_objection.stage)

            # forward candidate who fall under provided score and category
            self.forward_candidates(
                no_objection,
                current_process,
                new_stage
            )

            # reject candidate who failed to go to next stage
            self.reject_candidates(
                new_stage
            )

            # move forward selected candidate by initializing next step
            self.initialize_next_step(
                new_stage,
                next_step_class,
                letter_template_key
            )

            if extra_process and callable(extra_process):
                extra_process()

    def forward_candidates(self, no_objection, current_process, new_stage):
        """
        :param no_objection:
        :param current_process:
            Forward candidates to next step using previous process's score and categories
            if score and categories both are not provided all candidates are forwarded to next
            stage
        :param new_stage:
            It is defined in stage of no objection
            Move candidate to this stage and reject all candidates who doesn't fall under this
             stage.
        """
        if no_objection.job_apply:
            applications = JobApply.objects.filter(
                id=no_objection.job_apply_id,
            ).filter(
                Q(data__isnull=False) |
                Q(data__rostered__isnull=True)
            ).exclude(status=new_stage)
        else:
            categories = no_objection.categories
            score = no_objection.score
            job = self.job

            applications = JobApply.objects.filter(
                job=job,
                **{f'{current_process}__verified': True}
            ).filter(
                Q(data__isnull=True) |
                Q(data__rostered__isnull=True)
            ).exclude(status=new_stage)

            if categories:
                job_categories = job.hiring_info.get('categories', [])
                valid_categories = set(job_categories).intersection(set(categories))
                applications = applications.filter(
                    **{f'{current_process}__category__in': valid_categories}
                )

            if score and isinstance(score, (int, float)):
                applications = applications.filter(
                    **{f'{current_process}__score__gte': score}
                )

        if applications:
            applications_ids = list(applications.values_list('id', flat=True))
            # Update status to next status
            applications.update(status=new_stage)

            # Create next step stage
            JobApplyStage.objects.bulk_create([
                JobApplyStage(
                    job_apply_id=job_apply,
                    status=new_stage,
                    remarks=''
                ) for job_apply in applications_ids
            ])

    def reject_candidates(self, new_stage):
        invalid_candidates = JobApply.objects.filter(job=self.job).exclude(
            Q(status=new_stage) | Q(status__in=[SELECTED, REJECTED]) | Q(
                Q(data__rostered__isnull=False) & Q(data__rostered=True)
            )
        )

        invalid_candidates_ids = list(invalid_candidates.values_list('id', flat=True))
        if invalid_candidates_ids:
            invalid_candidates.update(status=REJECTED)
            JobApplyStage.objects.bulk_create([
                JobApplyStage(
                    job_apply_id=apply_id,
                    status=REJECTED,
                    remarks='Rejected By System'
                ) for apply_id in invalid_candidates_ids
            ])

    def initialize_next_step(self, new_stage, klass=None, letter_template_key=None):
        applications = JobApply.objects.filter(
            job=self.job,
            status=new_stage
        )
        applications_ids = applications.values_list('id', flat=True)

        if not applications_ids:
            return

        next_stage = get_next_stage(self.job, new_stage)
        if next_stage == SELECTED:
            JobApply.objects.filter(
                id__in=applications_ids
            ).update(status=SELECTED)
            JobApplyStage.objects.bulk_create(
                [
                    JobApplyStage(job_apply_id=job_apply_id, status=SELECTED)
                    for job_apply_id in applications_ids
                ]
            )
            return

        if not klass:
            return
        letter = dict()
        if letter_template_key and self.job.hiring_info and self.job.hiring_info.get(
            letter_template_key
        ):
            letter = {
                'email_template_id': self.job.hiring_info.get(
                    letter_template_key).get('id')
            }

        new_instances = klass.objects.bulk_create([
            klass(
                job_apply_id=apply_id,
                **letter
            ) for apply_id in applications_ids
        ])
        transaction.on_commit(lambda: self.send_success_email(new_instances))

    @staticmethod
    def send_success_email(new_instances):
        for instance in new_instances:
            instance.send_mail()

    def populate_reference_checkers(self):
        applicant_references = ApplicantReference.objects.filter(
            applicant_id__in=PreScreeningInterview.objects.filter(
                job_apply__job=self.job
            ).values_list('job_apply__applicant', flat=True)
        ).values_list('id', flat=True)
        ReferenceChecker.objects.bulk_create([
            ReferenceChecker(user_id=reference) for reference in applicant_references
        ], ignore_conflicts=True)

    @property
    def job(self):
        if self._job is None and self.kwargs.get('job_slug'):
            self._job = get_object_or_404(Job, slug=self.kwargs.get('job_slug'))
        return self._job
