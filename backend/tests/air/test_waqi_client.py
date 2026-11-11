from datetime import UTC, datetime

import httpx
import pytest

from apps.air.waqi import WaqiInvalidResponse, WaqiUnavailable, parse_feed
from tests.air.fake_waqi import TOKEN, FakeWaqi, feed, station_entry

BOUNDS = "/v2/map/bounds"


# ---------- parse_feed (pure function) ----------


def test_parse_feed_reads_aqi_time_and_pollutants():
    data = feed(85, pm25={"v": 85}, pm10={"v": 40.5}, t={"v": 12})["data"]

    reading = parse_feed(data)

    assert reading.aqi == 85
    assert reading.pm25 == 85.0
    assert reading.pm10 == 40.5
    assert reading.no2 is None  # station doesn't measure it
    # 20:00 in Tashkent (+05:00) is 15:00 UTC — timezone must be preserved.
    assert reading.measured_at == datetime(2026, 11, 11, 15, 0, tzinfo=UTC)


@pytest.mark.parametrize("bad_aqi", ["-", None, -5, 1000, True])
def test_parse_feed_returns_none_when_station_has_no_valid_value(bad_aqi):
    assert parse_feed(feed(bad_aqi)["data"]) is None


def test_parse_feed_rejects_missing_time():
    with pytest.raises(WaqiInvalidResponse):
        parse_feed({"aqi": 50})


# ---------- HTTP behaviour ----------


def test_token_is_sent_as_query_parameter():
    fake = FakeWaqi({BOUNDS: {"status": "ok", "data": []}})

    with fake.client() as client:
        client.stations_in_bounds(41.1, 69.0, 41.5, 69.5)

    assert fake.calls[0].url.params["token"] == TOKEN


def test_stations_in_bounds_skips_malformed_entries():
    fake = FakeWaqi(
        {
            BOUNDS: {
                "status": "ok",
                "data": [station_entry(1, "Chilonzor", 41.27, 69.20), {"uid": 2}],
            }
        }
    )

    with fake.client() as client:
        stations = client.stations_in_bounds(41.1, 69.0, 41.5, 69.5)

    assert [s.uid for s in stations] == ["1"]
    assert (stations[0].lat, stations[0].lng) == (41.27, 69.20)


def test_error_with_http_200_is_detected_and_token_not_leaked():
    # WAQI reports a bad token with HTTP 200 — checking status_code alone would miss it.
    fake = FakeWaqi({BOUNDS: {"status": "error", "data": "Invalid key"}})

    with fake.client() as client, pytest.raises(WaqiInvalidResponse) as exc_info:
        client.stations_in_bounds(41.1, 69.0, 41.5, 69.5)

    assert "Invalid key" in str(exc_info.value)
    assert TOKEN not in str(exc_info.value)


@pytest.mark.parametrize("status", [500, 502, 503, 429])
def test_server_errors_are_temporary(status):
    fake = FakeWaqi({BOUNDS: httpx.Response(status)})

    with fake.client() as client, pytest.raises(WaqiUnavailable):
        client.stations_in_bounds(41.1, 69.0, 41.5, 69.5)


def test_timeout_is_temporary():
    def timeout(request):
        raise httpx.ConnectTimeout("timed out", request=request)

    fake = FakeWaqi({BOUNDS: timeout})

    with fake.client() as client, pytest.raises(WaqiUnavailable):
        client.stations_in_bounds(41.1, 69.0, 41.5, 69.5)


def test_non_json_body_is_invalid():
    fake = FakeWaqi({BOUNDS: httpx.Response(200, text="<html>maintenance</html>")})

    with fake.client() as client, pytest.raises(WaqiInvalidResponse):
        client.stations_in_bounds(41.1, 69.0, 41.5, 69.5)
