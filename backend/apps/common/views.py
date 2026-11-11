from django.db import connection
from django.db.utils import OperationalError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])  # explicit opt-out of the IsAuthenticated default
def health(request: Request) -> Response:
    """Liveness + DB check, used by Docker/monitoring. Reveals no internal details."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except OperationalError:
        return Response({"status": "error", "database": "unavailable"}, status=503)
    return Response({"status": "ok", "database": "ok"})
