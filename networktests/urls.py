from django.urls import path
from . import views

urlpatterns = [
    path("get-all-testcases", views.get_all_testcases, name="get-all-testcases"),
    path("tests/", views.testcases_list, name="testcases-list"),
    path("tests/", views.test_list, name="testcases-list"),
    path(
        "api/search/test/classes",
        views.search_all_available_testcases,
        name="search_testclasses_api",
    ),
    path(
        "api/search/test/parameters",
        views.get_parameters_of_specific_testcase,
        name="search_test_parameters_api",
    ),
    path("api/create/test", views.create_test, name="create_test_api"),
    path("test/", views.test_page, name="test-page"),
    path("tests/<int:id>/run/", views.run_test, name="tests-run"),
]
