from django.urls import path
from . import views

urlpatterns = [
    path("", views.DeviceListView.as_view(), name="device-list"),
    path("create/", views.DeviceCreate.as_view(), name="device-create"),
    path("<str:pk>/", views.DeviceUpdate.as_view(), name="device-detail"),
    path("<str:pk>/delete", views.DeviceDelete.as_view(), name="device-delete"),
    path("<str:pk>/check", views.device_check, name="device-check"),
]
