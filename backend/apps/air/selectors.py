"""Read-only queries for the air module (see docs/02-architecture.md: selectors)."""

from datetime import datetime

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point

from .models import Reading, Station


def make_point(lat: float, lng: float) -> Point:
    # The API speaks lat/lng; PostGIS wants (x=lng, y=lat). Convert in ONE place only.
    return Point(lng, lat, srid=4326)


def active_stations():
    return Station.objects.filter(is_active=True).select_related("district").order_by("name")


def nearest_station(lat: float, lng: float) -> Station | None:
    """Closest active station to the given location, annotated with `.distance`. [FR-AQ3]"""
    return (
        Station.objects.filter(is_active=True)
        .select_related("district")
        .annotate(distance=Distance("location", make_point(lat, lng)))
        .order_by("distance")
        .first()
    )


def latest_reading(station: Station) -> Reading | None:
    """Most recent reading of a station. [FR-AQ2]"""
    return station.readings.order_by("-measured_at").first()


def latest_readings_by_station(station_ids: list[int]) -> dict[int, Reading]:
    """Latest reading of MANY stations in ONE query (avoids N+1). [FR-AQ2]

    PostgreSQL `DISTINCT ON (station_id)` keeps the first row per station,
    and ORDER BY station_id, measured_at DESC makes that first row the newest one.
    """
    readings = (
        Reading.objects.filter(station_id__in=station_ids)
        .order_by("station_id", "-measured_at")
        .distinct("station_id")
    )
    return {reading.station_id: reading for reading in readings}


def reading_history(station: Station, since: datetime):
    """Readings from `since` until now, oldest first (ready for a chart). [FR-AQ4]"""
    return station.readings.filter(measured_at__gte=since).order_by("measured_at")
