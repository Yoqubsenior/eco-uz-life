from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from . import selectors, services
from .serializers import (
    CategorySerializer,
    MapQuerySerializer,
    MapReportSerializer,
    MyReportSerializer,
    ReportCreateSerializer,
    ReportDetailSerializer,
)


class CategoryListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        return Response(CategorySerializer(selectors.active_categories(), many=True).data)


class ReportCreateView(APIView):
    """POST multipart: category, description?, lat, lng, photos (1-3 files). [FR-R1]"""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [UserRateThrottle, ScopedRateThrottle]
    throttle_scope = "report_create"

    def post(self, request: Request) -> Response:
        serializer = ReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        report = services.create_report(
            author=request.user,
            category=data["category"],
            description=data.get("description", ""),
            lat=data["lat"],
            lng=data["lng"],
            images=data["photos"],
        )
        report = selectors.report_detail_queryset(request.user).get(pk=report.pk)
        body = ReportDetailSerializer(report, context={"request": request}).data
        return Response(body, status=status.HTTP_201_CREATED)


class ReportMapView(APIView):
    """GET ?bbox=min_lng,min_lat,max_lng,max_lat&category=&status= [FR-R2]"""

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        query = MapQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        reports = selectors.public_reports_in_bbox(**query.validated_data)
        return Response(MapReportSerializer(reports, many=True).data)


class ReportDetailView(APIView):
    """GET: anyone, if visible to them. DELETE: author only, while `new`. [FR-R3, FR-R7]"""

    def get_permissions(self):
        return [AllowAny()] if self.request.method == "GET" else [IsAuthenticated()]

    def get(self, request: Request, pk) -> Response:
        # A report you may not see returns 404, not 403: we don't even confirm it exists.
        report = get_object_or_404(selectors.report_detail_queryset(request.user), pk=pk)
        return Response(ReportDetailSerializer(report, context={"request": request}).data)

    def delete(self, request: Request, pk) -> Response:
        report = get_object_or_404(selectors.my_reports(request.user), pk=pk)
        try:
            services.delete_report(report)
        except services.ReportNotDeletable:
            return Response(
                {"detail": "Faqat 'Yangi' holatdagi murojaatni o'chirish mumkin."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class MyReportsView(APIView):
    """GET: the current user's reports, every status. [FR-R4]"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        reports = selectors.my_reports(request.user)[:100]
        return Response(MyReportSerializer(reports, many=True, context={"request": request}).data)
