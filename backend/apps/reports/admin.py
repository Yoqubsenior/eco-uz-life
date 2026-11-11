from django.contrib import admin

from .models import Category

# Report moderation admin is built in Stage 5b.


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name_uz", "slug", "icon", "sort_order", "is_active")
    list_editable = ("sort_order", "is_active")
    prepopulated_fields = {"slug": ("name_uz",)}
