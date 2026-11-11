from django.urls import path

from . import views

app_name = "points"

urlpatterns = [
    path("me/", views.MyPointsView.as_view(), name="me"),
    path("leaderboard/", views.LeaderboardView.as_view(), name="leaderboard"),
]
