from django.db.models import Q

from django.contrib.auth import get_user_model

from irhrs.payroll.models import (
    PayrollVariablePlugin,
    Heading,
    PackageHeading
)

from irhrs.payroll.utils.helpers import (
    EmployeeConditionalVariableAdapter,
    EmployeeRuleVariableAdapter
)

from irhrs.payroll.internal_plugins.registry import (
    REGISTERED_INTERNAL_CALCULATOR_PLUGIN_VARS,
    REGISTERED_INTERNAL_CALCULATOR_PLUGIN_FXNS,
    REGISTERED_INTERNAL_CALCULATOR_PLUGIN_FXNS_ARGS_VALIDATORS
)

Employee = get_user_model()


class CalculatorVariable:
    def __init__(
        self,
        organization_slug,
        heading=None,
        package_heading=None,
        order=None,
        current_duration_unit=None,
        current_heading_type=None,
        package=None
    ):
        self.organization_slug = organization_slug
        self._heading = heading
        self._package_heading = package_heading
        self._order = order

        self._current_duration_unit = current_duration_unit
        self._current_heading_type = current_heading_type
        self._package = package

        

        assert (
            self.heading or (self._order is not None) 
        ), 'Either (package) heading or heading props are required'

    @property
    def heading(self):
        return self._heading or self._package_heading

    @property
    def order(self):
        return self.heading.order if self.heading else self._order

    @property
    def current_duration_unit(self):
        return self.heading.duration_unit if self.heading else self._current_duration_unit

    @property
    def current_heading_type(self):
        return self.heading.type if self.heading else self._current_heading_type

    @property
    def possible_heading_dependents_queryset(self):
        
        if self.heading:
            if self._package_heading:
                return PackageHeading.objects.filter(
                    package=self._package_heading.package,
                    order__lt=self.order
                )

        else:
            if self._package:
                 return PackageHeading.objects.filter(
                    package=self._package,
                    order__lt=self.order
                )

        return Heading.objects.filter(
            organization__slug=self.organization_slug,
            order__lt=self.order
        )

    @staticmethod
    def calculator_variable_name_from_heading_name(name, *suffixes):
        var_name = '_'.join(name.upper().split(' '))
        suffix = ''.join(suffixes)
        var_name += suffix
        return f'__{var_name}__'

    def get_organization_registered_plugins(self):
        return PayrollVariablePlugin.objects.filter(
            organization__slug=self.organization_slug
        )

    def get_scoped_dependent_headings(self):
        """Excludes scoped (ie less than self order headings) Addition/Deduction 
        type heading if self heading is also of Addition/Deduction type. 
        
        We do so because calculator proportionates the rule value based 
        on the propotion of worked days to total working 
        days in a month. Thus, when the heading of type Addition/Deduction 
        is directly dependent on Addition/Deduction type the dependent value in 
        self heading gets double proportionate.
        """

        exclude_query_condition = Q()

        TYPES_WITH_DURATION_UNIT = [
            'Addition',
            'Deduction'
        ]

        if (
            self.current_heading_type in TYPES_WITH_DURATION_UNIT
        ):
            exclude_query_condition = Q(
                Q(type__in=TYPES_WITH_DURATION_UNIT)
            )

        return self.possible_heading_dependents_queryset.exclude(
            exclude_query_condition
        )

    @classmethod
    def get_calculator_headings_variable(cls, headings):
        return [
            cls.calculator_variable_name_from_heading_name(
                heading.name
            ) for heading in headings
        ]

    @staticmethod
    def get_static_variables():
        return [
            "__ANNUAL_GROSS_SALARY__",
            '__YTD__',
            '__SLOT_DAYS_COUNT__',
            '__REMAINING_DAYS_IN_FY__',
            '__REMAINING_MONTHS_IN_FY__'
        ]

    @staticmethod
    def get_registered_methods():
        return REGISTERED_INTERNAL_CALCULATOR_PLUGIN_FXNS.keys()
    
    @staticmethod
    def get_registered_method_validators():
        return REGISTERED_INTERNAL_CALCULATOR_PLUGIN_FXNS_ARGS_VALIDATORS

    @staticmethod
    def get_employee_rule_variables():
        return EmployeeRuleVariableAdapter(
            'EMPLOYEE_',
            model=Employee
        ).generate_variables_only()

    @staticmethod
    def get_employee_conditional_variables():
        return EmployeeConditionalVariableAdapter(
            'EMPLOYEE_',
            model=Employee
        ).generate_variables_only()

    @staticmethod
    def merge_variables(set_a, set_b):
        set_a = set(set_a)
        set_b = set(set_b)

        assert (
            set_a.isdisjoint(set_b)
        ), 'Variables are duplicated while aggregating from different source'

        return set.union(
            set_a,
            set_b
        )

    @classmethod
    def get_all_calculator_variables(cls, organization_slug):
        union = cls.merge_variables

        variables = set()

        variables = union(
            variables,
            cls.get_static_variables()
        )

        variables = union(
            variables,
            # Use union instead of set.union TODO @wrufesh
            # That make functions like common, rule_only and condition only
            set.union(
                set(cls.get_employee_conditional_variables()),
                set(cls.get_employee_rule_variables())
            )
        )


        organization_headings = Heading.objects.filter(
            organization__slug=organization_slug
        )

        variables = union(
            variables,
            cls.get_calculator_headings_variable(organization_headings)
        )

        organization_plugins = PayrollVariablePlugin.objects.filter(
            organization__slug=organization_slug
        )

        variables = union(
            variables,
            cls.get_calculator_headings_variable(organization_plugins)
        )

        # Internal plugins
        variables = union(
            variables,
            REGISTERED_INTERNAL_CALCULATOR_PLUGIN_VARS.keys()
        )

        return variables

    def get_heading_scoped_variables(self, conditional=False):
        cls = self.__class__
        union = cls.merge_variables
        variables = set()

        variables = union(
            variables,
            cls.get_static_variables()
        )

        if conditional:
            variables = union(
                variables,
                cls.get_employee_conditional_variables()
            )
        else:
            variables = union(
                variables,
                cls.get_employee_rule_variables()
            )
        

        scoped_headings = self.get_scoped_dependent_headings()

        variables = union(
            variables,
            cls.get_calculator_headings_variable(scoped_headings)
        )

        registered_plugins = self.get_organization_registered_plugins()

        variables = union(
            variables,
            cls.get_calculator_headings_variable(registered_plugins)
        )

        # Internal plugins
        variables = union(
            variables,
            REGISTERED_INTERNAL_CALCULATOR_PLUGIN_VARS.keys()
        )

        return variables
