"""Claiming the install and signing in."""

from django.contrib.auth import login, views as auth_views
from django.contrib.auth.decorators import login_not_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from signin.claim import is_claimed
from signin.forms import OwnerForm, SetupCodeForm, SignInForm

# Set once the setup code is right, so the second step can't be reached by URL.
CODE_ACCEPTED = "signin.setup_code_accepted"


def _unclaimed_only(request: HttpRequest) -> None:
    if is_claimed():
        request.session.pop(CODE_ACCEPTED, None)
        raise Http404


@login_not_required
def claim(request: HttpRequest) -> HttpResponse:
    """Step 1 of claiming: the setup code from the server's log.

    Args:
        request: The incoming request.

    Returns:
        The form, or a redirect to step 2 once the code is right.
    """
    _unclaimed_only(request)
    form = SetupCodeForm(request.POST or None)
    if form.is_valid():
        request.session[CODE_ACCEPTED] = True
        return redirect("claim_owner")
    return render(request, "signin/claim.html", {"form": form, "step": 1})


@login_not_required
def claim_owner(request: HttpRequest) -> HttpResponse:
    """Step 2 of claiming: the name, email and password of the only login.

    Args:
        request: The incoming request.

    Returns:
        The form, or a redirect home signed in once the login is made.
    """
    _unclaimed_only(request)
    if not request.session.get(CODE_ACCEPTED):
        return redirect("claim")
    form = OwnerForm(request.POST or None)
    if form.is_valid():
        login(request, form.save())
        return redirect("home")
    return render(request, "signin/claim_owner.html", {"form": form, "step": 2})


class LoginView(auth_views.LoginView):
    """Password sign-in. An unclaimed install has no login, so it goes to claim."""

    template_name = "signin/login.html"
    authentication_form = SignInForm

    def get(
        self, request: HttpRequest, *args: object, **kwargs: object
    ) -> HttpResponse:
        """Send an unclaimed install to be claimed.

        Returns:
            The sign-in form, or a redirect to claim.
        """
        if not is_claimed():
            return redirect("claim")
        return super().get(request, *args, **kwargs)


@login_not_required
def admin_login(request: HttpRequest) -> HttpResponse:
    """Send the Django admin's sign-in to Folio's.

    Args:
        request: The incoming request.

    Returns:
        A redirect to Folio's sign-in, coming back to the admin after.
    """
    return auth_views.redirect_to_login(request.GET.get("next", reverse("admin:index")))
