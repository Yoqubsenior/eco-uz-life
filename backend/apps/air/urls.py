from django.urls import path

from . import views

app_name = "air"

urlpatterns = [
    path("stations/", views.StationListView.as_view(), name="stations"),
    path("stations/<int:pk>/history/", views.StationHistoryView.as_view(), name="history"),
    path("nearest/", views.NearestStationView.as_view(), name="nearest"),
]
