import json
import regex
from json import JSONDecodeError

from django.db.models import Q

from irhrs.payroll.utils.calculator_variable import CalculatorVariable
from irhrs.payroll.models.payroll import EXTRA_DEDUCTION, EXTRA_ADDITION

from irhrs.payroll.constants import FXN_CAPTURING_REGEX

class Equation(object):

    def __init__(self, *args, **kwargs):
        self.heading = kwargs.get('heading')
        self.equation = kwargs.get('equation')
        self.operators = kwargs.get('operators')
        self.available_variables = args[0]
        self.used_variables = set()
        self.error_messages = []
        self.fxn_regex = FXN_CAPTURING_REGEX

    def __repr__(self):
        return self.equation

    def __str__(self):
        return self.equation

    def validate_syntax_and_symbol_availability(self):
        errors = []
        local_scope = dict()

        for variable in self.available_variables:
            local_scope[variable] = 5.5

        for func_name in CalculatorVariable.get_registered_methods():
            def dummy_func(*args):
                return 5.5
            local_scope[func_name] = dummy_func

        try:
            equation_code = compile(self.equation, "<string>", "eval")

            local_scope_symbol_set = set(local_scope.keys())

            equation_used_symbol_set = set(equation_code.co_names)


            if not equation_used_symbol_set.issubset(local_scope_symbol_set):

                not_defined_variables = list(
                    equation_used_symbol_set - local_scope_symbol_set
                )

                errors.append(
                    f'{not_defined_variables}: Symbols not available'
                )

        except Exception as err:
            errors.append(err.args[0])

        if not errors:
            try:
                evaluated_value = eval(
                    equation_code,
                    {'__builtins__': {}},
                    local_scope
                )

                if not isinstance(evaluated_value, (int, float)):
                    errors.append("Arguments are required for functions.")
            except Exception as err:
                errors.append(err.args[0])

        return errors

    def check_if_function_has_function_arguments(self):
        errors = []

        equation = self.equation
        matches = regex.finditer(self.fxn_regex, equation)

        for match in matches:
            equation = equation.replace(match.group(), 'replaced_string')

        matches = regex.finditer(self.fxn_regex, equation)

        if any(True for _ in matches):
            errors.append('Argument as function not supported')
        return errors


    def filter_float(self, data):
        if regex.search(
            regex.compile('^(\\-|\\+)?([0-9]+(\\.[0-9]+)?|Infinity)$'),
            data
        ):
            return float(data)
        else:
            return None

    @property
    def is_valid(self):
        return not self.error_messages

    def validate_used_function_arguments(self):
        errors = []
        matches = regex.finditer(self.fxn_regex, self.equation)
        function_strings = set([match.group() for match in matches])

        for function_string in function_strings:
            function_name = regex.findall(r'[A-Z0-9_]+?(?=\()', function_string)[0]
            args_string = regex.findall(r'[A-Z0-9_]+(.*)', function_string)[0][1:-1]

            args = regex.findall(
                r"\s*('[^'\\]*'|\"[^\"\\]*\"|\d+(?:\.\d*)?|\w+(?:\(\w*\))?)",
                args_string
            )

            if not args:
                errors.append('At least one argument is required.')
                break

            if  not errors:
                try:
                    args = [eval(arg, {'__builtins__': {}}, {}) for arg in args]
                except:
                    errors.append('Only string and numerical arguments are supported')
                    break

            if not errors:
                errors += CalculatorVariable.get_registered_method_validators()[
                    function_name
                ](args, self)

                if errors:
                    break

        return errors

    def set_used_variables(self):
        rgx = '|'.join(self.available_variables)

        used_variables = set(
            regex.findall(rgx, self.equation)
        )
        self.used_variables.update(used_variables)

    def validate(self):
        self.error_messages = self.validate_syntax_and_symbol_availability()

        if not self.error_messages:
           self.error_messages += self.check_if_function_has_function_arguments()

        if not self.error_messages:
            self.error_messages += self.validate_used_function_arguments()

        if not self.error_messages:
            self.set_used_variables()


