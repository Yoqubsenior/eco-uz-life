import pytest
from django.core.management import call_command
from django.db import IntegrityError

from apps.geo.models import District, Region

pytestmark = pytest.mark.django_db


def test_seed_geo_creates_tashkent_districts_and_is_idempotent():
    call_command("seed_geo")
    call_command("seed_geo")  # running twice must not duplicate anything

    region = Region.objects.get(slug="toshkent-shahri")
    assert region.districts.count() == 12


def test_district_slug_is_unique_within_region_only():
    tashkent = Region.objects.create(name_uz="Toshkent shahri", slug="toshkent-shahri")
    samarkand = Region.objects.create(name_uz="Samarqand viloyati", slug="samarqand")

    District.objects.create(region=tashkent, name_uz="Markaziy", slug="markaziy")
    District.objects.create(region=samarkand, name_uz="Markaziy", slug="markaziy")  # OK

    with pytest.raises(IntegrityError):
        District.objects.create(region=tashkent, name_uz="Markaziy 2", slug="markaziy")
