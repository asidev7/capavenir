"""Seed BacSéries + matières + packs de crédits (contexte béninois/francophone)."""
from django.core.management.base import BaseCommand
from django.db import transaction

from credits.models import CreditPack
from orientation.models import BacSerie, Subject

# Séries officielles du Baccalauréat au Bénin (Office du Bac).
SERIES = [
    ("A1", "Littéraire — Langues vivantes", "Lettres, langues vivantes et philosophie."),
    ("A2", "Littéraire — Sciences humaines", "Lettres, philosophie et sciences humaines."),
    ("B", "Sciences économiques et sociales", "Économie, sciences sociales et mathématiques."),
    ("C", "Mathématiques et Sciences physiques", "Dominante mathématiques et physique-chimie."),
    ("D", "Mathématiques et Sciences de la nature", "Maths, physique-chimie et SVT."),
    ("E", "Mathématiques et Techniques", "Mathématiques et sciences techniques industrielles."),
    ("F1", "Construction mécanique", "Baccalauréat technique industriel — mécanique."),
    ("F2", "Électronique", "Baccalauréat technique industriel — électronique."),
    ("F3", "Électrotechnique", "Baccalauréat technique industriel — électrotechnique."),
    ("F4", "Génie civil", "Baccalauréat technique industriel — bâtiment et génie civil."),
    ("G1", "Techniques administratives", "Secrétariat et techniques administratives."),
    ("G2", "Techniques quantitatives de gestion", "Comptabilité et gestion."),
    ("G3", "Techniques commerciales", "Commerce, vente et marketing."),
]

# subject code -> (name, [série codes])
SUBJECTS = {
    "MATH": ("Mathématiques", ["A2", "B", "C", "D", "E", "F1", "F2", "F3", "F4", "G2"]),
    "PHYS": ("Physique-Chimie", ["C", "D", "E", "F1", "F2", "F3", "F4"]),
    "SVT": ("Sciences de la Vie et de la Terre", ["C", "D"]),
    "FR": ("Français", ["A1", "A2", "B", "C", "D", "E", "F1", "F2", "F3", "F4", "G1", "G2", "G3"]),
    "EPS": ("Éducation Physique et Sportive", ["A1", "A2", "B", "C", "D", "E", "F1", "F2", "F3", "F4", "G1", "G2", "G3"]),
    "PHILO": ("Philosophie", ["A1", "A2", "B", "C", "D"]),
    "ANG": ("Anglais", ["A1", "A2", "B", "C", "D", "E", "F1", "F2", "F3", "F4", "G1", "G2", "G3"]),
    "ALL": ("Allemand", ["A1", "A2"]),
    "ESP": ("Espagnol", ["A1", "A2"]),
    "HG": ("Histoire-Géographie", ["A1", "A2", "B", "D", "G1", "G3"]),
    "ECO": ("Sciences économiques", ["B", "G2", "G3"]),
    "COMPTA": ("Comptabilité", ["G2"]),
    "DROIT": ("Droit", ["B", "G1", "G2", "G3"]),
    "INFO": ("Informatique", ["E", "F2", "G2"]),
    "TECH": ("Technologie", ["E", "F1", "F2", "F3", "F4"]),
    "DESSIN": ("Dessin technique", ["F1", "F4"]),
    "ELEC": ("Électricité", ["F2", "F3"]),
    "MECA": ("Mécanique", ["F1"]),
    "GC": ("Génie civil", ["F4"]),
    "COM": ("Techniques commerciales", ["G3"]),
    "ORG": ("Organisation administrative", ["G1"]),
}

PACKS = [
    ("Orientation", 500, 500, 1),
]


class Command(BaseCommand):
    help = "Seed les séries du Bac, les matières et les packs de crédits."

    @transaction.atomic
    def handle(self, *args, **options):
        for order, (code, label, desc) in enumerate(SERIES, start=1):
            BacSerie.objects.update_or_create(
                code=code, defaults={"label": label, "description": desc, "order": order}
            )
        self.stdout.write(self.style.SUCCESS(f"{len(SERIES)} séries seedées."))

        for code, (name, series_codes) in SUBJECTS.items():
            subj, _ = Subject.objects.update_or_create(code=code, defaults={"name": name})
            subj.series.set(BacSerie.objects.filter(code__in=series_codes))
        self.stdout.write(self.style.SUCCESS(f"{len(SUBJECTS)} matières seedées."))

        for name, credits, price, order in PACKS:
            CreditPack.objects.update_or_create(
                name=name, defaults={"credits": credits, "price_xof": price, "order": order, "active": True}
            )
        CreditPack.objects.exclude(name__in=[p[0] for p in PACKS]).update(active=False)
        self.stdout.write(self.style.SUCCESS(f"{len(PACKS)} packs de crédits seedés."))
        self.stdout.write(self.style.SUCCESS("Seed terminé ✅"))
