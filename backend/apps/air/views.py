from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from . import selectors
from .models import Station
from .serializers import (
    HistoryPointSerializer,
    HistoryQuerySerializer,
    NearestQuerySerializer,
    StationSerializer,
)

PERIODS = {"24h": timedelta(hours=24), "7d": timedelta(days=7)}


class PublicAirView(APIView):
    # Air quality is public information: guests can see it (roles table, requirements §3).
    permission_classes = [AllowAny]


class StationListView(PublicAirView):
    """GET /air/stations/ — all active stations with their latest reading. [FR-AQ2, FR-G1]"""

    def get(self, request: Request) -> Response:
        stations = list(selectors.active_stations())
        latest = selectors.latest_readings_by_station([s.id for s in stations])
        return Response(StationSerializer(stations, many=True, context={"latest": latest}).data)


class NearestStationView(PublicAirView):
    """GET /air/nearest/?lat=..&lng=.. — closest station + its latest reading. [FR-AQ3]"""

    def get(self, request: Request) -> Response:
        query = NearestQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)  # 400 with field errors on bad input

        station = selectors.nearest_station(**query.validated_data)
        if station is None:
            return Response({"detail": "No active stations."}, status=404)

        reading = selectors.latest_reading(station)
        data = StationSerializer(station, context={"latest": {station.id: reading}}).data
        data["distance_m"] = round(station.distance.m)
        return Response(data)


class StationHistoryView(PublicAirView):
    """GET /air/stations/<id>/history/?period=24h|7d — readings for a chart. [FR-AQ4]"""

    def get(self, request: Request, pk: int) -> Response:
        station = get_object_or_404(Station, pk=pk, is_active=True)

        query = HistoryQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        period = query.validated_data["period"]

        readings = selectors.reading_history(station, since=timezone.now() - PERIODS[period])
        return Response(
            {
                "station_id": station.id,
                "period": period,
                "readings": HistoryPointSerializer(readings, many=True).data,
            }
        )
