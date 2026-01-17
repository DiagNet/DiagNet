from django import forms
from django.contrib.auth.models import Group, User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


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
                raise ValidationError("The two password fields didn't match.")
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

    ROLE_CHOICES = [
        ("Viewers", "Viewers - Read Only"),
        ("Editors", "Editors - View + Edit/Run"),
        ("Managers", "Managers - View + Edit + Delete"),
        ("Admins", "Admins - Full Access + User Management"),
    ]

    name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Group name"}
        ),
    )

    role_type = forms.ChoiceField(
        choices=ROLE_CHOICES, widget=forms.Select(attrs={"class": "form-select"})
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
