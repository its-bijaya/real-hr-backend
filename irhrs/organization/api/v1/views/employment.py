from django.db.models import Count, Q, Prefetch
from django.utils.timezone import timedelta, datetime
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from irhrs.core.constants.common import EMPLOYMENT_LEVEL_CHOICE, DURATION_CHOICES
from irhrs.core.mixins.file_import_mixin import BackgroundFileImportMixin
from irhrs.core.mixins.viewset_mixins import (OrganizationMixin,
                                              OrganizationCommonsMixin, ListViewSetMixin,
                                              HRSOrderingFilter, IStartsWithIContainsSearchFilter,
                                              ValidateUsedData)
from irhrs.organization.api.v1.permissions import (OrganizationSettingsWritePermission,
                                                   OrganizationReportPermission,
                                                   EmploymentStatusPermission,
                                                   EmploymentJobTitlePermission,
                                                   EmploymentLevelPermission)
from irhrs.organization.models import (EmploymentStatus, EmploymentLevel,
                                       EmploymentJobTitle, EmploymentStep)
from irhrs.users.models import UserExperience, UserSupervisor
from ..serializers.employment import (EmploymentLevelSerializer,
                                      EmploymentJobTitleSerializer,
                                      EmploymentStepSerializer,
                                      EmploymentStatusSerializer,
                                      EmploymentStatusReportSerializer)


class EmploymentStatusView(BackgroundFileImportMixin, OrganizationMixin,
                           OrganizationCommonsMixin, ValidateUsedData, ModelViewSet):
    """
    list:
    Lists all the employment status. The results are paginated.

    ### Result

    ```javascript
        {
            "title": "Employment Status",
            "description": "Optional Description",
            "organization": "xyz-company",
            "slug": "employment-status"
        }
    ```
    ### Searching

    Results can be filtered with ?search=<part-of-title>

    retrieve:
    Get details of an employment status given the slug of the employment title.

    create:
    Create a new employment status.

    ### Format

    ```javascript
    {
        "title": "Employment Status",
        "description": "Optional Description",
    }
    ```
    update:
    Perform full update of employment status.

    ### Format
    ```javascript
    {
        "title": "New Employment Status",
        "description": "Optional Description",
    }
    ```

    partial_update:
    Perform update on only some fields of the employment status. The format is
    same as of ```full_update```.

    delete:
    Perform delete on employment status provided the slug.
    """
    queryset = EmploymentStatus.objects.all()
    serializer_class = EmploymentStatusSerializer
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filter_fields = ('is_archived', )

    search_fields = ('title',)
    ordering_fields = (
        'title', 'created_at', 'modified_at', 'is_contract', 'is_archived'
    )
    permission_classes = [EmploymentStatusPermission]
    import_fields = [
        'TITLE',
        'DESCRIPTION',
        'IS CONTRACT'
    ]
    values = [
        'Junior Developer',
        'Description of employment status',
        'False'
    ]
    background_task_name = 'employment_type'
    sample_file_name = 'employment_type'
    non_mandatory_field_value = {
        'description': ''
    }
    related_names = ['userdetails', 'user_experiences', 'preemployment_set',
                     'advancesalarysetting_set', 'jobs']
    related_methods = ['delete']

    def get_queryset(self):
        return super().get_queryset()

    @action(methods=['get'], detail=False, url_path='report', url_name='report')
    def statistics(self, request, **kwargs):
        # TODO @Ravi: convert date check to __range()
        organization = self.get_organization()
        filter_by = request.GET.get('for', 'year')
        mapper = {
            'year': -365,
            'month': -30,
            'week': -7
        }
        start_date = datetime.now()
        end_date = start_date + timedelta(days=mapper.get(filter_by, -365))
        response = EmploymentStatus.objects.filter(
            organization=organization).annotate(
            number_of_employees=Count(
                'user_experiences',
                filter=Q(
                    user_experiences__is_current=True
                ) | Q(
                    user_experiences__start_date__range=(start_date, end_date)
                )
            )
        ).values(
            'title', 'number_of_employees', 'slug')
        return Response(response)

    @action(methods=['get'], detail=False, url_path='report-data',
            url_name='report-data')
    def report_data(self, request, **kwargs):
        organization = self.get_organization()
        filter_kwarg = request.query_params.get('status')
        search = request.query_params.get('search')
        instance = UserExperience.objects.filter(
            organization=organization)
        if filter_kwarg:
            instance = instance.filter(employment_status__slug=filter_kwarg)
        if search:
            # Add filter backend.
            instance = instance.filter(
                user__first_name__istartswith=search)
        page = self.paginate_queryset(instance)
        if page is not None:
            serializer = EmploymentStatusReportSerializer(page, many=True)
            resp = self.get_paginated_response(serializer.data)
            return resp
        return Response

    def get_queryset_fields_map(self):
        return {
            'is_contract': ['True', 'False']
        }

    def get_failed_url(self):
        return f"/admin/{self.organization.slug}/organization/settings/employment-type/?status=failed"

    def get_success_url(self):
        return f"/admin/{self.organization.slug}/organization/settings/employment-type/?status=success"


