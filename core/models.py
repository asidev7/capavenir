from django.db import models


class PlatformSettings(models.Model):
    """Singleton: clés API modifiables depuis l'admin, prioritaires sur le .env."""

    deepseek_api_key = models.CharField(
        max_length=200, blank=True, help_text="Laisser vide pour utiliser DEEPSEEK_API_KEY (.env)."
    )
    deepseek_api_base = models.CharField(max_length=200, blank=True)
    deepseek_model = models.CharField(max_length=100, blank=True)
    deepseek_embedding_model = models.CharField(max_length=100, blank=True)

    fedapay_environment = models.CharField(
        max_length=10, choices=[("sandbox", "Sandbox"), ("live", "Live")], blank=True
    )
    fedapay_public_key = models.CharField(max_length=200, blank=True)
    fedapay_secret_key = models.CharField(max_length=200, blank=True)
    fedapay_webhook_secret = models.CharField(max_length=200, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuration (FedaPay / DeepSeek)"
        verbose_name_plural = "Configuration (FedaPay / DeepSeek)"

    def __str__(self):
        return "Configuration FedaPay / DeepSeek"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # singleton : jamais supprimé

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
