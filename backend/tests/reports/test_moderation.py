import pytest
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.urls import reverse

from apps.points.models import PointTransaction
from apps.points.selectors import balance
from apps.reports.admin import ReportModerationForm
from apps.reports.models import Report
from apps.reports.services import InvalidTransition, change_status
from tests.air.factories import CHILONZOR

pytestmark = pytest.mark.django_db

S = Report.Status


@pytest.fixture
def report(user, make_report):
    return make_report(user, CHILONZOR)


# ---------- Service: workflow + points ----------


def test_verify_awards_points_records_history_and_makes_report_public(
    report, user, moderator, api_client
):
    change_status(report, S.VERIFIED, moderator=moderator)

    report.refresh_from_db()
    assert report.status == S.VERIFIED
    assert report.verified_at is not None
    last = report.history.last()
    assert (last.from_status, last.to_status, last.changed_by) == ("new", "verified", moderator)
    assert balance(user) == 10
    assert api_client.get(f"/api/v1/reports/{report.id}/").status_code == 200  # now public


def test_verifying_twice_is_refused_and_points_are_given_once(report, user, moderator):
    change_status(report, S.VERIFIED, moderator=moderator)

    with pytest.raises(InvalidTransition):
        change_status(report, S.VERIFIED, moderator=moderator)  # e.g. a second moderator

    assert balance(user) == 10
    assert PointTransaction.objects.count() == 1


@pytest.mark.parametrize("to_status", [S.RESOLVED, S.IN_PROGRESS, S.NEW])
def test_new_report_cannot_skip_steps(report, moderator, to_status):
    with pytest.raises(InvalidTransition):
        change_status(report, to_status, moderator=moderator)


def test_reject_requires_reason_and_gives_no_points(report, user, moderator):
    with pytest.raises(InvalidTransition, match="sababi"):
        change_status(report, S.REJECTED, moderator=moderator, rejection_reason="   ")

    change_status(report, S.REJECTED, moderator=moderator, rejection_reason="Rasm aniq emas")

    report.refresh_from_db()
    assert report.rejection_reason == "Rasm aniq emas"
    assert balance(user) == 0


def test_rejected_and_resolved_are_final(report, moderator):
    change_status(report, S.REJECTED, moderator=moderator, rejection_reason="Spam")

    with pytest.raises(InvalidTransition):
        change_status(report, S.VERIFIED, moderator=moderator)


def test_full_lifecycle_gives_verified_plus_resolved_bonus(report, user, moderator):
    change_status(report, S.VERIFIED, moderator=moderator)
    change_status(report, S.IN_PROGRESS, moderator=moderator)
    change_status(report, S.RESOLVED, moderator=moderator)

    assert balance(user) == 15
    assert [h.to_status for h in report.history.all()] == [
        "new",
        "verified",
        "in_progress",
        "resolved",
    ]


def test_duplicates_earn_no_points(user, other_user, moderator, make_report):
    make_report(other_user, CHILONZOR)
    duplicate = make_report(user, (CHILONZOR[0] + 0.0001, CHILONZOR[1]))
    assert duplicate.duplicate_of is not None

    change_status(duplicate, S.VERIFIED, moderator=moderator)

    assert balance(user) == 0


def test_report_with_points_cannot_be_hard_deleted(report, moderator):
    from django.db.models import ProtectedError

    change_status(report, S.VERIFIED, moderator=moderator)

    with pytest.raises(ProtectedError):  # the ledger must stay whole
        report.delete()


# ---------- Admin ----------


def test_admin_form_requires_reason_when_rejecting(report):
    form = ReportModerationForm(
        data={"status": "rejected", "rejection_reason": ""}, instance=report
    )

    assert not form.is_valid()
    assert "sababi" in str(form.errors)


def test_admin_form_blocks_invalid_transition(report):
    form = ReportModerationForm(
        data={"status": "resolved", "rejection_reason": ""}, instance=report
    )

    assert not form.is_valid()


def admin_post_data(response, **overrides) -> dict:
    """Rebuild the admin change form's POST data (incl. inline management forms) from a GET."""
    data = {}

    def collect(form) -> None:
        # BoundField.value() = what the rendered page would submit (incl. hidden pk fields).
        for name in form.fields:
            value = form[name].value()
            if value is not None:
                data[form.add_prefix(name)] = getattr(value, "pk", value)

    collect(response.context["adminform"].form)
    for inline in response.context["inline_admin_formsets"]:
        formset = inline.formset
        for key, value in formset.management_form.initial.items():
            data[f"{formset.prefix}-{key}"] = value
        for inline_form in formset.forms:
            collect(inline_form)
    data.update(overrides)
    return data


def test_admin_change_form_verifies_through_the_service(admin_client, report, user):
    url = reverse("admin:reports_report_change", args=[report.pk])
    page = admin_client.get(url)

    response = admin_client.post(url, admin_post_data(page, status="verified", note="Tekshirildi"))

    assert response.status_code == 302, response.content.decode()[:2000]
    report.refresh_from_db()
    assert report.status == S.VERIFIED
    assert report.history.last().note == "Tekshirildi"
    assert balance(user) == 10  # points came from the service, not a raw field write


def test_admin_bulk_verify_action(admin_client, user, make_report):
    first = make_report(user, CHILONZOR)
    second = make_report(user, (41.30, 69.25))

    admin_client.post(
        reverse("admin:reports_report_changelist"),
        {"action": "verify_selected", "_selected_action": [str(first.pk), str(second.pk)]},
    )

    assert set(Report.objects.values_list("status", flat=True)) == {"verified"}
    assert balance(user) == 20


def test_moderator_role_has_minimal_access(client, moderator):
    call_command("setup_roles")
    changelist = reverse("admin:reports_report_changelist")
    users = reverse("admin:accounts_user_changelist")

    client.force_login(moderator)
    assert client.get(changelist).status_code == 403  # staff, but not yet a moderator

    moderator.groups.add(Group.objects.get(name="Moderators"))
    assert client.get(changelist).status_code == 200
    assert client.get(users).status_code == 403  # can't manage users
