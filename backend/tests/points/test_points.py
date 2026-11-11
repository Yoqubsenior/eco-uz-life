from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone

from apps.points.models import PointTransaction
from apps.points.selectors import balance, top_districts, top_users
from apps.points.services import award_points
from tests.constants import PASSWORD

pytestmark = pytest.mark.django_db

R = PointTransaction.Reason
LEADERBOARD = "/api/v1/points/leaderboard/"
MY_POINTS = "/api/v1/points/me/"


def make_user(email, name, district=None):
    return get_user_model().objects.create_user(
        email=email, password=PASSWORD, display_name=name, district=district
    )


def test_award_without_report_is_not_limited_but_zero_is_rejected(user):
    award_points(user=user, amount=5, reason=R.ADMIN_ADJUSTMENT)
    award_points(user=user, amount=5, reason=R.ADMIN_ADJUSTMENT)
    assert balance(user) == 10

    with pytest.raises(IntegrityError):
        PointTransaction.objects.create(user=user, amount=0, reason=R.ADMIN_ADJUSTMENT)


def test_balance_is_sum_of_ledger_including_corrections(user):
    award_points(user=user, amount=10, reason=R.ADMIN_ADJUSTMENT)
    award_points(user=user, amount=-3, reason=R.ADMIN_ADJUSTMENT)  # correction = new row

    assert balance(user) == 7
    assert balance(make_user("new@mail.uz", "New")) == 0  # no rows -> 0, not None


def test_district_snapshot_survives_user_moving(district, other_district):
    user = make_user("a@mail.uz", "A", district=district)
    award_points(user=user, amount=10, reason=R.ADMIN_ADJUSTMENT)

    user.district = other_district  # the user moves
    user.save()
    award_points(user=user, amount=3, reason=R.ADMIN_ADJUSTMENT)

    board = {row["name"]: row["points"] for row in top_districts("all")}
    assert board == {"Chilonzor": 10, "Yunusobod": 3}  # history was not rewritten


def test_leaderboard_month_counts_only_this_month(district):
    old_hero = make_user("old@mail.uz", "Old Hero")
    new_hero = make_user("new@mail.uz", "New Hero")
    old_tx = award_points(user=old_hero, amount=100, reason=R.ADMIN_ADJUSTMENT)
    PointTransaction.objects.filter(pk=old_tx.pk).update(
        created_at=timezone.now() - timedelta(days=60)
    )
    award_points(user=new_hero, amount=20, reason=R.ADMIN_ADJUSTMENT)

    assert [r["name"] for r in top_users("month")] == ["New Hero"]
    assert [r["name"] for r in top_users("all")] == ["Old Hero", "New Hero"]
    assert top_users("all")[0]["rank"] == 1


def test_leaderboard_api_is_public_and_never_shows_emails(api_client, user):
    award_points(user=user, amount=10, reason=R.ADMIN_ADJUSTMENT)

    response = api_client.get(LEADERBOARD, {"scope": "users", "period": "all"})

    assert response.status_code == 200
    assert response.json()["results"] == [{"rank": 1, "name": "Ali", "points": 10}]
    assert user.email not in response.content.decode()


def test_leaderboard_api_validates_params(api_client):
    assert api_client.get(LEADERBOARD, {"scope": "planets"}).status_code == 400


def test_my_points_requires_login_and_shows_history(api_client, auth_client, user):
    award_points(user=user, amount=10, reason=R.ADMIN_ADJUSTMENT)

    assert api_client.get(MY_POINTS).status_code == 401
    body = auth_client.get(MY_POINTS).json()
    assert body["balance"] == 10
    assert body["transactions"][0]["reason_display"] == "Administrator tuzatishi"
