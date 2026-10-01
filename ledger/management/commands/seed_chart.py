"""Seed the Chart of Accounts if there is none."""

from django.core.management.base import BaseCommand

from ledger.chart import seed


class Command(BaseCommand):
    """Seed the Chart of Accounts if there is none."""

    help = "Seed the Chart of Accounts if there is none. An existing one is kept."

    def handle(self, *args: object, **options: object) -> None:  # noqa: ARG002
        """Seed it, saying whether it did."""
        if seed():
            self.stdout.write("Seeded the Chart of Accounts.")
        else:
            self.stdout.write("The Chart of Accounts already exists; left as it is.")
