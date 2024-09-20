import os
from django.core.management.base import BaseCommand
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from django.conf import settings

BASE_PATH = settings.PROJECT_DIR
PRIVATE_KEY_ABSOLUTE_PATH = os.path.join(
    BASE_PATH,
    'key-files/private_key.pem'
)
PUBLIC_KEY_ABSOLUTE_PATH = os.path.join(
    BASE_PATH,
    'key-files/public_key.pem'
)

class Command(BaseCommand):
    help = 'Generates rsa key pair for authentication'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-check',
            action='store_true',
            help="Skip check",
            default=True
        )
        parser.add_argument(
            '--regenerate',
            action='store_true',
            help="Force regenerate keys. Default behavior is to skip creation if found.",
        )

    def handle(self, *args, **options):
        regenerate = options.get('regenerate')
        if os.path.isfile(PRIVATE_KEY_ABSOLUTE_PATH) and not regenerate:
            self.stdout.write("private_key.pem found inside key-files  [skipping]")
        else:
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )

            private_key_bytes = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )

            with open(PRIVATE_KEY_ABSOLUTE_PATH, 'wb') as f:
                f.write(private_key_bytes)
            self.stdout.write("stored private_key.pem inside key-files [complete]")

        if os.path.isfile(PUBLIC_KEY_ABSOLUTE_PATH) and not regenerate:
            self.stdout.write("public_key.pem found inside key-files   [skipping]")
        else:
            public_key = private_key.public_key()
            public_key_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            with open(PUBLIC_KEY_ABSOLUTE_PATH, 'wb') as f:
                f.write(public_key_bytes)
            self.stdout.write("stored public_key.pem inside key-files   [complete]")
