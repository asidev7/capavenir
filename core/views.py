from datetime import date

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import render
from django.utils import timezone

from accounts.models import User
from credits.models import CreditPack, CreditTransaction
from knowledge.models import KnowledgeDocument
from orientation.models import OrientationReport, OrientationSession


def landing(request):
    return render(
        request,
        "core/landing.html",
        {
            "packs": CreditPack.objects.filter(active=True)[:3],
            "credits_per_report": settings.CREDITS_PER_REPORT,
            "advanced_surcharge": settings.ADVANCED_LEVEL_SURCHARGE,
            "stats": [
                ("10", "Questions ciblées"),
                ("Top 10", "Filières classées"),
                ("IA", "+ recherche web"),
                ("PDF", "Rapport à télécharger"),
            ],
        },
    )


def _last_months(n=6):
    """Return the last `n` (year, month, label) tuples, oldest first."""
    today = date.today()
    out = []
    y, m = today.year, today.month
    for _ in range(n):
        out.append((y, m))
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    out.reverse()
    labels = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]
    return [(y, m, labels[m - 1]) for y, m in out]


@staff_member_required
def dashboard(request):
    paid = CreditTransaction.objects.filter(
        type=CreditTransaction.Type.PURCHASE,
        payment_status=CreditTransaction.PaymentStatus.PAID,
    )
    revenue = paid.aggregate(total=Sum("pack__price_xof"))["total"] or 0
    credits_sold = paid.aggregate(total=Sum("amount"))["total"] or 0

    # Reports per month (simple bar chart).
    months = _last_months(6)
    monthly = []
    max_count = 1
    for y, m, label in months:
        c = OrientationReport.objects.filter(created_at__year=y, created_at__month=m).count()
        monthly.append({"label": label, "count": c})
        max_count = max(max_count, c)
    for row in monthly:
        row["pct"] = round(row["count"] / max_count * 100)

    context = {
        "stats": {
            "users": User.objects.count(),
            "reports": OrientationReport.objects.count(),
            "sessions": OrientationSession.objects.count(),
            "revenue": revenue,
            "credits_sold": credits_sold,
            "docs": KnowledgeDocument.objects.count(),
        },
        "monthly": monthly,
        "recent_tx": (
            CreditTransaction.objects.select_related("user", "pack").order_by("-created_at")[:8]
        ),
        "recent_reports": (
            OrientationReport.objects.select_related("session__user").order_by("-created_at")[:5]
        ),
        "top_series": (
            OrientationSession.objects.exclude(answers__bac_serie__isnull=True)
            .values("answers__bac_serie")
            .annotate(n=Count("id"))
            .order_by("-n")[:5]
        ),
        "now": timezone.now(),
    }
    return render(request, "core/dashboard.html", context)
