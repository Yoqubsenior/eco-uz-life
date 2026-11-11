from datetime import datetime

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.geo.models import District

from .models import PointTransaction

LEADERBOARD_SIZE = 10


def balance(user) -> int:
    """FR-P3: the balance is always derived from the ledger, never stored (decision DB4)."""
    return user.point_transactions.aggregate(total=Coalesce(Sum("amount"), 0))["total"]


def month_start(now: datetime | None = None) -> datetime:
    # "This month" in Tashkent time, not UTC: at 02:00 on the 1st local time it's already
    # a new month for users, while UTC still says the previous day.
    local = timezone.localtime(now)
    return local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _transactions(period: str):
    qs = PointTransaction.objects.all()
    if period == "month":
        qs = qs.filter(created_at__gte=month_start())
    return qs


def top_users(period: str) -> list[dict]:
    """FR-P4. One GROUP BY query. Only display names — never emails."""
    rows = (
        _transactions(period)
        .filter(user__is_active=True)
        .values("user_id")
        .annotate(points=Sum("amount"))
        .filter(points__gt=0)
        .order_by("-points", "user_id")[:LEADERBOARD_SIZE]
    )
    rows = list(rows)
    names = dict(
        get_user_model()
        .objects.filter(id__in=[r["user_id"] for r in rows])
        .values_list("id", "display_name")
    )
    return [
        {"rank": i, "name": names.get(r["user_id"]) or "Foydalanuvchi", "points": r["points"]}
        for i, r in enumerate(rows, start=1)
    ]


def top_districts(period: str) -> list[dict]:
    """FR-P4. Grouped by the district SNAPSHOT stored on each ledger row."""
    rows = list(
        _transactions(period)
        .filter(district__isnull=False)
        .values("district_id")
        .annotate(points=Sum("amount"))
        .filter(points__gt=0)
        .order_by("-points", "district_id")[:LEADERBOARD_SIZE]
    )
    names = dict(
        District.objects.filter(id__in=[r["district_id"] for r in rows]).values_list(
            "id", "name_uz"
        )
    )
    return [
        {"rank": i, "name": names[r["district_id"]], "points": r["points"]}
        for i, r in enumerate(rows, start=1)
    ]
