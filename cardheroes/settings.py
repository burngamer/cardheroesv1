"""Django settings for Card Heroes (ch_v1).

Every secret and every environment-specific value comes from ENVIRONMENT VARIABLES.
Nothing sensitive lives in this file, so it is safe to commit to GitHub.

Local development works with zero configuration (DEBUG on, SQLite, local media).
On Render (detected via the RENDER env var Render sets automatically) the safe
production defaults kick in: DEBUG off, HTTPS-only cookies, HSTS, etc.
See .env.example for the full list of variables.
"""
import logging
import mimetypes
import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _

# Windows registry sometimes maps .svg/.css/.js to wrong MIME types — force the correct ones
mimetypes.add_type('image/svg+xml', '.svg', True)
mimetypes.add_type('text/css', '.css', True)
mimetypes.add_type('text/javascript', '.js', True)

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None or value == '':
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


def env_list(name):
    return [item.strip() for item in os.environ.get(name, '').split(',') if item.strip()]


# --------------------------------------------------------------------------- core
IS_RENDER = 'RENDER' in os.environ           # Render sets RENDER=true on every service
DEBUG = env_bool('DJANGO_DEBUG', default=not IS_RENDER)

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-local-dev-only-key-never-use-in-production'
    else:
        raise ImproperlyConfigured('DJANGO_SECRET_KEY must be set when DEBUG is off.')

ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS')
CSRF_TRUSTED_ORIGINS = env_list('DJANGO_CSRF_TRUSTED_ORIGINS')
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')   # set by Render
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_EXTERNAL_HOSTNAME}')
if DEBUG:
    ALLOWED_HOSTS += ['localhost', '127.0.0.1', '[::1]']

# Hide the Django admin behind a configurable path (default "admin/")
ADMIN_URL = os.environ.get('DJANGO_ADMIN_URL', 'admin/').strip('/') + '/'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'shop.apps.ShopConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',          # serves /static/ in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',           # Greek / English switching
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cardheroes.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'shop.context_processors.cart_summary',
            ],
        },
    },
]

WSGI_APPLICATION = 'cardheroes.wsgi.application'

# ----------------------------------------------------------------------- database
# Local: SQLite file. Production: set DATABASE_URL (Render Postgres, Neon, etc.).
DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{(BASE_DIR / "db.sqlite3").as_posix()}',
        conn_max_age=600,
        conn_health_checks=True,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ------------------------------------------------------------------ languages
LANGUAGE_CODE = 'en'
LANGUAGES = [
    ('en', _('English')),
    ('el', _('Greek')),
]
LOCALE_PATHS = [BASE_DIR / 'locale']
LANGUAGE_COOKIE_AGE = 60 * 60 * 24 * 365   # remember the visitor's choice for a year
LANGUAGE_COOKIE_SAMESITE = 'Lax'
TIME_ZONE = 'Europe/Athens'
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------- static & media
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Uploaded card images go to Google Drive when these four variables are set.
GDRIVE_CLIENT_ID = os.environ.get('GDRIVE_CLIENT_ID', '')
GDRIVE_CLIENT_SECRET = os.environ.get('GDRIVE_CLIENT_SECRET', '')
GDRIVE_REFRESH_TOKEN = os.environ.get('GDRIVE_REFRESH_TOKEN', '')
GDRIVE_FOLDER_ID = os.environ.get('GDRIVE_FOLDER_ID', '')
# How a public Drive file is turned into an <img> URL. {id} is replaced with the file id.
GDRIVE_URL_TEMPLATE = os.environ.get('GDRIVE_URL_TEMPLATE', 'https://lh3.googleusercontent.com/d/{id}')
# Images larger than this (px, longest side) are downscaled before upload. 0 disables.
GDRIVE_MAX_DIMENSION = int(os.environ.get('GDRIVE_MAX_DIMENSION', '2000'))

USE_GDRIVE = all([GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET, GDRIVE_REFRESH_TOKEN, GDRIVE_FOLDER_ID])

STORAGES = {
    'default': {
        'BACKEND': 'shop.storage.GoogleDriveStorage' if USE_GDRIVE
        else 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage' if DEBUG
        else 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

DATA_UPLOAD_MAX_MEMORY_SIZE = 15 * 1024 * 1024   # allow phone-camera card photos

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'shop:login'
LOGIN_REDIRECT_URL = 'shop:home'
LOGOUT_REDIRECT_URL = 'shop:home'

CART_SESSION_ID = 'cart'

# --------------------------------------------------------------------- email
# Without EMAIL_HOST, emails (password resets) are printed to the logs instead of sent.
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
if EMAIL_HOST:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', True)
    EMAIL_TIMEOUT = 15
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Card Heroes <no-reply@cardheroes.example>')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# ------------------------------------------------------------------ security
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SESSION_COOKIE_HTTPONLY = True

if not DEBUG:
    # Render terminates HTTPS in front of the app and tells us via this header
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = env_bool('DJANGO_SECURE_SSL_REDIRECT', True)
    SECURE_REDIRECT_EXEMPT = [r'^healthz/$']
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    LANGUAGE_COOKIE_SECURE = True
    # Start HSTS small; raise DJANGO_HSTS_SECONDS to 31536000 once everything works over HTTPS.
    SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_HSTS_SECONDS', '3600'))
    # Only turn these on with your OWN domain (e.g. cardheroes.gr) — *.onrender.com is not yours.
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool('DJANGO_HSTS_INCLUDE_SUBDOMAINS', False)
    SECURE_HSTS_PRELOAD = env_bool('DJANGO_HSTS_PRELOAD', False)
    SILENCED_SYSTEM_CHECKS = [
        check for check, enabled in (('security.W005', SECURE_HSTS_INCLUDE_SUBDOMAINS),
                                     ('security.W021', SECURE_HSTS_PRELOAD)) if not enabled
    ]

# ------------------------------------------------------------------- logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {'simple': {'format': '[{levelname}] {name}: {message}', 'style': '{'}},
    'handlers': {'console': {'class': 'logging.StreamHandler', 'formatter': 'simple'}},
    'root': {'handlers': ['console'], 'level': 'INFO'},
    'loggers': {
        'django': {'handlers': ['console'], 'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'), 'propagate': False},
    },
}

if not DEBUG and not USE_GDRIVE:
    logging.getLogger(__name__).warning(
        'Google Drive is NOT configured: uploaded card images will be stored on the '
        'server disk, which Render wipes on every deploy/restart. Set the GDRIVE_* variables.'
    )