class UserDataTableView(HRSOrderingFilter, OrganizationMixin, ListViewSetMixin):
    """
    A view for extracting paginated table response for data-table view.
    """
    queryset = []
    serializer_class = EmploymentStatusReportSerializer
    search_fields = (
        'user__first_name',
        'user__middle_name',
        'user__last_name'
    )
    ordering_fields_map = {
        'name': 'user__first_name',
        'joined_date': 'start_date',
        'supervisor': 'user__supervisors__supervisor__first_name',
        'dob': 'user__detail__date_of_birth',
        'branch': 'branch__name',
    }
    filter_backends = (
        filters.SearchFilter, filters.OrderingFilter
    )
    valid_lookups = {
        'division': 'division__slug',
        'branch': 'branch__slug',
        'religion': 'user__detail__religion__slug',
        'employment_level': 'employee_level__slug',
        'ethnicity': 'user__detail__ethnicity__slug',
        'bank': 'user__banks__bank__slug',
        'employment_status': 'employment_status__slug'
    }
    permission_classes = [OrganizationReportPermission]

    def get_queryset(self):
        organization = self.organization
        filter_attr = self.request.query_params.get('category')
        filter_value = self.request.query_params.get('value')
        queryset = UserExperience.objects.filter(
            organization=organization, is_current=True
        ).select_related(
            'user',
            'user__detail',
            'user__detail__division',
            'user__detail__organization',
            'user__detail__job_title',
            'user__detail__employment_level',
            'user__detail__employment_status',
            'organization',
            'employee_level',
            'employment_status',
            'branch'
        ).prefetch_related(
            Prefetch('user__supervisors',
                     queryset=UserSupervisor.objects.filter(authority_order=1)
                     .select_related('supervisor',
                                     'supervisor__detail',
                                     'supervisor__detail__organization',
                                     'supervisor__detail__job_title',
                                     'supervisor__detail__division',
                                     'supervisor__detail__employment_level'),
                     to_attr='user_supervisors')
        )
        if filter_attr in self.valid_lookups.keys():
            fil = {self.valid_lookups[filter_attr]: filter_value}
            return queryset.filter(**fil)
        return queryset


