from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import Reading, Station


@admin.register(Station)
class StationAdmin(GISModelAdmin):
    list_display = ("name", "source", "external_id", "district", "is_active", "last_reading_at")
    list_filter = ("source", "is_active", "district")
    search_fields = ("name", "external_id")
    readonly_fields = ("last_reading_at", "created_at")


@admin.register(Reading)
class ReadingAdmin(admin.ModelAdmin):
    list_display = ("station", "measured_at", "aqi", "pm25", "pm10")
    list_filter = ("station",)
    date_hierarchy = "measured_at"
    list_select_related = ("station",)  # avoid one extra query per row (N+1)

    # Readings come from the ingestion task only; the admin is for looking, not editing.
    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False
