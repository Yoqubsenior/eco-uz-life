from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("api/v1/", include("apps.common.urls")),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/air/", include("apps.air.urls")),
    path("api/v1/reports/", include("apps.reports.urls")),
    path("api/v1/points/", include("apps.points.urls")),
]

if settings.DEBUG:
    # Dev only. In production, uploaded files are served by the web server / object storage,
    # never by Django.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
