import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import fedapay, services
from .models import CreditPack, CreditTransaction

logger = logging.getLogger(__name__)


@login_required
def packs(request):
    return render(request, "credits/packs.html", {"packs": CreditPack.objects.filter(active=True)})


@login_required
def my_credits(request):
    txs = request.user.transactions.all()[:100]
    return render(request, "credits/my_credits.html", {"transactions": txs})


@login_required
@require_POST
def checkout(request, pack_id):
    pack = get_object_or_404(CreditPack, pk=pack_id, active=True)
    tx = CreditTransaction.objects.create(
        user=request.user,
        type=CreditTransaction.Type.PURCHASE,
        amount=pack.credits,
        balance_after=0,
        pack=pack,
        payment_status=CreditTransaction.PaymentStatus.PENDING,
    )
    callback_url = request.build_absolute_uri(reverse("credits:my_credits"))
    try:
        fedapay_id, payment_url = fedapay.create_transaction(
            amount=pack.price_xof,
            description=f"Cap Avenir — {pack.name} ({pack.credits} crédits)",
            customer_email=request.user.email,
            callback_url=callback_url,
        )
    except Exception:  # pragma: no cover - network
        logger.exception("FedaPay checkout failed")
        tx.payment_status = CreditTransaction.PaymentStatus.FAILED
        tx.save(update_fields=["payment_status"])
        messages.error(request, "Le paiement n'a pas pu être initié. Réessayez plus tard.")
        return redirect("credits:packs")

    tx.fedapay_transaction_id = fedapay_id
    tx.save(update_fields=["fedapay_transaction_id"])
    if payment_url:
        return redirect(payment_url)
    messages.error(request, "URL de paiement indisponible.")
    return redirect("credits:packs")


@csrf_exempt
@require_POST
def fedapay_webhook(request):
    signature = request.headers.get("X-FEDAPAY-SIGNATURE", "")
    if not fedapay.verify_webhook_signature(request.body, signature):
        logger.warning("Invalid FedaPay webhook signature")
        return HttpResponseBadRequest("invalid signature")

    try:
        event = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return HttpResponseBadRequest("invalid payload")

    entity = event.get("entity", {})
    fedapay_id = str(entity.get("id", ""))
    status = entity.get("status", "")
    name = event.get("name", "")

    if not fedapay_id:
        return HttpResponse("ignored")

    tx = CreditTransaction.objects.filter(
        fedapay_transaction_id=fedapay_id, type=CreditTransaction.Type.PURCHASE
    ).first()
    if tx is None:
        return HttpResponse("unknown transaction")

    if name == "transaction.approved" or status in {"approved", "transferred"}:
        services.apply_purchase(tx)  # idempotent
    elif status in {"declined", "canceled", "failed"}:
        if tx.payment_status != CreditTransaction.PaymentStatus.PAID:
            tx.payment_status = CreditTransaction.PaymentStatus.FAILED
            tx.save(update_fields=["payment_status"])

    return HttpResponse("ok")
