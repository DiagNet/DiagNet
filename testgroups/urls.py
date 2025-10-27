from django.urls import path
from . import views

urlpatterns = [
    path("", views.testgroups_page, name="testgroup-page"),
    path("list-testgroups/", views.list_testgroups, name="testgroup-list"),
    path("create-testgroup/", views.create_testgroup, name="create-testgroup"),
    path("delete-testgroup/", views.delete_testgroup, name="delete-testgroup"),
    path(
        "testgroup-filter-testcases/",
        views.get_filtered_testcases,
        name="testgroup-filter-testcases",
    ),
    path(
        route="testcase-add/",
        view=views.add_testcases_to_testgroup,
        name="testgroup-add-testcase",
    ),
    path(
        route="testcase-remove/",
        view=views.remove_testcase_from_testgroup,
        name="testcase-remove",
    ),
    path("detail/<str:name>/", views.get_testgroup_detail, name="testgroup-detail"),
    path(
        "list-testcases/<str:testgroup_name>/",
        views.list_testcases,
        name="testcase-list",
    ),
    path("rename/<str:name>/", views.rename_testgroup, name="rename-testgroup"),
    path("run/<str:group>/<str:pk>", views.run_testcase, name="testgroup-testcase-run"),
    path(
        "popup/<str:testgroup_name>",
        views.get_testcase_search_popup,
        name="testcase-search-popup",
    ),
]
