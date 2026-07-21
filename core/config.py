"""Effective configuration: valeur admin (DB) si renseignée, sinon .env/settings."""
from django.conf import settings

from .models import PlatformSettings

_ENV_FALLBACK = {
    "deepseek_api_key": "DEEPSEEK_API_KEY",
    "deepseek_api_base": "DEEPSEEK_API_BASE",
    "deepseek_model": "DEEPSEEK_MODEL",
    "deepseek_embedding_model": "DEEPSEEK_EMBEDDING_MODEL",
    "fedapay_environment": "FEDAPAY_ENVIRONMENT",
    "fedapay_public_key": "FEDAPAY_PUBLIC_KEY",
    "fedapay_secret_key": "FEDAPAY_SECRET_KEY",
    "fedapay_webhook_secret": "FEDAPAY_WEBHOOK_SECRET",
}


def get(key):
    value = getattr(PlatformSettings.load(), key, "") or ""
    if value:
        return value
    return getattr(settings, _ENV_FALLBACK[key], "")
