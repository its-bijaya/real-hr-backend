import json

from django.db.models import Count, Q
from django.conf import settings
from django.http.response import HttpResponse

from rest_framework.views import APIView
from rest_framework.permissions import BasePermission

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

from irhrs.users.models import User
from irhrs.organization.models import Organization


class FernetKeyAuthentication(BasePermission):
    """
    Allows access to those having the fernet generated key.
    """

    def has_permission(self, request, view):
        HTTP_APP_KEY = request.META.get('HTTP_APP_KEY')
        if not HTTP_APP_KEY:
            return False
        fernet_key = settings.FERNET_KEY
        fer = Fernet(fernet_key)
        DECRYPTED_APP_KEY = fer.decrypt(bytes(HTTP_APP_KEY, 'utf-8'))
        if DECRYPTED_APP_KEY == settings.FERNET_KEY:
            return True


class IsKnownPublicKey(BasePermission):
    def has_permission(self, request, view):
        public_key_raw = request.headers.get(
            'Portal-Public-Key')
        if not public_key_raw:
            return False
        public_key_raw = public_key_raw.replace("\\n", "\n")
        with open('key-files/authorized_keys.json') as authorized_keys:
            known_keys = json.load(authorized_keys)

        print(public_key_raw)

        if public_key_raw and public_key_raw in known_keys:
            public_key = serialization.load_pem_public_key(
                public_key_raw.encode(),
                backend=default_backend()
            )
            view.public_key = public_key

            return True
        return False


class ExtractForPortal(APIView):
    """
    API to extract the data for portal
    """
    permission_classes = (IsKnownPublicKey,)
    authentication_classes = []

    def get(self, request):
        users_data = User.objects.exclude(email=settings.SYSTEM_BOT_EMAIL).aggregate(
            total=Count('pk'),
            active=Count('pk', filter=Q(is_active=True)),
            inactive=Count('pk', filter=Q(is_active=False))
        )
        organizations = Organization.objects.all().count()
        response_text = json.dumps({
            'users': users_data,
            'organizations': organizations
        })

        cypher_text = self.public_key.encrypt(
            response_text.encode(),
            padding=padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return HttpResponse(cypher_text, content_type='application/octet-stream')
