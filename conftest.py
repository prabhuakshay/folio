"""Project-wide test fixtures."""

from datetime import timedelta
from typing import TYPE_CHECKING

import pytest
from django.utils import timezone

if TYPE_CHECKING:
    from pytest_django.fixtures import SettingsWrapper


@pytest.fixture(autouse=True)
def _unhashed_static(settings: SettingsWrapper) -> None:
    # The hashed storage needs `collectstatic` to have run; tests only need URLs.
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> object:
    """Freeze `timezone.now`, moving only when a test advances it.

    Returns:
        The clock: read `now`, call `advance(**timedelta_kwargs)`.
    """

    class Clock:
        now = timezone.now()

        def advance(self, **delta: float) -> None:
            self.now += timedelta(**delta)

    c = Clock()
    monkeypatch.setattr(timezone, "now", lambda: c.now)
    return c
