from datetime import timedelta

from django.contrib.gis.db import models
from django.utils import timezone

from apps.geo.models import District

STALE_AFTER = timedelta(hours=3)  # US-2: show "data may be outdated" after this


class Station(models.Model):
    """An air monitoring station from an external data source."""

    class Source(models.TextChoices):
        WAQI = "waqi", "WAQI (aqicn.org)"

    source = models.CharField(max_length=20, choices=Source.choices)
    external_id = models.CharField(max_length=64)  # the station's id in the source system
    name = models.CharField(max_length=200)
    location = models.PointField(srid=4326)
    district = models.ForeignKey(
        District, on_delete=models.SET_NULL, null=True, blank=True, related_name="stations"
    )
    is_active = models.BooleanField(default=True)
    last_reading_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # Importing the same station twice is impossible.
            models.UniqueConstraint(
                fields=["source", "external_id"], name="air_station_source_external_uniq"
            ),
        ]

    def __str__(self) -> str:
        return self.name


class Reading(models.Model):
    """One hourly measurement. Append-only: written by the ingestion task, never edited."""

    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name="readings")
    measured_at = models.DateTimeField()
    aqi = models.PositiveSmallIntegerField()
    # Individual pollutants are optional: not every station measures every one.
    pm25 = models.FloatField(null=True, blank=True)
    pm10 = models.FloatField(null=True, blank=True)
    no2 = models.FloatField(null=True, blank=True)
    so2 = models.FloatField(null=True, blank=True)
    co = models.FloatField(null=True, blank=True)
    o3 = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # No default `ordering`: on a large, growing table it would add ORDER BY to every query.
        get_latest_by = "measured_at"
        constraints = [
            # A retried ingestion task can't store the same measurement twice.
            # Its index (station, measured_at) also serves "latest reading" and history queries.
            models.UniqueConstraint(
                fields=["station", "measured_at"], name="air_reading_station_time_uniq"
            ),
            models.CheckConstraint(condition=models.Q(aqi__lte=999), name="air_reading_aqi_range"),
        ]

    def __str__(self) -> str:
        return f"{self.station} @ {self.measured_at:%Y-%m-%d %H:%M} = {self.aqi}"

    def is_stale(self, now=None) -> bool:
        return (now or timezone.now()) - self.measured_at > STALE_AFTER
