from django.contrib import admin

from .models import PlatformSettings


@admin.register(PlatformSettings)
class PlatformSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            "DeepSeek (IA)",
            {"fields": ("deepseek_api_key", "deepseek_api_base", "deepseek_model", "deepseek_embedding_model")},
        ),
        (
            "FedaPay (paiement)",
            {
                "fields": (
                    "fedapay_environment",
                    "fedapay_public_key",
                    "fedapay_secret_key",
                    "fedapay_webhook_secret",
                )
            },
        ),
    )
    readonly_fields = ("updated_at",)

    def has_add_permission(self, request):
        return not PlatformSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        from django.shortcuts import redirect

        obj = PlatformSettings.load()
        return redirect("admin:core_platformsettings_change", obj.pk)
