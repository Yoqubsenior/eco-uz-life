from rest_framework import serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from . import selectors
from .models import PointTransaction


class TransactionSerializer(serializers.ModelSerializer):
    reason_display = serializers.CharField(source="get_reason_display")

    class Meta:
        model = PointTransaction
        fields = ("amount", "reason", "reason_display", "report", "created_at")


class LeaderboardQuerySerializer(serializers.Serializer):
    scope = serializers.ChoiceField(choices=["users", "districts"], default="users")
    period = serializers.ChoiceField(choices=["month", "all"], default="month")


class MyPointsView(APIView):
    """GET: my balance + latest ledger rows. [FR-P3]"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        transactions = request.user.point_transactions.all()[:50]
        return Response(
            {
                "balance": selectors.balance(request.user),
                "transactions": TransactionSerializer(transactions, many=True).data,
            }
        )


class LeaderboardView(APIView):
    """GET ?scope=users|districts&period=month|all — public. [FR-P4]"""

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        query = LeaderboardQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        scope, period = query.validated_data["scope"], query.validated_data["period"]

        rows = selectors.top_users(period) if scope == "users" else selectors.top_districts(period)
        return Response({"scope": scope, "period": period, "results": rows})
