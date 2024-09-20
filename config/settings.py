from config.hacks import *
import itertools
import logging
import os
import sys
from dotenv import load_dotenv
from corsheaders.defaults import default_headers
from datetime import timedelta
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from PIL import ImageFile

load_dotenv()

ImageFile.LOAD_TRUNCATED_IMAGES = True

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


ROOT_DIR = os.path.dirname(PROJECT_DIR)

APPS_DIR = os.path.join(PROJECT_DIR, 'irhrs')

BASE_DIR = os.path.join(PROJECT_DIR, 'config')

DEBUG = eval(os.environ.get('DEBUG', 'False'))

SQL_MIDDLEWARE_OUTPUT = eval(os.environ.get('SQL_MIDDLEWARE_OUTPUT', 'False'))

DJANGO_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
)

THIRD_PARTY_APPS = (
    'corsheaders',
    'rest_framework',
    'django_q',
    'django_filters',
    'django_extensions',
    'sorl.thumbnail',
    'cuser',
    'channels',
    'import_export',
    'oauth2_provider',
    # rangefilter for django admin customization
    'rangefilter',
)

PROJECT_APPS = (
    'irhrs.portal',
    'irhrs.common',
    'irhrs.users',
    'irhrs.organization',
    'irhrs.document',
    'irhrs.notification',
    'irhrs.noticeboard',
    'irhrs.permission',
    'irhrs.hrstatement',
    'irhrs.help',
    'irhrs.hris',
    'irhrs.export',
    'irhrs.attendance',
    'irhrs.leave',
    'irhrs.task',
    'irhrs.event',
    'irhrs.websocket',
    'irhrs.payroll',
    'irhrs.builder',
    'irhrs.worklog',
    'irhrs.openid',
    'irhrs.recruitment',
    'irhrs.reimbursement',

    # Merge ADMS into iRealHRSoft
    'irhrs.questionnaire',

    'irhrs.assessment',
    'irhrs.training',
    'irhrs.appraisal',
    'irhrs.forms',
)

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + PROJECT_APPS

if DEBUG:
    INSTALLED_APPS += (
        'debug_toolbar',
        # 'rest_framework_swagger'
    )


MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'irhrs.openid.utils.middleware.CookieRefreshTokenAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'cuser.middleware.CuserMiddleware',
    'oauth2_provider.middleware.OAuth2TokenMiddleware',
    'irhrs.core.middlewares.base.CurrentMethodMiddleware',
]

if DEBUG:
    MIDDLEWARE += (
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    )

    if SQL_MIDDLEWARE_OUTPUT:
        MIDDLEWARE += [
            'config.middleware.SQLPrintingMiddleware.SqlPrintingMiddleware',
        ]

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(APPS_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n'
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

TIME_ZONE = 'Asia/Kathmandu'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static Files Configuration
STATICFILES_DIRS = (
    os.path.join(APPS_DIR, 'static'),
)
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

DEFAULT_STATIC_ROOT = os.path.join(ROOT_DIR, 'static/')
STATIC_ROOT = os.environ.get('STATIC_ROOT', DEFAULT_STATIC_ROOT)
STATIC_URL = '/static/'

DEFAULT_MEDIA_ROOT = os.path.join(ROOT_DIR, 'media/')
MEDIA_ROOT = os.environ.get('MEDIA_ROOT', DEFAULT_MEDIA_ROOT)
MEDIA_URL = '/media/'

FIXTURE_DIRS = (
    os.path.join(APPS_DIR, 'fixtures'),
)

# /Static Files Configuration

AUTH_USER_MODEL = 'users.User'

LANGUAGES = (
    ('en', _('English')),
    ('ne', _('Nepali')),
)

LANGUAGE_CODE = 'en'

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)


CORS_ALLOW_HEADERS = default_headers + (
    'Accept-Confirm',
)

ASGI_APPLICATION = 'config.routing.application'


# https://docs.djangoproject.com/en/2.1/ref/settings/#data-upload-max-memory-size
DATA_UPLOAD_MAX_MEMORY_SIZE = 10*1024*1024  # 10 MB

PAYROLL_CALENDAR = 'BS'

PASSWORD_RESET_TIMEOUT_DAYS = 2 / 24  # 2 hours

# Max Acceptable Image Size in Megabytes
# irhrs.core.validators.validate_image_size
MAX_IMAGE_SIZE = int(os.environ.get('MAX_IMAGE_SIZE', 7))
MAX_FILE_SIZE = int(os.environ.get('MAX_FILE_SIZE', 7))

