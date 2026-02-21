from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import GroupProfile


class UserCreateForm(UserCreationForm):
    """Form for creating new users with group assignment."""

    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "Email"}
        ),
    )

    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
    )

    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2", "groups", "is_active"]
        widgets = {
            "username": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Username"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Password"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Confirm Password"}
        )


class SuperUserCreationForm(UserCreationForm):
    """Form for initial superuser creation."""

    class Meta:
        model = User
        fields = ["username", "email"]
        widgets = {
            "username": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Username"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "Email"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Password"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Confirm Password"}
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True
        user.is_superuser = True
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    """Form for updating existing users."""

    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "Email"}
        ),
    )

    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
    )

    is_active = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )

    class Meta:
        model = User
        fields = ["username", "email", "groups", "is_active"]
        widgets = {
            "username": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Username"}
            ),
        }

    def __init__(self, *args, request_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request_user = request_user

    def _is_admin(self, user):
        """Check if user is in a group with 'Admins' role type."""
        return user.groups.filter(profile__role_type="Admins").exists()

    def clean_is_active(self):
        is_active = self.cleaned_data.get("is_active")

        if is_active or not self.request_user:
            return is_active

        # Prevent deactivating your own account
        if self.instance == self.request_user:
            raise ValidationError("You cannot deactivate your own account.")

        # Superusers can deactivate anyone, but not the last active superuser
        if self.request_user.is_superuser:
            if self.instance.is_superuser:
                active_superuser_count = (
                    User.objects.filter(is_superuser=True, is_active=True)
                    .exclude(pk=self.instance.pk)
                    .count()
                )
                if active_superuser_count == 0:
                    raise ValidationError(
                        "Cannot deactivate the last active superuser account."
                    )
            return is_active

        # Non-superuser admins cannot deactivate superusers or other admins
        if self.instance.is_superuser:
            raise ValidationError("Only superusers can deactivate superuser accounts.")

        if self._is_admin(self.instance):
            raise ValidationError("Only superusers can deactivate admin accounts.")

        return is_active


class UserPasswordChangeForm(forms.Form):
    """Form for changing a user's password (admin action)."""

    old_password = forms.CharField(
        label="Current Password",
        required=False,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Current Password"}
        ),
    )
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "New Password"}
        ),
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Confirm New Password"}
        ),
    )

    def __init__(self, user, request_user=None, *args, **kwargs):
        self.user = user
        self.request_user = request_user
        super().__init__(*args, **kwargs)
        # Require old password if changing own password
        if request_user and request_user == user:
            self.fields["old_password"].required = True
        else:
            # Hide old password field when admin changes another user's password
            del self.fields["old_password"]

    def clean_old_password(self):
        old_password = self.cleaned_data.get("old_password")
        if self.request_user and self.request_user == self.user:
            if not self.user.check_password(old_password):
                raise ValidationError("Your current password is incorrect.")
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("new_password1")
        password2 = cleaned_data.get("new_password2")

        if password1 and password2:
            if password1 != password2:
                self.add_error("new_password2", "The two password fields didn't match.")
            try:
                validate_password(password1, self.user)
            except ValidationError as e:
                self.add_error("new_password1", e)

        return cleaned_data

    def save(self):
        password = self.cleaned_data["new_password1"]
        self.user.set_password(password)
        self.user.save()
        return self.user


class GroupForm(forms.Form):
    """Form for creating groups with a custom name and role type."""

    name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Group name"}
        ),
    )

    role_type = forms.ChoiceField(
        choices=GroupProfile.ROLE_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if Group.objects.filter(name=name).exists():
            raise ValidationError(f"Group '{name}' already exists.")
        return name

    def save(self):
        group = Group.objects.create(name=self.cleaned_data["name"])
        return group


class GroupMembershipForm(forms.Form):
    """Form for adding/removing users from a group."""

    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
    )

    def __init__(self, group=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group = group
        if group:
            self.fields["users"].initial = group.user_set.all()

    def save(self):
        if self.group:
            self.group.user_set.set(self.cleaned_data["users"])
            return self.group
        return None
