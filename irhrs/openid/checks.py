import logging
from django.core.checks import Tags, register, Critical
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

logger = logging.getLogger(__name__)


def check_secret_key_pair():
    errors = []
    try:
        with open("./key-files/private_key.pem", "rb") as key_file:
            serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )
        with open("./key-files/public_key.pem", "rb") as key_file:
            serialization.load_pem_public_key(
                key_file.read(),
                backend=default_backend()
            )

    except Exception:
        logger.error(
            "Private, Public key pair is invalid or not present.", exc_info=True)
        errors.append(
            Critical(
                "Private, Public key pair is invalid or not present.",
                hint="Generate using `./manage.py generate_rsa_keys",
                id="openid"
            )
        )

    return errors


@register(Tags.compatibility, deploy=True)
def check_secret_key_pair_deploy(app_configs, **kwargs):
    return check_secret_key_pair()


@register(Tags.compatibility)
def check_secret_key_pair_dev(app_configs, **kwargs):
    return check_secret_key_pair()
