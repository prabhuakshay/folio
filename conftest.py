"""Project-wide test fixtures."""

from typing import TYPE_CHECKING

import pytest

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
