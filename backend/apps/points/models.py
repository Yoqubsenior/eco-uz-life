from django.conf import settings
from django.db import models


class PointTransaction(models.Model):
    """Append-only Eco Points ledger (decision D4, FR-P2).

    Rows are NEVER updated or deleted. A user's balance is SUM(amount).
    A correction is a new row with a negative amount — so history always explains the balance.
    """

    class Reason(models.TextChoices):
        REPORT_VERIFIED = "report_verified", "Murojaat tasdiqlandi"
        REPORT_RESOLVED = "report_resolved", "Muammo hal qilindi"
        ADMIN_ADJUSTMENT = "admin_adjustment", "Administrator tuzatishi"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="point_transactions"
    )
    amount = models.IntegerField()
    reason = models.CharField(max_length=30, choices=Reason.choices)
    report = models.ForeignKey(
        "reports.Report",
        on_delete=models.PROTECT,  # a report with points can't be deleted: ledger stays whole
        null=True,
        blank=True,
        related_name="point_transactions",
    )
    # Snapshot of the user's district at award time (decision DB5):
    # moving to another district later must not rewrite past leaderboards.
    district = models.ForeignKey(
        "geo.District", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=~models.Q(amount=0), name="points_amount_not_zero"),
            # Idempotency: the same report can't earn the same kind of points twice,
            # no matter how many times the moderator clicks or a request is retried.
            # Partial: admin adjustments (report IS NULL) are not limited.
            models.UniqueConstraint(
                fields=["report", "reason"],
                condition=models.Q(report__isnull=False),
                name="points_once_per_report_and_reason",
            ),
        ]

    def __str__(self) -> str:
        sign = "+" if self.amount > 0 else ""
        return f"{self.user} {sign}{self.amount} ({self.get_reason_display()})"
