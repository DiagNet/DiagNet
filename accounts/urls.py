from django.urls import path
from . import views

urlpatterns = [
    # Self-service URLs
    path("password/", views.MyPasswordChangeView.as_view(), name="my-password-change"),
    # User management URLs
    path("manage/users/", views.UserListView.as_view(), name="user-list"),
    path("manage/users/create/", views.UserCreateView.as_view(), name="user-create"),
    path("manage/users/<int:pk>/", views.UserDetailView.as_view(), name="user-detail"),
    path(
        "manage/users/<int:pk>/edit/",
        views.UserUpdateView.as_view(),
        name="user-update",
    ),
    path(
        "manage/users/<int:pk>/delete/",
        views.UserDeleteView.as_view(),
        name="user-delete",
    ),
    path(
        "manage/users/<int:pk>/password/",
        views.UserPasswordChangeView.as_view(),
        name="user-password",
    ),
    # Group management URLs
    path("manage/groups/", views.GroupListView.as_view(), name="group-list"),
    path("manage/groups/create/", views.GroupCreateView.as_view(), name="group-create"),
    path(
        "manage/groups/<int:pk>/", views.GroupDetailView.as_view(), name="group-detail"
    ),
    path(
        "manage/groups/<int:pk>/delete/",
        views.GroupDeleteView.as_view(),
        name="group-delete",
    ),
    path(
        "manage/groups/<int:pk>/members/",
        views.GroupMembershipView.as_view(),
        name="group-membership",
    ),
]
