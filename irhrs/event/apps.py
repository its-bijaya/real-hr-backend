from django.apps import AppConfig


class EventConfig(AppConfig):
    name = 'irhrs.event'

    def ready(self):
        from . import signals