ACCEPTED_FILE_FORMATS = {
    'documents': ['doc', 'docx', 'odt', 'pdf', 'xls', 'xlsx', 'ods', 'ppt',
                  'pptx', 'txt', 'tif', 'tiff', 'jif', 'jfif', 'jp2', 'jpx', 'j2k',
                  'j2c', 'fpx', 'pcd', 'psd', 'rtf'],
    'images': ['gif', 'jpeg', 'jpg', 'png']
}

ACCEPTED_FILE_FORMATS_LIST = ACCEPTED_FILE_FORMATS['documents'] + \
    ACCEPTED_FILE_FORMATS['images']

default_renderer_classes = [
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
]

# Rest Framework Config
DRF_RENDERER_CLASSES = ['rest_framework.renderers.JSONRenderer']
DRF_AUTH_CLASSES = [
    'irhrs.core.utils.authentication.CustomSimpleJWTAuthentication',
    'rest_framework.authentication.SessionAuthentication'
]

DRF_BROWSABLE_API = eval(os.environ.get('DRF_BROWSABLE_API', 'False'))

if DRF_BROWSABLE_API:
    DRF_RENDERER_CLASSES.append('rest_framework.renderers.BrowsableAPIRenderer')
# End Rest Framework Config

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': DRF_AUTH_CLASSES,
    'DEFAULT_PAGINATION_CLASS': 'irhrs.core.pagination.LimitZeroNoResultsPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'DEFAULT_RENDERER_CLASSES': DRF_RENDERER_CLASSES
}

# AUTHENTICATION_BACKENDS = (
#     'oauth2_provider.backends.OAuth2Backend',
# )

MIN_USER_AGE = 16
MAX_USER_AGE = 99

# Number of hours to wait on off days for punch_out of
# previous work_day before declaring missing punch out
OFFDAY_PUNCHOUT_WAITING_TIME = 3


MAX_ORGANIZATION_COUNT = int(os.getenv('MAX_ORGANIZATION_COUNT', 4))
MAX_USERS_COUNT = int(os.getenv('MAX_USERS_COUNT', 500))

FERNET_KEY = b'ZmZezWVtKQRv4pUcVP1xpaub9nQ-SE14II2wIvLkmcE='

USE_MULTIPROCESSING = eval(os.getenv('USE_MULTIPROCESSING', 'False'))

Q_CLUSTER_SYNC = eval(os.getenv('Q_CLUSTER_SYNC', 'False'))
Q_CLUSTER_AFFINITY = int(os.environ.get('Q_CLUSTER_AFFINITY', 1))

# for qcluster configuration
# https://django-q.readthedocs.io/en/latest/configure.html
Q_CLUSTER = {
    'name': 'irhrs',
    'workers': 8,
    'recycle': 500,
    'timeout': int(os.environ.get('Q_CLUSTER_TIMEOUT', 60*15)),
    # retry value should be larger than timeout value
    'retry': int(os.environ.get('Q_CLUSTER_RETRY', 60*15 + 1)),
    'compress': True,
    'save_limit': 250,
    'queue_limit': 500,
    'cpu_affinity': Q_CLUSTER_AFFINITY,
    'label': 'Django Q',
    'redis': {
        'host': os.environ.get('Q_CLUSTER_REDIS_HOST', '127.0.0.1'),
        'port': int(os.environ.get('Q_CLUSTER_REDIS_PORT', '6379')),
        'db': int(os.environ.get('Q_CLUSTER_REDIS_DB', '0'))
    },
    'sync': Q_CLUSTER_SYNC,
    'daemonize_workers': eval(os.getenv('DAEMONIZE_WORKERS', 'True'))
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://{0}:{1}/{2}".format(
            os.environ.get('CACHES_REDIS_DB_HOST', Q_CLUSTER['redis']['host']),
            os.environ.get('CACHES_REDIS_DB_PORT', Q_CLUSTER['redis']['port']),
            os.environ.get('CACHES_REDIS_DB_NAME', '1')
        ),
        "TIMEOUT": os.environ.get('CACHE_TIMEOUT', '300'),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        },
    }
}

