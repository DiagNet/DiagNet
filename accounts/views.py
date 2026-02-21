import logging

from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from devices.models import Device
from networktests.models import TestCase, TestResult
from testgroups.models import TestGroup

from .forms import (
    GroupForm,
    GroupMembershipForm,
    SuperUserCreationForm,
    UserCreateForm,
    UserPasswordChangeForm,
    UserUpdateForm,
)
from .models import GroupProfile


@method_decorator(login_not_required, name="dispatch")
class SetupView(View):
    """View for initial superuser creation when no users exist."""

    def get(self, request):
        if User.objects.filter(is_superuser=True).exists():
            return redirect("login")

        form = SuperUserCreationForm()
        return render(request, "accounts/setup.html", {"form": form})

    def post(self, request):
        if User.objects.filter(is_superuser=True).exists():
            return redirect("login")

        form = SuperUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f"Superuser '{user.username}' created successfully. You are now logged in.",
            )
            login(request, user)
            return redirect("dashboard")
        return render(request, "accounts/setup.html", {"form": form})


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to require admin/superuser access."""

    def test_func(self):
        user = self.request.user
        return (
            user.is_superuser
            or user.has_perm("auth.view_user")
            or user.has_perm("auth.view_group")
            or user.has_perm("auth.add_user")
            or user.has_perm("auth.add_group")
            or user.has_perm("auth.change_user")
            or user.has_perm("auth.change_group")
            or user.has_perm("auth.delete_user")
            or user.has_perm("auth.delete_group")
        )


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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request_user"] = self.request.user
        return kwargs

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

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Prevent deleting yourself
        if self.object == request.user:
            if request.headers.get("HX-Request") == "true":
                return HttpResponse("You cannot delete your own account.", status=400)
            messages.error(request, "You cannot delete your own account.")
            return HttpResponseRedirect(self.success_url)

        # Prevent deleting superusers (block at dispatch level)
        if self.object.is_superuser:
            if request.headers.get("HX-Request") == "true":
                return HttpResponse(
                    "You cannot delete a superuser account.", status=400
                )
            messages.error(request, "You cannot delete a superuser account.")
            return HttpResponseRedirect(self.success_url)

        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        username = self.object.username

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
        """Determine the role type based on group metadata."""
        profile = GroupProfile.objects.filter(group=group).only("role_type").first()
        if profile is not None:
            return profile.role_type
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
            GroupProfile.objects.create(group=group, role_type=role_type)
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
        # Clear existing permissions
        group.permissions.clear()

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
        context["role_type"] = self._determine_role_type(self.object)
        return context

    def _determine_role_type(self, group):
        """Determine the role type based on group metadata."""
        profile = GroupProfile.objects.filter(group=group).only("role_type").first()
        if profile is not None:
            return profile.role_type
        return "Custom"


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
