from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

MODERATOR_GROUP = "Moderators"

# Principle of least privilege: exactly what a moderator needs, nothing more.
# No user management, no deleting, no editing categories or stations.
MODERATOR_PERMISSIONS = [
    ("reports", "view_report"),
    ("reports", "change_report"),
    ("reports", "view_category"),
    ("reports", "view_statushistory"),
    ("points", "view_pointtransaction"),
]


class Command(BaseCommand):
    help = "Create the Moderators group with minimal permissions. Idempotent."

    def handle(self, *args, **options) -> None:
        group, _ = Group.objects.get_or_create(name=MODERATOR_GROUP)
        perms = [
            Permission.objects.get(content_type__app_label=app, codename=codename)
            for app, codename in MODERATOR_PERMISSIONS
        ]
        group.permissions.set(perms)  # set(), not add(): removes anything granted by mistake
        self.stdout.write(
            self.style.SUCCESS(f"Group '{MODERATOR_GROUP}' has {len(perms)} permissions.")
        )
        self.stdout.write(
            "To make someone a moderator: Admin -> Users -> tick 'Staff status' "
            f"and add them to '{MODERATOR_GROUP}'."
        )
