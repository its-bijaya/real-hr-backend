import itertools
from itertools import chain
from tabnanny import verbose
from uuid import uuid4

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db.models import JSONField
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.functional import cached_property
from django.utils.http import urlsafe_base64_encode

from irhrs.common.models import TimeStampedModel, BaseModel
from irhrs.common.models.abstract import AbstractInterviewerAnswerModel
from irhrs.core.utils import nested_getattr
from irhrs.core.utils.common import modify_field_attributes, get_upload_path
from irhrs.recruitment.constants import (
    JOB_APPLY_STATUS_CHOICES,
    PROCESS_STATUS_CHOICES,
    PENDING,
    APPLIED,
    SALARY_DECLARATION_STATUS, NO_OBJECTION_STATUS, COMPLETED, REJECTED
)
from irhrs.recruitment.models.applicant import Applicant
from irhrs.recruitment.models.common import Template
from irhrs.recruitment.models.external_profile import External, ReferenceChecker
from irhrs.recruitment.models.job import Job
from irhrs.recruitment.models.question import QuestionSet
from irhrs.recruitment.utils.email import (
    send_no_objection_email, send_salary_declaration_email, send_email, send_custom_mail
)

USER = get_user_model()


class JobApply(TimeStampedModel):
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    applicant = models.OneToOneField(
        Applicant,
        on_delete=models.SET_NULL,
        null=True,
        related_name='applied_job'
    )
    internal_applicant = models.ForeignKey(
        USER,
        on_delete=models.SET_NULL,
        null=True,
        related_name='applied_jobs'
    )
    status = models.CharField(
        choices=JOB_APPLY_STATUS_CHOICES,
        max_length=50,
        db_index=True,
        default=APPLIED
    )

    # save most usable information like job title to prevent multiple table join
    # Rostered info are also saved in json field
    data = JSONField(default=dict)

    def __str__(self):
        return self.job.title.title
        # return "{} - {}".format(self.applicant, self.job)

    @property
    def current_stage(self):
        job_apply_stage = self.apply_stages.first()
        return job_apply_stage and job_apply_stage.status

    @property
    def job_title(self):
        title = self.data.get('job_title')
        if title:
            return title
        else:
            title = self.job.title.title
            self.data['job_title'] = title
            self.save()
        return title

    @property
    def candidate_name(self):
        name = self.data.get('candidate_name')
        if name:
            return name
        else:
            name = self.applicant.user.full_name
            self.data['candidate_name'] = name
            self.save()
        return name

    @property
    def recent_organization(self):
        recent_organization = self.data.get('recent_organization')
        if recent_organization:
            return recent_organization
        else:
            recent_organization = self.applicant.work_experiences.order_by(
                'id').first()
            if recent_organization:
                recent_organization = recent_organization.org_name
            else:
                recent_organization = 'N/A'
            self.data['recent_organization'] = recent_organization
            self.save()
        return recent_organization

    @property
    def recent_position(self):
        recent_position = self.data.get('recent_position')
        if recent_position:
            return recent_position
        else:
            recent_position = self.applicant.work_experiences.order_by(
                'id').first()
            if recent_position:
                recent_position = recent_position.designation
            else:
                recent_position = 'N/A'
            self.data['recent_position'] = recent_position
            self.save()
        return recent_position

    @property
    def candidate_address(self):
        address = self.data.get('candidate_address')
        if address:
            return address
        else:
            address = f'{self.applicant.address.address}, {self.applicant.address.city_name}, {str(self.applicant.address.country)}'
            self.data['candidate_address'] = address
            self.save()
        return address

    @property
    def candidate_email(self):
        email = self.data.get('candidate_email')
        if email:
            return email
        else:
            email = self.applicant.user.email
            self.data['candidate_email'] = email
            self.save()
        return email

    def send_selected_mail(self):
        if self.job.hiring_info.get('selected_letter'):
            try:
                template = Template.objects.get(
                    id=self.job.hiring_info.get('selected_letter').get('id')
                )
                subject = 'You have been selected'
                send_custom_mail(
                    subject,
                    template.message,
                    self.candidate_email,
                    candidate_name=self.candidate_name,
                    job_title=self.job_title
                )
            except (Template.DoesNotExist, ValueError):
                pass

    def send_rejected_mail(self):
        if self.job.hiring_info.get('rejected_letter'):
            try:
                template = Template.objects.get(
                    id=self.job.hiring_info.get('rejected_letter').get('id')
                )
                subject = 'You have been rejected'
                send_custom_mail(
                    subject,
                    template.message,
                    self.candidate_email,
                    candidate_name=self.candidate_name,
                    job_title=self.job_title
                )
            except (Template.DoesNotExist, ValueError):
                pass

