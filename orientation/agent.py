"""The Cap Avenir orientation agent: RAG + web search + DeepSeek reasoning.

Produces a strict-JSON orientation report from a consolidated profile.
"""
import json
import logging
import re

import requests
from django.conf import settings

from knowledge import services as knowledge

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Tu es un conseiller d'orientation expert du contexte AFRICAIN (Bénin et Afrique francophone en priorité).
À partir du profil d'un étudiant/chercheur d'emploi, de documents de référence et de résultats de recherche web,
tu produis un rapport d'orientation complet, réaliste et personnalisé.

RÈGLES STRICTES :
- Réponds UNIQUEMENT avec un objet JSON valide, sans texte avant ni après, sans balises markdown.
- Sois prudent sur les chiffres : donne des fourchettes et précise « estimation ».
- Cite tes sources web dans le champ "sources" (titre + url). N'invente jamais d'URL.
- Adapte les universités, coûts et débouchés au pays / à la zone d'étude préférée de l'utilisateur.
- Propose EXACTEMENT 10 propositions dans "top_filieres".

- ADAPTE IMPÉRATIVEMENT TOUT LE RAPPORT au champ « Besoin d'orientation » du profil. Ne propose JAMAIS un niveau inférieur à celui demandé :
  • Après le collège → séries et parcours du LYCÉE.
  • Après le Bac → filières de LICENCE / BTS / DUT post-Bac.
  • Pendant la Licence → spécialités et parcours de LICENCE + poursuite d'études.
  • Master → uniquement des SPÉCIALISATIONS et programmes de MASTER (jamais de filières post-Bac), les universités qui offrent ces Masters, leurs coûts et débouchés de niveau Master.
  • Doctorat → écoles doctorales, laboratoires et axes de RECHERCHE.
  • Réorientation / Emploi → passerelles, formations courtes/certifiantes et pistes d'insertion professionnelle.
- Le champ "top_filieres" doit contenir des propositions DU BON NIVEAU (ex : des Masters si le besoin est « Master »), et "top_universities", "cout_estime", "debouches", "salaire_moyen" et "plan_de_carriere" doivent tous correspondre à ce même niveau.
- Dans chaque "raison" et dans "conseils_personnalises", parle explicitement au niveau demandé (ex : « ce Master te permettra… »).

