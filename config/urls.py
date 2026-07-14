from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Cap Avenir Admin"
admin.site.site_title = "Cap Avenir Admin"
admin.site.index_title = "Administration Cap Avenir"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", include("core.urls")),
    path("", include("accounts.urls")),
    path("", include("orientation.urls")),
    path("", include("credits.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