REDIS_DATABASE = {
    'host': os.environ.get('ATTENDENCE_DEVICE_SYNC_REDIS_DB_HOST', Q_CLUSTER['redis']['host']),
    'port': int(os.environ.get('ATTENDENCE_DEVICE_SYNC_REDIS_DB_PORT', Q_CLUSTER['redis']['port'])),
    'db': int(os.environ.get('ATTENDENCE_DEVICE_SYNC_REDIS_DB_NAME', '2'))
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(
                os.environ.get('CHANNEL_LAYER_REDIS_DB_HOST',
                               Q_CLUSTER['redis']['host']),
                int(os.environ.get('CHANNEL_LAYER_REDIS_DB_PORT',
                                   Q_CLUSTER['redis']['port'])),
            )],
        },
    },
}

# monkey patch Django ModelAdmin readonly_fields
# config/hacks.py

LOGIN_URL = os.environ.get('LOGIN_URL', 'rest_framework:login')
LOGOUT_URL = os.environ.get('LOGOUT_URL', 'rest_framework:logout')
LOGIN_REDIRECT_URL = os.environ.get('LOGOUT_URL', '/api/v1/')

OAUTH2_PROVIDER = {
    "OAUTH2_SERVER_CLASS": "irhrs.openid.utils.server.OIDCServer",
    "OAUTH2_VALIDATOR_CLASS": "irhrs.openid.utils.openid_request_validator.OpenIDRequestValidator",
    "SCOPES_BACKEND_CLASS": "irhrs.openid.utils.scopes.SettingsScopes"
}

OAUTH2_PROVIDER_APPLICATION_MODEL = 'openid.Application'
OAUTH2_PROVIDER_ACCESS_TOKEN_MODEL = 'openid.AccessToken'
OAUTH2_PROVIDER_GRANT_MODEL = 'openid.Grant'
OAUTH2_PROVIDER_REFRESH_TOKEN_MODEL = 'openid.RefreshToken'

THUMBNAIL_FORMAT = 'PNG'


SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Set Default Runner to Custom Runner.
TEST_RUNNER = 'irhrs.core.utils.test_runner.DiscoverSlowestTestsRunner'


SHOW_LOGS_ON_CONSOLE = False

SHELL_PLUS_PRE_IMPORTS = [
    ('django.db.models', '*'),
    ('django.db.models.functions', '*')
]


SECRET_KEY = os.environ.get('SECRET_KEY', 'HFJFHFUJKklhsalkjhslakdjgf88989898')


ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')

ADMS_SERVER = os.environ.get('ADMS_SERVER', 'adms_database')

USING_ADMS = eval(os.environ.get('USING_ADMS', 'False'))


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('DATABASE_NAME', None),
        'USER': os.environ.get('DATABASE_USER', None),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD', None),
        'HOST': os.environ.get('DATABASE_HOST', 'localhost'),
        'PORT': os.environ.get('DATABASE_PORT', '5432'),
    },
}

if os.environ.get('DATABASE_TEST_TEMPLATE'):
    DATABASES['default']['TEST'] = {
        'TEMPLATE': os.environ.get('DATABASE_TEST_TEMPLATE')}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

ADMS_DIRECT = os.environ.get('ADMS_DIRECT', 'adms_direct')

# Do not connect to ADMS database if running migrations
RUNNING_MIGRATION_COMMAND = 'migrate' in sys.argv
if RUNNING_MIGRATION_COMMAND and USING_ADMS:
    print('Disconnecting ADMS database before proceeding to migration!')
# End ADMS/Migration Interceptor

if USING_ADMS and not RUNNING_MIGRATION_COMMAND:
    DATABASES.update({
        ADMS_DIRECT: {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('ADMS_DIRECT_DATABASE_NAME', None),
            'USER': os.environ.get('ADMS_DIRECT_DATABASE_USER', None),
            'PASSWORD': os.environ.get('ADMS_DIRECT_DATABASE_PASSWORD', None),
            'HOST': os.environ.get('ADMS_DIRECT_DATABASE_HOST', 'localhost'),
            'PORT': os.environ.get('ADMS_DIRECT_DATABASE_PORT', '3306'),
            'OPTIONS': {'isolation_level': None}
        }
    })


FRONTEND_URL = os.environ.get('FRONTEND_URL', "http://localhost:3000")
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:8000')

EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.mailtrap.io')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '73d8bce4fc587e')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'a1aa090d71c40f')
EMAIL_PORT = os.environ.get('EMAIL_PORT', '2525')
DEFAULT_FROM_EMAIL = os.environ.get('EMAIL_HOST_USER', 'admin@realhrsoft.com')


