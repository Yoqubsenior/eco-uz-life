from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.ReportCreateView.as_view(), name="create"),
    path("categories/", views.CategoryListView.as_view(), name="categories"),
    path("map/", views.ReportMapView.as_view(), name="map"),
    path("mine/", views.MyReportsView.as_view(), name="mine"),
    path("<uuid:pk>/", views.ReportDetailView.as_view(), name="detail"),
]
