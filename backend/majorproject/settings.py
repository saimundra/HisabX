import os
from pathlib import Path
from datetime import timedelta

# -----------------------
# BASE
# -----------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------
# SECURITY / ENV
# -----------------------
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret-key-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# -----------------------
# APPLICATIONS
# -----------------------
INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    'rest_framework_simplejwt.token_blacklist',
    # Project apps
    "accounts",
    "bills",
    "categories",
    "reports",
]

# -----------------------
# MIDDLEWARE
# -----------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "majorproject.urls"

# -----------------------
# TEMPLATES
# -----------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],  # add template dirs if needed
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "majorproject.wsgi.application"

# -----------------------
# DATABASE (env-friendly)
# -----------------------
DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("DB_NAME", str(BASE_DIR / "db.sqlite3")),
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", ""),
        "PORT": os.environ.get("DB_PORT", ""),
    }
}

# -----------------------
# PASSWORD VALIDATION
# -----------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# -----------------------
# INTERNATIONALIZATION
# -----------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = os.environ.get("DJANGO_TIME_ZONE", "Asia/Kathmandu")  # change if needed
USE_I18N = True
USE_TZ = True

# -----------------------
# STATIC & MEDIA
# -----------------------
STATIC_URL = "/static/"
STATIC_ROOT = os.environ.get("STATIC_ROOT", str(BASE_DIR / "staticfiles"))

MEDIA_URL = "/media/"
MEDIA_ROOT = os.environ.get("MEDIA_ROOT", str(BASE_DIR / "media"))

# -----------------------
# DEFAULT PRIMARY KEY
# -----------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -----------------------
# REST FRAMEWORK + SIMPLE JWT
# -----------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    # Require authentication by default; override per-view if required
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 20,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),  # Token valid for 1 day (24 hours)
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.environ.get("JWT_REFRESH_DAYS", 14))),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    # Add other SIMPLE_JWT settings here if needed (ALGORITHM, SIGNING_KEY, etc.)
}

# -----------------------
# CORS (for React dev)
# -----------------------
CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
).split(",")
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# -----------------------
# UPLOAD LIMITS & VALIDATION (use in serializers/views)
# -----------------------
MAX_UPLOAD_SIZE = int(os.environ.get("MAX_UPLOAD_SIZE", 10 * 1024 * 1024))  # 10 MB
ALLOWED_UPLOAD_TYPES = os.environ.get(
    "ALLOWED_UPLOAD_TYPES", "image/jpeg,image/png,image/webp,application/pdf"
).split(",")

# -----------------------
# EMAIL (console default - change for prod)
# -----------------------
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = os.environ.get("EMAIL_PORT", "")
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "False") == "True"

# -----------------------
# SECURITY (enable in production)
# -----------------------
SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "False") == "True"
CSRF_COOKIE_SECURE = os.environ.get("CSRF_COOKIE_SECURE", "False") == "True"
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "False") == "True"
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get("SECURE_HSTS_INCLUDE_SUBDOMAINS", "False") == "True"
SECURE_HSTS_PRELOAD = os.environ.get("SECURE_HSTS_PRELOAD", "False") == "True"

# -----------------------
# LOGGING (basic)
# -----------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO")},
}
AUTH_USER_MODEL = 'accounts.CustomUser'
# Custom user model
