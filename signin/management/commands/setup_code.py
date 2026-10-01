"""Print the setup code for an unclaimed install."""

from django.core.management.base import BaseCommand

from signin.claim import is_claimed, setup_code


class Command(BaseCommand):
    """Print the code that claims this install, while it has no login."""

    help = "Print the setup code that claims this install, while it has no login."

    def handle(self, *args: object, **options: object) -> None:  # noqa: ARG002
        """Print the code, or say the install is already claimed."""
        if is_claimed():
            self.stdout.write("Folio is claimed; there is no setup code.")
        else:
            self.stdout.write(
                f"Setup code: {setup_code()}  (enter it to claim this Folio)"
            )
