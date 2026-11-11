from django.db import IntegrityError, transaction

from .models import PointTransaction

VERIFIED_POINTS = 10
RESOLVED_BONUS = 5


def award_points(
    *, user, amount: int, reason: str, report=None, created_by=None
) -> PointTransaction | None:
    """Add a ledger row. Returns None if these points were already awarded (idempotent).

    The database decides "already awarded" via the partial unique constraint — not a Python
    `if exists()` check, which two concurrent requests could both pass (race condition).

    The inner atomic() creates a SAVEPOINT: if the INSERT fails, only it is rolled back,
    not the caller's whole transaction (e.g. the status change around it).
    """
    try:
        with transaction.atomic():
            return PointTransaction.objects.create(
                user=user,
                amount=amount,
                reason=reason,
                report=report,
                district_id=user.district_id,
                created_by=created_by,
            )
    except IntegrityError:
        return None
