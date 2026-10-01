"""Keep search engines out: Folio is one person's ledger, never a public page."""

from typing import TYPE_CHECKING

from django.contrib.auth.decorators import login_not_required
from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_safe

if TYPE_CHECKING:
    from collections.abc import Callable


@login_not_required
@require_safe
def robots_txt(request: HttpRequest) -> HttpResponse:  # noqa: ARG001
    """Disallow every path to every crawler.

    Args:
        request: The incoming request (unused).

    Returns:
        A plain-text `robots.txt` that disallows everything.
    """
    return HttpResponse("User-agent: *\nDisallow: /\n", content_type="text/plain")


def noindex_middleware(
    get_response: Callable[[HttpRequest], HttpResponse],
) -> Callable[[HttpRequest], HttpResponse]:
    """Mark every response `noindex`, for crawlers that ignore `robots.txt`.

    Args:
        get_response: The next middleware or view in the chain.

    Returns:
        The middleware.
    """

    def middleware(request: HttpRequest) -> HttpResponse:
        response = get_response(request)
        response["X-Robots-Tag"] = "noindex"
        return response

    return middleware
