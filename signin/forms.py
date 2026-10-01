"""Forms for claiming the install and signing in."""

from typing import TYPE_CHECKING

from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm

from signin.claim import is_setup_code

if TYPE_CHECKING:
    from django.contrib.auth.base_user import AbstractBaseUser


class SetupCodeForm(forms.Form):
    """The code printed in the server's log."""

    code = forms.CharField(max_length=32)

    def clean_code(self) -> str:
        """Refuse anything but this install's setup code.

        Returns:
            The code as entered.

        Raises:
            ValidationError: The code is wrong.
        """
        code = self.cleaned_data["code"]
        if not is_setup_code(code):
            msg = "That isn't the setup code. Check the server's log."
            raise forms.ValidationError(msg)
        return code


class OwnerForm(forms.Form):
    """The one login the install will ever have."""

    name = forms.CharField(max_length=150)
    # The email is the username, which holds 150 characters.
    email = forms.EmailField(max_length=150)
    password = forms.CharField(strip=False)

    def clean(self) -> dict:
        """Hold the password to Django's validators, name and email included.

        Returns:
            The cleaned data.
        """
        cleaned = super().clean()
        first, _, last = cleaned.get("name", "").partition(" ")
        email = cleaned.get("email", "").lower()
        # A superuser, so the Django admin is theirs too.
        self.owner = get_user_model()(
            username=email,
            email=email,
            first_name=first,
            last_name=last.strip(),
            is_staff=True,
            is_superuser=True,
        )
        if "password" in cleaned:
            try:
                password_validation.validate_password(cleaned["password"], self.owner)
            except forms.ValidationError as error:
                self.add_error("password", error)
        return cleaned

    def save(self) -> AbstractBaseUser:
        """Create the owner.

        Returns:
            The new user.
        """
        self.owner.set_password(self.cleaned_data["password"])
        self.owner.save()
        return self.owner


class SignInForm(AuthenticationForm):
    """Email and password. Emails are stored lower case."""

    def clean_username(self) -> str:
        """Match the email whatever case it's typed in.

        Returns:
            The email, lower case.
        """
        return self.cleaned_data["username"].lower()
