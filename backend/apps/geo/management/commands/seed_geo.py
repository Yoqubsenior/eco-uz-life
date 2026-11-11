from django.core.management.base import BaseCommand
from django.db import transaction

from apps.geo.models import District, Region

TASHKENT_CITY = ("toshkent-shahri", "Toshkent shahri")

# The 12 districts of Tashkent city. (slug, name)
TASHKENT_DISTRICTS = [
    ("bektemir", "Bektemir"),
    ("chilonzor", "Chilonzor"),
    ("mirobod", "Mirobod"),
    ("mirzo-ulugbek", "Mirzo Ulug'bek"),
    ("olmazor", "Olmazor"),
    ("sergeli", "Sergeli"),
    ("shayxontohur", "Shayxontohur"),
    ("uchtepa", "Uchtepa"),
    ("yakkasaroy", "Yakkasaroy"),
    ("yangihayot", "Yangihayot"),
    ("yashnobod", "Yashnobod"),
    ("yunusobod", "Yunusobod"),
]


class Command(BaseCommand):
    help = "Create Tashkent city and its districts. Idempotent: safe to run many times."

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        slug, name = TASHKENT_CITY
        region, _ = Region.objects.update_or_create(slug=slug, defaults={"name_uz": name})

        created = 0
        for d_slug, d_name in TASHKENT_DISTRICTS:
            _, was_created = District.objects.update_or_create(
                region=region, slug=d_slug, defaults={"name_uz": d_name}
            )
            created += was_created

        self.stdout.write(
            self.style.SUCCESS(
                f"{region}: {created} districts created, "
                f"{len(TASHKENT_DISTRICTS) - created} already existed."
            )
        )
