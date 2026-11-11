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


@pytest.fixture
def district(db):
    from apps.geo.models import District, Region

    region = Region.objects.create(name_uz="Toshkent shahri", slug="toshkent-shahri")
    return District.objects.create(region=region, name_uz="Chilonzor", slug="chilonzor")


@pytest.fixture
def other_district(district):
    from apps.geo.models import District

    return District.objects.create(region=district.region, name_uz="Yunusobod", slug="yunusobod")


@pytest.fixture
def moderator(db):
    return get_user_model().objects.create_user(
        email="moderator@eco.uz", password=PASSWORD, display_name="Moderator", is_staff=True
    )
