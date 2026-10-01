"""App shell views."""

from django.contrib.auth.decorators import login_not_required
from django.http import HttpRequest, JsonResponse
from django.templatetags.static import static
from django.urls import reverse

THEME_COLOUR = "#FFFFFF"


# Browsers fetch the manifest without cookies, so it can't sit behind sign-in.
@login_not_required
def manifest(request: HttpRequest) -> JsonResponse:  # noqa: ARG001
    """Describe Folio as an installable app.

    Args:
        request: The incoming request (unused).

    Returns:
        The web app manifest.
    """
    return JsonResponse(
        {
            "id": reverse("home"),
            "name": "Folio",
            "short_name": "Folio",
            "start_url": reverse("home"),
            "scope": reverse("home"),
            "display": "standalone",
            "background_color": THEME_COLOUR,
            "theme_color": THEME_COLOUR,
            "icons": [
                {
                    "src": static("icons/icon-192.png"),
                    "sizes": "192x192",
                    "type": "image/png",
                },
                {
                    "src": static("icons/icon-512.png"),
                    "sizes": "512x512",
                    "type": "image/png",
                },
                {
                    "src": static("icons/icon-maskable-512.png"),
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "maskable",
                },
            ],
        },
        content_type="application/manifest+json",
    )
