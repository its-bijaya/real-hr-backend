from django.apps import AppConfig


class CommonConfig(AppConfig):
    name = 'irhrs.common'

    def ready(self):
        from django.contrib.staticfiles.management.commands.runserver import (
            Command as DjangoRunserver,
        )
        from .management.commands.runserver import Command

        DjangoRunserver.__bases__ = (Command,)
