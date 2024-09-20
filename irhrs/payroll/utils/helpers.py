import functools
import itertools
from collections import OrderedDict
from datetime import date, timedelta
from functools import reduce
from dateutil.relativedelta import relativedelta
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import DateField, Q, Count
from rest_framework import serializers
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from irhrs.attendance.utils.payroll import get_worked_days
from irhrs.core.constants.payroll import APPROVED, DENIED, REQUESTED, REPAYMENT, \
    COMPLETED, CANCELED, CONFIRMED
from irhrs.core.constants.user import CHILDREN
from irhrs.core.utils import nested_getattr
from irhrs.core.utils.common import get_today
from irhrs.leave.utils.payroll import get_paid_leave_days
from irhrs.organization.models import EmploymentLevel, FiscalYear, FiscalYearMonth, GLOBAL
from irhrs.payroll.utils.mixins import InputChoiceSerializer

User = get_user_model()


def get_model_from_string(string):
    str_splits = string.split('.')
    app_name = str_splits[0]
    model_name = str_splits[1]
    return apps.get_model(app_label=app_name, model_name=model_name)


class UserSerializer(InputChoiceSerializer, serializers.ModelSerializer):
    label = serializers.ReadOnlyField(source='__str__')

    class Meta:
        model = User
        fields = ('email', 'username', 'groups')


def jwt_response_payload_handler(token, user=None, request=None):
    return {
        'token': token,
        'user': UserSerializer(user, context={'request': request}).data
    }


