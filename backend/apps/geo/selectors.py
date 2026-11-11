from django.contrib.gis.geos import Point

from .models import District


def district_for_point(point: Point) -> District | None:
    """Which district contains this point? None until district boundaries are loaded. (DB6)"""
    return District.objects.filter(boundary__contains=point).first()
