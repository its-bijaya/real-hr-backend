REGISTERED_INTERNAL_CALCULATOR_PLUGIN_VARS = dict()
REGISTERED_INTERNAL_CALCULATOR_PLUGIN_FXNS = dict()

REGISTERED_INTERNAL_CALCULATOR_PLUGIN_FXNS_ARGS_VALIDATORS = dict()

def register_plugin(plugin_name, is_func=False, args_validator=None):
    '''plugin function when decorated with this decorator and present in any proper 
    module will be marked as registered internal calculator plugin.
    '''
    from irhrs.payroll.utils.calculator_variable import CalculatorVariable

    plugin_name = plugin_name.replace('-', ' ')
    plugin_name = ' '.join(plugin_name.split())
    if not plugin_name.replace(' ', '').isalpha():
        raise AssertionError(
            'Only alphabetic characters are accepted'
        )

    variable = CalculatorVariable.calculator_variable_name_from_heading_name(
        plugin_name
    )

    if variable in REGISTERED_INTERNAL_CALCULATOR_PLUGIN_VARS.keys():
        raise AssertionError(
            'Internal calculator plugin with this name already  registered'
        )
    def wrapper(fxn):
        if is_func:
            REGISTERED_INTERNAL_CALCULATOR_PLUGIN_FXNS[variable] = fxn
            if args_validator:
                REGISTERED_INTERNAL_CALCULATOR_PLUGIN_FXNS_ARGS_VALIDATORS[variable] = args_validator

        else:
            REGISTERED_INTERNAL_CALCULATOR_PLUGIN_VARS[variable] = fxn
        return fxn
    return wrapper