class RuleEquation(Equation):
    def __init__(self, *args, **kwargs):
        kwargs['operators'] = ['+', '-', '*', '/', '^', '(', ')']
        super().__init__(*args, **kwargs)
        # import ipdb
        # ipdb.set_trace()
        self.rule_validator = kwargs.get('rule_validator')
        self.validate()

    # def operand_check(self, opernd, variables):
    #     # if true then rule is invalid
    #     if opernd in self.available_variables:
    #         self.used_variables.append(opernd)
    #     elif re.match(r"0+\d+$", opernd):
    #         # if value is of type 00001 then python raises Syntax error
    #         return True

    #     return (opernd not in variables) and (
    #         not (self.filter_float(opernd) == 0 or self.filter_float(opernd))
    #     )

    def validate(self):
        super().validate()
        if self.is_valid and self.rule_validator and (
                self.rule_validator.get('numberOnly')):
            rule_value = self.filter_float(self.equation)
            if not (isinstance(rule_value, float) or isinstance(rule_value, int)):
                err_msg = 'Please provide float type input'
                if err_msg not in self.error_messages:
                    self.error_messages.append(err_msg)
            if self.rule_validator.get('hasRange'):
                if (self.rule_validator.get('min') and self.rule_validator.get('max')) and (
                    self.filter_float(self.rule_validator.get('min')) and self.filter_float(
                        self.rule_validator.get('max'))
                ):
                    if (rule_value < self.filter_float(self.rule_validator.get('min'))) or (
                            rule_value > self.filter_float(self.rule_validator.get('max'))):
                        err_msg = 'Number out of given range'
                        if err_msg not in self.error_messages:
                            self.error_messages.append(err_msg)
                else:
                    err_msg = 'Please provide minimum and maximum range.'
                    if err_msg not in self.error_messages:
                        self.error_messages.append(err_msg)


class ConditionEquation(Equation):
    def __init__(self, *args, **kwargs):
        kwargs['operators'] = [
            '<=', '>=', '>', '<',
            'and', 'or', 'not',
            '==', '!=', '+', '-', '*',
            '/', '^', '(', ')'
        ]
        super().__init__(*args, **kwargs)
        self.validate()

    # def operand_check(self, opernd, variables):
    #     if opernd in self.available_variables:
    #         self.used_variables.append(opernd)
    #     return re.search(
    #         re.compile('^".*"$'),
    #         opernd
    #     ) and (
    #         opernd not in variables
    #     ) and (
    #         not (self.filter_float(opernd) == 0 or self.filter_float(opernd))
    #     )


class ConditionalRule(object):
    def __init__(self, *args, **kwargs):
        self.condition_equation = kwargs.get('condition_equation', None)
        self.rule_equation = kwargs.get('rule_equation')
        # self.is_tds = kwargs.get('is_tds')
        # self.tds_type = kwargs.get('tds_type')
        # self.tds_errors = []
        self.condition_equation_errors = []
        self.rule_equation_errors = []
        self.used_variables = []
        self.is_valid = True
        self.validity_check()
        self.set_used_variables()

    def __repr__(self):
        return "condition:%s -- rule:%s" % (
            str(self.condition_equation),
            str(self.rule_equation)
        )

    def __str__(self):
        return "condition:%s -- rule:%s" % (
            str(self.condition_equation),
            str(self.rule_equation)
        )

    def validity_check(self):
        # if self.is_tds:
        #     if str(self.tds_type).strip() in [None, '']:
        #         self.is_valid = False
        #         self.tds_errors = ["TDS Type is required"]
        #     elif len(str(self.tds_type)) > 50:
        #         self.is_valid = False
        #         self.tds_errors = ["Maximum number of characters allowed for TDS Type is 50"]


        if self.condition_equation is None:
            self.is_valid = self.rule_equation.is_valid and self.is_valid
            self.rule_equation_errors = self.rule_equation.error_messages
        else:
            self.valid = (
                self.rule_equation.is_valid and
                self.condition_equation.is_valid and
                self.is_valid
            )
            self.rule_equation_errors = self.rule_equation.error_messages
            self.condition_equation_errors = self.condition_equation.error_messages

    def set_used_variables(self):
        if self.condition_equation is None:
            self.used_variables = set(
                self.rule_equation.used_variables
            )
        else:
            self.used_variables = set(
                self.condition_equation.used_variables + self.rule_equation.used_variables
            )


