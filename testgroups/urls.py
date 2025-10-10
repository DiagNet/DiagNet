from django.urls import path
from . import views

urlpatterns = [
    path("", views.testgroups_page, name="testgroup-page"),
    path("list-testgroups/", views.list_testgroups, name="testgroup-list"),
    path("create-testgroup/", views.create_testgroup, name="create-testgroup"),
    path("delete-testgroup/", views.delete_testgroup, name="delete-testgroup"),
    path(
        route="testcase-add/", view=views.add_testcase_to_testgroup, name="testcase-add"
    ),
    path("detail/<str:name>/", views.get_testgroup_detail, name="testgroup-detail"),
    path("list-testcases/<str:name>/", views.list_testcases, name="list-testcases"),
    path("rename/<str:name>/", views.rename_testgroup, name="rename-testgroup"),
]
