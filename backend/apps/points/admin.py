from django.contrib import admin

from .models import PointTransaction


@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    """Read-only view of the ledger. Rows are never edited or deleted (append-only)."""

    list_display = ("user", "amount", "reason", "report", "district", "created_by", "created_at")
    list_filter = ("reason", "district")
    search_fields = ("user__email", "user__display_name")
    date_hierarchy = "created_at"
    list_select_related = ("user", "district", "created_by")

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
