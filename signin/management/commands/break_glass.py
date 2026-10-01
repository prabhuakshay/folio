"""Let the owner back in from the server when every way to sign in is lost."""

from axes.utils import reset as lift_pauses
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils.crypto import get_random_string
from django_otp.plugins.otp_static.models import StaticDevice
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp_webauthn.models import WebAuthnCredential

from signin import events, sessions

# Lower case without look-alikes (i, l, o), easy to type on a phone.
_LETTERS = "abcdefghjkmnpqrstuvwxyz"


class Command(BaseCommand):
    """Reset two-factor sign-in, the password, or both."""

    help = (
        "Reset two-factor sign-in and/or the password, sign out every device and "
        "lift every sign-in pause."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        """Choose what to reset."""
        parser.add_argument(
            "--two-factor",
            action="store_true",
            help="Remove every passkey, authenticator app and recovery code. "
            "The password alone then signs in, straight to setting up a new one.",
        )
        parser.add_argument(
            "--password",
            action="store_true",
            help="Set a new random password and print it.",
        )

    @transaction.atomic
    def handle(self, *args: object, **options: object) -> None:  # noqa: ARG002
        """Reset what was chosen.

        Raises:
            CommandError: Nothing was chosen, or there is no login yet.
        """
        two_factor, password = options["two_factor"], options["password"]
        if not two_factor and not password:
            msg = "Choose what to reset: --two-factor, --password or both."
            raise CommandError(msg)
        owner = get_user_model().objects.first()
        if owner is None:
            msg = "Folio isn't claimed yet; there's nothing to reset."
            raise CommandError(msg)

        reset = []
        if two_factor:
            for device in (TOTPDevice, StaticDevice, WebAuthnCredential):
                device.objects.filter(user=owner).delete()
            reset.append("two-factor")
            self.stdout.write(
                "Two-factor reset: sign in with the password to set it up again."
            )
        if password:
            new_password = "-".join(get_random_string(4, _LETTERS) for _ in range(4))
            owner.set_password(new_password)
            owner.save(update_fields=["password"])
            reset.append("password")
            self.stdout.write(
                f"New password: {new_password}  (change it once signed in)"
            )

        sessions.sign_out_everywhere(owner)
        lift_pauses()
        events.record(
            None, events.Kind.RESET_ON_SERVER, " and ".join(reset).capitalize()
        )
        self.stdout.write("Every device is signed out and every sign-in pause lifted.")
