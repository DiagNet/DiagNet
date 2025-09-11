from django.urls import path
from . import views

urlpatterns = [
    path("get-all-testcases", views.get_all_testcases, name="get-all-testcases"),
    path("test/", views.test_page, name="test-page")
]
