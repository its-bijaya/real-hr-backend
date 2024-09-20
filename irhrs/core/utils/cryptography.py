"""@irhrs_docs"""
import base64


from config import settings

Fernet = type('', (object,), {})

# Add `cryptography` if the below utils are to be used.
# from cryptography.fernet import Fernet
FERNET_ENCRYPT_KEY = getattr(settings, 'ENCRYPT_KEY', None)

def encrypt(txt):
    try:
        # convert integer etc to string first
        txt = str(txt)
        # get the key from settings
        cipher_suite = Fernet(FERNET_ENCRYPT_KEY)  # key should be byte
        # #input should be byte, so convert the text to byte
        encrypted_text = cipher_suite.encrypt(txt.encode('ascii'))
        # encode to urlsafe base64 format
        encrypted_text = base64.urlsafe_b64encode(encrypted_text).decode("ascii")
        return encrypted_text
    except Exception as e:
        # log the error if any
        return None


def decrypt(string):
    try:
        # base64 decode
        txt = base64.urlsafe_b64decode(string)
        cipher_suite = Fernet(FERNET_ENCRYPT_KEY)
        decoded_text = cipher_suite.decrypt(txt).decode("ascii")
        return decoded_text
    except Exception as e:
        # log the error
        return None
