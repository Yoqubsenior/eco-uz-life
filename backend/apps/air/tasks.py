import logging
from dataclasses import asdict

from celery import shared_task
from django.conf import settings

from .services import ingest_air_quality
from .waqi import WaqiClient, WaqiUnavailable

logger = logging.getLogger(__name__)


@shared_task(
    name="air.fetch_air_quality",
    autoretry_for=(WaqiUnavailable,),  # retry only TEMPORARY failures, not a bad token
    retry_backoff=60,  # wait 60s, 120s, 240s, 480s ... (exponential backoff)
    retry_backoff_max=15 * 60,
    retry_jitter=True,  # randomise waits so many workers don't retry at the same second
    max_retries=5,
)
def fetch_air_quality() -> dict:
    """Hourly job (scheduled in CELERY_BEAT_SCHEDULE). Thin wrapper around the service."""
    if not settings.AIR_API_TOKEN:
        logger.error("AIR_API_TOKEN is not set; skipping air quality import")
        return {"skipped": "no token"}

    with WaqiClient(token=settings.AIR_API_TOKEN) as client:
        result = ingest_air_quality(client, settings.AIR_BOUNDS)

    logger.info("Air quality import finished: %s", result)
    return asdict(result)
