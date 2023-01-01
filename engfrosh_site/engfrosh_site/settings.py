"""
Django settings for engfrosh_site project.

Generated by 'django-admin startproject' using Django 3.2.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

from pathlib import Path
import sys
import os
import logging

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

COLOR_POSITION = 3

# Hack for development to get around import issues
sys.path.append(str(BASE_DIR.parent))


# Check the deploy type
deploy_type = os.environ.get("ENGFROSH_DEPLOY_TYPE")
development = False
production = False
if deploy_type is None:
    logging.warning("ENGFROSH_DEPLOY_TYPE environment variable not set, assuming production.")
elif deploy_type == "DEV":
    logging.info("DEVELOPMENT DEPLOYMENT VERSION")
    development = True
elif deploy_type == "PROD":
    logging.info("PRODUCTION DEPLOYMENT VERSION")
    production = True
else:
    logging.warning(f"UNKNOWN DEPLOYMENT TYPE: {deploy_type}")


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY and production:
    raise Exception("No secret key provided in production!")

DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
if not DISCORD_BOT_TOKEN:
    logging.warning("No discord bot token provided")

# SECURITY WARNING: don't run with debug turned on in production!
# Production sets the settings values, but doesn't affect debug parts
if development:
    DEBUG = True
    PRODUCTION = False
else:
    DEBUG = False
    PRODUCTION = True

if development:
    ALLOWED_HOSTS = [
        "127.0.0.1",
        "localhost"
    ]
else:
    ALLOWED_HOSTS = [
        "mars.engfrosh.com"
    ]


# Discord API Settings
DEFAULT_DISCORD_API_VERSION = 10
DEFAULT_DISCORD_SCOPE = ["identify", "guilds.join"]


# Model Defaults
DEFAULT_SCAVENGER_PUZZLE_REQUIRE_PHOTO_UPLOAD = True


# Application definition

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'authentication.apps.AuthenticationConfig',
    'frosh.apps.FroshConfig',
    'scavenger.apps.ScavengerConfig',
    'management.apps.ManagementConfig',
    'common_models.apps.CommonModelsConfig',
    'check_in.apps.CheckInConfig',
    'ticket.apps.TicketConfig',
    'channels',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'engfrosh_site.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            './engfrosh_site/engfrosh_site/templates',
            './engfrosh_site/templates'
        ],
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

ASGI_APPLICATION = 'engfrosh_site.asgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "engfrosh_dev_2022_07_05",
        "USER": "engfrosh_site",
        "PASSWORD": "there-exercise-fenegle",
        "HOST": "localhost",
        "PORT": "5432",
    }}


# Password validation & Authentication
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'authentication.discord_auth.DiscordAuthBackend'
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Toronto'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'
# STATICFILES_DIRS with files/static shouldn't be used for production
STATICFILES_DIRS = []
if not PRODUCTION:
    STATICFILES_DIRS.append('files/static')
    MEDIA_ROOT = './files/media'

# STATIC_ROOT should not be present, at least for development as far as I know.
if PRODUCTION:
    STATICFILES_DIRS.append('/home/ubuntu/engfrosh/files/static')
    STATIC_ROOT = '/usr/share/engfrosh_site/files/static'
    MEDIA_ROOT = '/usr/share/engfrosh_site/files/media'

MEDIA_URL = '/media/'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CHANNEL_LAYERS = {
    'default': {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    },
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file_debug': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
            'formatter': 'simple'
        },
        'file_warn': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': 'warning.log',
            'formatter': 'simple'
        }
    },
    'root': {
        'handlers': ['console', 'file_debug', 'file_warn'],
        'level': 'DEBUG',
    },
}
