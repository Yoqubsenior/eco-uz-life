from io import BytesIO

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient

from apps.reports.images import process_image
from apps.reports.models import Category
from apps.reports.services import create_report
from tests.constants import PASSWORD


@pytest.fixture(autouse=True)
def _media_in_tmp(settings, tmp_path):
    # Uploaded files go to a temporary folder that pytest deletes, never into the project.
    settings.MEDIA_ROOT = tmp_path


def make_upload(
    fmt: str = "JPEG",
    size: tuple[int, int] = (800, 600),
    mode: str = "RGB",
    exif=None,
    name: str = "photo.jpg",
) -> SimpleUploadedFile:
    buffer = BytesIO()
    image = Image.new(mode, size, color="green" if mode != "RGBA" else (0, 128, 0, 128))
    kwargs = {"exif": exif} if exif is not None else {}
    image.save(buffer, format=fmt, **kwargs)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/jpeg")


@pytest.fixture
def category(db) -> Category:
    return Category.objects.create(slug="illegal-dump", name_uz="Noqonuniy chiqindixona")


@pytest.fixture
def other_category(db) -> Category:
    return Category.objects.create(slug="tree-damage", name_uz="Daraxtga zarar")


@pytest.fixture
def other_user(db):
    return get_user_model().objects.create_user(email="vali@mail.uz", password=PASSWORD)


@pytest.fixture
def other_client(other_user) -> APIClient:
    client = APIClient()
    client.force_authenticate(other_user)
    return client


@pytest.fixture
def make_report(category):
    """Create a report through the real service (with a real processed photo)."""

    def _make(author, lat_lng, cat=None):
        lat, lng = lat_lng
        return create_report(
            author=author,
            category=cat or category,
            lat=lat,
            lng=lng,
            images=[process_image(make_upload())],
        )

    return _make
