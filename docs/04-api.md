# 04 — API Reference

Base URL: `/api/v1/` · JSON · timestamps ISO 8601 · auth: `Authorization: Bearer <access>`.

## Rate limits

| Who | Limit |
|---|---|
| Anonymous | 60 requests / min |
| Logged-in user | 120 requests / min |
| `auth/login/` | 5 / min |
| `auth/register/` | 5 / hour |

Exceeding a limit returns `429 Too Many Requests`.

## Auth

| Method | Path | Auth | Body | Response |
|---|---|---|---|---|
| POST | `auth/register/` | — | `email`, `password`, `display_name?` | `201` user |
| POST | `auth/login/` | — | `email`, `password` | `200 {access, refresh}` · `401` |
| POST | `auth/refresh/` | — | `refresh` | `200 {access, refresh}` (old refresh is now invalid) |
| POST | `auth/logout/` | — | `refresh` | `200` (refresh token blacklisted) |
| GET / PATCH | `auth/me/` | ✅ | `display_name` | `200` user |

## Air quality (public)

| Method | Path | Query | Response |
|---|---|---|---|
| GET | `air/stations/` | — | list of stations with `latest` reading (or `null`) |
| GET | `air/nearest/` | `lat`, `lng` (required) | one station + `distance_m` · `400` bad coords · `404` no stations |
| GET | `air/stations/{id}/history/` | `period` = `24h` (default) \| `7d` | readings oldest → newest |

### Example: `GET /api/v1/air/nearest/?lat=41.28&lng=69.21`

```json
{
  "id": 3,
  "name": "Chilonzor, Tashkent",
  "source": "WAQI (aqicn.org)",
  "lat": 41.2756,
  "lng": 69.204,
  "district": "Chilonzor",
  "distance_m": 712,
  "latest": {
    "measured_at": "2026-11-11T15:00:00Z",
    "aqi": 158,
    "category": {
      "key": "unhealthy",
      "label": "Zararli",
      "color": "#FF0000",
      "advice": "Tashqaridagi og'ir jismoniy faollikni kamaytiring.",
      "sensitive_advice": "Bolalar va sezgir guruhlar tashqarida bo'lmasin, derazalarni yopiq tuting."
    },
    "pollutants": { "pm25": 158.0, "pm10": 61.0, "no2": null, "so2": null, "co": null, "o3": 12.0 },
    "is_stale": false
  }
}
```

- `pollutants` are WAQI per-pollutant **AQI sub-indices**, not µg/m³.
- `is_stale: true` → the reading is older than 3 hours; the app shows "data may be outdated".
- Data source attribution ("WAQI / aqicn.org") must be visible in the app.

## Errors

| Status | Meaning |
|---|---|
| 400 | Validation error — body is `{ "field": ["message", ...] }` |
| 401 | Missing / invalid / expired token |
| 404 | Not found (or not visible to you) |
| 429 | Rate limit exceeded |