INFO_EMAIL = os.environ.get('INFO_EMAIL', EMAIL_HOST_USER)

SYSTEM_BOT_EMAIL = os.environ.get('SYSTEM_BOT_EMAIL', 'info@realhrsoft.com')
SYSTEM_BOT_NAME = os.environ.get('SYSTEM_BOT_NAME', "RealHR Soft")
SYSTEM_BOT_PROFILE_IMAGE = os.environ.get(
    'SYSTEM_BOT_PROFILE_IMAGE', "logos/real-hr-leaf.png")

SYSTEM_NAME = os.environ.get('SYSTEM_NAME', "RealHRSoft")

THUMBNAIL_DEBUG = eval(os.environ.get('THUMBNAIL_DEBUG', 'False'))


CORS_ORIGIN_ALLOW_ALL = eval(os.environ.get('CORS_ORIGIN_ALLOW_ALL', 'False'))

INTERNAL_IPS = eval(os.environ.get('INTERNAL_IPS', "['127.0.0.1', ]"))

ALLOW_PAST_REQUESTS_FOR_PRE_APPROVAL = eval(
    os.environ.get('ALLOW_PAST_REQUESTS_FOR_PRE_APPROVAL', 'False'))

REQUIRE_PRE_APPROVAL_CONFIRMATION = eval(
    os.environ.get('REQUIRE_PRE_APPROVAL_CONFIRMATION', 'False'))

WEEK_START_DAY = int(os.environ.get('WEEK_START_DAY', 1))

ATTENDANCE_API_KEY = os.environ.get('ATTENDANCE_API_KEY', '')

INITIAL_EMPLOYEE_CODE = os.environ.get('INITIAL_EMPLOYEE_CODE', 'EMP')

SHOW_INVISIBLE_LEAVE_BALANCE = eval(
    os.environ.get('SHOW_INVISIBLE_LEAVE_BALANCE', 'False'))

try:
    with open("./key-files/private_key.pem", "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )
    with open("./key-files/public_key.pem", "rb") as key_file:
        public_key = serialization.load_pem_public_key(
            key_file.read(),
            backend=default_backend()
        )
    algorithm = 'RS256'
except:
    print("Private, Public key pair not found. Generate using `./manage.py generate_rsa_keys`")
    private_key = SECRET_KEY
    public_key = None
    algorithm = 'HS256'

# Begin Access/Refresh Token Config
ACCESS_TOKEN_LIFETIME = os.environ.get('ACCESS_TOKEN_LIFETIME', '6;hours')
REFRESH_TOKEN_LIFETIME = os.environ.get('REFRESH_TOKEN_LIFETIME', '7;days')

def generate_timedelta(td_string):
    try:
        _duration, _type = td_string.split(';')
        return timedelta(**{_type: int(_duration)})
    except (ValueError, TypeError):
        raise ValueError(f"{td_string} is invalid. use 5;minutes OR 30;days format")

ACCESS_TOKEN_VALUE = generate_timedelta(ACCESS_TOKEN_LIFETIME)
REFRESH_TOKEN_VALUE = generate_timedelta(REFRESH_TOKEN_LIFETIME)
# End Access/Refresh Token Config

# Simple JWT Config
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': ACCESS_TOKEN_VALUE,
    'REFRESH_TOKEN_LIFETIME': REFRESH_TOKEN_VALUE,
    'ROTATE_REFRESH_TOKENS': True,

    'ALGORITHM': algorithm,
    'SIGNING_KEY': private_key,
    'VERIFYING_KEY': public_key,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}
# /Simple JWT Config ends

INVALIDATE_TOKEN_ON_REFRESH = False  # Expire old tokens after refresh

# LOGGING FORMATS AND CONFIGURATIONS
LOG_DIRECTORY = os.path.join(
    PROJECT_DIR if ENVIRONMENT == 'development' else ROOT_DIR,
    'logs'
)
if not os.path.exists(LOG_DIRECTORY):
    os.mkdir(LOG_DIRECTORY)

extend_logging = dict()
extend_handlers = dict()

OPENID_LOGIN_URL = '/account/login/'


class RequireConsoleLog(logging.Filter):
    def filter(self, record):
        allowed_site_packages = ('django', 'rest_framework')
        if 'site-packages' in record.pathname:
            return any([x in record.pathname for x in allowed_site_packages])
        return SHOW_LOGS_ON_CONSOLE


