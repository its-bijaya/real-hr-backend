import base64
from mimetypes import guess_extension, guess_type

from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Count, Q, QuerySet, FloatField, Value, Avg
from django.db.models.functions import Coalesce, Cast
from django.utils.functional import cached_property
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response

from irhrs.core.mixins.viewset_mixins import ListRetrieveUpdateViewSetMixin
from irhrs.core.pagination import LimitZeroNoResultsPagination
from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.filters import FilterMapBackend
from irhrs.export.mixins.export import BackgroundExcelExportMixin
from irhrs.organization.models import Organization
from irhrs.permission.constants.permissions import OVERALL_RECRUITMENT_PERMISSION
from irhrs.recruitment.api.v1.permissions import RecruitmentPermission
from irhrs.recruitment.constants import COMPLETED, PROGRESS, DENIED
from irhrs.recruitment.models import PENDING, Job, NoObjection
from irhrs.recruitment.report import QuestionAnswerReport
from irhrs.recruitment.utils.util import get_no_objection_info


class FiveResultSetPagination(LimitZeroNoResultsPagination):
    default_limit = 5


class DynamicFieldViewSetMixin:
    """"
    :cvar serializer_include_fields:
        fields to include in serializer

        type -->  iterable

        set this value or override get_serializer_include_fields

    :cvar serializer_exclude_fields:
        fields to exclude in serializer

        type -->  iterable

        set this value or override get_serializer_exclude_fields

    """
    serializer_include_fields = None
    serializer_exclude_fields = None

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()

        kwargs['fields'] = self.get_serializer_include_fields()
        kwargs['exclude_fields'] = self.get_serializer_exclude_fields()
        return serializer_class(*args, **kwargs)

    def get_serializer_include_fields(self):
        return self.serializer_include_fields

    def get_serializer_exclude_fields(self):
        return self.serializer_exclude_fields


class Base64FileField(serializers.FileField):

    def to_internal_value(self, data):
        if data:
            if isinstance(data, (str, bytes)):
                # base64 encoded image - decode
                _format, data_string = data.split(';base64,')
                try:
                    ext = guess_extension(guess_type(data)[0])
                except (AttributeError, TypeError):
                    # format ~= data:image/X, <<-- Fallback mechanism
                    ext = f".{_format.split('/')[-1]}"  # guess file extension
                if not ext:
                    self.fail('invalid')
                data = ContentFile(base64.b64decode(
                    data_string), name='temp' + ext)
                return super().to_internal_value(data)
            else:
                return 'Ignore Image Update'


class RecruitmentOrganizationMixin:
    _organization = None

    def initial(self, *args, **kwargs):
        super().initial(*args, **kwargs)
        self.get_organization()

    def get_organization(self):
        if not self._organization:
            if hasattr(self, 'job') and self.job and self.job.organization:
                self._organization = self.job.organization
            else:
                slug = self.request.query_params.get('organization', None)
                if slug is not None:
                    self._organization = get_object_or_404(
                        Organization, slug=slug
                    )
        return self._organization

    @property
    def organization(self):
        return self.get_organization()


class HrAdminOrSelfQuerysetMixin(RecruitmentOrganizationMixin):
    user_field = None

    def get_queryset(self):
        qs = super().get_queryset()
        #         if not (self.is_hr_admin or self.user.is_audit_user):
        if not self.is_hr_admin:
            if self.user_field is None:
                qs = qs.none()
            else:
                qs = qs.filter(**{self.user_field: self.user})

        return qs

    @property
    def user(self):
        return self.request.user

    @cached_property
    def is_hr_admin(self):
        return self.request.user.is_authenticated and self.organization and validate_permissions(
            self.request.user.get_hrs_permissions(self.organization),
            OVERALL_RECRUITMENT_PERMISSION
        )


class RecruitmentPermissionMixin(RecruitmentOrganizationMixin):
    """
    Apply recruitment permission if user is hr admin
    """
    permission_classes = []

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        return [permission() for permission in self.get_permission_classes()]

    def get_permission_classes(self):
        if self.is_hr_admin:  # or self.is_audit_user:
            return [RecruitmentPermission]
        return self.permission_classes

    @cached_property
    def is_hr_admin(self):
        return self.request.user.is_authenticated and self.organization and validate_permissions(
            self.request.user.get_hrs_permissions(self.organization),
            OVERALL_RECRUITMENT_PERMISSION
        )

    @cached_property
    def is_audit_user(self):
        return self.request.user and self.request.user.is_authenticated and (
            self.request.user.is_audit_user)


