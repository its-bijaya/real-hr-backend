import types
from functools import reduce

from django.core.exceptions import FieldError
from django.db.models import Count, Prefetch, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, filters
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet, ViewSet

from irhrs.common.api.permission import CommonBankPermission, CommonReligionEthnicityPermission
from irhrs.common.api.permission import (
    CommonWritePermissionMixin,
    CommonHolidayCategoryPermission,
    CommonDocumentCategoryPermission,
    CommonEquipmentCategoryPermission)
from irhrs.common.models.commons import Bank, EquipmentCategory
from irhrs.core.constants.common import (
    NATIONALITY_CHOICES, EMPLOYEE, ORGANIZATION, BOTH,
    ORGANIZATION_ASSET_CHOICES)
from irhrs.core.constants.payroll import PENDING
from irhrs.core.mixins.file_import_mixin import BackgroundFileImportMixin
from irhrs.core.mixins.serializers import create_read_only_dummy_serializer, \
    add_fields_to_serializer_class
from irhrs.core.mixins.viewset_mixins import ListCreateRetrieveViewSetMixin, ListViewSetMixin, \
    ValidateUsedData
from irhrs.core.utils.dependency import get_dependency
from irhrs.core.utils.filters import OrderingFilterMap, FilterMapBackend
from irhrs.organization.api.v1.serializers.knowledge_skill_ability import \
    KnowledgeSkillAbilityThinSerializer
from irhrs.organization.models import Organization
from irhrs.organization.models.knowledge_skill_ability import KnowledgeSkillAbility
from irhrs.recruitment.api.v1.serializers.interview import InterViewAnswerSerializer, \
    ReferenceCheckAnswerSerializer
from irhrs.recruitment.api.v1.serializers.screening_assessment import (
    PreScreeningSerializer, PostScreeningSerializer,
    AssessmentAnswerSerializer,
    PreScreeningInterviewAnswerSerializer
)
from irhrs.recruitment.constants import COMPLETED, PROGRESS, OTHER
from irhrs.recruitment.models import (
    ReferenceCheckAnswer, InterViewAnswer,
    PreScreening, PostScreening,
    QuestionSet, PreScreeningInterviewAnswer, AssessmentAnswer,
    Job
)
from irhrs.forms.constants import (
    PENDING as FORM_PENDING,
    DRAFT as FORM_DRAFT,
)
from irhrs.forms.api.v1.views.answer import UserFormAnswerSheetFilter
from irhrs.forms.utils.stats import get_form_approval_stats
from irhrs.forms.utils.approval import get_answer_sheets_with_annotation
from irhrs.reimbursement.constants import TRAVEL
from irhrs.users.api.v1.serializers.thin_serializers import OrganizationThinSerializer
from irhrs.forms.api.v1.serializers.answer import (
    ListUserFormAnswerSheetSerializer
)
from ...api.serializers.common import (
    DocumentCategorySerializer,
    ReligionEthnicitySerializer, IndustrySerializer,
    DisabilitySerializer, HolidayCategorySerializer,
    BankSerializer, EquipmentCategorySerializer)
from ...models import (
    DocumentCategory, ReligionAndEthnicity, Industry,
    HolidayCategory, Disability)

get_advance_salary, __ = get_dependency('irhrs.payroll.utils.helpers.get_advance_salary')
get_advance_salary_stats, __ = get_dependency(
    'irhrs.payroll.utils.helpers.get_advance_salary_stats')

get_reimbursement, __ = get_dependency('irhrs.reimbursement.utils.helper.get_reimbursement')
get_reimbursement_stats, __ = get_dependency(
    'irhrs.reimbursement.utils.helper.get_reimbursement_stats')

get_exit_interview_stats, __ = get_dependency('irhrs.hris.utils.helper.get_exit_interview_stats')
get_exit_interview, __ = get_dependency('irhrs.hris.utils.helper.get_exit_interview')

get_resignation_stats, __ = get_dependency('irhrs.hris.utils.helper.get_resignation_stats')
get_resignation, __ = get_dependency('irhrs.hris.utils.helper.get_resignation')

