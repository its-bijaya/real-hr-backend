from django.apps import AppConfig


class PermissionConfig(AppConfig):
    name = 'irhrs.permission'

    def ready(self):
        from . import signals
        super().ready()
