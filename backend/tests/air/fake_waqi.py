"""A fake WAQI server for tests: no network, fully controlled responses."""

import httpx

from apps.air.waqi import WaqiClient

TOKEN = "test-token"


def station_entry(uid: int, name: str, lat: float, lng: float) -> dict:
    return {"uid": uid, "lat": lat, "lon": lng, "aqi": "80", "station": {"name": name}}


def feed(aqi, iso: str = "2026-11-11T20:00:00+05:00", **iaqi) -> dict:
    return {"status": "ok", "data": {"aqi": aqi, "time": {"iso": iso}, "iaqi": iaqi}}


class FakeWaqi:
    """Routes request paths to canned responses and records every call."""

    def __init__(self, routes: dict):
        self.routes = routes
        self.calls: list[httpx.Request] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        response = self.routes.get(request.url.path)
        if response is None:
            return httpx.Response(404)
        if callable(response):
            return response(request)
        if isinstance(response, httpx.Response):
            return response
        return httpx.Response(200, json=response)

    def client(self) -> WaqiClient:
        return WaqiClient(
            token=TOKEN, base_url="https://waqi.test", transport=httpx.MockTransport(self.handler)
        )

    def paths(self) -> list[str]:
        return [call.url.path for call in self.calls]