for module in PROJECT_APPS:
    extend_logging.update({
        module: {
            'handlers': [module],
            'propagate': False,
        }
    })
    extend_handlers.update({
        module: {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'formatter': 'verbose',
            'filename': os.path.join(
                LOG_DIRECTORY, module.split('.')[1] + '.log'
            ),
            'when': 'midnight',
        }
    })

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '\n%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s',
        },
        'simple': {
            'format': '{levelname} {message} -->from [{module}]',
            'style': '{'
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_console_log': {
            '()': RequireConsoleLog
        }
    },
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(LOG_DIRECTORY, 'debug.log'),
            'formatter': 'verbose',
            'when': 'midnight',
        },
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true', 'require_console_log'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'django': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIRECTORY, 'django.log'),
            'formatter': 'verbose',
        },
        'database': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIRECTORY, 'database.log'),
            'formatter': 'verbose',
        },
        **extend_handlers
    },
    'loggers': {
        '': {
            'handlers': ['default', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django': {
            'handlers': ['django'],
            'propagate': True,
        },
        'sorl.thumbnail': {
            'handlers': ['default'],
            'propagate': False
        },
        'django.db.backends': {
            'handlers': ['database'],
            'propagate': False,
        },
        'django.db.backends.schema': {
            'handlers': ['database'],
            'propagate': False,
        },
        **extend_logging
    },
}


GIFT_CARD_CONFIG = {
    # The fonts and images are to be placed at: irhrs/static/samples
    "anniversary": {
        "event": "anniversary",
        # Dimension of image template: 2296 x 1092
        "template": "anniversary.jpg",
        # This message will be posted on noticeboard as title. Not inside image.
        "message": f"Happy Work Anniversary! Thank you for your hard work, your "
                   f"generosity, and your contagious enthusiasm.",
        "thumbnail": {
            "position": [1850, 175],  # co-ordinate
            "width": 250  # radius
        },
        "alignment": "right",  # text-alignment
        # config for user's name
        "name": {
            "font_size": 40,
            "color": [59, 103, 94],  # RGB
            "coordinates": [2080, 440],
            "font": "montserrat.ttf"
        },
        # /config for user's name
        "anniversary_wish": {
            "font_size": 100,
            "color": [59, 103, 94],  # RGB
            "coordinates": [2080, 495],
            "font": "kaushanScript.ttf"
        },
        "texts": []
    },
    "birthday": {
        "event": "birthday",
        # Dimensions of the template image: 2296 x 1092
        "template": os.getenv('BIRTHDAY_BACKGROUND_IMAGE', 'birthday.png'),
        # This message will be posted on noticeboard as title. Not inside image.
        "message": "On Your Special Day :)",
        "thumbnail": {
            "position": [1850, 80],
            "width": 290
        },
        "alignment": "center",
        "name": {
            "font_size": 50,
            "color": eval(os.getenv('BIRTHDAY_TEXT_COLOR', '[255, 255, 255]')),
            "coordinates": [1150, 150],
            "font": "montserrat.ttf"
        },
        # This message will be inside image.
        "texts": [
            {
                "font_size": 50,
                "color": eval(os.getenv('BIRTHDAY_TEXT_COLOR', '[255, 255, 255]')),
                "coordinates": [1150, 525],
                "font": "montserrat.ttf",
                "title": "Wishing you all the best on this day and everyday!"
            }
        ]
    },
    "welcome": {
        "event": "welcome",
        # Dimension of image template: 2296 x 1092
        "template": "welcome.jpeg",
        # This message will be posted on noticeboard as title. Not inside image.
        "message": "We are delighted to have you among us. On behalf of all the members and the"
                   " management, we would like to extend our warmest welcome and good wishes!",
        "thumbnail": {
            "position": [1850, 90],  # co-ordinate
            "width": 250  # radius
        },
        "alignment": "right",  # text-alignment
        # config for user's name
        "name": {
            "font_size": 40,
            "color": [59, 103, 94],  # RGB
            "coordinates": [2080, 340],
            "font": "montserrat.ttf"
        },
        "job_title": {
            "font_size": 30,
            "color": [59, 103, 94],  # RGB
            "coordinates": [2080, 400],
            "font": "montserrat.ttf"
        },
        "division": {
            "font_size": 30,
            "color": [59, 103, 94],  # RGB
            "coordinates": [2080, 450],
            "font": "montserrat.ttf"
        },
        "employment_level": {
            "font_size": 30,
            "color": [59, 103, 94],  # RGB
            "coordinates": [2080, 500],
            "font": "montserrat.ttf"
        },
        "organization": {
            "font_size": 30,
            "color": [59, 103, 94],  # RGB
            "coordinates": [2080, 550],
            "font": "montserrat.ttf"
        },
        "texts": [
            {
                "font_size": 90,
                "color": [59, 103, 94],  # RGB
                "coordinates": [2080, 610],
                "font": "kaushanScript.ttf",
                "title": "Welcome To The Family!"
            },
            {
                "font_size": 50,
                "color": [59, 103, 94],  # RGB
                "coordinates": [2080, 750],
                "font": "montserrat.ttf",
                "title": "Wish you all the best for your work in upcoming days."
            },
            {
                "font_size": 50,
                "color": [59, 103, 94],  # RGB
                "coordinates": [2080, 810],
                "font": "montserrat.ttf",
                "title":  "We believe you will have a wonderful experience working here."
            },
        ]
    }
}

