from django.urls import path
from . import views

urlpatterns = [
    path("", views.TestCaseListView.as_view(), name="networktests-list"),
    path("create/", views.create_test_page, name="test-page"),
    path("get-all-testcases", views.get_all_testcases, name="get-all-testcases"),
    path(
        "api/search/test/parameters",
        views.get_parameters_of_specific_testcase,
        name="search_test_parameters_api",
    ),
    path("api/create/test", views.create_test, name="create_test_api"),
    path("tests/<int:id>/run/", views.run_testcase, name="tests-run"),
    path("tests/<int:pk>/delete/", views.delete_testcase, name="testcase_delete"),
    path(
        "api/get/tests",
        views.get_all_available_testcases,
        name="get_all_tests_api",
    ),
    path(
        "api/get/test/info",
        views.get_doc_of_testcase,
        name="get_doc_of_testcase",
    ),
    path(
        "api/get/test/info",
        views.get_doc_of_testcase,
        name="get_doc_of_testcase",
    ),
]
