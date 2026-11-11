from datetime import timedelta

import pytest
from django.db import IntegrityError
from django.utils import timezone

from apps.air.models import Reading
from apps.air.selectors import latest_reading, make_point, nearest_station
from tests.air.factories import CHILONZOR, YUNUSOBOD, make_station

pytestmark = pytest.mark.django_db


def test_make_point_puts_longitude_first():
    point = make_point(lat=41.3, lng=69.2)
    assert (point.x, point.y) == (69.2, 41.3)


def test_station_is_unique_per_source():
    make_station("123", CHILONZOR)
    with pytest.raises(IntegrityError):
        make_station("123", YUNUSOBOD)


def test_reading_is_unique_per_station_and_time():
    station = make_station("1", CHILONZOR)
    now = timezone.now()
    Reading.objects.create(station=station, measured_at=now, aqi=80)

    # Simulates the ingestion task retrying and inserting the same measurement again.
    with pytest.raises(IntegrityError):
        Reading.objects.create(station=station, measured_at=now, aqi=80)


def test_reading_aqi_above_scale_is_rejected_by_database():
    station = make_station("1", CHILONZOR)
    with pytest.raises(IntegrityError):
        Reading.objects.create(station=station, measured_at=timezone.now(), aqi=1000)


def test_nearest_station_uses_real_distance():
    chilonzor = make_station("chil", CHILONZOR)
    make_station("yunus", YUNUSOBOD)

    # A point a few hundred metres from Chilonzor.
    result = nearest_station(lat=41.28, lng=69.21)

    assert result == chilonzor
    assert result.distance.m < 1000  # GeoDjango returns a Distance object; .m = metres


def test_nearest_station_ignores_inactive():
    make_station("chil", CHILONZOR, is_active=False)
    yunusobod = make_station("yunus", YUNUSOBOD)

    assert nearest_station(lat=41.28, lng=69.21) == yunusobod


def test_nearest_station_returns_none_when_no_stations():
    assert nearest_station(lat=41.28, lng=69.21) is None


def test_latest_reading_and_staleness():
    station = make_station("1", CHILONZOR)
    now = timezone.now()
    Reading.objects.create(station=station, measured_at=now - timedelta(hours=5), aqi=60)
    newest = Reading.objects.create(station=station, measured_at=now - timedelta(hours=1), aqi=90)

    latest = latest_reading(station)

    assert latest == newest
    assert not latest.is_stale(now=now)
    assert latest.is_stale(now=now + timedelta(hours=3))