class ExtendedPageNumberPagination(LimitOffsetPagination):

    def get_paginated_response(self, data, extra_data):
        return Response(OrderedDict([
            ('count', self.count),
            ('extra_data', extra_data),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


def merge_two_dicts(x, y):
    z = x.copy()  # start with x's keys and values
    z.update(y)  # modifies z with y's keys and values & returns None
    return z


def get_variable_name(name, *suffixes):
    var_name = '_'.join(name.upper().split(' '))
    suffix = ''.join(suffixes)
    var_name += suffix
    return var_name


def get_heading_name_from_variable(variable_name):
    """
    Returns case insensitive heading name from variable name
    """
    return variable_name.replace("_", " ").strip()


def get_employee_age_variables():
    """
    :return: [(variable_name,  start, end), ...]
    """
    return [
        (f"children_count_aging_from_{start}_to_{end}", start, end)
        for start, end in getattr(settings, 'PAYROLL_CHILDREN_COUNT_VARIABLE_AGE_RANGES', [])
    ]


def get_children_count_for_age_range(employee, start=None, end=None) -> int:
    """
    Returns children count for given age range
    :param obj: dictionary with Employee (User) object in instance key
    :param start: lower limit of age, None if open
    :param end: upper limit of age, None if open
    :return: count of children in that date range
    """
    fil = {'is_dependent': True}
    if start:
        fil['date_of_birth__lte'] = get_today() - timedelta(days=365 * start)
    if end:
        fil['date_of_birth__gt'] = get_today() - timedelta(days=365 * end)

    if start or end:
        fil['date_of_birth__isnull'] = False

    return employee.contacts.filter(
        contact_of=CHILDREN,
        **fil
    ).distinct().count()


Employee = User
Designation = EmploymentLevel


class EmployeeAndDesignationCommonFieldAdapter(object):
    # todo @Ravi: Is this used? (Old todo if common fields contains date or datetime type data)
    def __init__(self):
        self.employee_model = Employee
        self.designation_model = Designation
        # self.common_fields = ('basic_salary', 'grade_rate', 'total_grade')

    @classmethod
    def get_common(cls):
        return cls().get_common_fields()

    def get_common_fields(self):
        common_fields = []
        employee_model_fields = self.employee_model._meta.fields
        designation_model_fields = self.designation_model._meta.fields

        for d_field in designation_model_fields:
            for e_field in employee_model_fields:
                # print(d_field.description)
                if d_field.name == e_field.name and d_field.description \
                    == e_field.description and d_field.name != 'id' and d_field.description in [
                        'Integer', 'Positive integer']:
                    common_fields.append(d_field)
        return common_fields

    def generate(self, employee_instance, designation_instance):
        assert (type(employee_instance) == self.employee_model)
        assert (type(designation_instance) == self.designation_model)
        fields = self.get_common_fields()
        data = dict()
        for field in fields:
            # if type(field) == DateField:
            #     data['__' + '' + get_variable_name(field.name) + '__'] =
            # datework_class.ad_to_date_class(
            #         getattr(instance, field.name)) if getattr(instance, field.name) else None
            # else:
            data['__' + '' + get_variable_name(field.name) + '__'] = getattr(employee_instance,
                                                                             field.name) or getattr(
                employee_instance, field.name)
        return data

    def get_variables_list(self):
        fields = self.get_common_fields()
        data = []
        for field in fields:
            data.append('__' + '' + get_variable_name(field.name) + '__')
        return data


class VariableAdapter(object):
    def __init__(self, prefix, **kwargs):
        self.instance = kwargs.get('instance')
        self.kwargs = kwargs
        self.model = type(
            self.instance) if self.instance else kwargs.get('model')
        self.prefix = prefix
        self.fields = self.get_fields()
        self.properties = self.Meta.properties

        # set dynamic attributes if any
        getattr(self, 'set_dynamic_attributes', lambda: None)()

    def get_fields(self):
        fields = []
        if self.Meta.fields == '__all__':
            fields = self.model._meta.fields
        if type(self.Meta.fields) == tuple:
            fields = [self.model._meta.get_field(
                item) for item in self.Meta.fields]
        return fields

    def generate_variables_only(self):
        data = []
        for field in self.fields:
            data.append('__' + self.prefix +
                        get_variable_name(field.name) + '__')
        for properti in self.properties:
            data.append('__' + self.prefix +
                        get_variable_name(properti) + '__')

        for method_field in self.Meta.method_fields:
            data.append('__' + self.prefix +
                        get_variable_name(method_field) + '__')
        return data

    def generate(self):
        data = dict()
        for field in self.fields:
            if type(field) == DateField:
                data['__' + self.prefix + get_variable_name(field.name) + '__'] = getattr(
                    self.instance, field.name) if getattr(self.instance, field.name) else None
            else:
                data['__' + self.prefix +
                     get_variable_name(field.name) + '__'] = getattr(self.instance, field.name)

        for properti in self.properties:
            value = getattr(self.instance, properti)
            if type(value) == DateField:
                data['__' + self.prefix +
                     get_variable_name(properti) + '__'] = value if value else None
            else:
                data['__' + self.prefix +
                     get_variable_name(properti) + '__'] = value

        for method_field in self.Meta.method_fields:
            method = getattr(self, 'get_%s' %
                                   (method_field))
            method_value = method(self.kwargs)
            data['__' + self.prefix +
                 get_variable_name(method_field) + '__'] = method_value

        return data


class EmployeeAdapterMixin(VariableAdapter):

    def __init__(self, *args, **kwargs):
        self.get_fiscal_month_from_date = functools.lru_cache(
            self.get_fiscal_month_from_date)
        self.get_fiscal_months_between_date_range = functools.lru_cache(
            self.get_fiscal_months_between_date_range)

        self._get_children_count_for_age_range = functools.lru_cache(
            get_children_count_for_age_range
        )
        self._get_payroll_increments = functools.lru_cache(
            self._get_payroll_increments
        )
        self._get_current_step = functools.lru_cache(self._get_current_step)
        super().__init__(*args, **kwargs)

    def set_dynamic_attributes(self):
        for var, start, end in get_employee_age_variables():
            def fn(obj):
                self._get_children_count_for_age_range(
                    obj['instance'],
                    start,
                    end
                )

            setattr(
                self,
                f"get_{var}",
                fn
            )

    def get_all_children_count(self, obj):
        return self._get_children_count_for_age_range(obj['instance'])

    def get_fiscal_month_from_date(self, date_, organization):
        fy = FiscalYear.objects.active_for_date(
            organization=organization, date_=date_)
        if not fy:
            return None
        return fy.fiscal_months.filter(start_at__lte=date_, end_at__gte=date_).first()

    def get_fiscal_months_between_date_range(
        self, date1, date2, organization, include_partial=False
    ):
        if include_partial:
            date_filter = (
                Q(start_at__lte=date1, end_at__gte=date1)  # partial beginning
                | Q(start_at__gt=date1, end_at__lt=date2) |  # complete
                Q(start_at__lte=date2, end_at__gte=date2)  # partial end
            )
        else:
            date_filter = Q(start_at__gt=date1, end_at__lt=date2)

        return FiscalYearMonth.objects.filter(
            fiscal_year__category=GLOBAL,
            fiscal_year__organization=organization
        ).filter(date_filter).count()

    @staticmethod
    def _get_payroll_increment_qs(obj):
        employee = obj.get('instance')
        package_assigned_date = obj.get('package_assigned_date') or get_today()
        payroll_to_date = obj.get('payroll_to_date')
        return employee.payroll_increments.filter(
            effective_from__gte=package_assigned_date,
            effective_from__lte=payroll_to_date
        ).order_by('effective_from')

    def _get_payroll_increments(self, **obj):
        qs = self._get_payroll_increment_qs(obj)
        return list(
            qs.values_list(
                'percentage_increment', flat=True
            )
        )

    def _get_current_step(self, **obj):
        from_date = obj.get('payroll_from_date')
        to_date = obj.get('payroll_to_date')
        employee = obj.get('instance')

        return employee.first_date_range_user_experiences(
            from_date,
            to_date
        ).current_step

    def get_current_step(self, obj):
        return self._get_current_step(**obj)

    @staticmethod
    def get_yos(obj):
        employee = obj.get('instance')
        payroll_to_date = obj.get('payroll_to_date')
        return ((payroll_to_date - employee.detail.joined_date).days + 1) / 365

    def get_mos(self, obj):
        employee = obj.get('instance')
        payroll_to_date = obj.get('payroll_to_date')
        joined_date = employee.detail.joined_date
        organization = employee.detail.organization

        return self.most_between_dates(joined_date, payroll_to_date, organization)

    def most_between_dates(self, joined_date, payroll_to_date, organization):
        rd = relativedelta(payroll_to_date, joined_date)
        if rd.years >= 1:
            # no further calculation required, as this value will not be used for calculating
            return rd.years * 12 + rd.months
        start_fiscal_month = self.get_fiscal_month_from_date(
            joined_date, organization)
        end_fiscal_month = self.get_fiscal_month_from_date(
            payroll_to_date, organization)
        complete_months_in_between = self.get_fiscal_months_between_date_range(
            joined_date, payroll_to_date, organization
        )
        if not (start_fiscal_month and end_fiscal_month):
            # if fiscal month is not present in the beginning,
            return rd.months + (rd.days / 30)
        if start_fiscal_month == end_fiscal_month:
            worked_days_in_first_month = (
                payroll_to_date - joined_date).days + 1
            total_days_in_first_month = (
                start_fiscal_month.end_at - start_fiscal_month.start_at
            ).days + 1
            first_month_portion = worked_days_in_first_month / total_days_in_first_month
            last_month_portion = 0

        else:
            days_between_joined_date_and_end_first_month = (
                start_fiscal_month.end_at - joined_date
            ).days + 1
            days_in_first_month = (
                start_fiscal_month.end_at - start_fiscal_month.start_at
            ).days + 1
            first_month_portion = days_between_joined_date_and_end_first_month / days_in_first_month

            days_between_to_date_and_last_month_start_date = (
                payroll_to_date - end_fiscal_month.start_at
            ).days + 1

            days_in_last_month = (
                end_fiscal_month.end_at - end_fiscal_month.start_at
            ).days + 1

            last_month_portion = days_between_to_date_and_last_month_start_date / days_in_last_month
        return first_month_portion + complete_months_in_between + last_month_portion

    def get_months_doj_to_fy_ceil(self, obj):
        employee = obj.get('instance')
        payroll_to_date = obj.get('payroll_to_date')
        joined_date = employee.detail.joined_date
        organization = employee.detail.organization

        end_fiscal_month = self.get_fiscal_month_from_date(
            payroll_to_date, organization)

        if not end_fiscal_month:
            return 0
        fy = end_fiscal_month.fiscal_year

        return self.get_fiscal_months_between_date_range(
            joined_date,
            fy.end_at,
            organization,
            include_partial=True
        )

    def get_months_doj_to_fy(self, obj):
        employee = obj.get('instance')
        payroll_to_date = obj.get('payroll_to_date')
        joined_date = employee.detail.joined_date
        organization = employee.detail.organization

        end_fiscal_month = self.get_fiscal_month_from_date(
            payroll_to_date, organization)

        if not end_fiscal_month:
            return 0
        fy = end_fiscal_month.fiscal_year

        return self.most_between_dates(joined_date, fy.end_at, organization)

    def get_payroll_increment_multiplier(self, obj):

        increments = self._get_payroll_increments(**obj)
        if not increments:
            return 1

        return reduce(
            lambda x, y: x * (1 + y / 100),
            itertools.chain([1], increments)
        )

    def get_recent_payroll_increment_percentage(self, obj):
        increments = self._get_payroll_increments(**obj)
        if increments:
            return increments[-1]
        return 0

    @staticmethod
    def get_employment_level(obj):
        employee = obj.get('instance')
        return nested_getattr(employee, 'detail.employment_level.title')


class EmployeeConditionalVariableAdapter(EmployeeAdapterMixin, VariableAdapter):
    """
    Adapters for including extra variables to the calculator

    Meta
    ----
    Inner class that defines available variables
    It can have following attributes

    -- fields
        Iterable consisting collection of fields in Employee Model
    -- properties
        Iterable consisting collection of fields which are properties of Employee Model
    -- method_fields
        Iterable consisting list of fields, whose get_{field} method must be defined in
        adapter. It will be provided a argument context, which will be a dictionary containing
        `instance`, `payroll_from_date` and `payroll_to_date`
        For Eg.

        def get_adapter(context): ...

        context example:

            {
                instance': <User: John Doe>,
                'payroll_from_date': datetime.date(2020, 1, 3),
                'payroll_to_date': datetime.date(2020, 1, 31)
            }
    """
    class Meta:
        fields = ()
        properties = ('marital_status', 'id')
        method_fields = ['current_step', 'gender', 'has_disabilities', 'yos', 'mos', 'nationality',
                         'recent_payroll_increment_percentage', 'months_doj_to_fy',
                         'months_doj_to_fy_ceil', 'all_children_count', 'employment_level'
                         ] + [var[0] for var in get_employee_age_variables()]

    @staticmethod
    def get_gender(obj):
        employee = obj.get('instance')
        return employee.detail.gender

    @staticmethod
    def get_employment_level(obj):
        employee = obj.get('instance')
        return nested_getattr(employee, 'detail.employment_level.title')

    @staticmethod
    def get_has_disabilities(obj):
        employee = obj.get('instance')
        return str(
            employee.medical_info.disabilities.exists() if hasattr(
                employee, 'medical_info') else False
        )

    @staticmethod
    def get_nationality(obj):
        employee = obj.get('instance')
        return employee.detail.nationality


class EmployeeRuleVariableAdapter(EmployeeAdapterMixin, VariableAdapter):
    class Meta:
        fields = ()
        properties = ()
        method_fields = ['current_step', 'yos', 'mos', 'payroll_increment_multiplier',
                         'recent_payroll_increment_percentage', 'months_doj_to_fy',
                         'months_doj_to_fy_ceil', 'all_children_count', 'employment_level'
                         ] + [var[0] for var in get_employee_age_variables()]


class NoEmployeeConditionalVariableAdapter(EmployeeConditionalVariableAdapter):
    # Adapter for no employee salary calculator, it gets PreEmployment as input

    def get_current_step(self, obj):
        # Because obj will be PreEmployment Instance
        return self.instance.step

    def get_gender(self, obj):
        return self.instance.gender

    def get_employment_level(self, obj):
        return nested_getattr(self.instance, 'employment_level.title')

    @staticmethod
    def get_has_disabilities(obj):
        return False

    @staticmethod
    def get_yos(obj):
        return 1

    @classmethod
    def get_mos(cls, obj):
        return 12

    def get_months_doj_to_fy(self, obj):
        return 12

    def get_months_doj_to_fy_ceil(self, obj):
        return 12

    @staticmethod
    def get_nationality(obj):
        return "Nepalese"

    def get_payroll_increment_multiplier(self, obj):
        return 1

    def get_recent_payroll_increment_percentage(self, obj):
        return 0

    def set_dynamic_attributes(self):
        for var, start, end in get_employee_age_variables():
            setattr(
                self,
                f"get_{var}",
                lambda x: 0
            )

    def get_all_children_count(self, obj):
        return 0


class NoEmployeeRuleVariableAdapter(EmployeeRuleVariableAdapter):
    # Adapter for no employee salary calculator, it gets PreEmployment as input

    def get_current_step(self, obj):
        # Because obj will be PreEmployment Instance
        return self.instance.step

    def get_employment_level(self, obj):
        return nested_getattr(self.instance, 'detail.employment_level.title')

    @staticmethod
    def get_yos(obj):
        return 1

    @classmethod
    def get_mos(cls, obj):
        return 12

    @classmethod
    def get_months_doj_to_fy(cls, obj):
        return 12

    @classmethod
    def get_months_doj_to_fy_ceil(cls, obj):
        return 12

    def get_payroll_increment_multiplier(self, obj):
        return 1

    def get_recent_payroll_increment_percentage(self, obj):
        return 0

    def set_dynamic_attributes(self):
        for var, start, end in get_employee_age_variables():
            setattr(
                self,
                f"get_{var}",
                lambda x: 0
            )

    def get_all_children_count(self, obj):
        return 0


class AvailabilityQueryHelper(object):
    def __init__(
            self,
            from_date,
            to_date,
            from_date_name,
            to_date_name):
        # Overlapping partially from left
        self.a = Q(**{'{0}__lt'.format(from_date_name): from_date})
        self.b = Q(**{'{0}__gt'.format(to_date_name): from_date})
        self.c = Q(**{'{0}__lt'.format(from_date_name): to_date})
        self.d = Q(**{'{0}__lte'.format(to_date_name): to_date})
        # End Overlapping partially from left

        # Overlapping partially from right
        self.e = Q(**{'{0}__lt'.format(from_date_name): to_date})
        self.f = Q(**{'{0}__gt'.format(to_date_name): to_date})
        self.g = Q(**{'{0}__gte'.format(from_date_name): from_date})
        self.h = Q(**{'{0}__gt'.format(to_date_name): from_date})
        # End Overlapping partially from right

        # Overlapping whole
        self.i = Q(**{'{0}__gte'.format(from_date_name): from_date})
        self.j = Q(**{'{0}__lt'.format(from_date_name): to_date})
        self.k = Q(**{'{0}__lte'.format(to_date_name): to_date})
        self.l = Q(**{'{0}__gt'.format(to_date_name): from_date})
        # End Overlapping whole

        # Engulfed
        self.m = Q(**{'{0}__lt'.format(from_date_name): from_date})
        self.n = Q(**{'{0}__gt'.format(to_date_name): from_date})
        self.o = Q(**{'{0}__lt'.format(from_date_name): to_date})
        self.p = Q(**{'{0}__gt'.format(to_date_name): to_date})
        # End Engulfed


class InvalidVariableTypeOperation(Exception):
    def __init__(self, message, employee, package_heading):
        super().__init__(message)

        self.employee = employee
        self.package_heading = package_heading


def get_days_to_be_paid(user: Employee, start: date, end: date,
                        include_non_working_days: bool = False,
                        count_offday_holiday_as_worked: bool = False):
    worked_days = get_worked_days(
        user, start, end,
        include_non_working_days=include_non_working_days,
        count_offday_holiday_as_worked=count_offday_holiday_as_worked
    )
    if include_non_working_days:
        return worked_days

    # Non holiday paid leaves
    # Leave can exist in Holidays/Off-day if holiday inclusive so considering workdays only
    paid_leave_days = get_paid_leave_days(user, start, end, is_workday=True)

    return worked_days + paid_leave_days


def get_last_payroll_generated_date(user):
    return nested_getattr(
        user.employee_payrolls.order_by(
            '-payroll__to_date'
        ).first(),
        'payroll.to_date'
    )


def get_last_payroll_generated_date_excluding_rejected_payroll(user):
    from irhrs.payroll.models import REJECTED
    payroll = user.employee_payrolls.exclude(payroll__status=REJECTED).order_by(
            '-payroll__to_date'
        ).first()
    if payroll and payroll.payroll.simulated_from:
        return nested_getattr(payroll, 'payroll.simulated_from')
    return nested_getattr(payroll, 'payroll.to_date')


def get_last_confirmed_payroll_generated_date(user):
    return nested_getattr(
        user.employee_payrolls.order_by(
            '-payroll__to_date'
        ).filter(payroll__status=CONFIRMED).first(),
        'payroll.to_date'
    )


def get_last_payroll_generated_date_excluding_simulated(user):
    last_payroll = user.employee_payrolls.order_by(
        '-payroll__to_date'
    ).first()
    if last_payroll:
        if last_payroll.payroll.simulated_from:
            return last_payroll.payroll.simulated_from - timedelta(days=1)
        else:
            return last_payroll.payroll.to_date
    return None


def get_appoint_date(employee, payroll_start_fiscal_year):
    first_fiscal_year_start_date = payroll_start_fiscal_year.start_fiscal_year.applicable_from

    ue_on_first_fiscal_year_start_date = employee.first_date_range_user_experiences(
        first_fiscal_year_start_date,
        first_fiscal_year_start_date
    )

    if ue_on_first_fiscal_year_start_date:
        return first_fiscal_year_start_date
    else:
        user_experience = employee.user_experiences.filter(
            start_date__gt=first_fiscal_year_start_date
        ).order_by('start_date').first()
        return user_experience.start_date if user_experience else None


def get_dismiss_date(employee, user_experience):
    get_dismiss_date_from_last_working_date = getattr(
        settings, 'GET_DISMISS_DATE_FROM_LAST_WORKING_DATE',
        False
    )
    if get_dismiss_date_from_last_working_date:
        return employee.detail.last_working_date
    else:
        user_experiences = employee.user_experiences.filter(
            start_date__gte=user_experience.start_date
        ).order_by('start_date')

        dismiss_date = getattr(user_experience, 'end_date', None)

        for index, user_experience in enumerate(user_experiences):
            try:
                if user_experiences[index].end_date == user_experiences[
                    index + 1
                ].start_date - timedelta(days=1):
                    dismiss_date = user_experiences[index + 1].end_date
                else:
                    break
            except IndexError:
                pass
        return dismiss_date


def create_payroll_edit_remarks(employee_payroll, edited_packages, remarks, **kwargs):
    from irhrs.payroll.models import EmployeePayrollHistory, PayrollEditHistoryAmount

    create_kwargs = dict()
    if kwargs.get('created_by'):
        create_kwargs['created_by'] = kwargs.get('created_by')

    history = EmployeePayrollHistory.objects.create(
        employee_payroll=employee_payroll,
        remarks=remarks,
        **create_kwargs
    )

    for heading_id, amounts in edited_packages.items():
        old, new = amounts
        PayrollEditHistoryAmount.objects.create(
            old_amount=old,
            new_amount=new,
            heading_id=heading_id,
            payroll_history=history
        )


def advance_salary_queryset(user):
    from irhrs.payroll.models import AdvanceSalaryRequest
    return AdvanceSalaryRequest.objects.filter(
        recipient=user
    )


def get_advance_salary_stats(user):
    return advance_salary_queryset(user).aggregate(
        total=Count('id'),
        pending=Count('id', filter=Q(status=REQUESTED))
    )


def get_advance_salary(user):
    queryset = advance_salary_queryset(user)
    stats = queryset.aggregate(
        All=Count('id'),
        Requested=Count('id', filter=Q(status=REQUESTED)),
        Approved=Count('id', filter=Q(status=APPROVED)),
        Denied=Count('id', filter=Q(status=DENIED)),
        Repayment=Count('id', filter=Q(status=REPAYMENT)),
        Completed=Count('id', filter=Q(status=COMPLETED)),
        Canceled=Count('id', filter=Q(status=CANCELED)),
    )
    from irhrs.payroll.api.v1.serializers.advance_salary_request import \
        AdvanceSalaryRequestListSerializer
    return queryset, stats, AdvanceSalaryRequestListSerializer
