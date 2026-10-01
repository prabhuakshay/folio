import pytest

from signin.client import describe


@pytest.mark.parametrize(
    ("user_agent", "device"),
    [
        (
            (
                "Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36"
            ),
            "Chrome on Android",
        ),
        (
            (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Mobile/15E148 "
                "Safari/604.1"
            ),
            "Safari on iPhone",
        ),
        (
            (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0"
            ),
            "Edge on Windows",
        ),
        (
            "Mozilla/5.0 (X11; Linux x86_64; rv:143.0) Gecko/20100101 Firefox/143.0",
            "Firefox on Linux",
        ),
        ("curl/8.5.0", "Unknown device"),
        ("", "Unknown device"),
    ],
)
def test_describe_names_the_browser_and_system(user_agent, device):
    assert describe(user_agent) == device
