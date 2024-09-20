# from django.contrib.auth import get_user_model
# User = get_user_model()
from django.db.models import (
    Q,
    Sum,
    Count
)

from rest_framework import serializers
from irhrs.users.models import UserDetail

from irhrs.payroll.utils.helpers import (
    AvailabilityQueryHelper
)

from irhrs.payroll.models import (
    ReportRowRecord,
    OverviewConfig,
    EmployeePayroll,
    SalaryHolding
)
from irhrs.organization.models import Organization

class OverViewReportDataSerializer(serializers.Serializer):
    organization = serializers.SlugRelatedField(
        queryset=Organization.objects.all(),
        slug_field='slug'
    )
    from_date = serializers.DateField()
    to_date = serializers.DateField()

    def validate(self, obj):
        from_date = obj.get('from_date')
        to_date = obj.get('to_date')
        validation_dict = dict()
        if from_date > to_date:
            validation_dict['from_date'] ='Start date should be less than end date.'

        if validation_dict.keys():
            raise serializers.ValidationError(validation_dict)
        return obj

    def get_data(self):
        if hasattr(self, 'initial_data') and not hasattr(self, '_validated_data'):
            msg = (
                'When a serializer is passed a `data` keyword argument you '
                'must call `.is_valid()` before attempting to access the '
                'serialized `.data` representation.\n'
                'You should either call `.is_valid()` first, '
                'or access `.initial_data` instead.'
            )
            raise AssertionError(msg)

        return OverviewReportData(
            self.validated_data.get('from_date'),
            self.validated_data.get('to_date'),
            self.validated_data.get('organization')
        ).data


