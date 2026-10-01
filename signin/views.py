"""Claiming the install, signing in and confirming it's you."""

from base64 import b32encode

import qrcode
from django.conf import settings
from django.contrib.auth import login, views as auth_views
from django.contrib.auth.decorators import login_not_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.safestring import mark_safe
from django_otp import login as otp_login
from django_otp.plugins.otp_static.models import StaticDevice
from django_otp.plugins.otp_totp.models import default_key
from qrcode.image.svg import SvgPathImage

from signin import events, factors, throttle
from signin.claim import is_claimed
from signin.forms import WRONG_CODE, CodeForm, OwnerForm, SetupCodeForm, SignInForm
from signin.middleware import second_factor_not_required

# Set once the setup code is right, so the second step can't be reached by URL.
CODE_ACCEPTED = "signin.setup_code_accepted"
# Kept until the app shows a right code, so reloading doesn't change the QR code.
AUTHENTICATOR_KEY = "signin.authenticator_key"
SECURITY_SCREEN = {"tab": "home", "back": "security", "title": "Authenticator app"}


def _next(request: HttpRequest) -> str:
    url = request.GET.get("next", "")
    if url_has_allowed_host_and_scheme(
        url, {request.get_host()}, require_https=request.is_secure()
    ):
        return url
    return reverse(settings.LOGIN_REDIRECT_URL)


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
        login(request, form.save(), backend="django.contrib.auth.backends.ModelBackend")
        return redirect("protect")
    return render(request, "signin/claim_owner.html", {"form": form, "step": 2})


@second_factor_not_required
def protect(request: HttpRequest) -> HttpResponse:
    """Step 3 of claiming: a passkey (recommended) or an authenticator app.

    Args:
        request: The incoming request.

    Returns:
        The choice, or a redirect once the login is already protected.
    """
    if factors.ways_to_sign_in(request.user):
        return redirect("home" if request.user.is_verified() else "verify")
    return render(request, "signin/protect.html", {"step": 3})


@second_factor_not_required
def authenticator(request: HttpRequest) -> HttpResponse:
    """Set up an authenticator app, replacing any there was.

    Args:
        request: The incoming request.

    Returns:
        The QR code and key, or a redirect once the app shows a right code: to
        the recovery codes if this is the first way to sign in, else back to
        Security. Once protected, a redirect home outside sudo mode, and to
        Security with no setup begun.
    """
    user = request.user
    first = not factors.ways_to_sign_in(user)
    if not factors.may_change_factors(request):
        return redirect("home")
    # Once protected, a setup starts only by POST from Security, so Back here
    # after one finishes can't start another.
    if not first and AUTHENTICATOR_KEY not in request.session:
        return redirect("security")
    key = request.session.setdefault(AUTHENTICATOR_KEY, default_key())
    device = factors.new_authenticator(user, key)
    if request.method == "POST" and factors.confirm_authenticator(
        device, request.POST.get("code", "")
    ):
        del request.session[AUTHENTICATOR_KEY]
        events.record(request, events.Kind.AUTHENTICATOR_SET_UP)
        # It replaces any old one, which may be what verified this session.
        otp_login(request, device)
        if first:
            return redirect("recovery_codes")
        return redirect("security")
    image = qrcode.make(device.config_url, image_factory=SvgPathImage, border=0)
    secret = b32encode(device.bin_key).decode()
    return render(
        request,
        "signin/authenticator.html",
        {
            **(
                {"base": "signin/page.html", "step": 3}
                if first
                else {"base": "ui/screen.html", **SECURITY_SCREEN}
            ),
            # Built from the key alone; nothing typed by anyone goes into it.
            "qr": mark_safe(image.to_string(encoding="unicode")),  # noqa: S308
            "secret": " ".join(secret[i : i + 4] for i in range(0, len(secret), 4)),
            "error": WRONG_CODE if request.method == "POST" else "",
        },
    )


def recovery_codes(request: HttpRequest) -> HttpResponse:
    """Step 4 of claiming: the recovery codes, shown this once.

    Args:
        request: The incoming request.

    Returns:
        The codes, or a redirect home once they have been issued.
    """
    if factors.has_recovery_codes(request.user):
        return redirect("home")
    codes = factors.issue_recovery_codes(request.user)
    events.record(request, events.Kind.RECOVERY_CODES_ISSUED)
    return render(request, "signin/recovery_codes.html", {"codes": codes, "step": 4})


class LoginView(auth_views.LoginView):
    """Password sign-in. An unclaimed install has no login, so it goes to claim."""

    template_name = "signin/login.html"
    authentication_form = SignInForm
    redirect_authenticated_user = True

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

    def form_valid(self, form: SignInForm) -> HttpResponse:
        """Sign in, logging it if the password is all there is to sign in with.

        Returns:
            A redirect on, to set up a second step if there's none.
        """
        response = super().form_valid(form)
        if not factors.ways_to_sign_in(form.get_user()):
            events.signed_in(self.request, "Password")
        return response

    def form_invalid(self, form: SignInForm) -> HttpResponse:
        """Log the wrong password.

        Returns:
            The form with its errors.
        """
        events.failed(self.request, events.Kind.WRONG_PASSWORD)
        return super().form_invalid(form)


@second_factor_not_required
def verify(request: HttpRequest) -> HttpResponse:
    """The second step of signing in after a password: a code or a passkey.

    Signing in counts as confirming it's you, so it opens sudo mode, even by a
    recovery code: the owner who lost their authenticator needs it to set up
    another.

    Args:
        request: The incoming request.

    Returns:
        The form, or a redirect on to `next` once verified.
    """
    user = request.user
    if user.is_verified():
        return redirect(_next(request))
    if not factors.ways_to_sign_in(user):
        return redirect("protect")
    if request.method == "POST" and (response := throttle.paused(request)):
        return response
    form = CodeForm(user, request.POST or None, recovery=True)
    if form.is_valid():
        otp_login(request, form.device)
        factors.start_sudo(request)
        recovery = isinstance(form.device, StaticDevice)
        events.signed_in(
            request,
            f"Password and {'recovery' if recovery else 'authenticator'} code",
        )
        return redirect(_next(request))
    if form.is_bound:
        throttle.wrong_code(request, user)
    return render(
        request,
        "signin/verify.html",
        {"form": form, "passkeys": factors.passkeys(user), "next": _next(request)},
    )


def confirm(request: HttpRequest) -> HttpResponse:
    """Confirm it's you by passkey or authenticator app, opening sudo mode.

    Args:
        request: The incoming request.

    Returns:
        The form, or a redirect on to `next` once confirmed or while still
        confirmed.
    """
    user = request.user
    if request.method == "GET" and factors.in_sudo(request):
        return redirect(_next(request))
    if request.method == "POST" and (response := throttle.paused(request)):
        return response
    form = CodeForm(user, request.POST or None, recovery=False)
    if form.is_valid():
        factors.start_sudo(request)
        return redirect(_next(request))
    if form.is_bound:
        throttle.wrong_code(request, user)
    return render(
        request,
        "signin/confirm.html",
        {
            "form": form,
            "passkeys": factors.passkeys(user),
            "authenticator": factors.authenticator(user),
            "next": _next(request),
            "tab": "home",
            "back": "settings",
            "title": "Confirm it's you",
        },
    )


@login_not_required
def admin_login(request: HttpRequest) -> HttpResponse:
    """Send the Django admin's sign-in to Folio's.

    Args:
        request: The incoming request.

    Returns:
        A redirect to Folio's sign-in, coming back to the admin after.
    """
    return auth_views.redirect_to_login(request.GET.get("next", reverse("admin:index")))
