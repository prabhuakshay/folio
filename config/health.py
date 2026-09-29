"""Health probe for the container runtime and load balancers."""

from django.db import DatabaseError, connection
from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_GET


@require_GET
def healthz(request: HttpRequest) -> HttpResponse:  # noqa: ARG001
    """Report whether this instance can serve requests.

    Checks the database as well as the process: a worker that is up but can't
    reach its database answers every real request with a 500, and a probe that
    ignored that would keep it in rotation.

    Args:
        request: The incoming request (unused).

    Returns:
        `200 ok` when the database answers, `503 unavailable` otherwise.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except DatabaseError:
        return HttpResponse("unavailable\n", status=503, content_type="text/plain")
    return HttpResponse("ok\n", content_type="text/plain")