class OverviewReportData():
    def __init__(self, from_date, to_date, organization):
        self.from_date = from_date
        self.to_date = to_date
        self.organization = organization
        calendar_days_delta = self.to_date - self.from_date
        self.calendar_days = calendar_days_delta.days + 1
        self.gender_percentage = self.get_gender_percentage()
        self.overview_config = self.get_or_create_overview_config()

    def get_or_create_overview_config(self):
        return OverviewConfig.objects.get_or_create(organization=self.organization)[0]

    def get_working_days(self):
        """
        Get working days was expected to return a constant (under the assumption, org has fixed working days.)
        However, Working days is defined in RealHRSoft as count of WorkDay Coefficient and varies per user.
        """
        return 0

    def get_gender_percentage(self):
        gender_counts = UserDetail.objects.filter(
            user__user_experiences__is_current=True
        ).aggregate(
            male_count=Count('id', filter=Q(gender='Male')),
            female_count=Count('id', filter=Q(gender='Female')),
            other_count=Count('id', filter=Q(gender='Other'))
        )

        male_count = gender_counts['male_count']
        female_count = gender_counts['female_count']
        other_count = gender_counts['other_count']
        total = male_count + female_count + other_count
        if total == 0:
            return {
                'male_percentage': None,
                'female_percentage': None,
                'other_percentage': None,
            }
        return {
            'male_percentage': (male_count * 100)/total,
            'female_percentage': (female_count * 100)/total,
            'other_percentage': (other_count * 100)/total
        }

    def get_total_organization_employees_count(self):
        return UserDetail.objects.filter(
            organization=self.organization
        ).count()

    def get_heading(self, heading_name):
        return getattr(self.overview_config, heading_name, None)

    def get_aggregated_heading_amount(self, heading_name):
        heading = self.get_heading(heading_name)
        amount = 0
        if heading:
            aggregated_data = ReportRowRecord.objects.filter(
                from_date__gte=self.from_date,
                to_date__lte=self.to_date,
                heading=heading,
                employee_payroll__payroll__organization=self.organization,
                employee_payroll__payroll__status='Confirmed'
            ).aggregate(
                Sum('amount')
            )
            amount = aggregated_data.get('amount__sum')
        return amount

    def get_cluster_field_wise_heading_amount(self, cluster_field, heading_name):
        heading = self.get_heading(heading_name)
        data = list()
        if heading:
            data = ReportRowRecord.objects.filter(
                from_date__gte=self.from_date,
                to_date__lte=self.to_date,
                heading=heading,
                employee_payroll__payroll__organization=self.organization,
                employee_payroll__payroll__status='Confirmed'
            ).values(
                cluster_field
            ).annotate(
                amount=Sum('amount'),
                count=Count('id')
            )
        return data

    @property
    def data(self):
        return {
            'top_bar': {
                'from_date': self.from_date,
                'to_date': self.to_date,
                'calendar_days': self.calendar_days,
                'total_employees': self.get_total_organization_employees_count(),
                'working_days': self.get_working_days(),
                'male_percentage': self.gender_percentage['male_percentage'],
                'female_percentage': self.gender_percentage['female_percentage'],
                'other_gender_percentage': self.gender_percentage['other_percentage'],
            },

            'second_bar': {
                'salary_payable': self.get_aggregated_heading_amount('salary_payable'),
                'tds_payment': self.get_aggregated_heading_amount('tds_payment'),
                'provident_fund': self.get_aggregated_heading_amount('provident_fund'),
                'cit': self.get_aggregated_heading_amount('cit'),
                'gratuity': self.get_aggregated_heading_amount('gratuity'),
            },
            'department_wise_salary': self.get_cluster_field_wise_heading_amount(
                'employee_payroll__employee__detail__division__name',
                'payroll_cost'
            ),
            'branch_wise_salary': self.get_cluster_field_wise_heading_amount(
                'employee_payroll__employee__detail__branch__name',
                'payroll_cost'
            ),
            'employment_wise_salary': self.get_cluster_field_wise_heading_amount(
                'employee_payroll__employee__detail__employment_level__title',
                'payroll_cost'
            ),
            'salary_disbursement_detail': {
                'bank_deposit': self.get_bank_deposit_salary_disbursement_count(),
                'hold': self.get_holded_salary_disbursement_count(),
            },
            'salary_range_breakdown': self.get_salary_range_breakdown(),
            'ctc': self.get_aggregated_heading_amount('cost_to_company'),
            'actual_earned': self.get_aggregated_heading_amount('actual_earned'),
            'salary_payment_detail': self.get_salary_payment_detail()
        }

    def get_bank_deposit_salary_disbursement_count(self):
        # TODO @Ravi: add 'user has bank account' filter
        return EmployeePayroll.objects.filter(
            payroll__status='Confirmed',
            payroll__from_date__gte=self.from_date,
            payroll__to_date__lte=self.to_date,
            payroll__organization=self.organization
        ).distinct().count()

    def get_holded_salary_disbursement_count(self):
        sh_q = AvailabilityQueryHelper(
            self.from_date,
            self.to_date,
            'from_date',
            'to_date'
        )
        to_date_not_none_query_object = Q(
            ~Q(to_date=None) &
            Q(
                Q(sh_q.a & sh_q.b & sh_q.c & sh_q.d) |
                Q(sh_q.e & sh_q.f & sh_q.g & sh_q.h) |
                Q(sh_q.i & sh_q.j & sh_q.k & sh_q.l) |
                Q(sh_q.m & sh_q.n & sh_q.o & sh_q.p))
        )

        to_date_none_query_object = Q(
            Q(to_date=None) &
            Q(
                Q(from_date__gte=self.from_date) &
                Q(from_date__lte=self.to_date)
            )
        )

        return SalaryHolding.objects.filter(
            released=False
        ).filter(
            to_date_not_none_query_object |
            to_date_none_query_object
        ).distinct().count()

    def get_salary_range_breakdown(self):
        heading = self.get_heading('salary_range')
        ranges = self.overview_config.salary_breakdown_ranges.all()
        data = list()
        if heading and ranges:
            aggregate_kwargs = dict()
            for rng in ranges:
                aggregate_kwargs["{} - {}".format(rng.from_amount, rng.to_amount)] = Count(
                    'employee_payroll__employee_id',
                    filter=Q(
                        total_amount__gte=rng.from_amount,
                        total_amount__lt=rng.to_amount
                    )
                )

            data = ReportRowRecord.objects.filter(
                from_date__gte=self.from_date,
                to_date__lte=self.to_date,
                heading=heading,
                employee_payroll__payroll__organization=self.organization,
                employee_payroll__payroll__status='Confirmed'
            ).values(
                'employee_payroll__employee_id'
            ).annotate(
                total_amount=Sum('amount')
            ).aggregate(
                **aggregate_kwargs
            )
        return data

    def get_salary_payment_detail(self):
        graph_headings = self.overview_config.salary_payment_detail_bar_graph_headings.all()
        data = dict()
        if graph_headings:
            aggregate_kwargs = dict()
            for heading in graph_headings:
                aggregate_kwargs[heading.name] = Sum(
                    'amount', filter=Q(heading=heading)
                )
            data = ReportRowRecord.objects.filter(
                from_date__gte=self.from_date,
                to_date__lte=self.to_date,
                employee_payroll__payroll__organization=self.organization,
                employee_payroll__payroll__status='Confirmed'
            ).aggregate(
                **aggregate_kwargs
            )
        return data
