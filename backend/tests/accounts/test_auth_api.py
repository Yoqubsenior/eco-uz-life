import pytest
from django.contrib.auth import get_user_model

from tests.constants import PASSWORD

User = get_user_model()
pytestmark = pytest.mark.django_db

REGISTER = "/api/v1/auth/register/"
LOGIN = "/api/v1/auth/login/"
REFRESH = "/api/v1/auth/refresh/"
LOGOUT = "/api/v1/auth/logout/"
ME = "/api/v1/auth/me/"


# ---------- Register [FR-A1] ----------


def test_register_creates_user_and_never_returns_password(api_client):
    response = api_client.post(
        REGISTER,
        {"email": "Vali@Mail.uz", "password": PASSWORD, "display_name": "Vali"},
        format="json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "vali@mail.uz"
    assert "password" not in body
    assert User.objects.get(email="vali@mail.uz").check_password(PASSWORD)


def test_register_rejects_duplicate_email_case_insensitively(api_client, user):
    response = api_client.post(
        REGISTER, {"email": "ALI@mail.uz", "password": PASSWORD}, format="json"
    )

    assert response.status_code == 400
    assert "email" in response.json()


@pytest.mark.parametrize("weak", ["12345678", "short", "password123"])
def test_register_rejects_weak_password(api_client, weak):
    response = api_client.post(REGISTER, {"email": "new@mail.uz", "password": weak}, format="json")

    assert response.status_code == 400
    assert "password" in response.json()
    assert not User.objects.filter(email="new@mail.uz").exists()


# ---------- Login [FR-A2] ----------


def test_login_returns_access_and_refresh(api_client, user):
    response = api_client.post(LOGIN, {"email": "ALI@MAIL.UZ", "password": PASSWORD}, format="json")

    assert response.status_code == 200
    assert {"access", "refresh"} <= response.json().keys()


@pytest.mark.parametrize(
    "email, password",
    [("ali@mail.uz", "wrong-password"), ("nobody@mail.uz", PASSWORD)],
)
def test_login_failure_gives_same_answer_for_wrong_password_and_unknown_email(
    api_client, user, email, password
):
    response = api_client.post(LOGIN, {"email": email, "password": password}, format="json")

    assert response.status_code == 401
    assert "access" not in response.json()


def test_login_is_rate_limited(api_client, user):
    for _ in range(5):
        api_client.post(LOGIN, {"email": user.email, "password": "wrong"}, format="json")

    response = api_client.post(LOGIN, {"email": user.email, "password": PASSWORD}, format="json")

    # Even the correct password is refused once the limit is hit.
    assert response.status_code == 429


# ---------- Me [FR-A5] ----------


def test_me_requires_authentication(api_client):
    assert api_client.get(ME).status_code == 401


def test_me_returns_current_user(auth_client, user):
    response = auth_client.get(ME)

    assert response.status_code == 200
    assert response.json()["email"] == user.email


def test_me_updates_display_name_but_not_email(auth_client, user):
    response = auth_client.patch(
        ME, {"display_name": "Ali Valiyev", "email": "hacker@mail.uz"}, format="json"
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.display_name == "Ali Valiyev"
    assert user.email == "ali@mail.uz"


# ---------- Refresh rotation [FR-A3] & logout [FR-A4] ----------


def test_refresh_rotates_token_and_old_one_stops_working(api_client, tokens):
    old_refresh = tokens["refresh"]

    first = api_client.post(REFRESH, {"refresh": old_refresh}, format="json")
    assert first.status_code == 200
    assert first.json()["refresh"] != old_refresh

    # Reusing the old refresh token (e.g. stolen copy) is rejected.
    reuse = api_client.post(REFRESH, {"refresh": old_refresh}, format="json")
    assert reuse.status_code == 401


def test_logout_blacklists_refresh_token(api_client, tokens):
    logout = api_client.post(LOGOUT, {"refresh": tokens["refresh"]}, format="json")
    assert logout.status_code == 200

    after = api_client.post(REFRESH, {"refresh": tokens["refresh"]}, format="json")
    assert after.status_code == 401
