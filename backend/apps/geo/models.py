"""Administrative areas and map places.

All geometry uses SRID 4326 (WGS 84, the GPS standard).
A PostGIS Point is Point(longitude, latitude) — longitude FIRST.
Geometry fields get a GiST spatial index automatically (spatial_index=True by default).
"""

from django.contrib.gis.db import models


class Region(models.Model):
    name_uz = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    boundary = models.MultiPolygonField(srid=4326, null=True, blank=True)

    class Meta:
        ordering = ["name_uz"]

    def __str__(self) -> str:
        return self.name_uz


class District(models.Model):
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="districts")
    name_uz = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    # Filled later from official boundary data; nullable until then (decision DB6).
    boundary = models.MultiPolygonField(srid=4326, null=True, blank=True)

    class Meta:
        ordering = ["name_uz"]
        constraints = [
            # "Markaziy" may exist in two regions, but only once per region.
            models.UniqueConstraint(
                fields=["region", "slug"], name="geo_district_region_slug_uniq"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name_uz} ({self.region})"


class EcoPoint(models.Model):
    """Green map layer: recycling points, parks, tree-planting sites. Admin-managed. [FR-G1]"""

    class Kind(models.TextChoices):
        RECYCLING = "recycling", "Qayta ishlash punkti"
        PARK = "park", "Park / yashil hudud"
        PLANTING = "planting", "Daraxt ekish joyi"

    kind = models.CharField(max_length=20, choices=Kind.choices)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.PointField(srid=4326)
    district = models.ForeignKey(
        District, on_delete=models.SET_NULL, null=True, blank=True, related_name="eco_points"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(kind__in=["recycling", "park", "planting"]),
                name="geo_ecopoint_kind_valid",
            ),
        ]

    def __str__(self) -> str:
        return self.name
