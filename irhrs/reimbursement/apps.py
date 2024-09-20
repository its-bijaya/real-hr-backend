from django.apps import AppConfig


class ReimbursementConfig(AppConfig):
    name = 'irhrs.reimbursement'

    def ready(self):
       from . import signals