get_leave_request_stats, __ = get_dependency('irhrs.leave.utils.helper.get_leave_request_stats')
get_leave_request, __ = get_dependency('irhrs.leave.utils.helper.get_leave_request')


class DocumentCategoryView(ModelViewSet):
    """
    list:
    Lists all the Document Category, applicable for any document

        {
            "name": "Personal",
            "slug": "personal",
            "associated_with": "Organization"/"Employee"/"Both"
        },
        {
            "name": "Bachelor Transcript",
            "slug": "bachelor-transcript",
            "associated_with": "Organization"/"Employee"/"Both"
        }

    filters -->
        for=Organization or for=Employee

    create:
    Create a new Document Category, applicable for any document.

        {
            "name": "ISO Certification",
            "associated_with": "Organization"/"Employee"/"Both"
        }

    """
    queryset = DocumentCategory.objects.all()
    serializer_class = DocumentCategorySerializer
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('name', 'modified_at', 'created_at', 'associated_with')
    permission_classes = [CommonDocumentCategoryPermission]

    def filter_queryset(self, queryset):
        associated_with = self.request.query_params.get("for", None)
        if associated_with:
            if associated_with.title() not in [EMPLOYEE, ORGANIZATION]:
                return queryset.none()
            return queryset.filter(associated_with__in=[BOTH, associated_with.title()])

        return super().filter_queryset(queryset)

    def perform_destroy(self, instance):
        if instance.has_associated_documents:
            raise ValidationError(
                {"non_field_errors": ["Could not delete type. It has associated documents."]})
        return super().perform_destroy(instance)


class ReligionEthnicityView(ValidateUsedData, ModelViewSet):
    """
    list:
    Lists all the Religion and Ethnicity.

    ```javascript
        {
            "name": "Brahmin/Bahun",
            "category": "Ethnicity", // Choices are ("Religion", "Ethnicity", )
            "slug": "brahminbahun"
        },,
    ```
    In case of requiring only religion or ethnicity/ religion.
    Pass the query as Religion or Ethnicity under category params.
    ```javascript
    ?category=Religion
    {
        "name": "Hinduism"
    }
    ```
    ```javascript
    ?category=Ethnicity
    {
        "name": "Raute"
    }
    ```
    create:
    Create new Religion/Ethnicity.
    ```javascript
    {
        "name": "Atheist",
        "category": "Religion" // Choices are ("Religion", "Ethnicity", )
    }
    ```

    retrieve:
    Get the detail for a religion or ethnicity.

    ```javascript
    {
        "name": "Atheist",
        "category": "Religion", // Choices are ("Religion", "Ethnicity", )
        "slug": "atheist"
    }
    ```


    delete:
    Deletes the selected religion/ethnicity.

    update:
    Updates the selected religion/ ethnicity details for the given organization.

    ```javascript
    {
        "name": "Raute",
        "category": "Ethnicity" // Choices are ("Religion", "Ethnicity", )
    }
    ```

    partial_update:
    Update only selected fields of a religion/ethnicity.

    Accepts the same parameters as ```.update()```.
    However, not all fields are required.

    """
    serializer_class = ReligionEthnicitySerializer
    queryset = ReligionAndEthnicity.objects.all().order_by('modified_at')
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter, filters.OrderingFilter,
                       DjangoFilterBackend,)
    filter_fields = 'category',
    search_fields = ('name', 'category')
    ordering_fields = ('name', 'modified_at',)
    permission_classes = [CommonReligionEthnicityPermission]
    related_names = ['religion_userdetails', 'ethnicity_userdetails', 'holiday_ethnicity',
                     'holiday_religion']

    def get_serializer(self, *args, **kwargs):
        category = self.request.query_params.get('category')
        if category and self.request.method == 'GET':
            kwargs.update({'fields': ('created_at', 'modified_at', 'name', 'slug',)})
        return super().get_serializer(*args, **kwargs)


class IndustryListView(CommonWritePermissionMixin, mixins.ListModelMixin, GenericViewSet):
    """
    list:

    Lists all the available choices of Industry.
    ```
    {
      "count": 27,
      "next": "http://localhost:8000/api/v1/commons/industry/?limit=10",
      "previous": null,
      "results": [
            {
              "name": "Airlines / GSA",
              "slug": "airlines-gsa"
            },
            {
              "name": "Architecture / Interior Design Firm",
              "slug": "architecture-interior-design-firm"
            }
        ]
    ```
    """
    queryset = Industry.objects.all().order_by('name')
    serializer_class = IndustrySerializer
    search_fields = ('name',)
    filter_backends = (filters.SearchFilter,)


