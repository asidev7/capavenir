from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Manager for the email-login custom user."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra):
        if not email:
            raise ValueError("L'adresse e-mail est obligatoire.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        if extra.get("is_staff") is not True:
            raise ValueError("Un superuser doit avoir is_staff=True.")
        if extra.get("is_superuser") is not True:
            raise ValueError("Un superuser doit avoir is_superuser=True.")
        return self._create_user(email, password, **extra)


class User(AbstractUser):
    username = None
    email = models.EmailField(_("adresse e-mail"), unique=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    is_google_account = models.BooleanField(default=False)
    credits = models.PositiveIntegerField(default=0)
    country = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def display_name(self):
        full = f"{self.first_name} {self.last_name}".strip()
        return full or self.email.split("@")[0]


class Profile(models.Model):
    class Level(models.TextChoices):
        APRES_BAC = "APRES_BAC", "Après le Bac"
        APRES_LICENCE = "APRES_LICENCE", "Après la Licence"
        AUTRE = "AUTRE", "Autre"

    class StudyLocation(models.TextChoices):
        BENIN = "BENIN", "Bénin"
        AFRIQUE = "AFRIQUE", "Afrique"
        EUROPE = "EUROPE", "Europe"
        CANADA = "CANADA", "Canada"
        USA = "USA", "États-Unis"
        PARTOUT = "PARTOUT", "Partout"

    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="profile")
    level = models.CharField(max_length=20, choices=Level.choices, blank=True)
    bac_serie = models.ForeignKey(
        "orientation.BacSerie", on_delete=models.SET_NULL, null=True, blank=True, related_name="profiles"
    )
    favorite_subjects = models.ManyToManyField("orientation.Subject", blank=True, related_name="fans")
    grades = models.JSONField(default=dict, blank=True)  # {"Maths": 15, ...}
    passions = models.TextField(blank=True)
    interests = models.TextField(blank=True)
    skills = models.TextField(blank=True)
    target_job = models.CharField(max_length=160, blank=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    study_location_pref = models.CharField(max_length=12, choices=StudyLocation.choices, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profil de {self.user.email}"
