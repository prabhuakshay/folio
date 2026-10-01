"""Accounts in the Chart of Accounts, and the words that name them."""

from django.db import models
from django.db.models import Exists, OuterRef, Q, Value
from django.db.models.functions import Lower, Replace
from simple_history.models import HistoricalRecords


def _spaceless(field: str) -> Replace:
    return Replace(Lower(field), Value(" "), Value(""))


def key(text: str) -> str:
    """How a typed name is compared: ignoring case and spaces.

    Returns:
        The text lowercased with its spaces removed.
    """
    return "".join(text.split()).lower()


class AssetClass(models.TextChoices):
    """What an Asset counts as in allocations."""

    EQUITY = "equity", "Equity"
    DEBT = "debt", "Debt"
    GOLD_SILVER = "gold_silver", "Gold & silver"
    REAL_ESTATE = "real_estate", "Real estate"
    CASH = "cash", "Cash"


class AccountQuerySet(models.QuerySet):
    """Queries over the Chart of Accounts."""

    def answering(self, text: str) -> AccountQuerySet:
        """Accounts that a typed word names, by their name or an alias.

        Returns:
            The matching Accounts; more than one when the word is ambiguous.
        """
        typed = key(text)
        aliased = Alias.objects.alias(k=_spaceless("word")).filter(
            account=OuterRef("pk"), k=typed
        )
        return self.alias(k=_spaceless("name")).filter(Q(k=typed) | Exists(aliased))


class Account(models.Model):
    """A node in the Chart of Accounts.

    Each Account Type has one root, with no parent; everything else sits under
    a group of its own type. Postings hit leaves only.
    """

    class Type(models.TextChoices):
        ASSET = "asset", "Asset"
        LIABILITY = "liability", "Liability"
        EQUITY = "equity", "Equity"
        INCOME = "income", "Income"
        EXPENSE = "expense", "Expense"

    class Role(models.TextChoices):
        OPENING_BALANCES = "opening_balances", "Opening Balances"
        REALISED_GAINS = "realised_gains", "Realised Gains"
        INTEREST = "interest", "Interest"
        DIVIDENDS = "dividends", "Dividends"
        REWARDS = "rewards", "Rewards & cashback"
        INTEREST_PAID = "interest_paid", "Interest paid"
        BANK_CHARGES = "bank_charges", "Bank charges & fees"
        INSURANCE_PREMIUMS = "insurance_premiums", "Insurance premiums"
        TAXES = "taxes", "Taxes"
        UNCATEGORISED = "uncategorised", "Uncategorised"

    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=16, choices=Type)
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
    )
    is_group = models.BooleanField(default=False)
    role = models.CharField(max_length=32, choices=Role, blank=True, default="")
    # On an Asset group, the defaults for new leaves under it.
    asset_class = models.CharField(
        max_length=16, choices=AssetClass, blank=True, default=""
    )
    emergency_fund_eligible = models.BooleanField(default=False)

    history = HistoricalRecords()

    objects = AccountQuerySet.as_manager()

    class Meta:
        ordering = [Lower("name")]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                "parent",
                name="account_name_unique_in_group",
                violation_error_message="Another Account in this group has this name.",
            ),
            models.UniqueConstraint(
                fields=["account_type"],
                condition=Q(parent=None),
                name="one_root_per_type",
            ),
            models.UniqueConstraint(
                fields=["role"],
                condition=~Q(role=""),
                name="role_on_one_account",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def add_child(self, name: str, **fields: object) -> Account:
        """Create an Account under this group, of its type.

        A new leaf under an Asset group takes the group's Asset Class and
        Emergency-Fund eligibility unless given its own.

        Args:
            name: The new Account's name.
            **fields: Any other Account fields.

        Returns:
            The new Account.

        Raises:
            ValueError: This Account is a leaf.
        """
        if not self.is_group:
            msg = f"{self} is a leaf; only a group has Accounts under it."
            raise ValueError(msg)
        fields = {
            "asset_class": self.asset_class,
            "emergency_fund_eligible": self.emergency_fund_eligible,
            **fields,
        }
        return Account.objects.create(
            name=name, account_type=self.account_type, parent=self, **fields
        )


class Alias(models.Model):
    """A word that also names its Account when typed, such as `gpay`."""

    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="aliases"
    )
    word = models.CharField(max_length=50)

    history = HistoricalRecords()

    class Meta:
        ordering = ["pk"]
        constraints = [
            models.UniqueConstraint(
                Lower("word"), "account", name="alias_unique_per_account"
            ),
        ]

    def __str__(self) -> str:
        return self.word
