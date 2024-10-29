import datetime
import os
from inspect import getmembers, isfunction

from mainapp.jinja import global_functions

ENVIRONMENT = 'dev'
print(ENVIRONMENT)
DEBUG = True

SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data')


ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
]



INSTALLED_APPS = [
    'daphne',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sitemaps',
    'django_jinja',
    'django_extensions',
    'rest_framework',
    'channels',
    'mainapp.apps.MainappConfig',
    # This is last or otherwise template overrides don't work: https://stackoverflow.com/a/35157729
    'django.contrib.admin',
]

MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'livereload.middleware.LiveReloadScript',
]

ROOT_URLCONF = 'cndict.urls'

TEMPLATES = [
    {
        "BACKEND": "django_jinja.backend.Jinja2",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "constants": {
                "current_year": datetime.datetime.now().year,
            },
            # https://niwi.nz/django-jinja/latest/#_custom_filters_globals_constants_and_tests
            "globals": {
                fn_name: f"mainapp.jinja.global_functions.{ fn_name }"
                for fn_name, fn in getmembers(global_functions, isfunction)
            },
            "context_processors": [
                "django.contrib.messages.context_processors.messages",
            ]
        },
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


WSGI_APPLICATION = 'cndict.wsgi.application'
ASGI_APPLICATION = 'cndict.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['DB_NAME'],
        'USER': os.environ['DB_USER'],
        'PASSWORD': os.environ['DB_PASS'],
        'HOST': os.environ['DB_HOST'],
        'PORT': '5432',
    }
}

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [f"redis://:{os.environ['REDIS_PASSWORD']}@redis:6379/0"],
        },
    },
}

CELERY_BROKER_URL = f"redis://:{os.environ['REDIS_PASSWORD']}@redis:6379/0"
CELERY_RESULT_BACKEND = f"redis://:{os.environ['REDIS_PASSWORD']}@redis:6379/0"
CELERY_TASK_DEFAULT_QUEUE = 'default'


SHELL_PLUS_POST_IMPORTS = [
    ('shell_plus', '*')
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')

LOGIN_URL = '/accounts/login'
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ]
}
