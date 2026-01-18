import logging

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group, User
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import (
    GroupForm,
    GroupMembershipForm,
    UserCreateForm,
    UserPasswordChangeForm,
    UserUpdateForm,
)


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to require admin/superuser access."""

    def test_func(self):
        return self.request.user.is_superuser


# ============== User Views ==============


class UserListView(AdminRequiredMixin, ListView):
    """List all users."""

    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"
    ordering = ["username"]


class UserCreateView(AdminRequiredMixin, CreateView):
    """Create a new user."""

    model = User
    form_class = UserCreateForm
    template_name = "accounts/partials/user_form.html"
    success_url = reverse_lazy("user-list")

    def form_valid(self, form):
        self.object = form.save()
        if self.request.headers.get("HX-Request") == "true":
            response = HttpResponse(status=204)
            response["HX-Trigger"] = "userCreated"
            return response
        messages.success(
            self.request, f"User '{self.object.username}' created successfully."
        )
        return HttpResponseRedirect(self.get_success_url())


class UserUpdateView(AdminRequiredMixin, UpdateView):
    """Update an existing user."""

    model = User
    form_class = UserUpdateForm
    template_name = "accounts/partials/user_form.html"
    context_object_name = "object"

    def get_success_url(self):
        return reverse_lazy("user-update", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        self.object = form.save()
        if self.request.headers.get("HX-Request") == "true":
            response = HttpResponse(status=204)
            response["HX-Trigger"] = "usersRefresh"
            return response
        messages.success(
            self.request, f"User '{self.object.username}' updated successfully."
        )
        return HttpResponseRedirect(reverse_lazy("user-list"))


class UserDeleteView(AdminRequiredMixin, DeleteView):
    """Delete a user."""

    model = User
    template_name = "accounts/user_confirm_delete.html"
    success_url = reverse_lazy("user-list")

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        username = self.object.username

        # Prevent deleting yourself
        if self.object == request.user:
            if request.headers.get("HX-Request") == "true":
                return HttpResponse("You cannot delete your own account.", status=400)
            messages.error(request, "You cannot delete your own account.")
            return HttpResponseRedirect(self.success_url)

        self.object.delete()

        if request.headers.get("HX-Request") == "true":
            response = HttpResponse(status=204)
            response["HX-Trigger"] = "usersRefresh"
            return response

        messages.success(request, f"User '{username}' deleted successfully.")
        return HttpResponseRedirect(self.success_url)


class UserDetailView(AdminRequiredMixin, DetailView):
    """View user details."""

    model = User
    template_name = "accounts/partials/user_details.html"
    context_object_name = "account"


class UserPasswordChangeView(AdminRequiredMixin, View):
    """Change a user's password (admin action)."""

    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        form = UserPasswordChangeForm(user, request_user=request.user)
        return render(
            request,
            "accounts/partials/user_password_form.html",
            {"form": form, "object": user},
        )

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        form = UserPasswordChangeForm(
            user, request_user=request.user, data=request.POST
        )
        if form.is_valid():
            form.save()
            # Keep the user logged in if they changed their own password
            if user == request.user:
                update_session_auth_hash(request, user)
            if request.headers.get("HX-Request") == "true":
                response = HttpResponse(status=204)
                response["HX-Trigger"] = "usersRefresh"
                return response
            messages.success(
                request, f"Password for '{user.username}' changed successfully."
            )
            return HttpResponseRedirect(reverse_lazy("user-list"))
        return render(
            request,
            "accounts/partials/user_password_form.html",
            {"form": form, "object": user},
        )


class MyPasswordChangeView(LoginRequiredMixin, View):
    """Allow any user to change their own password."""

    def get(self, request):
        form = UserPasswordChangeForm(request.user, request_user=request.user)
        return render(
            request,
            "accounts/my_password_change.html",
            {"form": form},
        )

    def post(self, request):
        form = UserPasswordChangeForm(
            request.user, request_user=request.user, data=request.POST
        )
        if form.is_valid():
            form.save()
            # Keep the user logged in after password change
            update_session_auth_hash(request, request.user)
            messages.success(request, "Your password has been changed successfully.")
            return HttpResponseRedirect(reverse_lazy("dashboard"))
        return render(
            request,
            "accounts/my_password_change.html",
            {"form": form},
        )


# ============== Group Views ==============


