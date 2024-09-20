import django_filters.rest_framework as filters
from django.db.models import Q
from django.utils import timezone

from irhrs.core.constants.user import EDUCATION_DEGREE_CHOICES
from irhrs.recruitment.constants import GENDER_CHOICES, MONTHLY, JOB_STATUS_CHOICES, \
    PUBLISHED, \
    JOB_APPLY_STATUS_CHOICES, PROCESS_STATUS_CHOICES
from irhrs.recruitment.models import Job, City, JobApply, PreScreening
from irhrs.recruitment.utils import filter_salary_range


class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    pass


class JobFilter(filters.FilterSet):
    locations = CharInFilter(
        label='Locations',
        field_name='job_locations',
        method='filter_by_location'
    )

    skills = CharInFilter(
        label="Skills",
        field_name='skills__slug',
        lookup_expr='in'
    )

    preferred_shift = CharInFilter(
        label="Preferred Shit",
        field_name='preferred_shift',
        lookup_expr='in'
    )

    tags = CharInFilter(
        label='Tags',
        lookup_expr='in',
        method='filter_by_tags'
    )

    categories = CharInFilter(
        label='Categories',
        field_name='categories__slug',
        lookup_expr='in'
    )

    industry = CharInFilter(
        label='Industries',
        field_name='organization__industry__slug',
        lookup_expr='in'
    )

    salary = filters.RangeFilter(
        label='Salary Range',
        method='filter_salary_range'
    )

    employment_level = CharInFilter(
        label='Employment Level',
        field_name='employment_level__slug',
        lookup_expr='in'
    )

    education_degree = filters.ChoiceFilter(
        label='Education',
        choices=EDUCATION_DEGREE_CHOICES
    )

    employment_status = CharInFilter(
        label='Employment Status',
        field_name='employment_status__slug',
        lookup_expr='in'
    )

    experience = filters.RangeFilter(
        label='Experience',
        method='filter_experience'
    )

    gender = filters.CharFilter(
        label='Gender',
        method='filter_gender',
    )

    age = filters.RangeFilter(label='Age', method='filter_age')

    urgent = filters.BooleanFilter(
        label="Urgently Required",
        method='filter_urgently_required'
    )

    two_wheeler = filters.BooleanFilter(
        label="Required Two Wheeler",
        field_name='setting__required_two_wheeler'
    )

    class Meta:
        model = Job
        fields = [
            'preferred_shift',
        ]

    @staticmethod
    def filter_gender(queryset, field_name, value):
        if value == 'No Preference':
            return queryset.filter(
                Q(setting__gender__isnull=True) |
                Q(setting__gender='')
            )
        return queryset.filter(setting__gender=value)

    @staticmethod
    def filter_by_location(queryset, field, value):
        if 'any' in value:
            return queryset
        else:
            queryset = queryset.filter(
                job_locations__city_id__in=value
            )
        return queryset

    @staticmethod
    def filter_by_tags(queryset, field, value):
        if 'any' in value:
            return queryset
        else:
            queryset = queryset.filter(
                tags__slug__in=value
            )
        return queryset

    @staticmethod
    def filter_education_degree(queryset, field, value):
        if value:
            queryset = queryset.filter(education_level__level__gte=value.level)
        return queryset

    @staticmethod
    def filter_by_slug(queryset, field, value):
        return queryset

    @staticmethod
    def filter_age(queryset, field, value):
        min_age, max_age = value.start, value.stop
        age_filter = Q()
        if min_age:
            age_filter.add(Q(setting__min_age__gte=min_age), Q.OR)
        if max_age:
            age_filter.add(Q(setting__max_age__lte=max_age), Q.OR)
        return queryset.filter(age_filter)

    @staticmethod
    def filter_experience(queryset, field, value):
        min_experience, max_experience = value.start, value.stop
        experience_filter = dict()
        if not min_experience.is_nan():
            if int(min_experience) == 0:
                experience_filter['setting__is_experience_required'] = False
                experience_filter['setting__min_experience_months__isnull'] = True
            elif int(min_experience) == 60:
                experience_filter['setting__min_experience_months__gte'] = min_experience
            else:
                experience_filter['setting__min_experience_months'] = min_experience

        if max_experience:
            experience_filter['setting__max_experience_months__lte'] = max_experience

        return queryset.filter(**experience_filter)

    @staticmethod
    def filter_urgently_required(queryset, field, value):
        one_week_from_now = timezone.now() + timezone.timedelta(weeks=1)
        if value:
            queryset = queryset.filter(deadline__lte=one_week_from_now)
        return queryset

    @staticmethod
    def filter_salary_range(queryset, value, unit):
        salary_field = 'offered_salary'
        return filter_salary_range(queryset, value, unit, salary_field)

    def filter_queryset(self, queryset):
        clean_fields = self.form.cleaned_data

        salary = clean_fields.pop('salary', None)
        if salary:
            queryset = self.filter_salary_range(queryset, salary, MONTHLY)
        return super().filter_queryset(queryset).distinct()


