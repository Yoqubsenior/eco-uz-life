import uuid

from django.conf import settings
from django.contrib.gis.db import models

from apps.geo.models import District


class Category(models.Model):
    slug = models.SlugField(max_length=50, unique=True)
    name_uz = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True)  # icon name used by the mobile app
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "name_uz"]
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return self.name_uz


class Report(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Yangi"
        VERIFIED = "verified", "Tasdiqlangan"
        IN_PROGRESS = "in_progress", "Jarayonda"
        RESOLVED = "resolved", "Hal qilindi"
        REJECTED = "rejected", "Rad etildi"

    # Visible to everyone (FR-R8). `new` and `rejected` are visible only to the author.
    PUBLIC_STATUSES = (Status.VERIFIED, Status.IN_PROGRESS, Status.RESOLVED)
    # Statuses a new report can be a duplicate of (FR-R5).
    OPEN_STATUSES = (Status.NEW, Status.VERIFIED, Status.IN_PROGRESS)

    # UUID: appears in public URLs, can't be enumerated (decision DB2).
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reports"
    )
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="reports")
    description = models.CharField(max_length=500, blank=True)
    location = models.PointField(srid=4326)
    district = models.ForeignKey(
        District, on_delete=models.SET_NULL, null=True, blank=True, related_name="reports"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    rejection_reason = models.CharField(max_length=300, blank=True)
    duplicate_of = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="duplicates"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"], name="report_status_created_idx"),
            models.Index(fields=["author", "created_at"], name="report_author_created_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                # Literal list: a nested class (Meta) can't see names from the outer class body.
                condition=models.Q(
                    status__in=["new", "verified", "in_progress", "resolved", "rejected"]
                ),
                name="report_status_valid",
            ),
            models.CheckConstraint(
                condition=~models.Q(status="rejected") | ~models.Q(rejection_reason=""),
                name="report_rejected_needs_reason",
            ),
            models.CheckConstraint(
                condition=~models.Q(duplicate_of=models.F("id")),
                name="report_not_own_duplicate",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.category} — {self.get_status_display()} ({self.created_at:%Y-%m-%d})"

    @property
    def is_public(self) -> bool:
        return self.status in self.PUBLIC_STATUSES


def report_photo_path(instance: "ReportPhoto", filename: str) -> str:
    # Never use the user's filename: it can contain "../", script extensions or personal info.
    return f"reports/{instance.report_id}/{uuid.uuid4().hex}.jpg"


class ReportPhoto(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to=report_photo_path)
    position = models.PositiveSmallIntegerField()
    # Set explicitly from ProcessedImage — we already know them, no need to re-read the file.
    width = models.PositiveSmallIntegerField()
    height = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["report", "position"], name="report_photo_position_uniq"
            ),
            models.CheckConstraint(
                condition=models.Q(position__gte=1, position__lte=3),
                name="report_photo_max_three",
            ),
        ]


class StatusHistory(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="history")
    from_status = models.CharField(max_length=20, blank=True)  # "" = report creation
    to_status = models.CharField(max_length=20, choices=Report.Status.choices)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True
    )
    note = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name_plural = "status history"

    def __str__(self) -> str:
        return f"{self.from_status or '∅'} → {self.to_status}"
