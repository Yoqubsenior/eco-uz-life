# 🌿 Eco UZ Life

> Community-driven environmental monitoring for Uzbekistan — see the air you breathe, report what's wrong, get rewarded for fixing it.

Eco UZ Life is an Android app (React Native + Expo) backed by a Django REST API with PostGIS. Citizens can:

- **Check air quality** (AQI, PM2.5, PM10, NO₂…) at the nearest monitoring station, with health advice.
- **Report environmental problems** — illegal dumps, damaged trees, broken irrigation — with a photo and GPS location.
- **Earn Eco Points** when moderators verify their reports, and compete on user and district leaderboards.

> **Status:** 🚧 Stage 1 — Requirements & Architecture. See the [roadmap](#roadmap).

---

## Tech stack

| Layer | Technology |
|---|---|
| Mobile | React Native, Expo, expo-router, TanStack Query, react-native-maps |
| API | Python 3.12, Django 5.2 LTS, Django REST Framework, SimpleJWT |
| Database | PostgreSQL 16 + PostGIS (GeoDjango) |
| Background jobs | Celery + Celery Beat, Redis |
| Moderation | Django Admin (customised) |
| Infra | Docker Compose, GitHub Actions CI |

## Repository structure

```
eco-uz-life/
├── backend/            Django project (API, business logic, admin)
├── mobile/             Expo app (Android first)
├── docs/
│   ├── 01-requirements.md
│   └── 02-architecture.md
├── .env.example        Environment variables template (copy to .env)
├── .editorconfig
├── .gitattributes
└── .gitignore
```

## Documentation

1. [Requirements](docs/01-requirements.md) — roles, features, MVP scope, non-functional requirements
2. [Architecture](docs/02-architecture.md) — components, data flows, key technical decisions

## Roadmap

- [x] **Stage 1** — Requirements, architecture, repository skeleton
- [ ] **Stage 2** — Database design (GeoDjango models, ERD)
- [ ] **Stage 3** — Backend: project setup, Docker, auth (JWT)
- [ ] **Stage 4** — Backend: air quality module + Celery ingestion
- [ ] **Stage 5** — Backend: reports, moderation, Eco Points
- [ ] **Stage 6** — Mobile: auth, map, air quality screen
- [ ] **Stage 7** — Mobile: report flow (camera + GPS), profile, leaderboard
- [ ] **Stage 8** — Testing, security hardening, CI
- [ ] **Stage 9** — Deployment + Android APK release

## License

MIT — see `LICENSE` (to be added).
