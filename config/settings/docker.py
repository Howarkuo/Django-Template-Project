import logging
import os

import sentry_sdk
from corsheaders.defaults import default_headers
from corsheaders.defaults import default_methods
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.logging import ignore_logger

from .base import *  # noqa: F403


ALLOWED_HOSTS = str(os.environ.get("DJANGO_ALLOWED_HOSTS")).split(" ")
CSRF_TRUSTED_ORIGINS = str(os.environ.get("CSRF_TRUSTED_ORIGINS")).split(" ")
CORS_ALLOWED_METHODS = [*list(default_methods)]
CORS_ALLOWED_HEADERS = [*list(default_headers), "*"]
CORS_ALLOW_ALL_ORIGINS = True


# EMAIL
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = os.environ.get("DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")

# SENTRY
SENTRY_DSN = os.environ.get("SENTRY_DSN")
SENTRY_LOG_LEVEL = int(os.environ.get("SENTRY_LOG_LEVEL", default=logging.INFO))

sentry_logging = LoggingIntegration(
    level=SENTRY_LOG_LEVEL,  # Capture info and above as breadcrumbs
    event_level=logging.ERROR,  # Send errors as events
)
integrations = [sentry_logging, DjangoIntegration(), CeleryIntegration()]
sentry_sdk.init(
    dsn=SENTRY_DSN,
    integrations=integrations,
    environment=os.environ.get("SENTRY_ENVIRONMENT", default="production"),
    traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", default=0.0)),
)
ignore_logger("django.security.DisallowedHost")

# django-debug-toolbar
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites
if DEBUG:  # noqa: F405
    INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
    # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa: F405
    # https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
    DEBUG_TOOLBAR_CONFIG = {
        "DISABLE_PANELS": ["debug_toolbar.panels.redirects.RedirectsPanel"],
        "SHOW_TEMPLATE_CONTEXT": True,
    }
    # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips
    INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]
