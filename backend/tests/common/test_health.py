import pytest

pytestmark = pytest.mark.django_db


def test_health_is_public_and_reports_database_ok(client):
    response = client.get("/api/v1/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