class JobQuestionAnswer(BaseModel):
    job_apply = models.OneToOneField(
        JobApply,
        on_delete=models.CASCADE,
        related_name='answer'
    )
    # data stores all the answers to questions and other unexpected fields
    data = JSONField(blank=True)

    def __str__(self):
        return f"Answer of {self.applicant_name} for Job {self.job_title}"

    @property
    def applicant_name(self):
        return nested_getattr(self, "job_apply.applicant.user.full_name")

    @property
    def job_title(self):
        return nested_getattr(self, 'job_apply.job.title.title')


@modify_field_attributes(
    created_by={
        'related_name': "created_job_apply_stages"
    }
)
class JobApplyStage(BaseModel):
    """
    Job workflow process for each Applicant who has applied for a particular job
    """
    job_apply = models.ForeignKey(
        JobApply,
        on_delete=models.CASCADE,
        related_name='apply_stages'
    )
    status = models.CharField(
        choices=JOB_APPLY_STATUS_CHOICES,
        max_length=50,
        db_index=True,
        default=APPLIED
    )
    on_hold = models.BooleanField(default=False)
    remarks = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.status


class JobApplyStageStatus(BaseModel):
    stage = models.ForeignKey(
        JobApplyStage,
        on_delete=models.CASCADE,
        related_name='stage_status'
    )
    on_hold = models.BooleanField(default=True)
    remarks = models.CharField(max_length=255, blank=True)


class NoObjection(BaseModel):
    title = models.CharField(max_length=100)

    # For candidate specific no objection
    job_apply = models.ForeignKey(
        JobApply,
        null=True,
        on_delete=models.SET_NULL,
        related_name='no_objections'
    )

    job = models.ForeignKey(
        Job,
        null=True,
        on_delete=models.SET_NULL,
        related_name='no_objections'
    )
    stage = models.CharField(
        choices=JOB_APPLY_STATUS_CHOICES,
        max_length=50,
        db_index=True
    )
    score = models.FloatField(default=0)
    categories = ArrayField(models.CharField(
        max_length=200), blank=True, null=True)

    file = models.FileField(
        upload_to=get_upload_path,
        validators=[FileExtensionValidator(
            allowed_extensions=list(chain.from_iterable(
                settings.ACCEPTED_FILE_FORMATS.values()))
        )]
    )

    email_template = models.ForeignKey(
        Template,
        null=True,
        on_delete=models.SET_NULL,
        related_name='no_objection_email_templates'
    )

    report_template = models.ForeignKey(
        Template,
        null=True,
        on_delete=models.SET_NULL,
        related_name='no_objection_report_templates'
    )

    # template modified by hr
    modified_template = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=15,
        choices=NO_OBJECTION_STATUS,
        default=PENDING,
        db_index=True
    )
    responsible_person = models.ForeignKey(
        USER,
        related_name='no_objections',
        on_delete=models.SET_NULL,
        null=True
    )
    remarks = models.CharField(max_length=200, blank=True)
    verified = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def send_mail(self):
        return send_no_objection_email(self, make_async=True)

    @property
    def notification_link(self):
        frontend_base_url = getattr(settings, 'FRONTEND_URL')
        frontend_url = '{}/admin/{}/recruitment/application-list?job_title={}&section=no_objection'.format(
            frontend_base_url,
            self.job.organization.slug,
            self.job.slug
        )
        return frontend_url


