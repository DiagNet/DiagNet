from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="networktests-page"),
    path("create/", views.create_test_page, name="test-page"),
    path("api/list-tests", views.TestCaseListView.as_view(), name="networktests-table"),
    path("get-all-testcases", views.get_all_testcases, name="get-all-testcases"),
    path(
        "api/search/test/parameters",
        views.get_parameters_of_specific_testcase,
        name="search_test_parameters_api",
    ),
    path("api/create/test", views.create_test, name="create_test_api"),
    path("tests/<int:pk>/run/", views.run_testcase, name="tests-run"),
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
    path("export-report/", views.export_report_pdf, name="networktests-export-pdf"),
    path(
        "tests/<int:pk>/details/", views.testcase_detail_view, name="testcase-details"
    ),
    path(
        "templates/manage/",
        views.manage_custom_templates,
        name="manage-custom-templates",
    ),
    path(
        "templates/toggle/<int:pk>/",
        views.toggle_custom_template,
        name="toggle-custom-template",
    ),
    path(
        "templates/sync/",
        views.sync_custom_templates_view,
        name="sync-custom-templates",
    ),
]
