"""Keep the browser from saving pages: they hold money, secrets and sign-in steps."""

from typing import TYPE_CHECKING

from django.utils.cache import add_never_cache_headers

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpRequest, HttpResponse


def no_store_middleware(
    get_response: Callable[[HttpRequest], HttpResponse],
) -> Callable[[HttpRequest], HttpResponse]:
    """Mark every response from the app's views `no-store`.

    Without it Back, Forward and reload can show recovery codes, an
    authenticator key or a signed-in screen from the browser's saved copy, even
    after signing out. Placed inside WhiteNoise, so static files stay cacheable.

    Args:
        get_response: The next middleware or view in the chain.

    Returns:
        The middleware.
    """

    def middleware(request: HttpRequest) -> HttpResponse:
        response = get_response(request)
        add_never_cache_headers(response)
        return response

    return middleware
