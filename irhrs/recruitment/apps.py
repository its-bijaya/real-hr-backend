from django.apps import AppConfig


class RecruitmentConfig(AppConfig):
    name = 'irhrs.recruitment'

    def ready(self):
       from . import signals