class EmploymentLevelView(BackgroundFileImportMixin, OrganizationMixin,
                          OrganizationCommonsMixin, ValidateUsedData, ModelViewSet):
    """
    list:
    Lists all the employment level. The results are paginated.

    ### Result

    ```javascript
        {
            "slug": "level-1",
            "title": "Level 1",
            "code": "L-1",
            "order_field": 1
        }
    ```
    ### Searching

    Results can be filtered with ?search=<part-of-title>

    retrieve:
    Get details of an employment level given the slug of the employment level.

    create:
    Create a new employment level.

    ### Format

    ```javascript
        {
            "title": "Level 11",
            "code": "L-11",
            "order_field": 2
        }
    ```
    update:
    Perform full update of employment level.

    ### Format
    ```javascript
        {
            "title": "Level 100",
            "code": "L-100",
            "order_field": 10
        }
    ```

    partial_update:
    Perform update on only some fields of the employment level. The format is
    same as of ```full_update```.

    delete:
    Perform delete on employment level provided the slug.
    """
    queryset = EmploymentLevel.objects.all()
    serializer_class = EmploymentLevelSerializer
    lookup_field = 'slug'
    filter_backends = (IStartsWithIContainsSearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filter_fields = ('is_archived', )
    search_fields = ('title',)
    ordering_fields = (
        'order_field', 'code', 'title', 'created_at', 'modified_at',
        'is_archived'
    )
    permission_classes = [EmploymentLevelPermission]
    import_fields = [
        'TITLE',
        'HIERARCHY ORDER',
        'CODE',
        'STEP',
        'DESCRIPTION',
        'AUTO INCREMENT',
        'INCREMENT STEP BY',
        'CHANGES ON FISCAL',
        'FREQUENCY FOR CHANGE',
        'DURATION FOR CHANGE',
        'LEVEL'
    ]
    values = [
        'Jr. Trainee ',
        '1',
        'jr-trainee',
        '1',
        'Description of employment level',
        'Must be selected either TRUE or FALSE',
        '1',
        'TRUE for "In Every Change in Fiscal Year" FALSE for "Increase Step in Every"',
        '1',
        '',
        ''
    ]
    model_fields_map = {
        'TITLE': 'title',
        'HIERARCHY ORDER': 'order_field',
        'CODE': 'code',
        'STEP': 'scale_max',
        'DESCRIPTION': 'description',
        'AUTO INCREMENT': 'auto_increment',
        'INCREMENT STEP BY': 'auto_add_step',
        'CHANGES ON FISCAL': 'changes_on_fiscal',
        'FREQUENCY FOR CHANGE': 'frequency',
        'DURATION FOR CHANGE': 'duration',
        'LEVEL': 'level'
    }
    background_task_name = 'employment_level'
    sample_file_name = 'employment_level'
    non_mandatory_field_value = {
        'code': '',
        'duration': '',
        'description': '',
        'level': ''
    }
    related_names = ['userdetails', 'user_experiences', 'preemployment_set', 'jobs']
    related_methods = ['delete']

    def get_queryset_fields_map(self):
        return {
            'scale_max': self.get_range_of_numbers(100),
            'auto_increment': ['true', 'false'],
            'auto_add_step': self.get_range_of_numbers(100),
            'changes_on_fiscal': ['true', 'false'],
            'duration': list(dict(DURATION_CHOICES).keys()),
            'frequency': self.get_range_of_numbers(3000),
            'level': list(dict(EMPLOYMENT_LEVEL_CHOICE).keys())
        }

    @staticmethod
    def get_range_of_numbers(max_num):
        return list(
            map(
                str,
                range(1, max_num + 1)
            )
        )

    def get_failed_url(self):
        return f"/admin/{self.organization.slug}/organization/settings/employment-level/?status=failed"

    def get_success_url(self):
        return f"/admin/{self.organization.slug}/organization/settings/employment-level/?status=success"


class EmploymentJobTitleView(BackgroundFileImportMixin, OrganizationMixin,
                             OrganizationCommonsMixin, ValidateUsedData, ModelViewSet):
    """
    list:
    Lists all the employment job title. The results are paginated.

    ### Result

    ```javascript
        {
            "title": "Job Title",
            "description": "Optional Description"
        }
    ```
    ### Searching

    Results can be filtered with ?search=<part-of-title>

    retrieve:
    Get details of an employment job title given the slug.

    create:
    Create a new employment status.

    ### Format

    ```javascript
    {
        "title": "Employment Job Title",
        "description": "Optional Description",
    }
    ```
    update:
    Perform full update of employment job title.

    ### Format
    ```javascript
    {
        "title": "New Employment Job Title",
        "description": "Optional Description",
    }
    ```

    partial_update:
    Perform update on only some fields of the employment job title.
    The format is same as of ```full_update```.

    delete:
    Perform delete on employment job title provided the slug.
    """
    queryset = EmploymentJobTitle.objects.all()
    serializer_class = EmploymentJobTitleSerializer
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter, filters.OrderingFilter,)
    search_fields = ('title',)
    ordering_fields = ('title', 'created_at', 'modified_at')
    permission_classes = [EmploymentJobTitlePermission]
    import_fields = [
        'TITLE',
        'DESCRIPTION',
    ]
    values = [
        'Jr. Dev.',
        'Description of job title.',
    ]
    background_task_name = 'job_title'
    sample_file_name = 'job_title'
    non_mandatory_field_value = {
        'description': ''
    }
    related_names = ['userdetails', 'user_experiences', 'preemployment_set', 'jobs']
    related_methods = ['delete']

    def get_failed_url(self):
        return f"/admin/{self.organization.slug}/organization/settings/job-title/?status=failed"

    def get_success_url(self):
        return f"/admin/{self.organization.slug}/organization/settings/job-title/?status=success"


class EmploymentStepViewSet(OrganizationMixin, OrganizationCommonsMixin,
                            ModelViewSet):
    """
    list:
    Lists Employment step for the selected organization.

    create:
    Create new Employment step for the given organization.

    retrieve:
    Get Employment step of the organization.

    delete:
    Deletes the selected Employment step of the organization.

    update:
    Updates the selected Employment step details for the given organization.

    """
    queryset = EmploymentStep.objects.all()
    serializer_class = EmploymentStepSerializer
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter, filters.OrderingFilter,)
    search_fields = ('title',)
    ordering_fields = ('title',)
    permission_classes = [OrganizationSettingsWritePermission]
