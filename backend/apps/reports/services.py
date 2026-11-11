"""Business actions for reports (see docs/02-architecture.md: services)."""

from datetime import timedelta

from django.contrib.gis.measure import D
from django.db import transaction
from django.utils import timezone

from apps.air.selectors import make_point
from apps.geo.selectors import district_for_point
from apps.points.models import PointTransaction
from apps.points.services import RESOLVED_BONUS, VERIFIED_POINTS, award_points

from .images import ProcessedImage
from .models import Category, Report, ReportPhoto, StatusHistory

S = Report.Status

# The status workflow as a state machine (FR-R6). Anything not listed here is forbidden.
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    S.NEW: {S.VERIFIED, S.REJECTED},
    S.VERIFIED: {S.IN_PROGRESS, S.RESOLVED},
    S.IN_PROGRESS: {S.RESOLVED},
    S.RESOLVED: set(),  # final
    S.REJECTED: set(),  # final
}


class InvalidTransition(Exception):
    """Status change not allowed by the workflow. The message is safe to show to moderators."""


DUPLICATE_RADIUS = D(m=50)
DUPLICATE_WINDOW = timedelta(days=30)
# ~111 m per 0.001° of latitude; generous so the index pre-filter never misses a real match.
DUPLICATE_PREFILTER_DEGREES = 0.001


class ReportNotDeletable(Exception):
    """Only `new` reports can be deleted by their author (FR-R7)."""


def find_duplicate(category: Category, lat: float, lng: float) -> Report | None:
    """An open report of the same category within 50 m, created in the last 30 days. [FR-R5]

    Two-step distance filter:
    1. `dwithin` in DEGREES — cheap and uses the GiST index, but degrees are not metres
       (a degree of longitude shrinks towards the poles), so it's only a rough pre-filter.
    2. `distance_lte` in METRES — exact (spherical distance) on the few rows left.
    """
    point = make_point(lat, lng)
    return (
        Report.objects.filter(
            category=category,
            status__in=Report.OPEN_STATUSES,
            duplicate_of__isnull=True,  # always link to the original, never to a duplicate
            created_at__gte=timezone.now() - DUPLICATE_WINDOW,
            location__dwithin=(point, DUPLICATE_PREFILTER_DEGREES),
            location__distance_lte=(point, DUPLICATE_RADIUS),
        )
        .order_by("created_at")
        .first()
    )


def create_report(
    *,
    author,
    category: Category,
    lat: float,
    lng: float,
    images: list[ProcessedImage],
    description: str = "",
) -> Report:
    """Create a report with its photos and first history entry, all-or-nothing. [FR-R1]

    Images are already validated and re-encoded (see images.py) before we get here,
    so slow work happens outside the transaction and bad uploads never touch the DB.
    """
    point = make_point(lat, lng)

    with transaction.atomic():
        report = Report.objects.create(
            author=author,
            category=category,
            description=description,
            location=point,
            district=district_for_point(point),
            duplicate_of=find_duplicate(category, lat, lng),
        )
        for position, image in enumerate(images, start=1):
            photo = ReportPhoto(
                report=report, position=position, width=image.width, height=image.height
            )
            photo.image.save("photo.jpg", image.content, save=False)  # name is replaced anyway
            photo.save()
        StatusHistory.objects.create(
            report=report, from_status="", to_status=Report.Status.NEW, changed_by=author
        )
    return report


def delete_report(report: Report) -> None:
    """Author deletes their own report — allowed only while it is `new`. [FR-R7]"""
    if report.status != Report.Status.NEW:
        raise ReportNotDeletable

    photos = list(report.photos.all())
    with transaction.atomic():
        report.delete()
    # Delete files only after the DB delete succeeded; the DB is the source of truth.
    for photo in photos:
        photo.image.delete(save=False)


def validate_transition(from_status: str, to_status: str, rejection_reason: str = "") -> None:
    if to_status not in ALLOWED_TRANSITIONS[from_status]:
        raise InvalidTransition(
            f"'{S(from_status).label}' holatidan '{S(to_status).label}' holatiga o'tib bo'lmaydi."
        )
    if to_status == S.REJECTED and not rejection_reason.strip():
        raise InvalidTransition("Rad etish sababi majburiy.")


def change_status(
    report: Report,
    to_status: str,
    *,
    moderator,
    rejection_reason: str = "",
    note: str = "",
) -> Report:
    """The ONLY way a report's status changes (admin, future API, scripts). [FR-R6, FR-M2, FR-M3]

    One transaction: status + history row + points. Either all of it happens or none.
    """
    with transaction.atomic():
        # Lock the row until the transaction ends. A second moderator verifying the same
        # report at the same moment waits here, then sees the NEW status and is refused —
        # instead of both of them "verifying" it.
        report = Report.objects.select_for_update().get(pk=report.pk)
        validate_transition(report.status, to_status, rejection_reason)

        from_status = report.status
        report.status = to_status
        update_fields = ["status", "updated_at"]
        now = timezone.now()
        if to_status == S.VERIFIED:
            report.verified_at = now
            update_fields.append("verified_at")
        elif to_status == S.RESOLVED:
            report.resolved_at = now
            update_fields.append("resolved_at")
        elif to_status == S.REJECTED:
            report.rejection_reason = rejection_reason.strip()
            update_fields.append("rejection_reason")
        report.save(update_fields=update_fields)

        StatusHistory.objects.create(
            report=report,
            from_status=from_status,
            to_status=to_status,
            changed_by=moderator,
            note=note,
        )

        # Duplicates earn no points: otherwise ten people photographing the same dump
        # would earn ten times the points for one problem.
        if report.duplicate_of_id is None:
            if to_status == S.VERIFIED:
                award_points(
                    user=report.author,
                    amount=VERIFIED_POINTS,
                    reason=PointTransaction.Reason.REPORT_VERIFIED,
                    report=report,
                    created_by=moderator,
                )
            elif to_status == S.RESOLVED:
                award_points(
                    user=report.author,
                    amount=RESOLVED_BONUS,
                    reason=PointTransaction.Reason.REPORT_RESOLVED,
                    report=report,
                    created_by=moderator,
                )
    return report
