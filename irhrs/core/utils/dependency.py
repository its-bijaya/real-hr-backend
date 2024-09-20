"""@irhrs_docs"""
from irhrs.core.constants.dependencies import DEPENDENCIES
from django.apps import apps
from importlib import import_module


def get_dependency(dependency: str):
    """
    get dependency function from DEPENDENCIES

    :param dependency: dependency name from irhrs.core.constants.dependencies.DEPENDENCIES
    :return: dependency function or function returning default values, status
    :raises KeyError: When dependency is not found in DEPENDENCIES.keys()
    :raises AttributeError: When module does not have given function_name
    :raises ModuleNotFoundError: When module is not found



    **Usage**

    Suppose we have DEPENDENCIES defined as

    .. code-block:: python

        DEPENDENCIES = {
            'attendance.utils.payroll.get_adjustment_request_status_summary': (
                'irhrs.attendance',
                'irhrs.attendance.utils.payroll.get_adjustment_request_status_summary',
                {
                    "pending": 0,
                    "approved": 0,
                    "forwarded": 0
                }
            )
        }

    Then we call

    .. code-block:: python

        from irhrs.core.utils.dependency import get_dependency
        fn, installed = get_dependency('attendance.utils.payroll.get_adjustment_request_status_summary')

    If `irhrs.attendance` is not installed then a fn that returns

    .. code-block:: python

        {
            "pending": 0,
            "approved": 0,
            "forwarded": 0
        }

    and installed  will be `False`

    .. code-block:: python

        fn, False

    If the app is installed then it will look for function `get_adjustment_request_status_summary` in
    `irhrs.attendance.utils.payroll`  and return the function if found.

    .. code-block:: python

        fn, True

    """
    app_name, path, default = DEPENDENCIES[dependency]

    # If app not found return a function that returns the default value
    if not apps.is_installed(app_name):
        def fn(*args, **kwargs):
            return default
        return fn, False

    splits = path.split('.')
    function_name = splits[-1]
    module_path = ".".join(splits[0: -1])

    module = import_module(module_path)
    return getattr(module, function_name), True
