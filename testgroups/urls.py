from django.urls import path
from . import views

urlpatterns = [
    path("", views.testgroups_page, name="testgroups-page"),
    path("list-testgroups/", views.list_testgroups, name="list-testgroups"),
    path("create-testgroup/", views.create_testgroup, name="create-testgroup"),
    path("delete-testgroup/", views.delete_testgroup, name="delete-testgroup"),
    path("detail/<str:name>/", views.get_testgroup_detail, name="testgroup-detail"),
    path("list-testcases/<str:name>/", views.list_testcases, name="list-testcases"),
]
