from django.urls import path
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    # Built-in views: no reason to rewrite well-tested security code.
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),  # [FR-A3]
    path("logout/", TokenBlacklistView.as_view(), name="logout"),  # [FR-A4]
    path("me/", views.MeView.as_view(), name="me"),
]
