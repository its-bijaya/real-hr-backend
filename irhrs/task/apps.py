from django.apps import AppConfig


class TaskConfig(AppConfig):
    name = 'irhrs.task'

    def ready(self):
        from . import signals
