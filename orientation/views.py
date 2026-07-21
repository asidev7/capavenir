import json
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from credits import services as credit_services

from .models import BacSerie, OrientationSession, Subject
from .questions import ADVANCED_LEVELS, build_questions
from .tasks import generate_report

logger = logging.getLogger(__name__)


def _extract_transcript_text(uploaded_file):
    """Best-effort text extraction from an uploaded transcript. PDF only.

    Images are stored as-is but not OCR'd (the model is text-only). Returns a
    trimmed string (may be empty).
    """
    name = (getattr(uploaded_file, "name", "") or "").lower()
    if not name.endswith(".pdf"):
        return ""
    try:
        from pypdf import PdfReader

        reader = PdfReader(uploaded_file)
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
        uploaded_file.seek(0)
        return text.strip()[:4000]
    except Exception:  # pragma: no cover - best effort
        logger.warning("Transcript extraction failed for %s", name)
        try:
            uploaded_file.seek(0)
        except Exception:
            pass
        return ""


def _report_cost(answers):
    """Base cost + surcharge for advanced orientation levels (licence, master...)."""
    cost = settings.CREDITS_PER_REPORT
    if (answers or {}).get("level") in ADVANCED_LEVELS:
        cost += settings.ADVANCED_LEVEL_SURCHARGE
    return cost


@login_required
def start(request):
    """Open the chatbot. Requires enough credits; reuses an in-progress session."""
    cost = settings.CREDITS_PER_REPORT
    if request.user.credits < cost:
        messages.error(
            request,
            f"Il te faut au moins {cost} crédits pour démarrer une orientation. Recharge ton compte.",
        )
        return redirect("credits:packs")
    session = (
        OrientationSession.objects.filter(
            user=request.user, status=OrientationSession.Status.IN_PROGRESS
        )
        .order_by("-created_at")
        .first()
    )
    if session is None:
        session = OrientationSession.objects.create(user=request.user)
    return redirect("orientation:chat", session_id=session.pk)


@login_required
def chat(request, session_id):
    session = get_object_or_404(OrientationSession, pk=session_id, user=request.user)
    if session.status in {OrientationSession.Status.COMPLETED} and hasattr(session, "report"):
        return redirect("orientation:report", report_id=session.report.pk)
    context = {
        "session": session,
        # Pass raw objects: the |json_script filter does the JSON encoding once.
        "questions_json": build_questions(),
        "answers_json": session.answers or {},
        "series": BacSerie.objects.all(),
        "credits_per_report": settings.CREDITS_PER_REPORT,
        "advanced_surcharge": settings.ADVANCED_LEVEL_SURCHARGE,
        "advanced_levels_json": list(ADVANCED_LEVELS),
    }
    return render(request, "orientation/chat.html", context)


@login_required
def subjects_for_serie(request):
    """AJAX: return subjects belonging to a given série code."""
    code = request.GET.get("serie", "")
    subjects = Subject.objects.filter(series__code=code).values("id", "name", "code").distinct()
    return JsonResponse({"subjects": list(subjects)})


@login_required
@require_POST
def save_answers(request, session_id):
    """AJAX: persist partial answers as the user progresses."""
    session = get_object_or_404(OrientationSession, pk=session_id, user=request.user)
    try:
        answers = json.loads(request.body.decode("utf-8")).get("answers", {})
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "invalid payload"}, status=400)
    if isinstance(answers, dict):
        session.answers = answers
        session.save(update_fields=["answers"])
    return JsonResponse({"ok": True})


@login_required
@require_POST
def upload_transcript(request, session_id):
    """AJAX: upload a relevé de notes (PDF/image) instead of entering grades manually.

    Stored on the session privately (media, not public), text extracted best-effort
    for the AI, never exposed back to the client.
    """
    session = get_object_or_404(OrientationSession, pk=session_id, user=request.user)
    transcript = request.FILES.get("transcript")
    if not transcript:
        return JsonResponse({"ok": False, "error": "Aucun fichier reçu."}, status=400)
    if transcript.size > 10 * 1024 * 1024:
        return JsonResponse({"ok": False, "error": "Fichier trop volumineux (10 Mo max)."}, status=400)

    text = _extract_transcript_text(transcript)
    session.transcript_file = transcript
    answers = dict(session.answers or {})
    answers["notes_mode"] = "upload"
    answers.pop("grades", None)
    if text:
        answers["transcript_text"] = text
    session.answers = answers
    session.save(update_fields=["transcript_file", "answers"])
    return JsonResponse({"ok": True, "filename": transcript.name})


@login_required
@require_POST
def generate(request, session_id):
    """Debit credits, then launch the async agent pipeline."""
    session = get_object_or_404(OrientationSession, pk=session_id, user=request.user)

    if session.status == OrientationSession.Status.GENERATING:
        return JsonResponse({"ok": True, "status": session.status})
    if session.status == OrientationSession.Status.COMPLETED and hasattr(session, "report"):
        return JsonResponse({"ok": True, "status": session.status, "report_id": session.report.pk})

    try:
        answers = json.loads(request.body.decode("utf-8")).get("answers", {})
        if isinstance(answers, dict) and answers:
            session.answers = answers
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass

    cost = _report_cost(session.answers)
    try:
        credit_services.consume_credits(request.user, cost, reason="Rapport d'orientation")
    except credit_services.InsufficientCredits:
        return JsonResponse(
            {"ok": False, "error": "insufficient_credits", "redirect": "/credits/"}, status=402
        )

    session.credits_spent = cost
    session.status = OrientationSession.Status.GENERATING
    session.progress_message = "Démarrage…"
    session.save(update_fields=["answers", "credits_spent", "status", "progress_message"])

    generate_report.delay(session.pk)
    return JsonResponse({"ok": True, "status": session.status})


@login_required
def status(request, session_id):
    """AJAX: poll generation status."""
    session = get_object_or_404(OrientationSession, pk=session_id, user=request.user)
    data = {
        "status": session.status,
        "message": session.progress_message,
    }
    if session.status == OrientationSession.Status.COMPLETED and hasattr(session, "report"):
        data["report_id"] = session.report.pk
    return JsonResponse(data)


@login_required
def report(request, report_id):
    from .models import OrientationReport

    report = get_object_or_404(OrientationReport, pk=report_id, session__user=request.user)
    return render(request, "orientation/report.html", {"report": report, "session": report.session})


@login_required
def report_pdf(request, report_id):
    from .models import OrientationReport

    from . import pdf as pdf_service

    report = get_object_or_404(OrientationReport, pk=report_id, session__user=request.user)
    if not report.pdf_file:
        pdf_service.build_report_pdf(report)
    if not report.pdf_file:
        raise Http404("PDF indisponible.")
    return FileResponse(report.pdf_file.open("rb"), as_attachment=True, filename=f"rapport-cap-avenir-{report.pk}.pdf")
