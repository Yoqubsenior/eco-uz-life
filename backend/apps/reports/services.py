"""Business actions for reports (see docs/02-architecture.md: services)."""

from datetime import timedelta

from django.contrib.gis.measure import D
from django.db import transaction
from django.utils import timezone

from apps.air.selectors import make_point
from apps.geo.selectors import district_for_point

from .images import ProcessedImage
from .models import Category, Report, ReportPhoto, StatusHistory

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
