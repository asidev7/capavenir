"""Minimal FedaPay REST client (no SDK dependency)."""
import hashlib
import hmac
import logging

import requests
from django.conf import settings

from core import config as platform_config

logger = logging.getLogger(__name__)


def _base_url():
    if platform_config.get("fedapay_environment") == "live":
        return "https://api.fedapay.com/v1"
    return "https://sandbox-api.fedapay.com/v1"


def _headers():
    return {
        "Authorization": f"Bearer {platform_config.get('fedapay_secret_key')}",
        "Content-Type": "application/json",
    }


def create_transaction(*, amount, description, customer_email, callback_url):
    """Create a FedaPay transaction and return (fedapay_id, payment_url)."""
    payload = {
        "description": description,
        "amount": int(amount),
        "currency": {"iso": settings.PAYMENT_CURRENCY},
        "callback_url": callback_url,
        "customer": {"email": customer_email},
    }
    resp = requests.post(f"{_base_url()}/transactions", json=payload, headers=_headers(), timeout=30)
    resp.raise_for_status()
    data = resp.json()["v1/transaction"]
    fedapay_id = data["id"]

    token_resp = requests.post(
        f"{_base_url()}/transactions/{fedapay_id}/token", headers=_headers(), timeout=30
    )
    token_resp.raise_for_status()
    payment_url = token_resp.json().get("url")
    return str(fedapay_id), payment_url


def verify_webhook_signature(payload_body: bytes, signature_header: str) -> bool:
    """Verify the FedaPay `X-FEDAPAY-SIGNATURE` header (HMAC-SHA256)."""
    secret = platform_config.get("fedapay_webhook_secret")
    if not secret or not signature_header:
        return False
    # Header format: "t=timestamp,s=signature"
    parts = dict(p.split("=", 1) for p in signature_header.split(",") if "=" in p)
    timestamp = parts.get("t", "")
    provided = parts.get("s", signature_header)
    signed_payload = f"{timestamp}.{payload_body.decode('utf-8')}" if timestamp else payload_body.decode("utf-8")
    expected = hmac.new(secret.encode(), signed_payload.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, provided)


def fetch_transaction(fedapay_id):
    resp = requests.get(f"{_base_url()}/transactions/{fedapay_id}", headers=_headers(), timeout=30)
    resp.raise_for_status()
    return resp.json()["v1/transaction"]
