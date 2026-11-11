"""Small helpers to create test data with sensible defaults."""

from datetime import datetime

from django.utils import timezone

from apps.air.models import Reading, Station
from apps.air.selectors import make_point

# Real Tashkent coordinates (lat, lng)
CHILONZOR = (41.2756, 69.2040)
YUNUSOBOD = (41.3647, 69.2867)
SERGELI = (41.2263, 69.2195)


def make_station(external_id: str, lat_lng: tuple[float, float], **kwargs) -> Station:
    lat, lng = lat_lng
    kwargs.setdefault("name", f"Station {external_id}")
    return Station.objects.create(
        source=Station.Source.WAQI,
        external_id=external_id,
        location=make_point(lat, lng),
        **kwargs,
    )


def make_reading(station: Station, aqi: int, measured_at: datetime | None = None, **kwargs):
    return Reading.objects.create(
        station=station, aqi=aqi, measured_at=measured_at or timezone.now(), **kwargs
    )