class GroupListView(AdminRequiredMixin, ListView):
    """List all groups."""

    model = Group
    template_name = "accounts/group_list.html"
    context_object_name = "groups"
    ordering = ["name"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add user count and role type for each group
        for group in context["groups"]:
            group.user_count = group.user_set.count()
            group.role_type = self._determine_role_type(group)
        return context

    def _determine_role_type(self, group):
        """Determine the role type based on group permissions."""
        perms = set(group.permissions.values_list("codename", flat=True))

        # Check for admin permissions (user management)
        if "add_user" in perms or "change_user" in perms:
            return "Admins"

        # Check for delete permissions (managers)
        if "delete_device" in perms or "delete_testcase" in perms:
            return "Managers"

        # Check for add/change permissions (editors)
        if "add_device" in perms or "change_device" in perms:
            return "Editors"

        # Check for view permissions (viewers)
        if "view_device" in perms or "view_testcase" in perms:
            return "Viewers"

        return "Custom"


class GroupCreateView(AdminRequiredMixin, View):
    """Create a new group."""

    def get(self, request):
        form = GroupForm()
        return render(request, "accounts/partials/group_form.html", {"form": form})

    def post(self, request):
        form = GroupForm(request.POST)
        if form.is_valid():
            group = form.save()
            role_type = form.cleaned_data["role_type"]
            self._assign_permissions(group, role_type)

            if request.headers.get("HX-Request") == "true":
                response = HttpResponse(status=204)
                response["HX-Trigger"] = "groupCreated"
                return response
            messages.success(request, f"Group '{group.name}' created successfully.")
            return HttpResponseRedirect(reverse_lazy("group-list"))
        return render(request, "accounts/partials/group_form.html", {"form": form})

    def _assign_permissions(self, group, role_type):
        """Assign permissions based on the role type."""
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

        # Clear existing permissions
        group.permissions.clear()

        # Import models to get permissions
        try:
            from devices.models import Device
            from networktests.models import TestCase, TestResult
            from testgroups.models import TestGroup
        except ImportError:
            return

        logger = logging.getLogger(__name__)

        def get_perms(model_class, actions):
            """Get permission objects for a model and actions."""
            ct = ContentType.objects.get_for_model(model_class)
            perms = []
            for action in actions:
                codename = f"{action}_{model_class._meta.model_name}"
                try:
                    perm = Permission.objects.get(content_type=ct, codename=codename)
                    perms.append(perm)
                except Permission.DoesNotExist:
                    logger.warning(
                        "Permission '%s' not found for model '%s'. "
                        "Ensure migrations have been run.",
                        codename,
                        model_class._meta.model_name,
                    )
            return perms

        permissions = []

        if role_type == "Viewers":
            # Read only
            permissions.extend(get_perms(Device, ["view"]))
            permissions.extend(get_perms(TestCase, ["view"]))
            permissions.extend(get_perms(TestResult, ["view"]))
            permissions.extend(get_perms(TestGroup, ["view"]))

        elif role_type == "Editors":
            # View + Edit/Run
            permissions.extend(get_perms(Device, ["view", "add", "change"]))
            permissions.extend(get_perms(TestCase, ["view", "add", "change"]))
            permissions.extend(get_perms(TestGroup, ["view", "add", "change"]))
            permissions.extend(get_perms(TestResult, ["view", "add"]))

        elif role_type == "Managers":
            # View + Edit + Delete
            permissions.extend(get_perms(Device, ["view", "add", "change", "delete"]))
            permissions.extend(get_perms(TestCase, ["view", "add", "change", "delete"]))
            permissions.extend(
                get_perms(TestGroup, ["view", "add", "change", "delete"])
            )
            permissions.extend(get_perms(TestResult, ["view", "add", "delete"]))

        elif role_type == "Admins":
            # Full access + User Management
            permissions.extend(get_perms(Device, ["view", "add", "change", "delete"]))
            permissions.extend(get_perms(TestCase, ["view", "add", "change", "delete"]))
            permissions.extend(
                get_perms(TestGroup, ["view", "add", "change", "delete"])
            )
            permissions.extend(get_perms(TestResult, ["view", "add", "delete"]))
            permissions.extend(get_perms(User, ["view", "add", "change", "delete"]))
            permissions.extend(get_perms(Group, ["view", "add", "change", "delete"]))

        group.permissions.add(*permissions)


class GroupDetailView(AdminRequiredMixin, DetailView):
    """View group details and members."""

    model = Group
    template_name = "accounts/partials/group_details.html"
    context_object_name = "group"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["members"] = self.object.user_set.all()
        context["permissions"] = self.object.permissions.all()
        return context


class GroupDeleteView(AdminRequiredMixin, DeleteView):
    """Delete a group."""

    model = Group
    template_name = "accounts/group_confirm_delete.html"
    success_url = reverse_lazy("group-list")

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        name = self.object.name
        self.object.delete()

        if request.headers.get("HX-Request") == "true":
            response = HttpResponse(status=204)
            response["HX-Trigger"] = "groupsRefresh"
            return response

        messages.success(request, f"Group '{name}' deleted successfully.")
        return HttpResponseRedirect(self.success_url)


class GroupMembershipView(AdminRequiredMixin, View):
    """Manage group membership."""

    def get(self, request, pk):
        group = get_object_or_404(Group, pk=pk)
        form = GroupMembershipForm(group=group)
        return render(
            request,
            "accounts/partials/group_membership_form.html",
            {"form": form, "group": group},
        )

    def post(self, request, pk):
        group = get_object_or_404(Group, pk=pk)
        form = GroupMembershipForm(group=group, data=request.POST)
        if form.is_valid():
            form.save()
            if request.headers.get("HX-Request") == "true":
                response = HttpResponse(status=204)
                response["HX-Trigger"] = "groupsRefresh"
                return response
            messages.success(
                request, f"Members of '{group.name}' updated successfully."
            )
            return HttpResponseRedirect(reverse_lazy("group-list"))
        return render(
            request,
            "accounts/partials/group_membership_form.html",
            {"form": form, "group": group},
        )
