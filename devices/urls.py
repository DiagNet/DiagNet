from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="devices-page"),
    path("api/get-table/", views.DeviceListView.as_view(), name="devices-table"),
    path("api/create/", views.DeviceCreate.as_view(), name="device-create"),
    path("api/update/<str:pk>/", views.DeviceUpdate.as_view(), name="device-update"),
    path("api/delete/<str:pk>/", views.DeviceDelete.as_view(), name="device-delete"),
    path("api/check/<str:pk>/", views.device_check, name="device-check"),
]
