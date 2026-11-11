from django.core.management.base import BaseCommand

from apps.reports.models import Category

# (slug, name, icon, sort_order) — icon names are from the icon set used by the mobile app.
CATEGORIES = [
    ("illegal-dump", "Noqonuniy chiqindixona", "trash-2", 1),
    ("tree-damage", "Daraxtga zarar / kesish", "tree", 2),
    ("air-pollution", "Havo ifloslanishi manbai", "factory", 3),
    ("water", "Suv / ariq muammosi", "droplet", 4),
    ("other", "Boshqa", "alert-circle", 99),
]


class Command(BaseCommand):
    help = "Create report categories. Idempotent."

    def handle(self, *args, **options) -> None:
        for slug, name, icon, order in CATEGORIES:
            Category.objects.update_or_create(
                slug=slug, defaults={"name_uz": name, "icon": icon, "sort_order": order}
            )
        self.stdout.write(self.style.SUCCESS(f"{len(CATEGORIES)} categories ready."))
