from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import District, EcoPoint, Region


@admin.register(Region)
class RegionAdmin(GISModelAdmin):
    list_display = ("name_uz", "slug")
    prepopulated_fields = {"slug": ("name_uz",)}


@admin.register(District)
class DistrictAdmin(GISModelAdmin):
    list_display = ("name_uz", "region", "slug")
    list_filter = ("region",)
    search_fields = ("name_uz",)
    prepopulated_fields = {"slug": ("name_uz",)}


@admin.register(EcoPoint)
class EcoPointAdmin(GISModelAdmin):
    list_display = ("name", "kind", "district", "is_active")
    list_filter = ("kind", "is_active", "district")
    search_fields = ("name",)
