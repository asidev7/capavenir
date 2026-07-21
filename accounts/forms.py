import json
import re

from django import forms

from .models import Profile, User

_INPUT_CLASS = (
    "w-full rounded-md border border-gray-300 px-3 py-2 "
    "focus:border-brand focus:ring-1 focus:ring-brand outline-none"
)

# Matches "Matière: 15" / "Physique-Chimie : 12,5" pairs, decimal comma or dot allowed.
_GRADE_RE = re.compile(r"([^:,;\n]+?)\s*[:=]\s*(\d+(?:[.,]\d+)?)")


def parse_grades(raw: str) -> dict:
    """Accept notes as JSON `{"Maths": 15}` OR text `Maths: 15, Physique: 12,5`."""
    raw = (raw or "").strip()
    if not raw:
        return {}
    # Try JSON first.
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return {str(k): _to_num(v) for k, v in data.items()}
        raise forms.ValidationError("Le JSON doit être un objet {matière: note}.")
    except json.JSONDecodeError:
        pass
    # Fallback: "Matière: note" pairs (comma-separated), decimals with , or .
    grades = {name.strip(): _to_num(note) for name, note in _GRADE_RE.findall(raw)}
    if not grades:
        raise forms.ValidationError(
            'Format invalide. Utilise du JSON {"Maths": 15} ou "Maths: 15, Physique: 12,5".'
        )
    return grades


def _to_num(v):
    try:
        return float(str(v).strip().replace(",", "."))
    except (TypeError, ValueError):
        return v


class SignupExtraForm(forms.Form):
    """Extra fields merged into allauth's signup form (see ACCOUNT_SIGNUP_FORM_CLASS)."""

    first_name = forms.CharField(label="Prénom", max_length=150)
    last_name = forms.CharField(label="Nom", max_length=150)
    level = forms.ChoiceField(label="Niveau d'études", choices=Profile.Level.choices)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} {_INPUT_CLASS}".strip()

    def signup(self, request, user):
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.save(update_fields=["first_name", "last_name"])
        Profile.objects.update_or_create(
            user=user, defaults={"level": self.cleaned_data["level"]}
        )


class AvatarForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "avatar"]
        labels = {"first_name": "Prénom", "last_name": "Nom", "avatar": "Photo de profil"}


class ProfileForm(forms.ModelForm):
    grades_json = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text='Sur 20. JSON {"Maths": 15, "Physique": 12} ou simplement "Maths: 15, Physique: 12".',
        label="Notes par matière",
    )

    class Meta:
        model = Profile
        fields = [
            "level",
            "bac_serie",
            "favorite_subjects",
            "passions",
            "interests",
            "skills",
            "target_job",
            "budget",
            "study_location_pref",
        ]
        labels = {
            "level": "Niveau d'études actuel",
            "bac_serie": "Série du Bac",
            "favorite_subjects": "Matières préférées",
            "passions": "Tes passions",
            "interests": "Centres d'intérêt",
            "skills": "Compétences",
            "target_job": "Métier visé",
            "budget": "Budget d'études (FCFA / an)",
            "study_location_pref": "Lieu d'études préféré",
        }
        help_texts = {
            "level": "Où en es-tu dans ton parcours scolaire.",
            "bac_serie": "Détermine les matières prises en compte par l'IA.",
            "favorite_subjects": "Celles où tu es le plus à l'aise ou que tu aimes.",
            "passions": "Ce qui t'anime, au-delà de l'école.",
            "interests": "Domaines, sujets ou activités qui t'attirent.",
            "skills": "Ce que tu sais déjà bien faire.",
            "target_job": "Le métier que tu aimerais exercer, si tu as une idée.",
            "budget": "Aide l'IA à proposer des filières et universités réalistes.",
            "study_location_pref": "Où tu envisages de poursuivre tes études.",
        }
        widgets = {
            "passions": forms.Textarea(attrs={"rows": 3}),
            "interests": forms.Textarea(attrs={"rows": 3}),
            "skills": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.grades:
            self.fields["grades_json"].initial = json.dumps(
                self.instance.grades, ensure_ascii=False
            )
        base = (
            "w-full rounded-md border border-gray-300 px-3 py-2 "
            "focus:border-brand focus:ring-1 focus:ring-brand outline-none"
        )
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} {base}".strip()

    def clean_grades_json(self):
        return parse_grades(self.cleaned_data.get("grades_json", ""))

    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.grades = self.cleaned_data.get("grades_json", {})
        if commit:
            profile.save()
            self.save_m2m()
        return profile
