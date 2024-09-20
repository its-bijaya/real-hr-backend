from .registry import register_plugin


@register_plugin('example-plugin-one')
def example_plugin1(calculator, package_heading):
    print('START_____________OUTPUT FROM TEST PLUGIN  1_____________')

    print(calculator.employee, package_heading, calculator.from_date, calculator.to_date)

    print('END_____________OUTPUT FROM TEST PLUGIN_____________')

    return 100, [
        dict(
            model_name="XYZ",
            instance_id=2,
            url=""
        )
    ]


@register_plugin('example-plugin-two')
def example_plugin2(calculator, package_heading):
    """
    :calculator -> takes runtime calculator for  finding out employee, fy, from_date, end_date.
    :package_heading -> parent package under which we register our plugin.
    `register_plugin` registers the heading name defined in the decorator.

    This function expects two values, i.e, `amount` and `sources`, to be returned.
    `amount` is the total_amount for that particular heading.
    `sources` provides information about the amount that is being calculated.
    """
    print('START_____________OUTPUT FROM TEST PLUGIN  2_____________')

    print(calculator.employee, package_heading, calculator.from_date, calculator.to_date)

    print('END_____________OUTPUT FROM TEST PLUGIN_____________')

    return 200, [
        dict(
            model_name="XYZ",
            instance_id=2,
            url=""
        )
    ]


def args_validator(fxn_args, equation_validator):
    """
    :fxn_args -> argument(s) that is sent along with function heading
    example:
    __PAYROLL_HEADING__('Payroll Args')
    Here, __PAYROLL_HEADING__ is function heading and  `Payroll Args` is argument.
    We can send more arguments according to our needs.

    :equation_validator -> validates equation from the run-time calculator
    Additionally, we can extract data such as `model`, `heading`, `package_heading` from it
    For more info visit : rule_validator.py

    argument in arguments should always be either integer or string.
    handles all the validation related to function heading.
    This function expects list of error to be returned.
    """

    errors = []

    if not isinstance(fxn_args[0], str):
        errors.append('First argument should be string')

    if not isinstance(fxn_args[1], int):
        errors.append('Second argument should be integer')

    return errors


@register_plugin('example-fxn-one', is_func=True, args_validator=args_validator)
def example_fxn_plugin(calculator, package_heading):
    """
    :calculator -> takes runtime calculator for  finding out employee, fy, from_date, end_date.
    :package_heading -> parent package under which we register our plugin.
    `register_plugin` registers the heading name defined in the decorator.
    This function expects two values, i.e, `amount` and `sources`, to be returned.
    :is_func -> boolean field to specify where it is functional plugin or non-functional plugin.

    Here, `example-fxn-one` is function_name which will be represented as `EXAMPLE_FXN_ONE`
    and the `fxn_args` from `args_validator` will be arguments for above function.

    This function expects function to be returned.
    """
    def fxn(a_string, a_integer):
        """
        :*headings -> function arguments for `args_validator` function. Can be one heading or many.
        `a_string`, `a_integer` are some of examples for headings arguments

        This function expects two values, i.e, `amount` and `sources`, to be returned.
        `amount` is the total_amount for that particular heading.
        `sources` provides information about the amount that is being calculated.
        """
        return 200, [
            dict(
                model_name="XYZ",
                instance_id=2,
                url=""
            )
        ]
    return fxn
