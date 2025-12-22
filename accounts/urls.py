from django.urls import path
from . import views

urlpatterns = [
    path("manage/users/", views.UserListView.as_view(), name="user-list"),
    path("manage/groups/", views.GroupListView.as_view(), name="group-list"),
]
