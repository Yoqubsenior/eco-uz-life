# Backend — Django API

Django 5.2 LTS · DRF · PostgreSQL 16 + PostGIS · Docker.

## Run locally

Requires Docker Desktop. From the **repository root**:

```bash
cp .env.example .env              # PowerShell: Copy-Item .env.example .env
docker compose up --build -d      # build image, start db + api in the background
docker compose exec api python manage.py migrate
docker compose exec api python manage.py createsuperuser
```

- API health check: http://localhost:8000/api/v1/health/
- Admin: http://localhost:8000/admin/
- Postgres from host tools: `localhost:5433`

## Common commands

```bash
docker compose exec api pytest                       # run tests
docker compose exec api ruff check .                 # lint
docker compose exec api python manage.py makemigrations
docker compose logs -f api                           # follow logs
docker compose down                                  # stop (data is kept in the pgdata volume)
```

## Structure

See [docs/02-architecture.md](../docs/02-architecture.md#3-backend-structure).
