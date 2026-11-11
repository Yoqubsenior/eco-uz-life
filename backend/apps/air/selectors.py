"""Read-only queries for the air module (see docs/02-architecture.md: selectors)."""

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point

from .models import Reading, Station


def make_point(lat: float, lng: float) -> Point:
    # The API speaks lat/lng; PostGIS wants (x=lng, y=lat). Convert in ONE place only.
    return Point(lng, lat, srid=4326)


def nearest_station(lat: float, lng: float) -> Station | None:
    """Closest active station to the given location, annotated with `.distance`. [FR-AQ3]"""
    return (
        Station.objects.filter(is_active=True)
        .annotate(distance=Distance("location", make_point(lat, lng)))
        .order_by("distance")
        .first()
    )


def latest_reading(station: Station) -> Reading | None:
    """Most recent reading of a station. [FR-AQ2]"""
    return station.readings.order_by("-measured_at").first()
