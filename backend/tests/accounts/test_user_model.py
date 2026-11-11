import pytest
from django.contrib.auth import authenticate, get_user_model
from django.db import IntegrityError

User = get_user_model()
pytestmark = pytest.mark.django_db


def test_create_user_normalizes_email_and_hashes_password():
    user = User.objects.create_user(email="  Ali@Mail.UZ ", password="s3cret-pass")

    assert user.email == "ali@mail.uz"
    assert user.password != "s3cret-pass"  # never stored in plain text
    assert user.check_password("s3cret-pass")
    assert not user.is_staff
    assert not user.is_superuser


def test_create_user_without_email_fails():
    with pytest.raises(ValueError):
        User.objects.create_user(email="", password="x")


def test_create_superuser_sets_flags():
    admin = User.objects.create_superuser(email="admin@eco.uz", password="s3cret-pass")

    assert admin.is_staff
    assert admin.is_superuser


def test_email_is_unique_case_insensitively_at_database_level():
    User.objects.create_user(email="ali@mail.uz", password="x")

    # bulk_create skips save() and its normalisation: only the DB constraint can stop this.
    with pytest.raises(IntegrityError):
        User.objects.bulk_create([User(email="ALI@mail.uz")])


def test_login_is_case_insensitive():
    User.objects.create_user(email="ali@mail.uz", password="s3cret-pass")

    user = authenticate(username="ALI@MAIL.UZ", password="s3cret-pass")

    assert user is not None
    assert user.email == "ali@mail.uz"
