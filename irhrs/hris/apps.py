from django.apps import AppConfig


class HrisConfig(AppConfig):
    name = 'irhrs.hris'

    def ready(self):
        from . import signals
