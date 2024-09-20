from django.db.models import Count, Q, Prefetch, Case, When, Value, F, CharField
from django.utils import timezone
from django.utils.functional import cached_property
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from irhrs.core.constants.common import SKILL
from irhrs.core.mixins.viewset_mixins import (
    HRSReadOnlyModelViewSet,
    DestroyViewSetMixin,
    ListCreateRetrieveUpdateViewSetMixin,
)
from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.permission.constants.permissions import OVERALL_RECRUITMENT_PERMISSION
from irhrs.recruitment.api.v1.filterset_classes import JobFilter, JobViewSetFilter
from irhrs.recruitment.api.v1.mixins import (
    DynamicFieldViewSetMixin,
    RecruitmentPermissionMixin,
    FiveResultSetPagination,
)
from irhrs.recruitment.api.v1.permissions import RecruitmentPermission
from irhrs.recruitment.api.v1.serializers.job import (
    JobBasicInformationSerializer,
    JobSpecificationSerializer,
    JobAdditionalInfoSerializer,
    JobPublicSerializer,
    JobSerializer,
    JobQuestionSerializer,
    JobHiringInformationSerializer,
    JobAttachmentSerializer,
)
from irhrs.recruitment.constants import PUBLISHED, DRAFT, PENDING, DENIED
from irhrs.recruitment.models import (
    Job,
    JobQuestion,
    KnowledgeSkillAbility,
    JobAttachment,
    Organization,
)


class AdminAndOrganizationMixin:
    @property
    def organization(self):
        slug = self.request.query_params.get("organization", None)
        if slug:
            return Organization.objects.filter(slug=slug).first()
        return None

    @cached_property
    def is_hr_admin(self):
        return validate_permissions(
            self.request.user.get_hrs_permissions(self.organization),
            OVERALL_RECRUITMENT_PERMISSION,
        )


