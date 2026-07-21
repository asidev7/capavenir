"""
Django settings for Cap Avenir (ASITECH SOLUTION).
"""

from pathlib import Path

import dj_database_url
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def env(key, default=None):
    return os.environ.get(key, default)


def env_bool(key, default=False):
    val = os.environ.get(key)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def env_int(key, default=0):
    try:
        return int(os.environ.get(key, default))
    except (TypeError, ValueError):
        return default


SECRET_KEY = env("SECRET_KEY", "django-insecure-dev-key-change-me")
DEBUG = env_bool("DEBUG", True)
ALLOWED_HOSTS = [h.strip() for h in env("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]

SITE_URL = env("SITE_URL", "http://localhost:8000")
SITE_ID = 1

# --- Email ---
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend" if DEBUG
    else "django.core.mail.backends.smtp.EmailBackend",
)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "Cap Avenir <no-reply@monchoix.bj>")

# --- Applications ---
INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    # Third-party
    "allauth",
    "allauth.account",
    # Local
    "accounts",
    "orientation",
    "credits",
    "knowledge",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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
                "credits.context_processors.credits_balance",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- Database ---
DATABASES = {
    "default": dj_database_url.parse(
        env("DATABASE_URL", f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=600,
    )
}

# --- Auth ---
AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- allauth ---
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USER_MODEL_EMAIL_FIELD = "email"
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_ADAPTER = "accounts.adapters.AccountAdapter"
ACCOUNT_SIGNUP_FORM_CLASS = "accounts.forms.SignupExtraForm"
ACCOUNT_SIGNUP_REDIRECT_URL = "credits:packs"
LOGIN_REDIRECT_URL = "orientation:start"
LOGOUT_REDIRECT_URL = "core:landing"
LOGIN_URL = "account_login"

# --- I18N ---
LANGUAGE_CODE = "fr"
TIME_ZONE = "Africa/Porto-Novo"
USE_I18N = True
USE_TZ = True

# --- Static / Media ---
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "config.storage.LenientManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Celery ---
CELERY_BROKER_URL = env("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
CELERY_TASK_ALWAYS_EAGER = env_bool("CELERY_TASK_ALWAYS_EAGER", False)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

# --- IA ---
DEEPSEEK_API_KEY = env("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_BASE = env("DEEPSEEK_API_BASE", "https://api.deepseek.com")
DEEPSEEK_MODEL = env("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_EMBEDDING_MODEL = env("DEEPSEEK_EMBEDDING_MODEL", "deepseek-embedding")
WEB_SEARCH_API_KEY = env("WEB_SEARCH_API_KEY", "")
WEB_SEARCH_ENDPOINT = env("WEB_SEARCH_ENDPOINT", "https://api.tavily.com/search")
EMBEDDING_DIM = env_int("EMBEDDING_DIM", 1024)

# --- FedaPay ---
FEDAPAY_PUBLIC_KEY = env("FEDAPAY_PUBLIC_KEY", "")
FEDAPAY_SECRET_KEY = env("FEDAPAY_SECRET_KEY", "")
FEDAPAY_WEBHOOK_SECRET = env("FEDAPAY_WEBHOOK_SECRET", "")
FEDAPAY_ENVIRONMENT = env("FEDAPAY_ENVIRONMENT", "sandbox")
PAYMENT_CURRENCY = env("PAYMENT_CURRENCY", "XOF")

# --- Credits economy ---
SIGNUP_BONUS_CREDITS = env_int("SIGNUP_BONUS_CREDITS", 0)
CREDITS_PER_REPORT = env_int("CREDITS_PER_REPORT", 300)
ADVANCED_LEVEL_SURCHARGE = env_int("ADVANCED_LEVEL_SURCHARGE", 100)
MIN_PACK_PRICE_XOF = env_int("MIN_PACK_PRICE_XOF", 500)

# --- Security (prod) ---
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

CSRF_TRUSTED_ORIGINS = [o for o in [SITE_URL] if o.startswith("https")]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}


# --- Jazzmin (admin theme) ---
JAZZMIN_SETTINGS = {
    "site_title": "Cap Avenir Admin",
    "site_header": "Cap Avenir",
    "site_brand": "Cap Avenir",
    "site_icon": "img/favicon.svg",
    "welcome_sign": "Bienvenue sur l'administration Cap Avenir",
    "copyright": "ASITECH SOLUTION",
    "search_model": ["accounts.User", "knowledge.KnowledgeDocument"],
    "topmenu_links": [
        {"name": "Tableau de bord", "url": "core:dashboard", "permissions": ["auth.view_user"]},
        {"name": "Voir le site", "url": "/", "new_window": True},
    ],
    "icons": {
        "accounts.User": "fas fa-user",
        "accounts.Profile": "fas fa-id-card",
        "orientation.BacSerie": "fas fa-layer-group",
        "orientation.Subject": "fas fa-book",
        "orientation.OrientationSession": "fas fa-comments",
        "orientation.OrientationReport": "fas fa-file-pdf",
        "credits.CreditPack": "fas fa-coins",
        "credits.CreditTransaction": "fas fa-credit-card",
        "knowledge.KnowledgeDocument": "fas fa-database",
    },
    "show_ui_builder": False,
}

JAZZMIN_UI_TWEAKS = {
    "theme": "default",
    "navbar": "navbar-dark",
    "brand_colour": "navbar-dark",
    "accent": "accent-primary",
    "sidebar": "sidebar-dark-primary",
    "button_classes": {
        "primary": "btn-primary",
        "success": "btn-success",
    },
}
