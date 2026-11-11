import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

from tests.constants import PASSWORD


@pytest.fixture(autouse=True)
def _clear_cache():
    # Throttle counters live in the cache. Without this, requests from one test
    # would count against the limit in the next test, and tests would fail randomly.
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(
        email="ali@mail.uz", password=PASSWORD, display_name="Ali"
    )


@pytest.fixture
def tokens(api_client, user) -> dict:
    response = api_client.post(
        "/api/v1/auth/login/", {"email": user.email, "password": PASSWORD}, format="json"
    )
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def auth_client(tokens) -> APIClient:
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    return client
