from django.contrib.gis.geos import Polygon
from django.db.models import Q

from .models import Category, Report

MAP_LIMIT = 500


def active_categories():
    return Category.objects.filter(is_active=True)


def public_reports_in_bbox(
    bbox: tuple[float, float, float, float],
    category: str | None = None,
    status: str | None = None,
):
    """Reports for the map: public, originals only, inside the visible area. [FR-R2, FR-R8]

    bbox = (min_lng, min_lat, max_lng, max_lat). `within` uses the GiST index.
    """
    area = Polygon.from_bbox(bbox)
    area.srid = 4326
    reports = Report.objects.filter(
        status__in=Report.PUBLIC_STATUSES,
        duplicate_of__isnull=True,
        location__within=area,
    ).select_related("category")
    if category:
        reports = reports.filter(category__slug=category)
    if status:
        reports = reports.filter(status=status)
    return reports.order_by("-created_at")[:MAP_LIMIT]


def visible_reports(user):
    """Everything this user may see: public reports + their own (any status). [FR-R8]"""
    condition = Q(status__in=Report.PUBLIC_STATUSES)
    if user.is_authenticated:
        condition |= Q(author=user)
    return Report.objects.filter(condition)


def report_detail_queryset(user):
    return (
        visible_reports(user)
        .select_related("category", "district", "author")
        .prefetch_related("photos", "history")
    )


def my_reports(user):
    return (
        Report.objects.filter(author=user)
        .select_related("category")
        .prefetch_related("photos")
        .order_by("-created_at")
    )
