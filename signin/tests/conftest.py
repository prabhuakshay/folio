from datetime import timedelta

import pytest
from django.utils import timezone


@pytest.fixture
def clock(monkeypatch):
    class Clock:
        now = timezone.now()

        def advance(self, **delta):
            self.now += timedelta(**delta)

    c = Clock()
    monkeypatch.setattr(timezone, "now", lambda: c.now)
    return c