class HolidayCategoryView(ValidateUsedData, ModelViewSet):
    """
    list:
    Retrieve the list of Holiday Categories.
    ```
    {
       "name": "Festival",
       "description": "According to Religion and Ethnicity",
       "slug": "festival"
    }
    ```
    ## Ordering & Filtering
    ### Ordering
    Can be ordered with name in ascending and descending order.

    ### Filtering
    Can be filtered with ?search=<holiday_category_name>

    create:
    Create a new Holiday Category name.
    ```
    {
        "name": "Festival",
        "description": "According to Religion and Ethnicity"
    }
    ```
    update:
    Edit the holiday category name.
    ```
    {
        "name": "Festival",
        "description": "According to Religion and Ethnicity"
    }```

    partial_update:
    Partially edit the holiday category name. Accepts the same parameters as
    `.put()` method.

    delete:
    Deletes the selected holiday category slug.

    retrieve:
    Get the details of a selected holiday category.
    ```
    {
        "name": "Festival",
        "description": "According to Religion and Ethnicity",
        "slug": "festival"
    }
    ```
    """
    queryset = HolidayCategory.objects.all()
    serializer_class = HolidayCategorySerializer
    lookup_field = 'slug'
    search_fields = ('name',)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter,)
    ordering_fields = ('name', 'created_at', 'modified_at',)
    permission_classes = [CommonHolidayCategoryPermission]
    related_names = ['holiday_set']
    related_methods = ['delete']


class DisabilityViewSet(CommonWritePermissionMixin, ListCreateRetrieveViewSetMixin):
    """
    list:

    list disabilities

    search `?search=search_string`

    create:

    create disability

    data =

        {
            "title": "title of disability",
            "description": "description"
        }
    """
    queryset = Disability.objects.all()
    serializer_class = DisabilitySerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('title', 'slug')
    lookup_field = 'slug'
    lookup_url_kwarg = 'slug'


class ConstantViewSet(CommonWritePermissionMixin, ViewSet):
    """
    list:

    List of constants values and display. It accepts query_param 'field' which
    can be set to get values of required constant.

    eg. constants/?field=nationality

    available fields are

        [nationality,]

    """

    def list(self, request):
        response = {}
        fields = request.query_params.getlist('field')
        for field in fields:
            fn = getattr(self, f"get_{field}", None)
            if fn:
                response.update({field: fn()})
        return Response(response)

    @staticmethod
    def get_nationality():
        return [{'display': display, 'value': value}
                for display, value in NATIONALITY_CHOICES]


class BankViewSet(ModelViewSet, ValidateUsedData):
    queryset = Bank.objects.all()
    serializer_class = BankSerializer
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter, filters.OrderingFilter,)
    search_fields = ('name', 'address',)
    ordering_fields = ('name', 'address', 'created_at', 'modified_at')
    permission_classes = [CommonBankPermission]
    related_names = ['user_banks', 'organization_banks']
    related_methods = ['delete']


class EquipmentCategoryViewSet(BackgroundFileImportMixin, ModelViewSet):
    queryset = EquipmentCategory.objects.all()
    serializer_class = EquipmentCategorySerializer
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter, filters.OrderingFilter,)
    search_fields = ('name', 'slug')
    ordering_fields = ('name', 'type', 'created_at', 'modified_at')
    permission_classes = [CommonEquipmentCategoryPermission]
    import_fields = [
        'NAME',
        'TYPE'
    ]
    sample_file_name = 'equipment_category'
    background_task_name = 'equipment_category'
    failed_url = '/common/settings/equipment-category/?status=failed'
    success_url = '/common/settings/equipment-category/?status=success'

    def get_queryset_fields_map(self):
        return {
            'type': list(dict(ORGANIZATION_ASSET_CHOICES).keys())
        }