TEXT_FIELD_MAX_LENGTH = 600  # TEN THOUSAND

DAYS_BEFORE_NOTIFICATION = 15

ORGANIZATION_SPECIFIC_EMPLOYEE_DIRECTORY = True
# if organization_specific_employee_directory is set to false employee  from all organization
# are listed in employee directory

# Add notification to HR on Attendance and Leave Actions
SHADOW_NOTIFY_ORGANIZATION_OVERTIME = eval(os.environ.get('SHADOW_NOTIFY_ORGANIZATION_OVERTIME', 'False'))
SHADOW_NOTIFY_ORGANIZATION_TRAVEL_ATTENDANCE = eval(os.environ.get('SHADOW_NOTIFY_ORGANIZATION_TRAVEL_ATTENDANCE', 'False'))
SHADOW_NOTIFY_ORGANIZATION_ATTENDANCE_ADJUSTMENT = eval(os.environ.get('SHADOW_NOTIFY_ORGANIZATION_ATTENDANCE_ADJUSTMENT', 'False'))
SHADOW_NOTIFY_ORGANIZATION_CREDIT_REQUEST = eval(os.environ.get('SHADOW_NOTIFY_ORGANIZATION_CREDIT_REQUEST', 'False'))
SHADOW_NOTIFY_ORGANIZATION_LEAVE_REQUEST = eval(os.environ.get('SHADOW_NOTIFY_ORGANIZATION_LEAVE_REQUEST', 'False'))
# / End Shadow notification configurations.

# For travel expense
PER_DIEM_RATE = 0.75
LODGING_RATE = 1
OTHER_RATE = 1

EMAIL_BACKEND = "irhrs.core.utils.custom_mail.CustomEmailBackend"

# --- Timesheet Entry Method Options -----
# 'Device'
# 'Web App'
# 'Mobile App'
# 'RFID Card'
# 'Password'
# 'Att Adjustment'
# 'Travel Att'
# 'Other'
# 'Import'

DELETE_ALLOWED_TIMESHEET_ENTRY_METHODS = eval(
    os.environ.get('DELETE_ALLOWED_TIMESHEET_ENTRY_METHODS',
                   "['Web App', 'Mobile App', 'Travel Att', 'Att Adjustment']"))


ALLOWED_HOSTS = eval(os.environ.get('ALLOWED_HOSTS', '[]'))
DEPLOY_TARGET_HOST = os.environ.get('DEPLOY_TARGET_HOST')
if not ALLOWED_HOSTS and DEPLOY_TARGET_HOST:
    ALLOWED_HOSTS = [DEPLOY_TARGET_HOST]

# START: PAYROLL SETTINGS

PAYROLL_EXPORT_TITLE = eval(os.environ.get('PAYROLL_EXPORT_TITLE', '''
['MILLENNIUM CHALLENGE ACCOUNT NEPAL (MCA - NEPAL)',
    '(A Joint Initiative of the Government of Nepal and the',
    ' Millennium Challenge Corporation, USA)',
    'Kathmandu, Nepal',
]
'''))

# lifted from MCC
PAYROLL_NUMBER_FORMAT = os.environ.get(
    'PAYROLL_NUMBER_FORMAT', '[>0][$NPR] * #,##0.00 ;[<0][$NPR] * (#,##0.00);[$NPR] * -# ;" "@" "')

