from django.apps import AppConfig


class PayrollConfig(AppConfig):
    name = 'irhrs.payroll'

    def ready(self):
        from . import signals
