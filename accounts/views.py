from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import Group, User
from django.views.generic import ListView


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class UserListView(AdminRequiredMixin, ListView):
    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"


class GroupListView(AdminRequiredMixin, ListView):
    model = Group
    template_name = "accounts/group_list.html"
    context_object_name = "groups"
