import pytest

pytestmark = pytest.mark.django_db

ME = "/api/v1/auth/me/"


def test_user_can_set_home_district(auth_client, district):
    response = auth_client.patch(ME, {"district": district.id}, format="json")

    assert response.status_code == 200
    assert response.json()["district"] == district.id
    assert response.json()["district_name"] == "Chilonzor"


def test_unknown_district_is_rejected(auth_client):
    response = auth_client.patch(ME, {"district": 999999}, format="json")

    assert response.status_code == 400
    assert "district" in response.json()
