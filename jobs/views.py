"""Settings > Price feeds."""

from typing import TYPE_CHECKING

from django.shortcuts import render

from jobs.models import Run

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse

LOG_LENGTH = 100


def price_feeds(request: HttpRequest) -> HttpResponse:
    """The latest runs of every scheduled command, newest first.

    Args:
        request: The incoming request.

    Returns:
        The screen.
    """
    return render(
        request,
        "jobs/price_feeds.html",
        {
            "tab": "home",
            "back": "settings",
            "title": "Price feeds",
            "runs": Run.objects.all()[:LOG_LENGTH],
        },
    )
