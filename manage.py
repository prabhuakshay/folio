#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys

DJANGO_IMPORT_ERROR = (
    "Couldn't import Django. Are you sure it's installed and "
    "available on your PYTHONPATH environment variable? Did you "
    "forget to activate a virtual environment?"
)


def main() -> None:
    """Run administrative tasks.

    Raises:
        ImportError: If Django is not installed or not importable.
    """
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(DJANGO_IMPORT_ERROR) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
