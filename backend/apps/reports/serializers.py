from rest_framework import serializers

from .images import InvalidImage, ProcessedImage, process_image
from .models import Category, Report, ReportPhoto, StatusHistory

# Uzbekistan bounding box (lat, lng). Reports from elsewhere are almost certainly abuse or bugs.
UZ_LAT = (37.1, 45.6)
UZ_LNG = (55.9, 73.2)
MAX_BBOX_SPAN_DEGREES = 1.0  # roughly 110 km — more than enough for a city map


# ---------- Input ----------


class ReportCreateSerializer(serializers.Serializer):
    category = serializers.SlugRelatedField(
        slug_field="slug", queryset=Category.objects.filter(is_active=True)
    )
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)
    lat = serializers.FloatField(min_value=UZ_LAT[0], max_value=UZ_LAT[1])
    lng = serializers.FloatField(min_value=UZ_LNG[0], max_value=UZ_LNG[1])
    photos = serializers.ListField(
        child=serializers.FileField(), min_length=1, max_length=3, allow_empty=False
    )

    def validate_photos(self, files) -> list[ProcessedImage]:
        processed = []
        for index, upload in enumerate(files, start=1):
            try:
                processed.append(process_image(upload))
            except InvalidImage as exc:
                raise serializers.ValidationError(f"{index}-rasm: {exc}") from exc
        return processed


class MapQuerySerializer(serializers.Serializer):
    bbox = serializers.CharField(help_text="min_lng,min_lat,max_lng,max_lat")
    category = serializers.SlugField(required=False)
    status = serializers.ChoiceField(choices=Report.PUBLIC_STATUSES, required=False)

    def validate_bbox(self, value: str) -> tuple[float, float, float, float]:
        try:
            min_lng, min_lat, max_lng, max_lat = (float(part) for part in value.split(","))
        except ValueError as exc:
            raise serializers.ValidationError("Format: min_lng,min_lat,max_lng,max_lat") from exc

        if not (-180 <= min_lng < max_lng <= 180 and -90 <= min_lat < max_lat <= 90):
            raise serializers.ValidationError("Invalid coordinates or min >= max.")
        # Without this, one request for "the whole world" could pull every row.
        if max_lng - min_lng > MAX_BBOX_SPAN_DEGREES or max_lat - min_lat > MAX_BBOX_SPAN_DEGREES:
            raise serializers.ValidationError("Area too large; zoom in.")
        return min_lng, min_lat, max_lng, max_lat


# ---------- Output ----------


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("slug", "name_uz", "icon")


class PhotoSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = ReportPhoto
        fields = ("url", "width", "height")

    def get_url(self, obj: ReportPhoto) -> str:
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if request else obj.image.url


class HistorySerializer(serializers.ModelSerializer):
    # Deliberately NOT exposing changed_by or note: moderator identity and internal notes
    # stay private. Citizens see what happened and when.
    class Meta:
        model = StatusHistory
        fields = ("to_status", "created_at")


class _LocationMixin(serializers.Serializer):
    lat = serializers.SerializerMethodField()
    lng = serializers.SerializerMethodField()

    def get_lat(self, obj) -> float:
        return obj.location.y

    def get_lng(self, obj) -> float:
        return obj.location.x


class MapReportSerializer(_LocationMixin, serializers.ModelSerializer):
    category = serializers.CharField(source="category.slug")

    class Meta:
        model = Report
        fields = ("id", "category", "status", "lat", "lng", "created_at")


class ReportDetailSerializer(_LocationMixin, serializers.ModelSerializer):
    category = CategorySerializer()
    status_display = serializers.CharField(source="get_status_display")
    district = serializers.CharField(source="district.name_uz", default=None)
    author_name = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()
    rejection_reason = serializers.SerializerMethodField()
    photos = PhotoSerializer(many=True)
    history = HistorySerializer(many=True)

    class Meta:
        model = Report
        fields = (
            "id",
            "category",
            "description",
            "status",
            "status_display",
            "rejection_reason",
            "lat",
            "lng",
            "district",
            "author_name",
            "is_mine",
            "duplicate_of",
            "photos",
            "history",
            "created_at",
        )

    def _is_mine(self, obj: Report) -> bool:
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and obj.author_id == request.user.id)

    def get_is_mine(self, obj: Report) -> bool:
        return self._is_mine(obj)

    def get_author_name(self, obj: Report) -> str:
        # Display name only — never the email (privacy requirement).
        return obj.author.display_name or "Foydalanuvchi"

    def get_rejection_reason(self, obj: Report) -> str | None:
        return obj.rejection_reason if self._is_mine(obj) and obj.rejection_reason else None


class MyReportSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.slug")
    status_display = serializers.CharField(source="get_status_display")
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = ("id", "category", "status", "status_display", "thumbnail", "created_at")

    def get_thumbnail(self, obj: Report) -> str | None:
        photos = list(obj.photos.all())  # uses the prefetch, no extra query
        if not photos:
            return None
        return PhotoSerializer(photos[0], context=self.context).data["url"]
