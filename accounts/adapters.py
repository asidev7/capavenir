from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.db import transaction


def grant_signup_bonus(user):
    """Grant the signup bonus once, atomically, and log the transaction."""
    from credits.models import CreditTransaction

    bonus = settings.SIGNUP_BONUS_CREDITS
    if bonus <= 0:
        return
    with transaction.atomic():
        # Skip if a bonus already exists (idempotent).
        if CreditTransaction.objects.filter(user=user, type=CreditTransaction.Type.SIGNUP_BONUS).exists():
            return
        user.credits = (user.credits or 0) + bonus
        user.save(update_fields=["credits"])
        CreditTransaction.objects.create(
            user=user,
            type=CreditTransaction.Type.SIGNUP_BONUS,
            amount=bonus,
            balance_after=user.credits,
            payment_status=CreditTransaction.PaymentStatus.PAID,
        )


class AccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=commit)
        if commit:
            grant_signup_bonus(user)
        return user