class ExtraInfoApiMixin:
    forwarded_qs = None
    _job = None

    @action(detail=False, url_name='extra_info', url_path='extra-info')
    def get_extra_info(self, request, *args, **kwargs):
        job_obj = self.job

        stat = self.get_queryset().aggregate(
            pending=Count('id', filter=Q(status=PENDING)),
            completed=Count('id', filter=Q(status=COMPLETED)),
            progress=Count('id', filter=Q(status=PROGRESS)),
            denied=Count('id', filter=Q(status=DENIED)),
            total=Count('id')
        )

        if self.forwarded_qs is not None:
            stat['forwarded'] = self.forwarded_queryset().count()

        data = {
            'stat': stat,
            'hiring_info': job_obj.hiring_info or dict()
        }

        if hasattr(self, 'is_no_objection_initialized'):
            data['freeze_candidate'] = self.is_no_objection_initialized

        data.update(self.get_additional_info(job_obj))
        return Response(data)

    def forwarded_queryset(self):
        if hasattr(self, "get_forwarded_qs"):
            return self.get_forwarded_qs()

        if self.forwarded_qs is not None and isinstance(self.forwarded_qs, QuerySet):
            queryset = self.forwarded_qs
            queryset = queryset.filter(job_apply__job=self.job)
        else:
            queryset = self.get_queryset().none()

        return queryset

    @property
    def job(self):
        if not self._job:
            self._job = get_object_or_404(Job, slug=self.kwargs.get('job_slug'))
        return self._job

    @staticmethod
    def get_additional_info(job):
        return {}

    def filter_queryset(self, queryset):
        status = self.request.query_params.get('status')
        if status == 'Forwarded' and self.forwarded_qs is not None:
            queryset = self.forwarded_queryset()
        elif status in ['Pending', 'Progress', 'Completed']:
            queryset = queryset.filter(status=status)

        return super().filter_queryset(queryset.order_by('-score'))


class ApplicantFreezeMixin:
    """
    Only allow safe methods if no objection is completed.
    """

    no_objection_stage = None
    safe_actions = ['export']

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if not hasattr(self, 'job'):
            raise NotImplementedError('Subclass must implement job Property.')

        if self.no_objection_stage is None:
            raise NotImplementedError('Subclass must specify no objection stage.')

        not_safe_method = request.method not in SAFE_METHODS
        not_safe_action = self.action not in self.safe_actions

        if (not_safe_method and not_safe_action) and self.is_no_objection_initialized:
            self.permission_denied(request, 'Applicants are in freeze state.')

    @cached_property
    def is_no_objection_initialized(self):
        no_objection = NoObjection.objects.filter(
            job=self.job,
            stage=self.no_objection_stage
        ).order_by('-modified_at').first()

        return no_objection and no_objection.status not in [PENDING, DENIED]

    @cached_property
    def no_objection(self):
        return NoObjection.objects.filter(
            job=self.job,
            stage=self.no_objection_stage
        ).order_by('-modified_at').first()

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['freeze_candidate'] = self.is_no_objection_initialized
        return ctx