class JobViewSet(
    RecruitmentPermissionMixin,
    DynamicFieldViewSetMixin,
    ListCreateRetrieveUpdateViewSetMixin,
):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    lookup_field = "slug"
    permission_classes = [IsAuthenticated]

    filter_backends = (
        SearchFilter,
        DjangoFilterBackend,
        FilterMapBackend,
        OrderingFilterMap,
    )

    ordering_fields_map = {
        "created_at": "created_at",
        "modified_at": "modified_at",
        "posted_at": "posted_at",
        "job_title": "title__title",
        "deadline": "deadline",
        "application_count": "application_count",
        "status": "status",
    }

    search_fields = [
        "title__title",
    ]
    filterset_class = JobViewSetFilter

    filter_map = {
        "deadline_gte": "deadline__gte",
        "deadline_lte": "deadline__lte",
    }
    serializer_include_fields = [
        "job_title",
        "posted_at",
        "deadline",
        "application_count",
        "status",
        "title",
        "created_at",
        "slug",
        "current_status",
    ]

    def get_serializer_include_fields(self):
        limit_field = self.request.query_params.get("limit_field")
        if limit_field:
            return ["job_title", "slug"]
        if self.action.lower() == "list":
            return self.serializer_include_fields
        return None

    def get_queryset(self):
        qs = super().get_queryset().select_related(
            "employment_status",
            "employment_level",
            "title"
        ).prefetch_related(
            "applications",
            Prefetch(
                "attachments",
                queryset=JobAttachment.objects.filter(is_archived=False),
            ),
        )

        if self.is_hr_admin:  # or self.is_audit_user:
            pass
        elif self.is_supervisor:
            qs = qs.filter(created_by=self.request.user)
        else:
            qs = qs.none()

        return qs.filter(organization=self.organization).annotate(
            current_status=Case(
                When(deadline__lte=timezone.now(), then=Value("Expired")),
                default=F("status"),
                output_field=CharField(),
            ),
            application_count=Count("applications"),
        )

    def check_permissions(self, request):
        # disallow create and update actions directly
        # however these methods are called from actions
        # added below
        if self.action in ["create", "update", "partial_update"]:
            raise self.permission_denied(request)
        return super().check_permissions(request)

    def create(self, request, *args, **kwargs):
        self.check_permission_for_create()
        return super().create(request, *args, **kwargs)

    def check_permission_for_create(self):
        if not (self.is_hr_admin or self.is_supervisor):
            raise PermissionDenied

    def update(self, request, *args, **kwargs):
        if self.is_hr_admin:
            return super().update(request, *args, **kwargs)
        if not self.get_object().applications.exists():
            return super().update(request, *args, **kwargs)
        return Response(
            {
                "non_field_errors": [
                    "This job has already been applied by some candidates."
                ]
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(methods=["GET"], detail=False)
    def stats(self, request, *args, **kwargs):

        counts = (
            self.get_queryset()
            .order_by()
            .values("status")
            .aggregate(
                total=Count("id", distinct=True),
                active=Count(
                    "id",
                    filter=Q(deadline__gte=timezone.now(), status=PUBLISHED),
                    distinct=True,
                ),
                draft=Count("id", filter=Q(status=DRAFT), distinct=True),
                expired=Count(
                    "id",
                    filter=Q(deadline__lt=timezone.now(), status=PUBLISHED),
                    distinct=True,
                ),
                pending=Count("id", filter=Q(status=PENDING), distinct=True),
                denied=Count("id", filter=Q(status=DENIED), distinct=True),
            )
        )
        return Response(counts)

    @action(
        methods=["POST"],
        detail=False,
        url_path="basic-info",
        url_name="basic-info-create",
        serializer_class=JobBasicInformationSerializer,
    )
    def basic_info(self, request, *args, **kwargs):

        return self.create(request, *args, **kwargs)

    @action(
        methods=["PUT"],
        detail=True,
        url_path="basic-info",
        url_name="basic-info-update",
        serializer_class=JobBasicInformationSerializer,
    )
    def basic_info_update(self, request, *args, **kwargs):
        if self.is_hr_admin or not self.get_object().status == PUBLISHED:
            return self.update(request, *args, **kwargs)
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    @property
    def is_supervisor(self):
        mode = self.request.query_params.get("as")
        if mode == "supervisor" and not self.request.user.subordinates_pks:
            return self.permission_denied(
                self.request, "You do not have permission to perform this action."
            )
        return mode == "supervisor"

    @cached_property
    def is_hr_admin(self):
        mode = self.request.query_params.get("as")
        if mode == "hr" and not (
            self.request.user.is_authenticated
            and validate_permissions(
                self.request.user.get_hrs_permissions(self.organization),
                OVERALL_RECRUITMENT_PERMISSION,
            )
        ):
            return self.permission_denied(
                self.request, "You do not have permission to perform this action."
            )
        return mode == "hr"

    @action(
        methods=["PATCH"],
        detail=True,
        serializer_include_fields=["id", "status"],
        url_path="status-change",
        url_name="status-change",
    )
    def status_change(self, request, *args, **kwargs):
        supervisor_allowed = request.data.get("status") in [PENDING, DRAFT]
        job = self.get_object()

        if self.is_hr_admin:
            if request.data.get("status") == PUBLISHED and not job.hiring_info:
                raise ValidationError(
                    {
                        "status": [
                            """Hiring information has not been populated.
                         Please update hiring information before publishing this job"""
                        ]
                    }
                )

            if job.current_status == "Expired":
                job.status = PUBLISHED
                job.save()
                raise ValidationError(
                    {
                        "expiry_message": [
                            f"Job with title '{job.title.title}' has been expired."
                        ]
                    }
                )

            return self.partial_update(request, *args, **kwargs)

        if bool(self.request.user.subordinates_pks) and not supervisor_allowed:
            self.permission_denied(
                request, message="You can only change status to `Pending` and `Draft`."
            )

        return self.partial_update(request, *args, **kwargs)

    @action(
        methods=["PUT"],
        detail=True,
        url_path="specification",
        url_name="specification",
        serializer_class=JobSpecificationSerializer,
    )
    def specification(self, request, *args, **kwargs):
        if self.is_hr_admin or not self.get_object().status == PUBLISHED:
            return self.update(request, *args, **kwargs)
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(
        methods=["PUT"],
        detail=True,
        url_path="additional-info",
        url_name="additional-info",
        serializer_class=JobAdditionalInfoSerializer,
    )
    def additional_info(self, request, *args, **kwargs):
        return self.update(request, args, kwargs)

    @action(
        methods=["PUT"],
        detail=True,
        url_path="hiring-info",
        url_name="hiring-info",
        serializer_class=JobHiringInformationSerializer,
    )
    def hiring_info(self, request, *args, **kwargs):
        return self.update(request, args, kwargs)


class JobSearchAPIView(
    DynamicFieldViewSetMixin, AdminAndOrganizationMixin, HRSReadOnlyModelViewSet
):
    queryset = Job.get_qs()
    serializer_class = JobPublicSerializer
    permission_classes = []  # all public so no need to implement permission
    lookup_field = "slug"
    pagination_class = FiveResultSetPagination

    filter_backends = (SearchFilter, DjangoFilterBackend)
    # TODO: @Shital remove comment if needed
    # serializer_include_fields = [
    #     'slug', 'offered_salary', 'location', 'title', 'organization',
    #     'job_title', 'vacancies', 'deadline', 'description',
    # ]

    filterset_class = JobFilter

    search_fields = ["title__title", "title__slug"]

    def get_serializer_include_fields(self):
        fields = super().get_serializer_include_fields()
        if self.action == "retrieve":
            return None  # Show all fields in retrieve
        return fields

    def get_queryset(self):
        fil = dict()
        organization = self.request.query_params.get("organization")
        if organization:
            fil.update({"organization__slug": organization})
        if not self.request.user.is_authenticated:
            # if user is not authenticated, do not show internal vacancy
            fil.update({"is_internal": False})

        if self.action != "list":
            # all published including expired in detail
            qs = Job.objects.filter(status=PUBLISHED)
        else:
            # active jobs in list api
            qs = Job.get_qs()

        # in case of retrieve filter using authenticated user
        if self.request.user.is_authenticated and self.action.lower() == "retrieve":
            if self.organization:
                if self.is_hr_admin:
                    qs = Job.objects.all()
                # else:
                #     qs = Job.objects.filter(created_by=self.request.user)
            else:
                qs = Job.get_qs()

            fil = dict()

        return (
            qs.filter(**fil)
            .select_related(
                "offered_salary",
                "title",
                "organization",
                "branch",
                "division",
                "employment_level",
                "employment_status",
            )
            .prefetch_related(
                "document_categories",
                Prefetch(
                    "skills",
                    queryset=KnowledgeSkillAbility.objects.filter(ksa_type=SKILL),
                ),
                Prefetch(
                    "attachments",
                    queryset=JobAttachment.objects.filter(is_archived=False),
                ),
            )
            .order_by("-modified_at")
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["is_hr_admin"] = self.request.user.is_authenticated and self.is_hr_admin
        ctx["hide_answer"] = True
        return ctx

    def list(self, request, *args, **kwargs):
        """ Overriding list method to hide `vacancies` if `show_vacancy_number` is False """
        response = super().list(request, *args, **kwargs)
        jobs = response.data['results']
        for job in jobs:
            if not job.get('show_vacancy_number'):
                job.pop('vacancies')

        return response

class JobQuestionViewSet(AdminAndOrganizationMixin, HRSReadOnlyModelViewSet):
    queryset = JobQuestion.objects.all()
    serializer_class = JobQuestionSerializer
    permission_classes = []
    lookup_url_kwarg = "slug"
    lookup_field = "job__slug"

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        as_hr = self.request.query_params.get("as") == "hr"
        if not (self.request.user.is_authenticated and as_hr and self.is_hr_admin):
            ctx["hide_answer"] = True
        return ctx


class JobAttachmentViewSet(RecruitmentPermissionMixin, DestroyViewSetMixin):
    queryset = JobAttachment.objects.filter(is_archived=False)
    serializer_class = JobAttachmentSerializer
    permission_classes = [RecruitmentPermission]

    def get_queryset(self):
        qs = super().get_queryset()

        if self.is_hr_admin:  # or self.is_audit_user:
            return qs
        if self.is_supervisor:
            return qs.filter(job__created_by=self.request.user)

        return qs.none()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_archived = True
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @property
    def is_supervisor(self):
        return bool(self.request.user.subordinates_pks)
