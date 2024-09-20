from django.apps import AppConfig


class NoticeboardConfig(AppConfig):
    name = 'irhrs.noticeboard'

    def ready(self):
        from . import signals
