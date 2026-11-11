import pytest

from apps.air.models import Reading, Station
from apps.air.services import ingest_air_quality
from apps.air.tasks import fetch_air_quality
from tests.air.fake_waqi import FakeWaqi, feed, station_entry

pytestmark = pytest.mark.django_db

BOUNDS_PATH = "/v2/map/bounds"
AREA = (41.15, 69.05, 41.45, 69.45)


def two_station_routes(feed_1=None, feed_2=None) -> dict:
    return {
        BOUNDS_PATH: {
            "status": "ok",
            "data": [
                station_entry(101, "Chilonzor", 41.2756, 69.2040),
                station_entry(102, "Yunusobod", 41.3647, 69.2867),
            ],
        },
        "/feed/@101/": feed_1 or feed(85, pm25={"v": 85}),
        "/feed/@102/": feed_2 or feed(120, pm25={"v": 120}),
    }


def test_ingest_creates_stations_and_readings():
    fake = FakeWaqi(two_station_routes())

    with fake.client() as client:
        result = ingest_air_quality(client, AREA)

    assert result.stations_created == 2
    assert result.readings_created == 2
    chilonzor = Station.objects.get(external_id="101")
    assert (chilonzor.location.x, chilonzor.location.y) == (69.2040, 41.2756)  # lng, lat
    assert chilonzor.last_reading_at is not None
    assert chilonzor.readings.get().aqi == 85


def test_ingest_is_idempotent():
    """The homework question: a retried task must not duplicate data."""
    fake = FakeWaqi(two_station_routes())

    with fake.client() as client:
        ingest_air_quality(client, AREA)
        second = ingest_air_quality(client, AREA)  # same data again, like a retry

    assert second.stations_created == 0
    assert second.readings_created == 0
    assert Station.objects.count() == 2
    assert Reading.objects.count() == 2


def test_station_without_current_value_is_skipped():
    fake = FakeWaqi(two_station_routes(feed_2=feed("-")))

    with fake.client() as client:
        result = ingest_air_quality(client, AREA)

    assert result.readings_created == 1
    assert result.skipped == 1


def test_one_broken_station_does_not_stop_the_others():
    broken = {"status": "error", "data": "Unknown station"}
    fake = FakeWaqi(two_station_routes(feed_1=broken))

    with fake.client() as client:
        result = ingest_air_quality(client, AREA)

    assert result.readings_created == 1
    assert Reading.objects.get().station.external_id == "102"


def test_inactive_station_is_not_fetched_and_admin_fields_are_kept():
    fake = FakeWaqi(two_station_routes())
    with fake.client() as client:
        ingest_air_quality(client, AREA)
    Station.objects.filter(external_id="102").update(is_active=False)
    fake.calls.clear()

    with fake.client() as client:
        ingest_air_quality(client, AREA)

    assert "/feed/@102/" not in fake.paths()
    assert Station.objects.get(external_id="102").is_active is False  # not overwritten


def test_task_skips_without_token(settings):
    settings.AIR_API_TOKEN = ""

    assert fetch_air_quality() == {"skipped": "no token"}
