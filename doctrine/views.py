"""Settings > Doctrine thresholds."""

from itertools import groupby
from typing import TYPE_CHECKING

from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from doctrine import thresholds
from doctrine.forms import ThresholdForm
from doctrine.models import Threshold

if TYPE_CHECKING:
    from decimal import Decimal

    from django.db.models import QuerySet
    from django.http import HttpRequest, HttpResponse


def _spec_or_404(key: str) -> thresholds.Spec:
    try:
        return thresholds.BY_KEY[thresholds.Key(key)]
    except ValueError:
        raise Http404 from None


def _row(spec: thresholds.Spec, value: Decimal) -> dict:
    return {
        "spec": spec,
        "shown": spec.format(value),
        "default": spec.format(spec.default),
        "input": thresholds.number(value),
        "outside": not spec.within_band(value),
        "changed": value != spec.default,
    }


def thresholds_screen(
    request: HttpRequest, refused: ThresholdForm | None = None, key: str = ""
) -> HttpResponse:
    """Every threshold, grouped as the Doctrine lists them, with value and band.

    Args:
        request: The incoming request.
        refused: A form whose value wasn't a number, to show again.
        key: The threshold `refused` was for, whose sheet opens on load.

    Returns:
        The screen.
    """
    values = thresholds.current()
    rows = [_row(spec, values[spec.key]) for spec in thresholds.SPECS]
    if refused:
        refused_row = next(r for r in rows if r["spec"].key == key)
        refused_row["input"] = refused.data.get("value", "")
        refused_row["errors"] = refused.errors["value"]
    return render(
        request,
        "doctrine/thresholds.html",
        {
            "tab": "home",
            "back": "settings",
            "title": "Doctrine thresholds",
            "groups": [
                (group, list(rows))
                for group, rows in groupby(rows, lambda r: r["spec"].group)
            ],
            "open": key,
            "any_changed": any(r["changed"] for r in rows),
        },
    )


def _delete(rows: QuerySet[Threshold]) -> None:
    # One at a time, so simple-history records each deletion.
    for row in rows:
        row.delete()


@require_POST
def edit(request: HttpRequest, key: str) -> HttpResponse:
    """Set a threshold. A value outside its band is kept, with a warning.

    Args:
        request: The incoming request.
        key: Which threshold.

    Returns:
        A redirect to the screen, or the screen with the sheet reopened on a
        value that isn't a number.
    """
    spec = _spec_or_404(key)
    form = ThresholdForm(request.POST)
    if not form.is_valid():
        return thresholds_screen(request, form, spec.key)
    value = form.cleaned_data["value"]
    if value == spec.default:
        _delete(Threshold.objects.filter(key=spec.key))
    else:
        row, created = Threshold.objects.get_or_create(
            key=spec.key, defaults={"value": value}
        )
        if not created and row.value != value:
            row.value = value
            row.save()
    return redirect("thresholds")


@require_POST
def reset(request: HttpRequest, key: str) -> HttpResponse:  # noqa: ARG001
    """Put a threshold back to its default.

    Args:
        request: The incoming request (unused).
        key: Which threshold.

    Returns:
        A redirect to the screen.
    """
    _delete(Threshold.objects.filter(key=_spec_or_404(key).key))
    return redirect("thresholds")


@require_POST
def reset_all(request: HttpRequest) -> HttpResponse:  # noqa: ARG001
    """Put every threshold back to its default.

    Args:
        request: The incoming request (unused).

    Returns:
        A redirect to the screen.
    """
    _delete(Threshold.objects.all())
    return redirect("thresholds")
