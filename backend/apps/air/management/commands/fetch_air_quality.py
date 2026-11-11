from django.core.management.base import BaseCommand

from apps.air.tasks import fetch_air_quality


class Command(BaseCommand):
    help = "Import air quality now, synchronously (same code the hourly Celery task runs)."

    def handle(self, *args, **options) -> None:
        result = fetch_air_quality()  # calling a task directly runs it in this process
        self.stdout.write(self.style.SUCCESS(f"Done: {result}"))
