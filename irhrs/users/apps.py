from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'irhrs.users'

    def ready(self):
        from . import signals
