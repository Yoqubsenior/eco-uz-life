import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("ecouz")
# Read every Django setting that starts with CELERY_ (e.g. CELERY_BROKER_URL -> broker_url).
app.config_from_object("django.conf:settings", namespace="CELERY")
# Find tasks.py in every installed app.
app.autodiscover_tasks()
