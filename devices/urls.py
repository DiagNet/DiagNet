from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="devices-page"),
    path("api/get-devices/", views.get_all_devices, name="devices-all"),
    path("api/get-table/", views.DeviceListView.as_view(), name="devices-table"),
    path("api/create/", views.DeviceCreate.as_view(), name="device-create"),
    path("api/update/<int:pk>/", views.DeviceUpdate.as_view(), name="device-update"),
    path("api/delete/<int:pk>/", views.DeviceDelete.as_view(), name="device-delete"),
    path("api/check/<int:pk>/", views.device_check, name="device-check"),
    path("api/export/", views.export_devices_from_yaml, name="devices-export"),
    path("import-devices/", views.import_devices_from_yaml, name="device-import"),
]