class ApplicationShortlistFilter(filters.FilterSet):
    salary = filters.RangeFilter(
        label='Salary Range',
        method='filter_salary_range'
    )
    gender = filters.CharFilter(
        label='Gender',
        method='filter_gender',
    )
    education_degree = filters.MultipleChoiceFilter(
        label='Education Degree',
        choices=EDUCATION_DEGREE_CHOICES,
        field_name='applicant__education_degree'
    )
    experience = filters.NumberFilter(
        label='Experience Months',
        method='filter_experience')
    location = filters.ModelChoiceFilter(
        label='Location',
        queryset=City.objects.all(),
        field_name='applicant__address',
    )

    age = filters.RangeFilter(label='Age', method='filter_age')

    skills = CharInFilter(
        label="Skills",
        field_name='applicant__skills__slug',
        lookup_expr='in'
    )

    status = filters.ChoiceFilter(
        label='Status',
        choices=JOB_APPLY_STATUS_CHOICES,
        field_name='status'
    )

    class Meta:
        model = JobApply
        fields = []

    @staticmethod
    def filter_salary_range(queryset, value, unit):
        salary_field = 'applicant__expected_salary'
        return filter_salary_range(queryset, value, unit, salary_field)

    @staticmethod
    def filter_gender(queryset, field_name, value):
        if value == 'No Preference':
            return queryset.filter(
                Q(applicant__user__gender__isnull=True) |
                Q(applicant__user__gender='')
            )
        return queryset.filter(applicant__user__gender=value)

    @staticmethod
    def filter_age(queryset, field_name, value):
        if value:
            fil = dict()
            if value.start:
                relative_year_start = timezone.now().year - value.start
                fil.update({'applicant__user__dob__year__lte': relative_year_start})
            if value.stop:
                relative_year_stop = timezone.now().year - value.stop
                fil.update({'applicant__user__dob__year__gte': relative_year_stop})

            queryset = queryset.filter(**fil)
        return queryset

    @staticmethod
    def filter_experience(queryset, field, value):
        experience_filter = dict()
        if value == 5:
            experience_filter['applicant__experience_years__gte'] = value
        else:
            experience_filter['applicant__experience_years__lte'] = value

        return queryset.filter(**experience_filter)

    def filter_queryset(self, queryset):
        clean_fields = self.form.cleaned_data

        salary = clean_fields.pop('salary', None)
        salary_unit = clean_fields.pop('salary_unit', None) or MONTHLY
        if salary:
            queryset = self.filter_salary_range(queryset, salary, salary_unit)
        return super().filter_queryset(queryset).distinct()


class JobViewSetFilter(filters.FilterSet):
    status_choices = list(JOB_STATUS_CHOICES)
    status_choices += [("Active", "Active"), ("Expired", "Expired")]

    status = filters.ChoiceFilter(
        choices=status_choices,
        method='filter_status'
    )

    class Meta:
        model = Job
        fields = ['status']

    def filter_status(self, queryset, field, value):
        if value in ["Active", "Published"]:
            return queryset.filter(
                deadline__gte=timezone.now(),
                status=PUBLISHED)
        elif value == "Expired":
            return queryset.filter(deadline__lt=timezone.now(),
                                   status=PUBLISHED)
        else:
            return queryset.filter(status=value)


class ApplicantProcessFilter(filters.FilterSet):
    status_choices = list(PROCESS_STATUS_CHOICES)
    status_choices += [("Forwarded", "Forwarded"), ]

    status = filters.ChoiceFilter(
        choices=status_choices,
        method='filter_status'
    )

    class Meta:
        model = PreScreening
        fields = ['status']

    def filter_status(self, queryset, field, value):
        if value == 'Forwarded':
            # Need job information so handled in filter queryset
            return queryset
        else:
            return queryset.filter(status=value)