PAYROLL_HEADING_MAP = eval(os.environ.get('PAYROLL_HEADING_MAP', 'None'))

EMPLOYMENT_TYPE_ID_FOR_TAX_EXEMPT = eval(
    os.environ.get("EMPLOYMENT_TYPE_ID_FOR_TAX_EXEMPT", "[]"))

TAX_EXEMPT_FILTERS = (
    ~Q(employee__detail__employment_status__slug__in=EMPLOYMENT_TYPE_ID_FOR_TAX_EXEMPT),
    Q(employee__detail__employment_status__slug__in=EMPLOYMENT_TYPE_ID_FOR_TAX_EXEMPT)
)

# Setting to get dismiss date, defaults to False,
# By default it gets dismiss date from experience end date if set
# When set to True, dismiss date will be picked up from UserDetail.last_working_date
GET_DISMISS_DATE_FROM_LAST_WORKING_DATE = eval(
    os.environ.get('GET_DISMISS_DATE_FROM_LAST_WORKING_DATE', 'True'))


# When set to True, Tax fluctuation due to extra addition/deduction will be adjusted
# in same month.
ADJUST_TAX_CHANGE_DUE_TO_EXTRA_ADDITION_DEDUCTION_IN_SAME_MONTH = eval(
    os.environ.get(
        'ADJUST_TAX_CHANGE_DUE_TO_EXTRA_ADDITION_DEDUCTION_IN_SAME_MONTH',
        'False'
    )
)

# END: PAYROLL SETTINGS


TEA_BREAK, CLIENT_VISIT, LUNCH_BREAK, MEETING, PERSONAL, OTHERS = (
    'Tea Break', 'Client Visit', 'Lunch Break', 'Meeting', 'Personal Break', 'Others'
)
UNPAID_BREAK_TYPES = eval(
    os.environ.get('UNPAID_BREAK_TYPES', '(OTHERS, PERSONAL)')
)

PAYROLL_CHILDREN_COUNT_VARIABLE_AGE_RANGES = eval(
    os.environ.get(
        'PAYROLL_CHILDREN_COUNT_VARIABLE_AGE_RANGES',
        '[(0, 10), (10, 20), (20, 30), (30, 40), (40, 60), (60, 100)]'
    )
)

# By default, adjacent holiday/offday tests 7 days before start and 7 days after end.
ADJACENT_HOLIDAY_OFFDAY_INCLUSION_DAYS = int(
    os.environ.get('ADJACENT_HOLIDAY_OFFDAY_INCLUSION_DAYS', 7)
)

COMPENSATORY_LEAVE_CALCULATION_DURATION = int(
    os.environ.get('COMPENSATORY_LEAVE_CALCULATION_DURATION', 6 * 30)
)  # days

RESIGNATION_REQUEST_INACTION_EMAIL_AFTER_DAYS = int(
    os.environ.get('RESIGNATION_REQUEST_INACTION_EMAIL_AFTER_DAYS', 10)
)

GOOGLE_RECAPTCHA_PRIVATE_KEY = os.environ.get(
    'GOOGLE_RECAPTCHA_PRIVATE_KEY',
    "add google recaptcha private key"
)

CALCULATE_UNPAID_BREAKS_IN_INTERNAL_PLUGIN = eval(os.environ.get(
    'CALCULATE_UNPAID_BREAKS_IN_INTERNAL_PLUGIN',
    'True'
))

IGNORE_SECOND_IN_TOTAL_LOST_HOURS = eval(os.environ.get(
    'IGNORE_SECOND_IN_TOTAL_LOST_HOURS',
    'False'
))

GENERATE_PAYROLL_EVEN_IF_OVERTIME_EXISTS = eval(os.environ.get(
    'GENERATE_PAYROLL_EVEN_IF_OVERTIME_EXISTS',
    'False'
))

ROUND_LEAVE_BALANCE = eval(os.environ.get('ROUND_LEAVE_BALANCE', 'False'))

# BEGIN Sentry Configurations
# https://docs.sentry.io/platforms/python/guides/django/

SENTRY_DSN = os.environ.get('SENTRY_DSN', '')
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration()],
            server_name=BACKEND_URL,
        )
    except ImportError:
        raise ImportError("Sentry is not installed")

# END Sentry Configurations
