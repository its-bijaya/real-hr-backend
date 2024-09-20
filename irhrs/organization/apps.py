from django.apps import AppConfig


class OrganizationConfig(AppConfig):
    name = 'irhrs.organization'

    def ready(self):
        from . import signals
