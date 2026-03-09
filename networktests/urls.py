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
        "tests/<int:pk>/modal/",
        views.testcase_modal_content,
        name="testcase-modal-content",
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
    # Testgroup management (consolidated)
    path(
        "groups/dashboard/",
        views.dashboard_content,
        name="dashboard-content",
    ),
    path(
        "groups/create/",
        views.testgroup_form_modal,
        name="testgroup-create-modal",
    ),
    path(
        "groups/<int:pk>/edit/",
        views.testgroup_form_modal,
        name="testgroup-edit-modal",
    ),
    path(
        "groups/save/",
        views.save_testgroup,
        name="testgroup-save",
    ),
    path(
        "groups/<int:pk>/save/",
        views.save_testgroup,
        name="testgroup-save-pk",
    ),
    path(
        "groups/<int:pk>/delete/",
        views.delete_testgroup,
        name="testgroup-delete",
    ),
    path(
        "groups/<int:pk>/run/",
        views.run_group_tests,
        name="testgroup-run-all",
    ),
    path(
        "groups/<int:pk>/export-pdf/",
        views.export_group_pdf,
        name="testgroup-export-pdf",
    ),
    path(
        "groups/<int:pk>/table/",
        views.group_table_partial,
        name="group-table-partial",
    ),
    path(
        "groups/all-tests-table/",
        views.all_tests_table_partial,
        name="all-tests-table-partial",
    ),
    path(
        "groups/<int:pk>/accordion-item/",
        views.group_accordion_item_partial,
        name="group-accordion-item-partial",
    ),
    path(
        "groups/<int:pk>/comparison/",
        views.group_comparison_modal,
        name="group-comparison-modal",
    ),
]
