from datetime import timedelta

import pytest
from django.utils import timezone

from tests.air.factories import CHILONZOR, SERGELI, YUNUSOBOD, make_reading, make_station

pytestmark = pytest.mark.django_db

STATIONS = "/api/v1/air/stations/"
NEAREST = "/api/v1/air/nearest/"


def history_url(station_id: int) -> str:
    return f"/api/v1/air/stations/{station_id}/history/"


# ---------- Station list [FR-AQ2] ----------


def test_station_list_is_public_and_includes_latest_reading(api_client):
    station = make_station("1", CHILONZOR, name="Chilonzor")
    make_reading(station, 60, timezone.now() - timedelta(hours=2))
    make_reading(station, 160, timezone.now() - timedelta(minutes=30), pm25=160)

    response = api_client.get(STATIONS)  # no token: guests can see air quality

    assert response.status_code == 200
    [item] = response.json()
    assert (item["lat"], item["lng"]) == CHILONZOR
    assert item["latest"]["aqi"] == 160  # the NEWEST reading, not the first
    assert item["latest"]["category"]["key"] == "unhealthy"
    assert item["latest"]["category"]["color"] == "#FF0000"
    assert item["latest"]["pollutants"]["pm25"] == 160
    assert item["latest"]["is_stale"] is False


def test_station_list_hides_inactive_and_handles_station_without_readings(api_client):
    make_station("1", CHILONZOR, name="A no data")
    make_station("2", YUNUSOBOD, is_active=False)

    [item] = api_client.get(STATIONS).json()

    assert item["name"] == "A no data"
    assert item["latest"] is None


def test_station_list_has_no_n_plus_one(api_client, django_assert_max_num_queries):
    for i, coords in enumerate([CHILONZOR, YUNUSOBOD, SERGELI]):
        station = make_station(str(i), coords)
        make_reading(station, 50 + i)

    # 3 stations or 300 — the number of SQL queries must stay the same:
    # 1 for stations (+ district via JOIN), 1 for all latest readings.
    with django_assert_max_num_queries(2):
        response = api_client.get(STATIONS)

    assert len(response.json()) == 3


# ---------- Nearest station [FR-AQ3] ----------


def test_nearest_returns_closest_station_with_distance(api_client):
    chilonzor = make_station("1", CHILONZOR)
    make_station("2", YUNUSOBOD)
    make_reading(chilonzor, 95)

    response = api_client.get(NEAREST, {"lat": 41.28, "lng": 69.21})

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == chilonzor.id
    assert 0 < body["distance_m"] < 1000
    assert body["latest"]["category"]["key"] == "moderate"


def test_nearest_marks_old_data_as_stale(api_client):
    station = make_station("1", CHILONZOR)
    make_reading(station, 95, timezone.now() - timedelta(hours=5))

    body = api_client.get(NEAREST, {"lat": 41.28, "lng": 69.21}).json()

    assert body["latest"]["is_stale"] is True  # US-2: "data may be outdated"


@pytest.mark.parametrize(
    "params, bad_field",
    [
        ({"lng": 69.2}, "lat"),  # missing
        ({"lat": 100, "lng": 69.2}, "lat"),  # out of range
        ({"lat": "abc", "lng": 69.2}, "lat"),  # not a number
        ({"lat": 41.3, "lng": 200}, "lng"),
    ],
)
def test_nearest_validates_coordinates(api_client, params, bad_field):
    response = api_client.get(NEAREST, params)

    assert response.status_code == 400
    assert bad_field in response.json()


def test_nearest_without_stations_returns_404(api_client):
    assert api_client.get(NEAREST, {"lat": 41.3, "lng": 69.2}).status_code == 404


# ---------- History [FR-AQ4] ----------


def test_history_filters_by_period_and_sorts_oldest_first(api_client):
    station = make_station("1", CHILONZOR)
    now = timezone.now()
    make_reading(station, 70, now - timedelta(hours=2))
    make_reading(station, 80, now - timedelta(hours=30))
    make_reading(station, 90, now - timedelta(days=10))

    day = api_client.get(history_url(station.id)).json()  # default period = 24h
    week = api_client.get(history_url(station.id), {"period": "7d"}).json()

    assert day["period"] == "24h"
    assert [r["aqi"] for r in day["readings"]] == [70]
    assert [r["aqi"] for r in week["readings"]] == [80, 70]  # chronological for charts
    assert week["readings"][0]["color"] == "#FFFF00"


def test_history_rejects_unknown_period(api_client):
    station = make_station("1", CHILONZOR)

    response = api_client.get(history_url(station.id), {"period": "1y"})

    assert response.status_code == 400
    assert "period" in response.json()


def test_history_of_inactive_or_missing_station_is_404(api_client):
    inactive = make_station("1", CHILONZOR, is_active=False)

    assert api_client.get(history_url(inactive.id)).status_code == 404
    assert api_client.get(history_url(999999)).status_code == 404
