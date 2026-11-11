"""Minimal client for the WAQI (World Air Quality Index) API.

Two things about this API that the code below handles explicitly:

1. Errors often come back with HTTP 200 and {"status": "error", "data": "Invalid key"},
   so checking the status code alone is not enough.
2. Values in `iaqi` (pm25, pm10, ...) are per-pollutant AQI SUB-INDICES, not concentrations
   in µg/m³. Our Reading fields store them as-is.

The token travels as a query parameter, so error messages here never include the URL.
"""

from dataclasses import dataclass
from datetime import datetime

import httpx
from django.conf import settings

POLLUTANTS = ("pm25", "pm10", "no2", "so2", "co", "o3")


class WaqiError(Exception):
    """Base error for the WAQI client."""


class WaqiUnavailable(WaqiError):
    """Temporary problem (network, timeout, 5xx). Worth retrying later."""


class WaqiInvalidResponse(WaqiError):
    """Permanent problem (bad token, unexpected format). Retrying won't help."""


@dataclass(frozen=True)
class StationInfo:
    uid: str
    name: str
    lat: float
    lng: float


@dataclass(frozen=True)
class ReadingData:
    measured_at: datetime
    aqi: int
    pm25: float | None = None
    pm10: float | None = None
    no2: float | None = None
    so2: float | None = None
    co: float | None = None
    o3: float | None = None


def parse_feed(data: dict) -> ReadingData | None:
    """Turn a /feed/ `data` object into ReadingData. None if the station has no current value."""
    aqi = data.get("aqi")
    # WAQI sends "-" when a station has no data right now. bool is excluded: True is an int.
    if not isinstance(aqi, int) or isinstance(aqi, bool) or not 0 <= aqi <= 999:
        return None

    try:
        measured_at = datetime.fromisoformat(data["time"]["iso"])
    except (KeyError, TypeError, ValueError) as exc:
        raise WaqiInvalidResponse("Feed has no valid time.iso") from exc
    if measured_at.tzinfo is None:
        raise WaqiInvalidResponse("Feed time has no timezone")

    iaqi = data.get("iaqi") or {}

    def value(key: str) -> float | None:
        item = iaqi.get(key)
        v = item.get("v") if isinstance(item, dict) else None
        if not isinstance(v, int | float) or isinstance(v, bool):
            return None
        # Sensors near zero sometimes report negative values (calibration noise).
        # A negative pollution level is physically impossible: treat it as "no data".
        return float(v) if v >= 0 else None

    return ReadingData(measured_at=measured_at, aqi=aqi, **{p: value(p) for p in POLLUTANTS})


class WaqiClient:
    def __init__(
        self,
        token: str,
        base_url: str | None = None,
        timeout: float = 10.0,
        transport: httpx.BaseTransport | None = None,  # tests pass a MockTransport
    ) -> None:
        self._token = token
        self._http = httpx.Client(
            base_url=base_url or settings.WAQI_BASE_URL, timeout=timeout, transport=transport
        )

    def __enter__(self) -> "WaqiClient":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    def close(self) -> None:
        self._http.close()

    def _get(self, path: str, params: dict | None = None):
        try:
            response = self._http.get(path, params={**(params or {}), "token": self._token})
        except httpx.TimeoutException as exc:
            raise WaqiUnavailable("WAQI request timed out") from exc
        except httpx.TransportError as exc:
            raise WaqiUnavailable("WAQI is unreachable") from exc

        if response.status_code >= 500 or response.status_code == 429:
            raise WaqiUnavailable(f"WAQI returned HTTP {response.status_code}")
        if response.status_code != 200:
            raise WaqiInvalidResponse(f"WAQI returned HTTP {response.status_code}")

        try:
            body = response.json()
        except ValueError as exc:
            raise WaqiInvalidResponse("WAQI returned non-JSON body") from exc

        if not isinstance(body, dict) or body.get("status") != "ok":
            detail = body.get("data") if isinstance(body, dict) else None
            raise WaqiInvalidResponse(f"WAQI error: {detail}")
        return body.get("data")

    def stations_in_bounds(
        self, south: float, west: float, north: float, east: float
    ) -> list[StationInfo]:
        data = self._get("/v2/map/bounds", {"latlng": f"{south},{west},{north},{east}"})
        if not isinstance(data, list):
            raise WaqiInvalidResponse("Bounds response is not a list")

        stations = []
        for item in data:
            try:
                stations.append(
                    StationInfo(
                        uid=str(item["uid"]),
                        name=item["station"]["name"],
                        lat=float(item["lat"]),
                        lng=float(item["lon"]),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue  # one malformed entry must not break the whole import
        return stations

    def station_feed(self, uid: str) -> ReadingData | None:
        data = self._get(f"/feed/@{uid}/")
        if not isinstance(data, dict):
            raise WaqiInvalidResponse("Feed response is not an object")
        return parse_feed(data)
