"""Hold a signed-in session at its second factor until it's passed."""

from typing import TYPE_CHECKING

from django.contrib.auth.views import redirect_to_login
from django.utils.deprecation import MiddlewareMixin

from signin.factors import ways_to_sign_in

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpRequest, HttpResponse


def second_factor_not_required[V: Callable](view: V) -> V:
    """Let a password-only session reach this view: it is part of signing in.

    Returns:
        The view, marked.
    """
    view.second_factor_required = False
    return view


class SecondFactorRequiredMiddleware(MiddlewareMixin):
    """Send a session that only passed the password on to its second factor.

    A login with nothing set up yet is sent to set one up instead. Runs after
    `LoginRequiredMiddleware` and django-otp's `OTPMiddleware`.
    """

    def process_view(
        self,
        request: HttpRequest,
        view_func: Callable,
        view_args: object,  # noqa: ARG002
        view_kwargs: object,  # noqa: ARG002
    ) -> HttpResponse | None:
        """Redirect an unverified session away from every view that needs one.

        Returns:
            A redirect, or None to let the request through.
        """
        user = request.user
        if not user.is_authenticated or user.is_verified():
            return None
        if not getattr(view_func, "login_required", True):
            return None
        if not getattr(view_func, "second_factor_required", True):
            return None
        target = "verify" if ways_to_sign_in(user) else "protect"
        return redirect_to_login(request.get_full_path(), target)