class OpenKnowledgeSkillAbilityViewSet(
    mixins.ListModelMixin, GenericViewSet
):
    serializer_class = KnowledgeSkillAbilityThinSerializer
    permission_classes = []
    authentication_classes = []
    queryset = KnowledgeSkillAbility.objects.all()

    @property
    def organization(self):
        slug = self.request.query_params.get('organization')
        return Organization.objects.filter(slug=slug).first()

    def get_queryset(self):
        organization = self.organization
        queryset = super().get_queryset().filter(
            ksa_type=self.kwargs.get('ksa_type')
        )
        if organization:
            queryset = queryset.filter(organization=organization)
        return queryset


class FrontendLinkListViewSet(ListViewSetMixin):
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['status']

    # ordering_fields_map = {
    #     'name': 'separation__user__first_name'
    # }

    def list(self, request, *args, **kwargs):
        _type = self.kwargs.get('type').replace('-', '_')
        get_data = getattr(self, f'get_{_type}')
        return get_data()

    def applicant_process_queryset(self, klass):
        queryset = klass.objects.select_related(
            'responsible_person', 'question_set', 'job_apply__applicant__user',
            'job_apply__job'
        ).prefetch_related(
            Prefetch(
                'question_set',
                queryset=QuestionSet.objects.prefetch_related('questions')
            )
        ).filter(
            responsible_person=self.request.user
        )
        return self.filter_queryset_by_job_slug(queryset)

    def pre_screening_queryset(self):
        return self.applicant_process_queryset(PreScreening)

    def post_screening_queryset(self):
        return self.applicant_process_queryset(PostScreening)

    def pre_screening_interview_queryset(self):
        return self.filter_queryset_by_job_slug(
            PreScreeningInterviewAnswer.objects.filter(internal_interviewer=self.request.user))

    def assessment_queryset(self):
        return self.filter_queryset_by_job_slug(
            AssessmentAnswer.objects.filter(internal_assessment_verifier=self.request.user))

    def reference_check_queryset(self):
        return self.filter_queryset_by_job_slug(ReferenceCheckAnswer.objects.filter(
            internal_reference_checker=self.request.user))

    def form_approval_queryset(self):
        user = self.request.user
        qs = get_answer_sheets_with_annotation(
            user,
            filters={"is_draft": False}
        ).filter(
            is_current_user_low_level_approver=True,
        )
        return qs

    def interview_queryset(self):
        return self.filter_queryset_by_job_slug(InterViewAnswer.objects.filter(
            internal_interviewer=self.request.user))

    def filter_queryset_by_job_slug(self, queryset):
        supported_query_params = [
            'job_apply__job__slug',
            'interview__job_apply__job__slug',
            'pre_screening_interview__job_apply__job__slug',
            'assessment__job_apply__job__slug',
            'reference_check__job_apply__job__slug',
        ]
        valid_params = set(self.request.query_params.keys()).intersection(
            set(supported_query_params))
        queryset = queryset
        if valid_params:
            for field in valid_params:
                if self.request.query_params.get(field):
                    try:
                        queryset = queryset.filter(**{field: self.request.query_params.get(field)})
                    except FieldError:
                        pass
        return queryset

    def get_queryset(self):
        _type = self.kwargs.get('type').replace('-', '_')
        return getattr(self, f'{_type}_queryset')()

    def filter_queryset(self, queryset):
        return super().filter_queryset(
            self.filter_queryset_by_job_slug(queryset)
        )

    @staticmethod
    def recruitment_stat_aggregation(queryset, fort_stat_api=False):
        if fort_stat_api:
            return queryset.aggregate(
                total=Count('id'),
                pending=Count('id', filter=Q(status=PENDING))
            )
        else:
            return queryset.aggregate(
                All=Count('id'),
                Pending=Count('id', filter=Q(status=PENDING)),
                Completed=Count('id', filter=Q(status=COMPLETED)),
                Progress=Count('id', filter=Q(status=PROGRESS)),
            )

    def form_approval_stat_aggregation(self, queryset, fort_stat_api=False):
        if fort_stat_api:
            stats = get_form_approval_stats(
                queryset,
                fields=(FORM_PENDING, "total")
            )
        else:
            form_name = self.request.query_params.get('form_name')
            if form_name:
                queryset = queryset.filter(form__name__icontains=form_name)
            stats = get_form_approval_stats(
                queryset,
                exclude_fields=(FORM_DRAFT,)
            )
        return stats

    def get_pre_screening_interview(self):
        queryset = self.pre_screening_interview_queryset()
        response = self._paginated_data(
            serializer_class=PreScreeningInterviewAnswerSerializer,
            fields=(
                'id', 'job_title', 'status', 'scheduled_at', 'verified',
                'candidate', 'score', 'applicant_id'
            )
        )
        response.data['stats'] = self.recruitment_stat_aggregation(queryset)
        return response

    def get_assessment(self):
        queryset = self.assessment_queryset()
        response = self._paginated_data(
            serializer_class=AssessmentAnswerSerializer,
            fields=(
                'id', 'job_title', 'status', 'scheduled_at', 'verified',
                'candidate', 'score', 'applicant_id'
            )
        )
        response.data['stats'] = self.recruitment_stat_aggregation(queryset)
        return response

    def get_reference_check(self):
        queryset = self.reference_check_queryset()
        response = self._paginated_data(
            serializer_class=ReferenceCheckAnswerSerializer,
            fields=(
                'id', 'job_title', 'status', 'scheduled_at', 'verified',
                'candidate', 'score', 'applicant_id'
            )
        )
        response.data['stats'] = self.recruitment_stat_aggregation(queryset)
        return response

    def get_interview(self):
        queryset = self.interview_queryset()
        response = self._paginated_data(
            serializer_class=InterViewAnswerSerializer,
            fields=(
                'id', 'job_title', 'job_slug',
                'status', 'candidate', 'verified',
                'score', 'applicant_id', 'scheduled_at'
            )
        )
        response.data['stats'] = self.recruitment_stat_aggregation(queryset)
        return response

    def get_form_approval(self):
        self.filter_backends = (
            DjangoFilterBackend,
            FilterMapBackend,
            OrderingFilterMap,
            SearchFilter
        )
        self.filter_map = {
            'form_name': ('form__name', 'icontains'),
        }
        self.ordering_fields_map = {
            'title': 'form__name',
            'deadline': 'form__deadline',
            'modified_at': 'modified_at',
        }
        self.search_fields = ('user__first_name', 'user__middle_name', 'user__last_name')
        self.filter_class = UserFormAnswerSheetFilter
        queryset = self.form_approval_queryset()
        response = self._paginated_data(
            serializer_class=ListUserFormAnswerSheetSerializer,
            fields=('id', 'form', 'form_name', 'status', 'user', 'deadline')
        )
        response.data['stats'] = self.form_approval_stat_aggregation(queryset)
        return response

    def applicant_initial_process_stat(self, queryset, serializer_class):
        response = self._paginated_data(
            serializer_class=serializer_class,
            fields=(
                'id', 'job_title', 'status', 'candidate', 'scheduled_at',
                'questions', 'job_apply', 'job_slug', 'score', 'data', 'category',
                'applicant_id'
            )
        )
        response.data['stats'] = self.recruitment_stat_aggregation(queryset)
        return response

    def get_pre_screening(self):
        return self.applicant_initial_process_stat(
            self.pre_screening_queryset(),
            PreScreeningSerializer
        )

    def get_post_screening(self):
        return self.applicant_initial_process_stat(
            self.post_screening_queryset(),
            PostScreeningSerializer
        )

    def get_advance_salary(self):
        queryset, stats, serializer_class = get_advance_salary(self.request.user)

        def get_queryset(s):
            return queryset

        self.get_queryset = types.MethodType(get_queryset, self)
        response = self._paginated_data(
            serializer_class=serializer_class
        )
        response.data['stats'] = stats
        return response

    def get_reimbursement(self):
        queryset, stats, serializer_class = get_reimbursement(self.request.user, 'advance')

        def get_queryset(s):
            return queryset

        self.get_queryset = types.MethodType(get_queryset, self)
        response = self._paginated_data(
            serializer_class=serializer_class,
            fields=[
                'id', 'title', 'type', 'associates', 'reason',
                'created_at', 'total_amount', 'status', 'employee',
                'recipient'
            ]
        )
        response.data['stats'] = stats
        return response

    def get_settlement(self):
        queryset, stats, serializer_class = get_reimbursement(self.request.user, 'settlement')

        def get_queryset(s):
            return queryset.order_by('created_at')

        self.get_queryset = types.MethodType(get_queryset, self)

        response = self._paginated_data(
            serializer_class=serializer_class,
            fields=[
                'id', 'reason', 'type', 'remark', 'created_at', 'total_amount',
                'status', 'employee', 'recipient'
            ]
        )
        response.data['stats'] = stats
        return response

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        view_type = self.kwargs.get('type')
        expense_type = self.request.query_params.get('expense_type', OTHER)
        if view_type == 'cancel-request':
            ctx['expense_type'] = expense_type.title()
        return ctx

    def get_cancel_request(self):
        queryset, stats, serializer_class = get_reimbursement(self.request.user, 'cancel')

        def get_queryset(s):
            return queryset.distinct().order_by('created_at')

        self.get_queryset = types.MethodType(get_queryset, self)
        response = self._paginated_data(
            serializer_class=serializer_class,
            fields=[
                'id', 'remarks', 'created_at', 'status', 'advance_expense', 'recipient'
            ]
        )
        response.data['stats'] = stats
        return response

    def get_exit_interview(self):
        queryset, stats, serializer_class = get_exit_interview(self.request.user)

        self.get_queryset = lambda *args: queryset
        self.filter_backends = [DjangoFilterBackend, OrderingFilterMap]
        self.ordering_fields_map = {
            'name': 'separation__employee__first_name',
            'scheduled_at': 'scheduled_at'
        }

        response = self._paginated_data(
            serializer_class=serializer_class,
            fields=['id', 'separation', 'scheduled_at', 'location', 'status']
        )
        response.data['stats'] = stats
        return response

    def get_leave_request(self):
        queryset, stats, serializer_class = get_leave_request(self.request.user)
        self.get_queryset = lambda *args: queryset
        self.filter_backends = (filters.SearchFilter, FilterMapBackend)
        self.search_fields = ('user__first_name', 'user__middle_name', 'user__last_name')
        self.filter_map = {
            'status': 'status',
            'branch':
                'user__detail__branch__slug',
            'division':
                'user__detail__division__slug',
            'employment_level':
                'user__detail__employment_level__slug',
            'start_time': 'start',
            'end_time': 'end',
            'recipient': 'recipient',
            'user': 'leave_account__user',
            'leave_type': 'leave_rule__leave_type',
            'start_date': 'end__date__gte',
            'end_date': 'start__date__lte'
        }

        response = self._paginated_data(
            serializer_class=serializer_class
        )
        response.data['stats'] = stats
        return response

    def get_resignation(self):
        queryset, stats, serializer_class = get_resignation(self.request.user)

        self.get_queryset = lambda *args: queryset
        self.filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilterMap]
        self.filter_fields = ['release_date', 'status', ]
        self.search_fields = ['employee__first_name', 'employee__middle_name',
                              'employee__last_name']
        self.ordering_fields_map = {
            'created_at': 'created_at',
            'released_date': 'released_date',
            'employee': ('employee__first_name', 'employee__middle_name', 'employee__last_name')
        }

        response = self._paginated_data(
            serializer_class=serializer_class,
            fields=['id', 'employee', 'created_at', 'status', 'recipient', 'hr_approval']
        )
        response.data['stats'] = stats
        return response

    def payroll_approval_queryset(self):
        return self.request.user.pending_payroll_approvals.filter(
            status='Approval Pending'
        )

    def get_payroll_approval(self):
        serializer_class = create_read_only_dummy_serializer(
            ['id',
             'title',
             'from_date',
             'to_date',
             'timestamp',
             'status', ]
        )
        serializer_class = add_fields_to_serializer_class(serializer_class, {
            'organization': OrganizationThinSerializer()
        })
        self.filter_backends = [SearchFilter, FilterMapBackend]
        self.search_fields = ['title']
        self.filter_map = {
            'from_date': 'from_date__gte',
            'to_date': 'to_date__lte'
        }
        return self._paginated_data(serializer_class)

    def get_payroll_approval_stats(self):
        count = self.payroll_approval_queryset().count()
        return {
            "total": count,
            "pending": count
        }

    def get_stats(self):
        dependent_stats = {}
        salary_stats = get_advance_salary_stats(self.request.user)
        reimbursement_stats = get_reimbursement_stats(self.request.user, 'advance')
        settlement_stats = get_reimbursement_stats(self.request.user, 'settlement')
        exit_interview_stats = get_exit_interview_stats(self.request.user)
        leave_request_stats = get_leave_request_stats(self.request.user)
        resignation = get_resignation_stats(self.request.user)
        advance_cancel_stats = get_reimbursement_stats(self.request.user, 'cancel')

        if salary_stats:
            dependent_stats.update({
                'advance_salary': salary_stats
            })
        if reimbursement_stats:
            dependent_stats.update({
                'reimbursement': reimbursement_stats
            })
        if settlement_stats:
            dependent_stats.update({
                'settlement': settlement_stats
            })
        if exit_interview_stats:
            dependent_stats.update({
                'exit_interview': exit_interview_stats
            })
        if resignation:
            dependent_stats.update({
                'resignation': resignation
            })
        if leave_request_stats:
            dependent_stats.update({
                'leave_request': leave_request_stats
            })
        if advance_cancel_stats:
            dependent_stats.update({
                'cancel_request': advance_cancel_stats
            })
        dependent_stats.update({
            'payroll_approval': self.get_payroll_approval_stats()
        })

        stats = {
            'reference_checks': self.recruitment_stat_aggregation(
                self.reference_check_queryset(),
                fort_stat_api=True
            ),
            'interviews': self.recruitment_stat_aggregation(
                self.interview_queryset(),
                fort_stat_api=True
            ),
            'pre_screenings': self.recruitment_stat_aggregation(
                self.pre_screening_queryset(),
                fort_stat_api=True
            ),
            'post_screenings': self.recruitment_stat_aggregation(
                self.post_screening_queryset(),
                fort_stat_api=True
            ),
            'form_request': self.form_approval_stat_aggregation(
                self.form_approval_queryset(),
                fort_stat_api=True
            ),
            'pre_screening_interviews': self.recruitment_stat_aggregation(
                self.pre_screening_interview_queryset(),
                fort_stat_api=True
            ),
            'assessments': self.recruitment_stat_aggregation(
                self.assessment_queryset(),
                fort_stat_api=True
            ),
            **dependent_stats
        }
        stats['summary'] = self.get_total_stats(
            data=stats.values()
        )
        return Response(stats)

    @staticmethod
    def get_total_stats(data):
        return reduce(
            lambda d1, d2: {key: (d1.get(key, 0) + d2.get(key, 0)) for key in d1.keys()},
            data
        )

    def _paginated_data(self, serializer_class, fields=None):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        field_dict = {}
        if fields:
            field_dict = {
                'fields': fields
            }
        if page is not None:
            serializer = serializer_class(
                page,
                fields=fields,
                many=True,
                context=self.get_serializer_context()
            )
            return self.get_paginated_response(serializer.data)
        serializer = serializer_class(
            qs,
            many=True,
            context=self.get_serializer_context(),
            **field_dict
        )
        return Response(serializer.data)

    @action(detail=False, url_name='related_jobs', url_path='related-jobs')
    def get_related_jobs(self, request, *args, **kwargs):
        filter_mapper = {
            'pre-screening': Q(applications__pre_screening__responsible_person=self.request.user),
            'post-screening': Q(
                applications__post_screening__responsible_person=self.request.user),
            'pre-screening-interview': Q(
                applications__pre_screening_interview__pre_screening_interview_question_answers__internal_interviewer=self.request.user),
            'assessment': Q(
                applications__assessment__assessment_question_answers__internal_assessment_verifier=self.request.user),
            'interview': Q(
                applications__interview__interview_question_answers__internal_interviewer=self.request.user),
            'reference-check': Q(
                applications__reference_check__reference_check_question_answers__internal_reference_checker=self.request.user),
        }
        results = Job.objects.filter(
            filter_mapper.get(self.kwargs.get('type', Q()))
        ).values('title__title', 'slug')
        return Response(results)
