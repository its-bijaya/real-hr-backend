from base64 import b64encode

from django.utils.crypto import get_random_string

chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
SECRET_KEY = get_random_string(50, chars)
print("*"*65)
print("Secret Key:", SECRET_KEY)
print("*"*65)
SECRET_KEY_DUPLICATE = SECRET_KEY * 32  # Fernet requires 32 length key.
FERNET_KEY = b64encode(SECRET_KEY_DUPLICATE.encode()[:32])
print("FERNET KEY:", FERNET_KEY)
print("*"*65)