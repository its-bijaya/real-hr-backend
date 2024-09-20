"""Utils required for testing"""
from unittest.mock import patch


def disable_notification(decorated):

    with patch('irhrs.notification.utils.add_notification', return_value=None):

        if isinstance(decorated, type):
            return_value = type(f"{decorated.__name__}Decorated", (decorated,), {})
        else:
            def return_value(*x, **y): return decorated(*x, **y)

        return return_value


def disable_organization_notification(decorated):
    with patch('irhrs.notification.utils.notify_organization', return_value=None):

        if isinstance(decorated, type):
            return_value = type(f"{decorated.__name__}Decorated", (decorated,), {})
        else:
            def return_value(*x, **y):
                return decorated(*x, **y)

        return return_value
