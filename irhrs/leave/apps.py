from django.apps import AppConfig


class LeaveConfig(AppConfig):
    name = 'irhrs.leave'

    def ready(self):
        from . import signals
