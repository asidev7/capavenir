"""The orientation questionnaire (10 steps) served to the Alpine chatbot."""

STUDY_LOCATIONS = [
    ("BENIN", "Au Bénin"),
    ("AFRIQUE", "En Afrique"),
    ("EUROPE", "En Europe"),
    ("CANADA", "Au Canada"),
    ("USA", "Aux États-Unis"),
    ("PARTOUT", "Partout"),
]

# Le « besoin d'orientation » : c'est lui qui pilote tout le rapport.
# On adapte les filières, diplômes, universités et coûts EXACTEMENT à ce choix.
LEVELS = [
    ("APRES_BREVET", "Après le collège — choisir ma série au lycée"),
    ("APRES_BAC", "Après le Bac — choisir ma filière"),
    ("LICENCE", "Pendant la Licence — spécialité / parcours"),
    ("MASTER", "Pour un Master — spécialisation"),
    ("DOCTORAT", "Pour un Doctorat — la recherche"),
    ("REORIENTATION", "Me réorienter / changer de voie"),
    ("EMPLOI", "Insertion professionnelle / reconversion"),
]

# Niveaux "avancés" : recherche plus poussée (spécialisation, marché de l'emploi...),
# facturée en supplément (voir settings.ADVANCED_LEVEL_SURCHARGE).
ADVANCED_LEVELS = {"LICENCE", "MASTER", "DOCTORAT", "REORIENTATION", "EMPLOI"}

LEARNING_STYLES = [
    ("THEORIE", "Plutôt la théorie"),
    ("PRATIQUE", "Plutôt la pratique"),
    ("MIXTE", "Un mélange des deux"),
    ("PROJETS", "Par projets concrets"),
]

WORK_ENVIRONMENTS = [
    ("BUREAU", "Dans un bureau"),
    ("TERRAIN", "Sur le terrain"),
    ("LABO", "En laboratoire"),
    ("REMOTE", "À distance / freelance"),
    ("ENTREPRISE", "Créer mon entreprise"),
    ("PEU_IMPORTE", "Peu importe"),
]

PERSONALITIES = [
    ("CREATIF", "Créatif"),
    ("ANALYTIQUE", "Analytique / logique"),
    ("SOCIAL", "Sociable / à l'écoute"),
    ("ORGANISE", "Organisé / méthodique"),
    ("LEADER", "Leader / entreprenant"),
    ("MANUEL", "Manuel / technique"),
]

SECTORS = [
    ("SANTE", "Santé & médecine"),
    ("TECH", "Informatique & numérique"),
    ("BUSINESS", "Commerce & gestion"),
    ("DROIT", "Droit & sciences politiques"),
    ("INGENIERIE", "Ingénierie & industrie"),
    ("ARTS", "Arts, design & culture"),
    ("AGRO", "Agriculture & environnement"),
    ("EDUCATION", "Éducation & sciences humaines"),
    ("FINANCE", "Banque & finance"),
    ("COMMUNICATION", "Communication & médias"),
]

MOTIVATIONS = [
    ("SALAIRE", "Bien gagner ma vie"),
    ("IMPACT", "Avoir un impact / aider"),
    ("PASSION", "Vivre de ma passion"),
    ("STABILITE", "La stabilité de l'emploi"),
    ("PRESTIGE", "Le prestige / la reconnaissance"),
    ("LIBERTE", "La liberté / l'autonomie"),
]

STUDY_DURATIONS = [
    ("COURT", "Court (1 à 2 ans)"),
    ("LICENCE", "Licence (3 ans)"),
    ("MASTER", "Master (5 ans)"),
    ("LONG", "Long (7 ans et +)"),
    ("INDIFFERENT", "Peu importe la durée"),
]

# Tranches de budget annuel réalistes pour le Bénin :
# du public (UAC ~ frais réduits) au privé, jusqu'aux études à l'étranger.
# On stocke un libellé lisible comme valeur pour que l'IA le lise directement.
BUDGET_RANGES = [
    ("Moins de 100 000 FCFA/an", "Moins de 100 000 FCFA (public, budget serré)"),
    ("100 000 à 300 000 FCFA/an", "100 000 à 300 000 FCFA"),
    ("300 000 à 600 000 FCFA/an", "300 000 à 600 000 FCFA"),
    ("600 000 à 1 500 000 FCFA/an", "600 000 à 1 500 000 FCFA (privé au Bénin)"),
    ("1 500 000 à 5 000 000 FCFA/an", "1 500 000 à 5 000 000 FCFA (privé haut / sous-région)"),
    ("Plus de 5 000 000 FCFA/an", "Plus de 5 000 000 FCFA (études à l'étranger)"),
    ("Je ne sais pas encore", "Je ne sais pas encore"),
]


