from django.apps import AppConfig


class OpenidConfig(AppConfig):
    name = 'irhrs.openid'

    def ready(self):
        from .checks import (
            check_secret_key_pair_dev,
            check_secret_key_pair_deploy
        )
