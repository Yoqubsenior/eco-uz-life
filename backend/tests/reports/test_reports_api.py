from pathlib import Path

import pytest
from django.conf import settings

from apps.reports.models import Report
from tests.air.factories import CHILONZOR, YUNUSOBOD
from tests.reports.conftest import make_upload

pytestmark = pytest.mark.django_db

CREATE = "/api/v1/reports/"
MAP = "/api/v1/reports/map/"
MINE = "/api/v1/reports/mine/"
TASHKENT_BBOX = "69.1,41.2,69.4,41.45"


def detail_url(report_id) -> str:
    return f"/api/v1/reports/{report_id}/"


def payload(category="illegal-dump", lat_lng=CHILONZOR, photos=1, **extra) -> dict:
    lat, lng = lat_lng
    return {
        "category": category,
        "lat": lat,
        "lng": lng,
        "description": "Ariq bo'yida chiqindi",
        "photos": [make_upload() for _ in range(photos)],
        **extra,
    }


def set_status(report, status, **fields):
    Report.objects.filter(pk=report.pk).update(status=status, **fields)


# ---------- Create [FR-R1] ----------


def test_create_requires_login(api_client, category):
    response = api_client.post(CREATE, payload(), format="multipart")
    assert response.status_code == 401


def test_create_report_with_photo(auth_client, category):
    response = auth_client.post(CREATE, payload(photos=2), format="multipart")

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "new"
    assert body["is_mine"] is True
    assert body["category"]["slug"] == "illegal-dump"
    assert [h["to_status"] for h in body["history"]] == ["new"]
    assert len(body["photos"]) == 2

    report = Report.objects.get(pk=body["id"])
    stored = Path(settings.MEDIA_ROOT) / report.photos.first().image.name
    assert stored.exists()
    assert stored.suffix == ".jpg"
    assert "photo" not in stored.name  # the user's filename is never used


@pytest.mark.parametrize("count", [0, 4])
def test_create_requires_one_to_three_photos(auth_client, category, count):
    response = auth_client.post(CREATE, payload(photos=count), format="multipart")

    assert response.status_code == 400
    assert "photos" in response.json()
    assert not Report.objects.exists()


def test_create_rejects_location_outside_uzbekistan(auth_client, category):
    london = (51.5, -0.12)
    response = auth_client.post(CREATE, payload(lat_lng=london), format="multipart")

    assert response.status_code == 400
    assert "lat" in response.json()


def test_create_rejects_fake_image_and_saves_nothing(auth_client, category):
    data = payload(photos=0)
    data["photos"] = [make_upload(), make_upload(fmt="GIF", mode="P", name="x.gif")]

    response = auth_client.post(CREATE, data, format="multipart")

    assert response.status_code == 400
    assert "2-rasm" in response.json()["photos"][0]
    assert not Report.objects.exists()  # all-or-nothing


def test_create_rejects_inactive_category(auth_client, category):
    category.is_active = False
    category.save()

    response = auth_client.post(CREATE, payload(), format="multipart")

    assert response.status_code == 400
    assert "category" in response.json()


# ---------- Visibility [FR-R3, FR-R8] ----------


def test_new_report_is_visible_only_to_its_author(
    auth_client, other_client, api_client, user, make_report
):
    report = make_report(user, CHILONZOR)

    assert auth_client.get(detail_url(report.id)).status_code == 200
    assert other_client.get(detail_url(report.id)).status_code == 404  # 404, not 403
    assert api_client.get(detail_url(report.id)).status_code == 404


def test_public_report_is_visible_to_everyone_without_email(api_client, user, make_report):
    report = make_report(user, CHILONZOR)
    set_status(report, "verified")

    response = api_client.get(detail_url(report.id))

    assert response.status_code == 200
    assert response.json()["author_name"] == "Ali"
    assert user.email not in response.content.decode()  # privacy
    assert response.json()["is_mine"] is False


