import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from .database import postgres_options

BASE_DIR = Path(__file__).resolve().parents[2]
RUNTIME = Path(os.environ.get("GATI_RUNTIME", BASE_DIR / "runtime"))
SECRET_KEY = os.environ.get("GATI_SECRET_KEY", "")
if len(SECRET_KEY) < 50:
    raise ImproperlyConfigured("Defina GATI_SECRET_KEY aleatória com pelo menos 50 caracteres.")
DEBUG = False
ALLOWED_HOSTS = [x for x in os.environ.get("GATI_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if x]
CSRF_TRUSTED_ORIGINS = [x for x in os.environ.get("GATI_CSRF_ORIGINS", "").split(",") if x]
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "drf_spectacular",
]
INSTALLED_APPS += [
    "gati.apps." + name
    for name in [
        "usuarios",
        "auditoria",
        "cadastros",
        "pessoas",
        "ativos",
        "manutencoes",
        "arquivos",
        "importacoes",
        "termos",
        "movimentacoes",
        "dashboard",
    ]
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "gati.apps.usuarios.middleware.SessionLimitsMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "gati.common.middleware.SecurityHeadersMiddleware",
]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "gati.common.context.navigation",
            ]
        },
    }
]
_PG_HOST = os.environ.get("PGHOST", "127.0.0.1")
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("PGDATABASE", "gati"),
        "USER": os.environ.get("PGUSER", "gati"),
        "PASSWORD": os.environ.get("PGPASSWORD", ""),
        "HOST": _PG_HOST,
        "PORT": os.environ.get("PGPORT", "5432"),
        "CONN_MAX_AGE": 60,
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": postgres_options(
            _PG_HOST, os.environ.get("PGSSLMODE"), os.environ.get("PGSSLROOTCERT")
        ),
    }
}
AUTH_USER_MODEL = "usuarios.UsuarioTI"
AUTHENTICATION_BACKENDS = ["gati.apps.usuarios.authentication.IdentityBackend"]
PASSWORD_HASHERS = ["django.contrib.auth.hashers.Argon2PasswordHasher"]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 15}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
]
LOGIN_URL = "/entrar/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/entrar/"
SESSION_COOKIE_AGE = 43200
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_NAME = "gati_admin"
SESSION_SAVE_EVERY_REQUEST = True
PASSWORD_RESET_TIMEOUT = 3600
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Cuiaba"
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
DATA_UPLOAD_MAX_MEMORY_SIZE = 27 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["gati.apps.usuarios.permissions.InternalPermission"],
    "DEFAULT_PAGINATION_CLASS": "gati.api.pagination.Pagination",
    "PAGE_SIZE": 50,
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.NamespaceVersioning",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "gati.api.exceptions.problem_handler",
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}
SPECTACULAR_SETTINGS = {
    "TITLE": "GATI — núcleo patrimonial",
    "VERSION": "1.0.0",
    "OAS_VERSION": "3.1.0",
    "SERVE_PERMISSIONS": ["gati.apps.usuarios.permissions.AdminPermission"],
}
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = os.environ.get("GATI_FROM_EMAIL", "gati@example.invalid")
PUBLIC_BASE_URL = os.environ.get("GATI_PUBLIC_URL", "http://127.0.0.1:8765")
CLAMAV_HOST = os.environ.get("GATI_CLAMAV_HOST", "127.0.0.1")
CLAMAV_PORT = int(os.environ.get("GATI_CLAMAV_PORT", "3310"))
CLAMAV_TIMEOUT = 15
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
# Mantém Origin/Referer nos formulários internos sem enviar referência a outros sites.
SECURE_REFERRER_POLICY = "same-origin"