class AbstractApplicantStepModel(BaseModel):
    status = models.CharField(
        max_length=20,
        choices=PROCESS_STATUS_CHOICES,
        default=PENDING,
        db_index=True
    )
    scheduled_at = models.DateTimeField(null=True, blank=True)

    verified = models.BooleanField(default=False)

    # data stores all the answers to questions
    data = JSONField(blank=True, null=True)
    score = models.FloatField(default=0, null=True)
    category = models.CharField(max_length=100, blank=True)

    class Meta:
        abstract = True

    @property
    def assigned_user(self):
        return ''

    @property
    def external_user(self):
        return None

    def completed_question_answer_list(self, internal=None, external=None, conflict=False):
        """
        :return: Return question answer with respective marks provided to candidate
        """
        candidate_name = ''
        if hasattr(self, 'job_apply'):
            candidate_name = self.job_apply.candidate_name
            candidate_id = self.job_apply.applicant_id

        final_data = {
            'candidate_name': candidate_name,
            'candidate_id': candidate_id,
            'question_set_name': '',
            'question_answers': list()
        }
        if hasattr(self, 'has_weightage'):
            final_data['has_weightage'] = self.has_weightage

        if hasattr(self, 'question_answer_with_filter') and callable(
            self.question_answer_with_filter
        ):
            for question_answer in self.question_answer_with_filter(
                internal=internal, external=external
            ):
                if conflict and getattr(question_answer, 'conflict_of_interest', False):
                    continue
                question_answer.data = question_answer.data or dict()

                if not final_data['question_set_name']:
                    final_data['question_set_name'] = question_answer.data.get(
                        'name', '')

                final_data['question_answers'].append(
                    self.extract_question_answer(question_answer)
                )
        else:
            if self.data:
                self.data = self.data or dict()
                if not final_data['question_set_name']:
                    final_data['question_set_name'] = self.data.get('name', '')
                final_data['question_answers'] = self.extract_question_answer(
                    self)
        return final_data

    @staticmethod
    def extract_question_answer(obj):
        data = dict()
        if obj.data:
            data['assigned_person'] = str(obj.assigned_user)

            assigned_user = 'external' if obj.external_user else 'internal'
            if hasattr(obj, 'interviewer_weightage'):
                data['interviewer_weightage'] = getattr(obj, 'interviewer_weightage', 0)
            user_encoded_pk = urlsafe_base64_encode(force_bytes(
                obj.assigned_user.pk)) if obj.assigned_user else uuid4().hex
            data['assigned_person_code'] = f"{assigned_user}_{user_encoded_pk}"

            data['total_score'] = obj.data.get('total_score', 0)

            data['given_score'] = obj.data.get('given_score', 0)

            data['percentage'] = obj.data.get('percentage', 0)
            data['remarks'] = obj.data.get('overall_remarks', '')
            has_conflict_of_interest = hasattr(obj, 'conflict_of_interest')
            if has_conflict_of_interest:
                data["conflict_of_interest"] = obj.conflict_of_interest
            question_answers = []
            for section in obj.data.get('sections', []):
                answers = []
                for question in section.get('questions'):
                    answer = {
                        'id': question.get('question').get('id'),
                        'title': question.get('question').get('title'),
                        'answer': question.get('question').get('answers'),
                        'weightage': question.get('question').get('weightage'),
                        'score': float(
                            '{:0.2f}'.format(question.get('question').get('score', 0))
                        )
                    }
                    answers.append(answer)
                question_answers.append(answers)

        else:
            question_answers = []
        data['question_answers'] = list(itertools.chain(*question_answers))
        return data