def test_rejection_reason_is_shown_to_author(auth_client, user, make_report):
    report = make_report(user, CHILONZOR)
    set_status(report, "rejected", rejection_reason="Rasm aniq emas")

    body = auth_client.get(detail_url(report.id)).json()

    assert body["status"] == "rejected"
    assert body["rejection_reason"] == "Rasm aniq emas"


# ---------- Duplicates [FR-R5] ----------


def test_report_within_50m_same_category_is_linked_as_duplicate(
    auth_client, other_user, make_report
):
    original = make_report(other_user, CHILONZOR)
    about_20m_north = (CHILONZOR[0] + 0.00018, CHILONZOR[1])

    body = auth_client.post(CREATE, payload(lat_lng=about_20m_north), format="multipart").json()

    assert body["duplicate_of"] == str(original.id)


def test_far_away_or_other_category_is_not_a_duplicate(
    auth_client, other_user, other_category, make_report
):
    make_report(other_user, CHILONZOR)
    about_200m_north = (CHILONZOR[0] + 0.0018, CHILONZOR[1])

    far = auth_client.post(CREATE, payload(lat_lng=about_200m_north), format="multipart")
    other_cat = auth_client.post(CREATE, payload(category="tree-damage"), format="multipart")

    assert far.json()["duplicate_of"] is None
    assert other_cat.json()["duplicate_of"] is None


# ---------- Map [FR-R2] ----------


def test_map_shows_only_public_original_reports_inside_bbox(api_client, user, make_report):
    public = make_report(user, CHILONZOR)
    set_status(public, "verified")
    make_report(user, YUNUSOBOD)  # still `new` -> hidden
    duplicate = make_report(user, (CHILONZOR[0] + 0.0001, CHILONZOR[1]))
    set_status(duplicate, "verified")  # verified, but a duplicate -> hidden
    far = make_report(user, (40.0, 65.0))  # Navoiy region, outside the bbox
    set_status(far, "verified")

    response = api_client.get(MAP, {"bbox": TASHKENT_BBOX})

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [str(public.id)]
    assert response.json()[0]["lat"] == CHILONZOR[0]


@pytest.mark.parametrize(
    "bbox",
    [
        "abc",
        "69.1,41.2,69.4",
        "69.4,41.2,69.1,41.45",
        "60,35,75,46",
    ],  # bad / 3 parts / min>max / huge
)
def test_map_validates_bbox(api_client, bbox):
    response = api_client.get(MAP, {"bbox": bbox})

    assert response.status_code == 400
    assert "bbox" in response.json()


# ---------- Mine [FR-R4] ----------


def test_mine_lists_own_reports_in_every_status(auth_client, user, other_user, make_report):
    mine_new = make_report(user, CHILONZOR)
    mine_rejected = make_report(user, YUNUSOBOD)
    set_status(mine_rejected, "rejected", rejection_reason="x")
    make_report(other_user, CHILONZOR)

    ids = {item["id"] for item in auth_client.get(MINE).json()}

    assert ids == {str(mine_new.id), str(mine_rejected.id)}


# ---------- Delete [FR-R7] ----------


def test_author_can_delete_new_report_and_files_are_removed(auth_client, user, make_report):
    report = make_report(user, CHILONZOR)
    stored = Path(settings.MEDIA_ROOT) / report.photos.first().image.name

    response = auth_client.delete(detail_url(report.id))

    assert response.status_code == 204
    assert not Report.objects.filter(pk=report.pk).exists()
    assert not stored.exists()


def test_verified_report_cannot_be_deleted(auth_client, user, make_report):
    report = make_report(user, CHILONZOR)
    set_status(report, "verified")

    assert auth_client.delete(detail_url(report.id)).status_code == 409


def test_cannot_delete_someone_elses_report(other_client, user, make_report):
    report = make_report(user, CHILONZOR)

    assert other_client.delete(detail_url(report.id)).status_code == 404  # no IDOR
    assert Report.objects.filter(pk=report.pk).exists()
