from django.apps import AppConfig


class BuilderConfig(AppConfig):
    name = 'irhrs.builder'

    def ready(self):
        # System checks
        from .checks import report_builder_stability  # NOQA