class PreScreening(AbstractApplicantStepModel):
    responsible_person = models.ForeignKey(
        USER,
        on_delete=models.SET_NULL,
        null=True,
        related_name="pre_screenings"
    )
    job_apply = models.OneToOneField(
        JobApply,
        on_delete=models.CASCADE,
        related_name="pre_screening"
    )
    question_set = models.ForeignKey(
        QuestionSet,
        on_delete=models.PROTECT,
        null=True,
        related_name="pre_screenings"
    )
    email_template = models.ForeignKey(
        Template,
        null=True,
        on_delete=models.SET_NULL,
        related_name='pre_screenings'
    )

    def send_mail(self):
        if self.job_apply.status != REJECTED:
            return send_email(self, for_candidate=True, make_async=True)
        return None

    @property
    def notification_link(self):
        return '/user/recruitment/pre-screening-list/?job_title={}'.format(
            self.job_apply.job.slug
        )

    @property
    def assigned_user(self):
        return self.responsible_person


class PostScreening(AbstractApplicantStepModel):
    responsible_person = models.ForeignKey(
        USER,
        on_delete=models.SET_NULL,
        null=True,
        related_name="post_screenings"
    )
    job_apply = models.OneToOneField(
        JobApply,
        on_delete=models.CASCADE,
        related_name="post_screening"
    )
    question_set = models.ForeignKey(
        QuestionSet,
        on_delete=models.PROTECT,
        null=True,
        related_name="post_screenings"
    )
    email_template = models.ForeignKey(
        Template,
        null=True,
        on_delete=models.SET_NULL,
        related_name='post_screenings'
    )

    def send_mail(self):
        return send_email(self, for_candidate=True, make_async=True)

    @property
    def notification_link(self):
        return '/user/recruitment/post-screening-list/?job_title={}'.format(
            self.job_apply.job.slug
        )

    @property
    def assigned_user(self):
        return self.responsible_person


class PreScreeningInterview(AbstractApplicantStepModel):
    responsible_person = models.ForeignKey(
        USER,
        on_delete=models.SET_NULL,
        null=True,
        related_name="pre_screening_interviews"
    )
    job_apply = models.OneToOneField(
        JobApply,
        on_delete=models.CASCADE,
        related_name="pre_screening_interview"
    )
    question_set = models.ForeignKey(
        QuestionSet,
        on_delete=models.PROTECT,
        null=True,
        related_name="pre_screening_interviews"
    )

    # Email Template for candidate
    email_template = models.ForeignKey(
        Template,
        null=True,
        on_delete=models.SET_NULL,
        related_name='pre_screening_interviews'
    )

    email_template_external = models.ForeignKey(
        Template,
        null=True,
        on_delete=models.SET_NULL,
        related_name='pre_screening_interviews_external'
    )
    has_weightage = models.BooleanField(default=False)

    def send_mail(self):
        return send_email(self, for_candidate=True, make_async=True)

    @property
    def notification_link(self):
        return '/user/recruitment/pre-screening-interview-list/?job_title={}'.format(
            self.job_apply.job.slug
        )

    @cached_property
    def completed_answers(self):
        return self.pre_screening_interview_question_answers.filter(status=COMPLETED)

    def question_answer_with_filter(self, internal=None, external=None):
        fil = dict()
        if internal:
            fil['internal_interviewer'] = internal
        if external:
            fil['external_interviewer'] = external
        return self.question_answers.filter(**fil)

    @cached_property
    def question_answers(self):
        return self.pre_screening_interview_question_answers.select_related(
            'internal_interviewer',
            'external_interviewer'
        )

    def __str__(self):
        return self.job_apply.job.title.title


