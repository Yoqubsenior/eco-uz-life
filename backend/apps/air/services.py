"""Business actions for the air module (see docs/02-architecture.md: services)."""

import logging
from dataclasses import dataclass

from apps.geo.selectors import district_for_point

from .models import Reading, Station
from .selectors import make_point
from .waqi import WaqiClient, WaqiInvalidResponse

logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    stations_seen: int = 0
    stations_created: int = 0
    readings_created: int = 0
    skipped: int = 0


def ingest_air_quality(
    client: WaqiClient, bounds: tuple[float, float, float, float]
) -> IngestResult:
    """Import stations and their current readings for an area. [FR-AQ1]

    IDEMPOTENT: running it twice in a row (e.g. a retried task) creates nothing the second time.
    That is guaranteed by the DB constraints UNIQUE(source, external_id) and
    UNIQUE(station, measured_at), combined with update_or_create / get_or_create.

    WaqiUnavailable is NOT caught here: it propagates so the Celery task can retry.
    """
    result = IngestResult()

    for info in client.stations_in_bounds(*bounds):
        result.stations_seen += 1
        point = make_point(info.lat, info.lng)

        station, created = Station.objects.update_or_create(
            source=Station.Source.WAQI,
            external_id=info.uid,
            # Only fields owned by the source. is_active / district are owned by admins.
            defaults={"name": info.name, "location": point},
        )
        if created:
            result.stations_created += 1
            district = district_for_point(point)
            if district:
                station.district = district
                station.save(update_fields=["district"])

        if not station.is_active:
            continue

        try:
            data = client.station_feed(info.uid)
        except WaqiInvalidResponse:
            # One broken station must not stop the others.
            logger.warning("Skipping WAQI station %s: invalid response", info.uid, exc_info=True)
            result.skipped += 1
            continue

        if data is None:
            result.skipped += 1
            continue

        _, reading_created = Reading.objects.get_or_create(
            station=station,
            measured_at=data.measured_at,
            defaults={
                "aqi": data.aqi,
                "pm25": data.pm25,
                "pm10": data.pm10,
                "no2": data.no2,
                "so2": data.so2,
                "co": data.co,
                "o3": data.o3,
            },
        )
        if reading_created:
            result.readings_created += 1
            if station.last_reading_at is None or data.measured_at > station.last_reading_at:
                station.last_reading_at = data.measured_at
                station.save(update_fields=["last_reading_at"])

    return result
