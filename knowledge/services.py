"""Embeddings + semantic retrieval over KnowledgeDocument."""
import logging

import requests

from core import config as platform_config

from .models import HAS_PGVECTOR, KnowledgeDocument

logger = logging.getLogger(__name__)


def extract_pdf_text(file_field) -> str:
    """Extract plain text from an uploaded PDF file. Returns '' on failure."""
    if not file_field:
        return ""
    try:
        from pypdf import PdfReader

        file_field.open("rb")
        reader = PdfReader(file_field)
        parts = [(page.extract_text() or "") for page in reader.pages]
        return "\n".join(parts).strip()
    except Exception as exc:  # pragma: no cover - depends on file
        logger.warning("PDF extraction failed: %s", exc)
        return ""
    finally:
        try:
            file_field.close()
        except Exception:
            pass


def embed_text(text: str):
    """Return an embedding vector for `text` via DeepSeek, or None on failure.

    Kept provider-agnostic: any OpenAI-compatible /embeddings endpoint works.
    """
    api_key = platform_config.get("deepseek_api_key")
    if not api_key or not text.strip():
        return None
    try:
        resp = requests.post(
            f"{platform_config.get('deepseek_api_base')}/embeddings",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": platform_config.get("deepseek_embedding_model"), "input": text[:8000]},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["data"][0]["embedding"]
    except Exception as exc:  # pragma: no cover - network
        logger.warning("Embedding failed: %s", exc)
        return None


def index_document(doc: KnowledgeDocument):
    """Compute and store the embedding for a single document."""
    vector = embed_text(f"{doc.title}\n{doc.content}")
    if vector is not None:
        doc.embedding = vector
        doc.save(update_fields=["embedding"])
    return vector is not None


def reindex_all():
    count = 0
    for doc in KnowledgeDocument.objects.all():
        if index_document(doc):
            count += 1
    return count


def search(query: str, *, top_k: int = 6, country_scope: str = ""):
    """Return the most relevant documents for `query`.

    Uses pgvector cosine distance when available and the query can be embedded;
    otherwise falls back to a simple keyword filter so the pipeline still works.
    """
    qs = KnowledgeDocument.objects.all()
    if country_scope:
        from django.db.models import Q

        qs = qs.filter(Q(country_scope__iexact=country_scope) | Q(country_scope=""))

    if HAS_PGVECTOR:
        vector = embed_text(query)
        if vector is not None:
            from pgvector.django import CosineDistance

            return list(
                qs.exclude(embedding__isnull=True)
                .annotate(distance=CosineDistance("embedding", vector))
                .order_by("distance")[:top_k]
            )

    # Fallback: naive keyword match.
    terms = [t for t in query.lower().split() if len(t) > 3]
    from django.db.models import Q

    kw = Q()
    for t in terms[:8]:
        kw |= Q(content__icontains=t) | Q(title__icontains=t)
    if kw:
        qs = qs.filter(kw)
    return list(qs[:top_k])