class PreScreeningInterviewAnswer(AbstractApplicantStepModel):
    pre_screening_interview = models.ForeignKey(
        PreScreeningInterview,
        on_delete=models.CASCADE,
        related_name='pre_screening_interview_question_answers'
    )
    internal_interviewer = models.ForeignKey(
        USER,
        related_name='pre_screening_interview_question_answers',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    external_interviewer = models.ForeignKey(
        External,
        related_name='pre_screening_interview_question_answers',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    interviewer_weightage = models.PositiveIntegerField(blank=True, null=True)

    @property
    def notification_link(self):
        return '/user/recruitment/pre-screening-interview-list/?job_title={}'.format(
            self.pre_screening_interview.job_apply.job.slug
        )

    def send_notification(self, candidate_name=None):
        from irhrs.notification.utils import add_notification

        if not candidate_name:
            candidate_name = self.pre_screening_interview.job_apply.candidate_name

        if self.internal_interviewer:
            return add_notification(
                f'You have been assigned interview of candidate {candidate_name}',
                self.internal_interviewer,
                self,
                url=self.notification_link
            )

    def send_mail(self, for_candidate=False):
        if self.external_interviewer:
            return send_email(self, for_candidate=for_candidate, make_async=True)

    @property
    def parent(self):
        return self.pre_screening_interview

    @property
    def external_user(self):
        return self.external_interviewer

    @property
    def assigned_user(self):
        return self.internal_interviewer or self.external_interviewer

    @cached_property
    def frontend_link(self):
        frontend_base_url = getattr(settings, 'FRONTEND_URL')
        frontend_url = '{}/preliminary-interview/{}/{}'.format(
            frontend_base_url,
            'me' if self.internal_interviewer else nested_getattr(
                self.external_interviewer, 'user.uuid'),
            self.id
        )
        return frontend_url


class Assessment(AbstractApplicantStepModel):
    responsible_person = models.ForeignKey(
        USER,
        on_delete=models.SET_NULL,
        null=True,
        related_name="job_apply_assessments"
    )
    job_apply = models.OneToOneField(
        JobApply,
        on_delete=models.CASCADE,
        related_name="assessment"
    )
    question_set = models.ForeignKey(
        QuestionSet,
        on_delete=models.PROTECT,
        null=True,
        related_name="job_apply_assessments"
    )
    email_template = models.ForeignKey(
        Template,
        null=True,
        on_delete=models.SET_NULL,
        related_name='assessments'
    )
    email_template_external = models.ForeignKey(
        Template,
        null=True,
        on_delete=models.SET_NULL,
        related_name='assessments_external'
    )

    def send_mail(self):
        return send_email(self, for_candidate=True, make_async=True)

    @property
    def notification_link(self):
        return '/user/recruitment/assessment-list/?job_title={}'.format(
            self.job_apply.job.slug
        )

    @cached_property
    def completed_answers(self):
        return self.assessment_question_answers.filter(status=COMPLETED)

    def question_answer_with_filter(self, internal=None, external=None):
        fil = dict()
        if internal:
            fil['internal_assessment_verifier'] = internal
        if external:
            fil['external_assessment_verifier'] = external
        return self.question_answers.filter(**fil)

    @cached_property
    def question_answers(self):
        return self.assessment_question_answers.select_related(
            'internal_assessment_verifier',
            'external_assessment_verifier'
        )

    def __str__(self):
        return self.job_apply.job.title.title


class AssessmentAnswer(AbstractInterviewerAnswerModel):
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name='assessment_question_answers'
    )
    internal_assessment_verifier = models.ForeignKey(
        USER,
        related_name='assessment_question_answers',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    external_assessment_verifier = models.ForeignKey(
        External,
        related_name='assessment_question_answers',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    conflict_of_interest = models.BooleanField(default=False)

    @property
    def notification_link(self):
        return '/user/recruitment/assessment-list/?job_title={}'.format(
            self.assessment.job_apply.job.slug
        )

    def send_notification(self, candidate_name=None):
        from irhrs.notification.utils import add_notification

        if not candidate_name:
            candidate_name = self.assessment.job_apply.candidate_name

        if self.internal_assessment_verifier:
            return add_notification(
                f'You have been assigned assessment of candidate {candidate_name}',
                self.internal_assessment_verifier,
                self,
                url=self.notification_link
            )

    def send_mail(self):
        if self.external_assessment_verifier:
            return send_email(self, make_async=True)

    @property
    def parent(self):
        return self.assessment

    @property
    def external_user(self):
        return self.external_assessment_verifier

    @property
    def assigned_user(self):
        return self.internal_assessment_verifier or self.external_assessment_verifier

    @cached_property
    def frontend_link(self):
        frontend_base_url = getattr(settings, 'FRONTEND_URL')
        frontend_url = '{}/assessment/{}/{}'.format(
            frontend_base_url,
            'me' if self.internal_assessment_verifier else nested_getattr(
                self.external_assessment_verifier, 'user.uuid'),
            self.id
        )
        return frontend_url


class Interview(AbstractApplicantStepModel):
    job_apply = models.OneToOneField(
        JobApply,
        on_delete=models.CASCADE,
        related_name='interview'
    )
    question_set = models.ForeignKey(
        QuestionSet,
        on_delete=models.PROTECT,
        null=True,
        related_name='interview_questions'
    )
    email_template = models.ForeignKey(
        Template,
        null=True,
        on_delete=models.SET_NULL,
        related_name='interviews'
    )
    email_template_external = models.ForeignKey(
        Template,
        null=True,
        on_delete=models.SET_NULL,
        related_name='interviews_external'
    )

    def send_mail(self):
        if self.email_template:
            return send_email(self, for_candidate=True, make_async=True)

    @cached_property
    def completed_answers(self):
        return self.interview_question_answers.filter(status=COMPLETED)

    @cached_property
    def question_answers(self):
        return self.interview_question_answers.select_related(
            'internal_interviewer',
            'external_interviewer'
        )

    def question_answer_with_filter(self, internal=None, external=None):
        fil = dict()
        if internal:
            fil['internal_interviewer'] = internal
        if external:
            fil['internal_interviewer'] = external
        return self.question_answers.filter(**fil)


class InterViewAnswer(AbstractInterviewerAnswerModel):
    interview = models.ForeignKey(
        Interview,
        on_delete=models.CASCADE,
        related_name='interview_question_answers'
    )
    internal_interviewer = models.ForeignKey(
        USER,
        related_name='interview_question_answers',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    external_interviewer = models.ForeignKey(
        External,
        related_name='interview_question_answers',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    conflict_of_interest = models.BooleanField(default=False)

    @property
    def parent(self):
        return self.interview

    def send_mail(self):
        if self.external_interviewer:
            return send_email(self, make_async=True)

    def send_notification(self, candidate_name=None):
        from irhrs.notification.utils import add_notification

        if not candidate_name:
            candidate_name = self.interview.job_apply.candidate_name

        if self.internal_interviewer:
            return add_notification(
                f'You have been assigned interview of candidate {candidate_name}',
                self.internal_interviewer,
                self,
                url=self.notification_link
            )

    def __str__(self):
        return f'{str(self.interviewer)} Question Answers'

    @property
    def interviewer(self):
        return self.internal_interviewer or self.external_interviewer

    @property
    def link(self):
        link = reverse(
            'api_v1:recruitment:interview:interview_answer-detail',
            kwargs={
                'interviewer_id': 'me' if self.internal_interviewer else nested_getattr(
                    self.external_interviewer, 'user.uuid'
                ),
                'pk': self.id
            }
        )
        return link.split('api/v1')[1]

    @cached_property
    def frontend_link(self):
        frontend_base_url = getattr(settings, 'FRONTEND_URL')
        frontend_url = '{}/interview/{}/{}'.format(
            frontend_base_url,
            'me' if self.internal_interviewer else nested_getattr(
                self.external_interviewer, 'user.uuid'),
            self.id
        )
        return frontend_url

    @property
    def notification_link(self):
        return '/user/recruitment/interview-list/?job_title={}'.format(
            self.interview.job_apply.job.slug
        )

    @property
    def external_user(self):
        return self.external_interviewer

    @property
    def assigned_user(self):
        return self.internal_interviewer or self.external_interviewer

    class Meta:
        # Naming the model as per the user need
        verbose_name_plural = "Interview answers"


class ReferenceCheck(AbstractApplicantStepModel):
    job_apply = models.OneToOneField(
        JobApply,
        on_delete=models.CASCADE,
        related_name='reference_check'
    )
    question_set = models.ForeignKey(
        QuestionSet,
        on_delete=models.PROTECT,
        null=True,
        related_name='reference_checks'
    )
    email_template = models.ForeignKey(
        Template,
        null=True,
        on_delete=models.SET_NULL,
        related_name='reference_checks'
    )
    email_template_external = models.ForeignKey(
        Template,
        null=True,
        on_delete=models.SET_NULL,
        related_name='reference_check_external'
    )

    def question_answer_with_filter(self, internal=None, external=None):
        fil = dict()
        if internal:
            fil['internal_reference_checker'] = internal
        if external:
            fil['external_reference_checker'] = external
        return self.question_answers.filter(**fil)

    @cached_property
    def question_answers(self):
        return self.reference_check_question_answers.select_related(
            'internal_reference_checker',
            'external_reference_checker'
        )

    def send_mail(self):
        return send_email(self, for_candidate=True, make_async=True)

    @cached_property
    def completed_answers(self):
        return self.reference_check_question_answers.filter(status=COMPLETED)


class ReferenceCheckAnswer(AbstractInterviewerAnswerModel):
    reference_check = models.ForeignKey(
        ReferenceCheck,
        on_delete=models.CASCADE,
        related_name='reference_check_question_answers'
    )
    internal_reference_checker = models.ForeignKey(
        USER,
        related_name='reference_check_question_answers',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    external_reference_checker = models.ForeignKey(
        ReferenceChecker,
        related_name='reference_check_question_answers',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def send_mail(self):
        if self.external_reference_checker:
            return send_email(self, make_async=True)

    def send_notification(self, candidate_name=None):
        from irhrs.notification.utils import add_notification

        if not candidate_name:
            candidate_name = self.reference_check.job_apply.candidate_name

        if self.internal_reference_checker:
            return add_notification(
                f'You have been assigned for reference check of candidate {candidate_name}',
                self.internal_reference_checker,
                self,
                url=self.notification_link
            )

    @property
    def frontend_link(self):
        frontend_base_url = getattr(settings, 'FRONTEND_URL')
        frontend_url = '{}/reference-check/{}/{}/'.format(
            frontend_base_url,
            'me' if self.internal_reference_checker else nested_getattr(
                self.external_reference_checker, 'uuid'
            ),
            self.id
        )
        return frontend_url

    @property
    def notification_link(self):
        return '/user/recruitment/reference-check-list/?job_title={}'.format(
            self.reference_check.job_apply.job.slug
        )

    @property
    def job_apply(self):
        return self.reference_check.job_apply

    @property
    def parent(self):
        return self.reference_check

    @property
    def external_user(self):
        return self.external_reference_checker

    @property
    def assigned_user(self):
        return self.internal_reference_checker or self.external_reference_checker


class SalaryDeclaration(BaseModel):
    job_apply = models.ForeignKey(
        JobApply,
        on_delete=models.CASCADE,
        related_name='salary_declarations'
    )
    email_template = models.ForeignKey(
        Template,
        null=True,
        on_delete=models.SET_NULL,
        related_name='salary_declarations'
    )
    salary = models.FloatField(default=0)

    score = models.FloatField(default=0)
    categories = ArrayField(
        models.CharField(max_length=200), blank=True, null=True)

    status = models.CharField(
        max_length=15,
        choices=SALARY_DECLARATION_STATUS,
        default=PENDING,
        db_index=True
    )
    verified = models.BooleanField(default=False)
    candidate_remarks = models.CharField(max_length=200, blank=True)

    def send_mail(self):
        return send_salary_declaration_email(self, make_async=True)

    @property
    def frontend_link(self):
        frontend_base_url = getattr(settings, 'FRONTEND_URL')
        frontend_url = '{}/salary-declaration/{}/{}/'.format(
            frontend_base_url,
            nested_getattr(
                self.job_apply, 'applicant.user.uuid'
            ),
            self.id
        )
        return frontend_url