Schéma JSON EXACT à respecter :
{
  "profile_score": 0-100,
  "top_filieres": [{"nom": "", "raison": "", "adequation": 0-100}],
  "top_universities": [{"nom": "", "pays": "", "filiere": "", "cout_estime": "", "lien": ""}],
  "debouches": [{"filiere": "", "metiers": [], "demande_marche": ""}],
  "salaire_moyen": [{"metier": "", "zone": "", "fourchette": ""}],
  "competences_a_developper": [""],
  "conseils_personnalises": "",
  "plan_de_carriere": [{"etape": "", "duree": "", "objectif": ""}],
  "sources": [{"titre": "", "url": ""}]
}"""


def web_search(query, *, max_results=5):
    """Run a web search (Tavily-compatible). Returns a list of {title,url,content}.

    Fails soft: returns [] if not configured or on error (RAG still covers us).
    """
    api_key = settings.WEB_SEARCH_API_KEY
    if not api_key:
        return []
    try:
        resp = requests.post(
            settings.WEB_SEARCH_ENDPOINT,
            json={
                "api_key": api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
            },
            timeout=30,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return [
            {"title": r.get("title", ""), "url": r.get("url", ""), "content": r.get("content", "")[:800]}
            for r in results
        ]
    except Exception as exc:  # pragma: no cover - network
        logger.warning("Web search failed: %s", exc)
        return []


# Le besoin d'orientation : libellé lisible + mot-clé de niveau pour la recherche web.
LEVEL_LABELS = {
    "APRES_BREVET": "Après le collège (choisir sa série au lycée)",
    "APRES_BAC": "Après le Bac (choisir sa filière de Licence)",
    "LICENCE": "Pendant la Licence (spécialité / parcours)",
    "MASTER": "Pour un Master (spécialisation)",
    "DOCTORAT": "Pour un Doctorat (recherche)",
    "REORIENTATION": "Réorientation / changement de voie",
    "EMPLOI": "Insertion professionnelle / reconversion",
}
LEVEL_SEARCH = {
    "APRES_BREVET": "séries et parcours du lycée",
    "APRES_BAC": "filières de licence BTS DUT après le bac",
    "LICENCE": "spécialités et parcours de licence universitaire",
    "MASTER": "programmes de master spécialisation",
    "DOCTORAT": "doctorat école doctorale laboratoire recherche",
    "REORIENTATION": "réorientation passerelle formation certifiante",
    "EMPLOI": "formation professionnelle insertion emploi reconversion",
}


def consolidate_profile(answers: dict) -> str:
    """Turn raw session answers into a readable profile block."""
    lines = []
    # Le niveau/besoin est stocké en code : on l'expose en clair pour le modèle.
    answers = dict(answers)
    if answers.get("level") in LEVEL_LABELS:
        answers["level"] = LEVEL_LABELS[answers["level"]]
    labels = {
        "country": "Pays", "level": "Besoin d'orientation", "bac_serie": "Série du Bac",
        "favorite_subjects": "Matières préférées",
        "passions_interests": "Passions & centres d'intérêt",
        "skills_strengths": "Compétences & points forts",
        "dream_sector": "Secteur qui attire",
        "target_job": "Métier souhaité",
        "budget": "Budget annuel (FCFA)", "study_location_pref": "Lieu d'étude préféré",
        # Mode express : description libre + texte extrait du relevé de notes.
        "free_description": "Description libre de l'étudiant",
        "transcript_text": "Relevé de notes (extrait)",
    }
    for key, label in labels.items():
        val = answers.get(key)
        if val in (None, "", [], {}):
            continue
        if isinstance(val, (list, dict)):
            val = json.dumps(val, ensure_ascii=False)
        lines.append(f"- {label} : {val}")
    return "\n".join(lines) if lines else "Profil incomplet."


def _build_search_queries(answers):
    country = answers.get("country") or "Bénin"
    job = answers.get("target_job") or ""
    loc = answers.get("study_location_pref") or "BENIN"
    # Mot-clé de niveau : garantit des résultats du bon niveau (Master ≠ Licence).
    level_kw = LEVEL_SEARCH.get(answers.get("level"), "filières universitaires")
    zone = {
        "BENIN": "Bénin", "AFRIQUE": "Afrique", "EUROPE": "Europe",
        "CANADA": "Canada", "USA": "États-Unis", "PARTOUT": "monde",
    }.get(loc, country)
    queries = [
        f"{level_kw} pour devenir {job} en {zone}" if job
        else f"{level_kw} porteuses en {zone}",
        f"universités {zone} {level_kw} débouchés admission {job}".strip(),
        f"salaire moyen {job} {zone}".strip() if job else f"métiers bien rémunérés {zone}",
    ]
    return [q for q in queries if q]


def gather_context(answers):
    """RAG documents + web results for the profile. Returns (rag_text, web_results)."""
    profile = consolidate_profile(answers)
    country = answers.get("country", "")

    rag_docs = knowledge.search(profile, top_k=6, country_scope=country)
    rag_text = "\n\n".join(f"[{d.category}] {d.title}\n{d.content[:1200]}" for d in rag_docs)

    web_results = []
    for q in _build_search_queries(answers):
        web_results.extend(web_search(q, max_results=4))
    # De-duplicate by URL.
    seen, deduped = set(), []
    for r in web_results:
        if r["url"] and r["url"] not in seen:
            seen.add(r["url"])
            deduped.append(r)
    return rag_text, deduped[:10]


def _extract_json(text: str) -> dict:
    """Robustly extract the first JSON object from an LLM response."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def call_deepseek(profile, rag_text, web_results):
    if not settings.DEEPSEEK_API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY manquante.")

    web_block = "\n\n".join(
        f"SOURCE: {r['title']}\nURL: {r['url']}\n{r['content']}" for r in web_results
    ) or "Aucun résultat web (utilise le RAG et tes connaissances)."
    rag_block = rag_text or "Aucun document de référence pertinent."

    user_prompt = (
        f"PROFIL DE L'UTILISATEUR :\n{profile}\n\n"
        f"DOCUMENTS DE RÉFÉRENCE (RAG) :\n{rag_block}\n\n"
        f"RÉSULTATS DE RECHERCHE WEB :\n{web_block}\n\n"
        "Génère le rapport d'orientation au format JSON strict décrit dans les règles."
    )

    resp = requests.post(
        f"{settings.DEEPSEEK_API_BASE}/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.DEEPSEEK_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.5,
            "response_format": {"type": "json_object"},
        },
        timeout=120,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]
    return _extract_json(content)


def generate_report_data(answers, *, on_progress=None):
    """Full pipeline. Returns the parsed report dict. Raises on hard failure."""

    def step(msg):
        if on_progress:
            on_progress(msg)

    step("Analyse du profil…")
    profile = consolidate_profile(answers)

    step("Recherche des filières et universités…")
    rag_text, web_results = gather_context(answers)

    step("Rédaction du rapport…")
    data = call_deepseek(profile, rag_text, web_results)

    # Ensure web sources are surfaced even if the model omitted some.
    data.setdefault("sources", [])
    known = {s.get("url") for s in data["sources"]}
    for r in web_results:
        if r["url"] and r["url"] not in known:
            data["sources"].append({"titre": r["title"], "url": r["url"]})
    return data
