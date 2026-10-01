"""Where a request comes from: its address and the device that sent it."""

import re
from typing import TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:
    from django.http import HttpRequest

# First match wins, so Edge and Opera come before the Chrome they claim to be,
# and Chrome before the Safari it claims to be.
_BROWSERS = [
    ("Edge", r"Edg(e|A|iOS)?/"),
    ("Opera", r"OPR/"),
    ("Samsung Internet", r"SamsungBrowser/"),
    ("Firefox", r"Firefox/|FxiOS/"),
    ("Chrome", r"Chrome/|CriOS/"),
    ("Safari", r"Safari/"),
]
_SYSTEMS = [
    ("iPhone", r"iPhone"),
    ("iPad", r"iPad"),
    ("Android", r"Android"),
    ("Mac", r"Macintosh"),
    ("Windows", r"Windows"),
    ("ChromeOS", r"CrOS"),
    ("Linux", r"Linux"),
]


def ip_address(request: HttpRequest) -> str:
    """The client's address.

    Behind the proxy, it's the last address in X-Forwarded-For: the one the
    proxy added. Any before it were sent by the client and can't be trusted.

    Returns:
        The address, or an empty string when there is none.
    """
    forwarded = request.headers.get("X-Forwarded-For", "")
    if settings.USE_X_FORWARDED_FOR and forwarded:
        return forwarded.rsplit(",", 1)[-1].strip()
    return request.META.get("REMOTE_ADDR", "")


def describe(user_agent: str) -> str:
    """Name a device the way its owner would recognise it.

    Versions are left out, so a browser update isn't a new device.

    Args:
        user_agent: The User-Agent header.

    Returns:
        Such as `Chrome on Android`, or `Unknown device`.
    """
    browser = next((name for name, p in _BROWSERS if re.search(p, user_agent)), "")
    system = next((name for name, p in _SYSTEMS if re.search(p, user_agent)), "")
    if browser and system:
        return f"{browser} on {system}"
    return browser or system or "Unknown device"


def device(request: HttpRequest) -> str:
    """The device the request came from.

    Returns:
        Such as `Safari on iPhone`.
    """
    return describe(request.headers.get("User-Agent", ""))
