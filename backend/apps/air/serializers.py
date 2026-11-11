from rest_framework import serializers

from .aqi import categorize
from .models import Reading, Station
from .waqi import POLLUTANTS

# ---------- Input (query parameters) ----------


class NearestQuerySerializer(serializers.Serializer):
    lat = serializers.FloatField(min_value=-90, max_value=90)
    lng = serializers.FloatField(min_value=-180, max_value=180)


class HistoryQuerySerializer(serializers.Serializer):
    period = serializers.ChoiceField(choices=["24h", "7d"], default="24h")


# ---------- Output ----------


class CategorySerializer(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    color = serializers.CharField()
    advice = serializers.CharField()
    sensitive_advice = serializers.CharField()


class ReadingSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    pollutants = serializers.SerializerMethodField()
    is_stale = serializers.SerializerMethodField()

    class Meta:
        model = Reading
        fields = ("measured_at", "aqi", "category", "pollutants", "is_stale")

    def get_category(self, obj: Reading) -> dict:
        # Computed from aqi on the fly, never stored (decision DB3).
        return CategorySerializer(categorize(obj.aqi)).data

    def get_pollutants(self, obj: Reading) -> dict:
        # WAQI per-pollutant AQI sub-indices (see apps/air/waqi.py).
        return {name: getattr(obj, name) for name in POLLUTANTS}

    def get_is_stale(self, obj: Reading) -> bool:
        return obj.is_stale()


class StationSerializer(serializers.ModelSerializer):
    """Expects context["latest"]: {station_id: Reading}, prepared in ONE query by the view."""

    source = serializers.CharField(source="get_source_display")
    lat = serializers.SerializerMethodField()
    lng = serializers.SerializerMethodField()
    district = serializers.CharField(source="district.name_uz", default=None)
    latest = serializers.SerializerMethodField()

    class Meta:
        model = Station
        fields = ("id", "name", "source", "lat", "lng", "district", "latest")

    def get_lat(self, obj: Station) -> float:
        return obj.location.y  # PostGIS: y = latitude

    def get_lng(self, obj: Station) -> float:
        return obj.location.x  # PostGIS: x = longitude

    def get_latest(self, obj: Station) -> dict | None:
        reading = self.context["latest"].get(obj.id)
        return ReadingSerializer(reading).data if reading else None


class HistoryPointSerializer(serializers.ModelSerializer):
    color = serializers.SerializerMethodField()

    class Meta:
        model = Reading
        fields = ("measured_at", "aqi", "color", "pm25", "pm10")

    def get_color(self, obj: Reading) -> str:
        return categorize(obj.aqi).color
