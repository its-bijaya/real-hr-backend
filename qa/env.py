# LOCAL SETTINGS

from .local import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'qarhrs',
        'USER': 'qa',
        'PASSWORD': 'qapass',
        'HOST': 'localhost',
        'PORT': '5432',
    }
    # ADMS_SERVER: {
    #     'ENGINE': 'django.db.backends.mysql',
    #     'NAME': 'aayulogic',
    #     'USER': '',
    #     'PASSWORD': '',
    #     'HOST': '',
    #     'PORT': '',
    #     'OPTIONS': {'isolation_level': None}
    # }
}

ALLOWED_HOSTS = [ '*']
CORS_ORIGIN_ALLOW_ALL = True

STATIC_ROOT = "/dj-static/"
MEDIA_ROOT = "/dj-media/"

Q_CLUSTER['timeout'] = 60*60*24