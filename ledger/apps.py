"""The ledger: the Chart of Accounts and the Postings that hit it."""

from django.apps import AppConfig
from django.db.models.signals import post_migrate


class LedgerConfig(AppConfig):
    """Ledger configuration."""

    name = "ledger"

    def ready(self) -> None:
        """Seed the Chart of Accounts once the tables exist."""
        from ledger.chart import seed_after_migrate  # noqa: PLC0415

        post_migrate.connect(seed_after_migrate, sender=self)
