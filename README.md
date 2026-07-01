# MonChoix — Orientation IA pour étudiants & chercheurs d'emploi en Afrique

**by ASITECH SOLUTION**

MonChoix guide l'utilisateur à travers un **questionnaire conversationnel** (chatbot),
puis un **agent IA** (RAG + recherche web + DeepSeek) génère un **rapport d'orientation
complet** : score de profil, top 10 filières, universités, débouchés, salaires, compétences,
conseils et plan de carrière. Monétisation par **système de crédits** (paiement FedaPay).

## Stack

Django 5/6 · PostgreSQL + pgvector · Tailwind (CDN) · Alpine.js · DeepSeek ·
Web search (Tavily-compatible) · FedaPay (XOF) · Google OAuth (allauth) · Celery + Redis ·
WeasyPrint (PDF).

## Apps

| App | Rôle |
|-----|------|
| `accounts` | User (email login, crédits), Profile académique, auth + Google, bonus inscription |
| `orientation` | BacSerie/Subject, sessions chatbot, agent IA, rapports, PDF |
| `credits` | CreditPack, CreditTransaction, débit atomique, FedaPay + webhook |
| `knowledge` | KnowledgeDocument (RAG pgvector), embeddings, ré-indexation |
| `core` | Landing, context processor crédits, commande `seed_data` |

## Installation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # puis renseigner les clés

# PostgreSQL + extension pgvector
sudo -u postgres psql -c "CREATE DATABASE monchoix;"
sudo -u postgres psql -d monchoix -c "CREATE EXTENSION IF NOT EXISTS vector;"
# (la migration knowledge.0001 crée aussi l'extension automatiquement)

python manage.py migrate
python manage.py seed_data          # séries, matières, packs de crédits
python manage.py createsuperuser
python manage.py runserver
```

> **pgvector** : requiert l'extension PostgreSQL `vector`
> (paquet `postgresql-16-pgvector` ou compilation depuis https://github.com/pgvector/pgvector).
> Sans elle, utilisez un `EMBEDDING_DIM` cohérent avec le modèle d'embeddings choisi.

### Celery (génération asynchrone des rapports)

```bash
redis-server                                   # broker
celery -A config worker -l info                # worker
```

Pour tester sans worker/Redis : `CELERY_TASK_ALWAYS_EAGER=True` dans `.env`
(la génération s'exécute alors de façon synchrone).

## Configuration (`.env`)

Voir `.env.example`. Clés importantes :

- `DEEPSEEK_API_KEY` — raisonnement LLM + embeddings (endpoint OpenAI-compatible).
- `WEB_SEARCH_API_KEY` / `WEB_SEARCH_ENDPOINT` — recherche web (Tavily par défaut ; échoue en douceur, le RAG prend le relais).
- `FEDAPAY_SECRET_KEY` / `FEDAPAY_WEBHOOK_SECRET` / `FEDAPAY_ENVIRONMENT` (`sandbox`/`live`).
- `GOOGLE_OAUTH_CLIENT_ID` / `GOOGLE_OAUTH_CLIENT_SECRET`.
- Économie de crédits : `SIGNUP_BONUS_CREDITS` (10), `CREDITS_PER_REPORT` (5), `MIN_PACK_PRICE_XOF` (200).

Tout est aussi configurable via l'**admin Django** (`/admin/`) : packs, coût, base RAG, séries/matières.

## Système de crédits

- **+10 crédits** à l'inscription (email ou Google) — `CreditTransaction(SIGNUP_BONUS)`, idempotent.
- **Achat** de packs dès 200 FCFA via FedaPay → transaction `PENDING` → redirection → **webhook** (`transaction.approved`) → `PAID` + créditation idempotente.
- **Consommation** : génération de rapport = `CREDITS_PER_REPORT` crédits, débit **atomique** (`select_for_update`).
- **Remboursement automatique** si la génération échoue.

## Webhook FedaPay

`POST /webhooks/fedapay/` — signature HMAC-SHA256 vérifiée (`FEDAPAY_WEBHOOK_SECRET`),
traitement idempotent. À déclarer dans le dashboard FedaPay.

## Pipeline de l'agent (Celery)

1. Consolidation du profil (réponses du chatbot).
2. RAG : documents pertinents via pgvector (fallback mots-clés).
3. Recherche web ciblée (universités, filières, salaires) + citation des sources.
4. DeepSeek → **JSON strict** parsé côté serveur.
5. Sauvegarde `OrientationReport` + génération PDF (WeasyPrint).

## URLs principales

`/` · `/accounts/login|signup/` · `/accounts/google/login/` · `/profil/` ·
`/orientation/` · `/orientation/<id>/` · `/rapport/<id>/` · `/rapport/<id>/pdf/` ·
`/credits/` · `/mes-credits/` · `/mes-rapports/` · `/webhooks/fedapay/` · `/admin/`.

## Sécurité

Débit atomique + remboursement, webhook signé & idempotent, clés API côté serveur,
CSRF, cookies sécurisés + HSTS en production (`DEBUG=False`).
# monchoix