class ApplicantProcessViewSetMixin(
    BackgroundExcelExportMixin,
    ApplicantFreezeMixin,
    ExtraInfoApiMixin,
    RecruitmentOrganizationMixin,
    DynamicFieldViewSetMixin,
    ListRetrieveUpdateViewSetMixin
):
    permission_classes = [RecruitmentPermission, ]
    filter_backends = [SearchFilter, OrderingFilter, ]
    ordering_fields = ('scheduled_at', 'score')
    _job = None
    no_objection_stage = None
    reverse_question_answer = ""
    queryset = None

    export_fields = []
    safe_actions = ['export']

    def get_queryset(self):
        assert self.queryset is not None
        status = self.request.query_params.get('status')
        forwarded_qs = getattr(self, "get_forwarded_qs", self.forwarded_qs)
        if status == 'Forwarded' and forwarded_qs is not None:
            self.queryset = forwarded_qs
        return self.queryset

    def get_additional_info(self, job):
        return {
            'no_objection': get_no_objection_info(self.no_objection_stage, job)
        }

    def get_serializer_include_fields(self):
        if self.request.method.lower() in ['PUT', 'PATCH']:
            return ['scheduled_at', 'question_set', 'email_template', 'email_template_external']
        return super().get_serializer_include_fields()

    def get_export_type(self):
        status = self.request.query_params.get('status', '')
        interviewer_code = self.request.query_params.get('interviewer')
        if self.get_interviewer_filter():
            return 'Job:{} Status:{} key:{}'.format(
                str(self.job.id),
                status,
                interviewer_code
            )
        else:
            return 'Job:{} with status {}'.format(
                str(self.job.id),
                status
            )

    def raise_validation_if_interviewer_does_not_provide_score_to_all_candidate(self, obj):
        question_answers = getattr(obj, self.reverse_question_answer)
        if not question_answers:
            return

        if question_answers.filter(
            status__in=[PENDING, PROGRESS]
        ).exists():
            raise ValidationError(_('All interviewer must conduct interview.'))

    @action(
        detail=True,
        methods=['POST'],
        url_name='complete',
        url_path='complete',
        permission_classes=[RecruitmentPermission]
    )
    def mark_as_complete(self, request, *args, **kwargs):
        obj = self.get_object()
        completed_answer_qs = obj.completed_answers

        self.raise_validation_if_interviewer_does_not_provide_score_to_all_candidate(obj)

        if completed_answer_qs.exists():
            fil = {}
            if hasattr(completed_answer_qs.first(), 'conflict_of_interest'):
                # if responsible person has conflict of interest then do not add score to
                # total score
                fil['conflict_of_interest'] = False
            score = completed_answer_qs.filter(**fil).annotate(
                given_score=Coalesce(
                    Cast(
                        KeyTextTransform('percentage', 'data'), FloatField()
                    ),
                    Value(0.0)
                )).aggregate(avg_score=Avg('given_score')).get('avg_score')

            obj.score = score
            obj.status = COMPLETED
            obj.verified = True
            obj.save()
            return Response({'status': 'Completed'})
        else:
            raise ValidationError(_('Any one of the Question Answer should be completed'))

    @action(
        detail=True,
        url_name='question-answers',
        url_path='question-answers',
        permission_classes=[RecruitmentPermission]
    )
    def question_answers(self, request, *args, **kwargs):
        obj = self.get_object()
        return Response(obj.completed_question_answer_list())

    def get_interviewer_filter(self):
        fil = dict()
        interviewer = self.request.query_params.get('interviewer')
        if interviewer:
            try:
                if 'internal' in interviewer:
                    encoded_user_id = interviewer.split('internal_')[1]
                    fil['internal'] = urlsafe_base64_decode(encoded_user_id).decode()
                else:
                    encoded_user_id = interviewer.split('external_')[1]
                    fil['external'] = urlsafe_base64_decode(encoded_user_id).decode()
                return fil
            except IndexError:
                return fil
        else:
            return fil

    @action(
        detail=False,
        url_name='question-answers',
        url_path='question-answers',
        permission_classes=[RecruitmentPermission]
    )
    def question_answers_list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        return Response({
            'data': [
                obj.completed_question_answer_list(
                    **self.get_interviewer_filter()
                ) for obj in queryset
            ]
        })

    def get_extra_export_data(self):
        return {
            "fil": self.get_interviewer_filter(),
            "job_title": self.job.title.title
        }

    @classmethod
    def get_exported_file_content(cls, queryset, *args, **kwargs):
        extra_content = kwargs.get('extra_content', {})
        job_title = extra_content.get('job_title')
        scheduled_at = queryset.first().scheduled_at.date() if queryset else ""
        data = [
            obj.completed_question_answer_list(
                **extra_content.get('fil', {}), conflict=True
            ) for obj in queryset
        ]
        report = QuestionAnswerReport(
            question_answers=data,
            job_position=job_title,
            scheduled_at=scheduled_at
        )
        report.create_header()
        report.create_candidate_detail_header()
        report.fill_candidate_data()
        from openpyxl.writer.excel import save_virtual_workbook
        return ContentFile(save_virtual_workbook(report.wb))


class ApplicantProcessAnswerViewSetMixin(
    RecruitmentPermissionMixin,
    DynamicFieldViewSetMixin,
    ListRetrieveUpdateViewSetMixin
):
    permission_classes = []

    internal_user_field = ''
    external_user_field = ''

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.user

    def get_serializer_include_fields(self):
        if self.request.method.lower() == 'update':
            return [self.internal_user_field, self.external_user_field, 'data']
        return super().get_serializer_include_fields()

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_anonymous:
            return qs.filter(
                **{self.external_user_field: self.user}
            )

        if self.is_hr_admin:  # or self.is_audit_user:
            return qs

        if self.user == self.request.user:
            return qs.filter(
                **{self.internal_user_field: self.user}
            )
        return qs.none()

    @cached_property
    def user(self):
        user_lookup = self.kwargs.get('user_id')
        if user_lookup == 'me':
            if self.request.user.is_anonymous:
                self.permission_denied(self.request, 'User must be logged in User')
            return self.request.user
        else:
            if self.request.user.is_authenticated:
                if self.is_hr_admin and (self.request.method.upper() in SAFE_METHODS):
                    pass
                else:
                    self.permission_denied(
                        self.request,
                        'You are not permitted to perform this action.'
                    )
            return self.get_user_object(user_lookup)

    @staticmethod
    def get_user_object(uuid):
        NotImplementedError()
