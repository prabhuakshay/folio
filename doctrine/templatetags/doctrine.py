"""Template helpers for the Doctrine."""

from django import template

from doctrine import thresholds

register = template.Library()


@register.simple_tag
def thresholds_changed() -> str:
    """How many thresholds differ from their defaults, for Settings' row.

    Returns:
        `All at default`, or a line such as `2 changed`.
    """
    values = thresholds.current()
    count = sum(values[spec.key] != spec.default for spec in thresholds.SPECS)
    return f"{count} changed" if count else "All at default"