def _opts(pairs):
    return [{"value": v, "label": l} for v, l in pairs]


def build_questions():
    """Return the ordered list of 10 questions as plain dicts for the frontend.

    Même logique de départ qu'avant (pays → niveau → série → matières),
    puis le profil, les aspirations et enfin les contraintes (budget, lieu).
    Les champs texte libres ont été fusionnés pour rester à 10 questions.
    """
    return [
        # --- Début : identité & parcours ---
        {"key": "country", "type": "text", "label": "Quel est ton pays ?",
         "placeholder": "Ex : Bénin", "required": True,
         "description": "On adapte les universités, les coûts et les débouchés à ton pays."},
        {"key": "level", "type": "single", "label": "Quel type d'orientation cherches-tu ?",
         "options": _opts(LEVELS), "required": True,
         "description": "C'est le point le plus important : on adapte tout le rapport (filières, diplôme visé, universités, coûts) exactement à ce besoin. Ex : pour un Master, on te propose des spécialisations de Master, pas des filières post-Bac."},
        {"key": "bac_serie", "type": "serie", "label": "Quelle est ta série du Bac ?",
         "help": "Cela déterminera les matières proposées.", "required": False,
         "description": "Ta série (C, D, G2…) sert à te proposer les bonnes matières. Choisis celle prévue si tu n'as pas encore le Bac, ou celle obtenue si tu es déjà à l'université."},
        {"key": "favorite_subjects", "type": "subjects_multi",
         "label": "Tes matières préférées ?", "depends_on": "bac_serie", "required": False,
         "description": "Sélectionne les matières où tu es le plus à l'aise ou que tu aimes le plus."},
        {"key": "grades", "type": "grades", "label": "Tes notes par matière (si tu les as)",
         "depends_on": "bac_serie", "required": False,
         "description": "Facultatif : indique tes notes sur 20, elles apparaîtront dans ton rapport et affinent les recommandations."},
        # --- Profil : ce qui te caractérise ---
        {"key": "passions_interests", "type": "textarea",
         "label": "Tes passions et centres d'intérêt ?",
         "placeholder": "Ce qui te passionne, les domaines et activités qui t'intéressent...",
         "required": False,
         "description": "Parle-nous de ce qui te fait vibrer : loisirs, sujets, causes, activités du quotidien."},
        {"key": "skills_strengths", "type": "textarea",
         "label": "Tes compétences et points forts ?",
         "placeholder": "Ce que tu sais bien faire et ce que ton entourage apprécie chez toi...",
         "required": False,
         "description": "Ce que tu réussis facilement et les qualités que les autres remarquent chez toi."},
        # --- Aspirations : où tu veux aller ---
        {"key": "dream_sector", "type": "single", "label": "Quel secteur t'attire le plus ?",
         "options": _opts(SECTORS), "required": False,
         "description": "Le grand domaine dans lequel tu t'imagines travailler plus tard."},
        {"key": "target_job", "type": "text", "label": "Quel métier souhaites-tu exercer ?",
         "placeholder": "Ex : Ingénieur logiciel, Médecin... (facultatif)", "required": False,
         "description": "Si tu as déjà une idée de métier, indique-le. Sinon laisse vide, l'IA te proposera des pistes."},
        # --- Contraintes : budget & lieu ---
        {"key": "budget", "type": "single", "label": "Quel budget annuel prévois-tu pour tes études ?",
         "help": "Frais de scolarité par an, en FCFA.",
         "options": _opts(BUDGET_RANGES), "required": False,
         "description": "Une estimation des frais de scolarité par an. Ça nous aide à te proposer des filières réalistes (public, privé ou étranger)."},
        {"key": "study_location_pref", "type": "single", "label": "Où préfères-tu étudier ?",
         "options": _opts(STUDY_LOCATIONS), "required": True,
         "description": "L'endroit où tu aimerais poursuivre tes études après le Bac."},
    ]
