"""Moderation UI (FR-M1..M3). Moderators are staff users in the "Moderators" group.

Every status change goes through services.change_status() — the admin never writes
`status` directly, so history and points can't be skipped.
"""

from django import forms
from django.contrib import admin, messages
from django.contrib.gis.admin import GISModelAdmin
from django.db.models import Count
from django.utils.html import format_html, format_html_join

from . import services
from .models import Category, Report, StatusHistory


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name_uz", "slug", "icon", "sort_order", "is_active")
    list_editable = ("sort_order", "is_active")
    prepopulated_fields = {"slug": ("name_uz",)}


class StatusHistoryInline(admin.TabularInline):
    model = StatusHistory
    extra = 0
    can_delete = False
    fields = ("created_at", "from_status", "to_status", "changed_by", "note")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None) -> bool:
        return False


class ReportModerationForm(forms.ModelForm):
    """Only `status` and `rejection_reason` are editable; the workflow is validated here
    so the moderator gets a normal form error instead of a crash."""

    note = forms.CharField(
        required=False, max_length=300, help_text="Ichki izoh (fuqaroga ko'rsatilmaydi)."
    )

    class Meta:
        model = Report
        fields = ("status", "rejection_reason")

    def clean(self):
        cleaned = super().clean()
        if "status" in self.changed_data:
            try:
                services.validate_transition(
                    self.initial["status"],
                    cleaned.get("status"),
                    cleaned.get("rejection_reason", ""),
                )
            except services.InvalidTransition as exc:
                raise forms.ValidationError(str(exc)) from exc
        return cleaned


@admin.register(Report)
class ReportAdmin(GISModelAdmin):
    form = ReportModerationForm
    inlines = [StatusHistoryInline]
    list_display = (
        "short_id",
        "category",
        "status",
        "district",
        "author_name",
        "photo_count",
        "is_duplicate",
        "created_at",
    )
    list_filter = ("status", "category", "district")
    search_fields = ("description", "author__display_name")
    ordering = ("created_at",)  # FR-M1: moderation queue, oldest first
    list_select_related = ("category", "district", "author")
    actions = ["verify_selected", "mark_in_progress", "mark_resolved"]
    fieldsets = (
        ("Moderatsiya", {"fields": ("status", "rejection_reason", "note")}),
        (
            "Murojaat",
            {
                "fields": (
                    "photos_preview",
                    "category",
                    "description",
                    "map_link",
                    "district",
                    "author_name",
                    "duplicate_of",
                    "created_at",
                    "verified_at",
                    "resolved_at",
                )
            },
        ),
    )
    readonly_fields = (
        "photos_preview",
        "category",
        "description",
        "map_link",
        "district",
        "author_name",
        "duplicate_of",
        "created_at",
        "verified_at",
        "resolved_at",
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_photo_count=Count("photos"))

    # ----- Display helpers -----

    @admin.display(description="ID")
    def short_id(self, obj: Report) -> str:
        return str(obj.id)[:8]

    @admin.display(description="Muallif")
    def author_name(self, obj: Report) -> str:
        return obj.author.display_name or f"#{obj.author_id}"

    @admin.display(description="Rasmlar", ordering="_photo_count")
    def photo_count(self, obj: Report) -> int:
        return obj._photo_count

    @admin.display(description="Takroriy", boolean=True)
    def is_duplicate(self, obj: Report) -> bool:
        return obj.duplicate_of_id is not None

    @admin.display(description="Rasmlar")
    def photos_preview(self, obj: Report) -> str:
        # format_html escapes every value: even a malicious filename can't inject HTML/JS (XSS).
        return format_html_join(
            "",
            '<a href="{}" target="_blank" rel="noopener">'
            '<img src="{}" style="max-height:200px;margin:0 8px 8px 0;border-radius:6px"></a>',
            ((p.image.url, p.image.url) for p in obj.photos.all()),
        )

    @admin.display(description="Joylashuv")
    def map_link(self, obj: Report) -> str:
        lat, lng = obj.location.y, obj.location.x
        return format_html(
            '<a href="https://www.openstreetmap.org/?mlat={}&mlon={}#map=18/{}/{}" '
            'target="_blank" rel="noopener">{:.5f}, {:.5f} — xaritada ochish</a>',
            lat,
            lng,
            lat,
            lng,
            lat,
            lng,
        )

    # ----- Saving: route status changes through the service -----

    def save_model(self, request, obj: Report, form, change: bool) -> None:
        if change and "status" in form.changed_data:
            services.change_status(
                obj,
                form.cleaned_data["status"],
                moderator=request.user,
                rejection_reason=form.cleaned_data.get("rejection_reason", ""),
                note=form.cleaned_data.get("note", ""),
            )
        # Nothing else is editable, so there is nothing else to save.
        # NOTE: save_related() is deliberately NOT overridden. Django's default calls
        # formset.save(), which the admin's change log needs (formset.new_objects).
        # The history inline is fully read-only, so that save changes nothing.

    # ----- Permissions: moderators change status; nobody adds or deletes here -----

    def has_add_permission(self, request) -> bool:
        return False  # reports come from citizens via the app

    def has_delete_permission(self, request, obj=None) -> bool:
        return False  # reject instead; deleting would break history and the points ledger

    # ----- Bulk actions -----

    def _bulk_change(self, request, queryset, to_status: str) -> None:
        done, skipped = 0, 0
        for report in queryset:
            try:
                services.change_status(report, to_status, moderator=request.user)
                done += 1
            except services.InvalidTransition:
                skipped += 1
        self.message_user(request, f"{done} ta murojaat yangilandi.", messages.SUCCESS)
        if skipped:
            self.message_user(
                request,
                f"{skipped} ta murojaat o'tkazib yuborildi (bu holatdan o'tish mumkin emas).",
                messages.WARNING,
            )

    @admin.action(description="Tanlanganlarni tasdiqlash (+10 ball)")
    def verify_selected(self, request, queryset):
        self._bulk_change(request, queryset, Report.Status.VERIFIED)

    @admin.action(description="Jarayonda deb belgilash")
    def mark_in_progress(self, request, queryset):
        self._bulk_change(request, queryset, Report.Status.IN_PROGRESS)

    @admin.action(description="Hal qilindi deb belgilash (+5 ball)")
    def mark_resolved(self, request, queryset):
        self._bulk_change(request, queryset, Report.Status.RESOLVED)
