from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import MeSerializer, RegisterSerializer


class RegisterView(generics.CreateAPIView):
    """POST: create an account. Returns the user (no tokens) — the app logs in next. [FR-A1]"""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    authentication_classes = []  # an expired token in the header must not block registration
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_register"


class LoginView(TokenObtainPairView):
    """POST email + password -> access + refresh tokens. [FR-A2]

    Wrong email and wrong password return the same 401 message, so the endpoint
    can't be used to discover which emails are registered.
    """

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_login"


class MeView(generics.RetrieveUpdateAPIView):
    """GET / PATCH the current user's profile. [FR-A5]

    There is no user id in the URL: the object is always request.user,
    so reading or editing someone else's profile (IDOR) is impossible by design.
    """

    serializer_class = MeSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]  # no full PUT replacement

    def get_object(self):
        return self.request.user