class HeadingRuleValidator(object):
    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs
        self.heading = kwargs.get('heading')
        # self.latest_tax_deduction_heading = None
        # self.oldest_addition_or_deduction_heading = None
        self.possible_dependent_headings = list()
        self.actual_dependent_headings = list()
        # self.variables = self.get_variables()
        self.rule_variables = self.get_variables(False)
        self.conditional_variables = self.get_variables(True)
        self.rules = self.get_rules()  # ConditionalRule List
        # self.error_messages = self.get_error_messages()
        self.used_variables = self.get_used_variables()
        self.set_actual_dependent_heading()
        self.is_valid, self.error_messages = self.validity_check()

    def get_used_variables(self):
        data = []
        for rule in self.rules:
            data += rule.used_variables
        return list(set(data))

    def set_actual_dependent_heading(self):
        data = []
        for heading in self.possible_dependent_headings:
            if (
                CalculatorVariable.calculator_variable_name_from_heading_name(
                    self.get_heading_name(heading)
                )
            ) in self.used_variables:
                data.append(heading)
        self.actual_dependent_headings = data

    def get_heading_name(self, heading):
        if heading.__class__.__name__ == 'Heading':
            return heading.name
        elif heading.__class__.__name__ == 'PackageHeading':
            return heading.heading.name

    def get_oldest_non_taxable_deduction(self):
        filter_kwargs = dict(
            type='Deduction',
            taxable=False
        )
        if self.heading.__class__.__name__ == 'Heading':
            filter_kwargs['organization'] = self.heading.organization
        elif self.heading.__class__.__name__ == 'PackageHeading':
            filter_kwargs['package'] = self.heading.package

        return self.heading.__class__.objects.filter(
            **filter_kwargs
        ).order_by('-order').first()

    def get_oldest_taxable_addition(self):
        filter_kwargs = dict(
            type='Addition',
            taxable=True
        )
        if self.heading.__class__.__name__ == 'Heading':
            filter_kwargs['organization'] = self.heading.organization
        elif self.heading.__class__.__name__ == 'PackageHeading':
            filter_kwargs['package'] = self.heading.package

        return self.heading.__class__.objects.filter(
            **filter_kwargs
        ).order_by('-order').first()

    def get_latest_tax_deduction(self):
        filter_kwargs = dict(
            type='Tax Deduction'
        )
        if self.heading.__class__.__name__ == 'Heading':
            filter_kwargs['organization'] = self.heading.organization
        elif self.heading.__class__.__name__ == 'PackageHeading':
            filter_kwargs['package'] = self.heading.package

        return self.heading.__class__.objects.filter(
            **filter_kwargs
        ).order_by('-order').first()

    def get_variables(self, is_conditional=True):

        organization = self.heading.organization if self.heading.__class__.__name__ == 'Heading' else self.heading.package.organization

        calculator_variable = CalculatorVariable(
            organization.slug,
            heading=self.heading if self.heading.__class__.__name__ == 'Heading' else None,
            package_heading=self.heading if self.heading.__class__.__name__ == 'PackageHeading' else None
        )

        self.possible_dependent_headings = calculator_variable.get_scoped_dependent_headings()

        variables_set = calculator_variable.get_heading_scoped_variables(conditional=is_conditional)
        return list(variables_set)

    def get_cleaned_rules_list(self):
        if type(self.heading.rules) == str:
            try:
                return json.loads(self.heading.rules)
            except JSONDecodeError:
                # empty rules will raise error
                return []
        
        return self.heading.rules

    # def _get_tax_slab_kwarg(self, rule):
    #     if self._is_tds():
    #         return {'tds_type': rule.get('tds_type'), 'is_tds': True}
    #     return {'is_tds': False}

    # def _is_tds(self):
    #     return self.heading.type == 'Tax Deduction'

    def get_rules(self):
        output_rules = []
        rule_list = self.get_cleaned_rules_list()
        if len(rule_list) > 1:
            for rule in rule_list:
                output_rules.append(
                    ConditionalRule(
                        conditional_equation=ConditionEquation(
                            self.conditional_variables,
                            equation=rule.get('condition'),
                            heading=self.heading
                        ),
                        rule_equation=RuleEquation(
                            self.rule_variables,
                            equation=rule.get('rule'),
                            rule_validator=rule.get('rule_validator'),
                            heading=self.heading
                        )
                        # **self._get_tax_slab_kwarg(rule)
                    )
                )
        elif len(rule_list) == 1:
            output_rules.append(
                ConditionalRule(
                    conditional_equation=None,
                    rule_equation=RuleEquation(
                        self.rule_variables,
                        equation=rule_list[0].get('rule'),
                        rule_validator=rule_list[0].get('rule_validator'),
                        heading=self.heading
                    )
                    # **self._get_tax_slab_kwarg(rule_list[0])
                )
            )

        return output_rules

    def validity_check(self):
        valid = True
        errors = []
        non_field_error = None

        #  START Addition/Deduction heading cannot be dependent on Addition/Deduction heading
        dependent_heading_types = [
            head.type for head in self.actual_dependent_headings]
        if self.heading.type in ['Addition', 'Deduction'] and (
            any(x in dependent_heading_types for x in [
                'Addition', 'Deduction'])
        ):
            valid = False
            non_field_error = 'Addition/Deduction type heading cannot be dependent of Addition/Deduction type heading'

        #  START Addition/Deduction heading cannot be dependent on Addition/Deduction heading

        # import ipdb
        # ipdb.set_trace()
        # >= comparison for fake order is compared with actual order of latest_tax_deduction_heading

        latest_tax_deduction_heading = self.get_latest_tax_deduction()

        non_field_error, valid = self.validate_tax_deduction_order(
            heading=self.heading,
            latest_tax_deduction_heading_order=getattr(latest_tax_deduction_heading, 'order', None),
            oldest_taxable_addition_order=getattr(self.get_oldest_taxable_addition(), 'order', None),
            oldest_non_taxable_deduction_order=getattr(self.get_oldest_non_taxable_deduction(), 'order', None),
        )

        if not self.rules:
            non_field_error = 'Invalid Rule.'
            valid = False

        for rule in self.rules:
            errors.append(
                {
                    'condition_equation_errors': rule.condition_equation_errors,
                    'rule_equation_errors': rule.rule_equation_errors
                }
            )
            if not rule.is_valid:
                valid = False
                non_field_error = 'Invalid Rule.'
        return valid, {
            'errors': errors,
            'non_field_errors': non_field_error
        }

    @staticmethod
    def validate_tax_deduction_order(
        heading,
        latest_tax_deduction_heading_order,
        oldest_taxable_addition_order,
        oldest_non_taxable_deduction_order,
    ):
        non_field_error = None
        valid = True
        if latest_tax_deduction_heading_order is not None and (
            (
                heading.taxable and heading.type in ('Addition', EXTRA_ADDITION, EXTRA_DEDUCTION)
            ) or (
                not heading.taxable and heading.type == 'Deduction'
            )
        ) and heading.order >= latest_tax_deduction_heading_order:
            non_field_error = 'Tax impacting headings cannot be after Tax Deduction heading'

            valid = False

        if oldest_taxable_addition_order is not None and heading.type == 'Tax Deduction' and (
            (
                heading.order <= oldest_taxable_addition_order
            )
        ):
            non_field_error = 'Tax Deduction cannot be before tax impacting headings'
            valid = False

        if oldest_non_taxable_deduction_order is not None and heading.type == 'Tax Deduction' and (
            (
                heading.order <= oldest_non_taxable_deduction_order
            )
        ):
            non_field_error = 'Tax Deduction cannot be before tax impacting headings'
            valid = False

        return non_field_error, valid


    # def get_error_messages(self):
    #     errors = []
    #     non_field_errors = []
    #     for rule in self.rules:
    #         errors.append(
    #             {
    #                 'condition_equation_errors': rule.condition_equation_errors,
    #                 'rule_equation_errors': rule.rule_equation_errors
    #             }
    #         )
    #     return errors
