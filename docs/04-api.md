# 04 — API Reference

Base URL: `/api/v1/` · JSON · timestamps ISO 8601 · auth: `Authorization: Bearer <access>`.

## Rate limits

| Who | Limit |
|---|---|
| Anonymous | 60 requests / min |
| Logged-in user | 120 requests / min |
| `auth/login/` | 5 / min |
| `auth/register/` | 5 / hour |
| `reports/` (create) | 10 / hour |

Exceeding a limit returns `429 Too Many Requests`.

## Auth

| Method | Path | Auth | Body | Response |
|---|---|---|---|---|
| POST | `auth/register/` | — | `email`, `password`, `display_name?` | `201` user |
| POST | `auth/login/` | — | `email`, `password` | `200 {access, refresh}` · `401` |
| POST | `auth/refresh/` | — | `refresh` | `200 {access, refresh}` (old refresh is now invalid) |
| POST | `auth/logout/` | — | `refresh` | `200` (refresh token blacklisted) |
| GET / PATCH | `auth/me/` | ✅ | `display_name`, `district` (id) | `200` user |

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

## Reports

| Method | Path | Auth | Input | Response |
|---|---|---|---|---|
| GET | `reports/categories/` | — | — | list of `{slug, name_uz, icon}` |
| POST | `reports/` | ✅ | **multipart**: `category` (slug), `lat`, `lng`, `description?`, `photos` (1–3 files, JPEG/PNG/WEBP, ≤ 5 MB each) | `201` report detail (`status: "new"`, `duplicate_of`) |
| GET | `reports/map/` | — | `bbox=min_lng,min_lat,max_lng,max_lat` (≤ 1° each side), `category?`, `status?` | public, non-duplicate reports (max 500) |
| GET | `reports/mine/` | ✅ | — | my reports, every status, with `thumbnail` |
| GET | `reports/{uuid}/` | optional | — | detail · `404` if not visible to you |
| DELETE | `reports/{uuid}/` | ✅ | — | `204` · `409` if no longer `new` · `404` if not yours |

Status flow: `new → verified → in_progress → resolved`, or `new → rejected`.
`new` / `rejected` reports are visible only to their author. Photos are re-encoded and stripped of EXIF (incl. GPS).

## Eco Points

| Method | Path | Auth | Query | Response |
|---|---|---|---|---|
| GET | `points/me/` | ✅ | — | `{balance, transactions[]}` |
| GET | `points/leaderboard/` | — | `scope=users\|districts`, `period=month\|all` | `{scope, period, results: [{rank, name, points}]}` |

+10 when a report is verified, +5 bonus when resolved. Duplicates earn nothing.

## Errors

| Status | Meaning |
|---|---|
| 400 | Validation error — body is `{ "field": ["message", ...] }` |
| 401 | Missing / invalid / expired token |
| 404 | Not found (or not visible to you) |
| 409 | Conflict — action not allowed in the current state |
| 429 | Rate limit exceeded |
