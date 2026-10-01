"""The seeded Chart of Accounts, and finding the Accounts that hold a role.

Roles let Folio find the Accounts it depends on without relying on names. Ask
for one with `account_for(role)`: if its Account was deleted, it comes back,
named and shaped as seeded, at the top of its Account Type's tree.
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.db import connections, transaction
from django.db.models import Q

from ledger.models import Account, AssetClass

if TYPE_CHECKING:
    from collections.abc import Iterator

    from django.db.models import QuerySet

Role = Account.Role
Type = Account.Type

SEP = " \N{SINGLE RIGHT-POINTING ANGLE QUOTATION MARK} "


@dataclass(frozen=True)
class Node:
    """An Account as seeded."""

    name: str
    children: tuple[Node, ...] = ()
    is_group: bool = False
    role: str = ""
    asset_class: str = ""
    emergency_fund_eligible: bool = False

    def walk(self) -> Iterator[Node]:
        """This node and everything under it, depth first.

        Yields:
            Each node.
        """
        yield self
        for child in self.children:
            yield from child.walk()


def group(name: str, *children: Node | str, **fields: object) -> Node:
    """A seeded group, whose children may be given as leaf names.

    Returns:
        The node.
    """
    nodes = tuple(Node(c) if isinstance(c, str) else c for c in children)
    return Node(name, nodes, is_group=True, **fields)


SEED: dict[Type, Node] = {
    Type.ASSET: group(
        "Assets",
        group("Bank & Cash", asset_class=AssetClass.CASH, emergency_fund_eligible=True),
        group("Deposits", asset_class=AssetClass.DEBT),
        group("Retirement", asset_class=AssetClass.DEBT),
        # A Holding's class comes from its Instrument's split.
        group("Mutual Funds"),
        group("Stocks & ETFs", asset_class=AssetClass.EQUITY),
        group("Bonds & SGBs", asset_class=AssetClass.DEBT),
        group("Gold & Silver", asset_class=AssetClass.GOLD_SILVER),
        group("Property", asset_class=AssetClass.REAL_ESTATE),
        group("Insurance Policies", asset_class=AssetClass.DEBT),
        group("Chit Funds", asset_class=AssetClass.DEBT),
        # Money lent counts in Net Worth but in no allocation.
        group("Receivables"),
    ),
    Type.LIABILITY: group(
        "Liabilities",
        group("Credit Cards"),
        group("Loans"),
        group("Card EMIs"),
        group("Payables"),
    ),
    Type.INCOME: group(
        "Income",
        group("Salary", "Gross salary", "Bonus", "Employer contributions (PF/NPS)"),
        Node("Business & freelance"),
        Node("Rental income"),
        Node("Interest", role=Role.INTEREST),
        Node("Dividends", role=Role.DIVIDENDS),
        Node("Realised Gains", role=Role.REALISED_GAINS),
        Node("Rewards & cashback", role=Role.REWARDS),
        Node("Gifts received"),
        Node("Other income"),
    ),
    Type.EXPENSE: group(
        "Expenses",
        group("Housing", "Rent", "Maintenance & society", "Property tax", "Repairs"),
        group(
            "Utilities",
            "Electricity",
            "Water",
            "Gas (LPG/PNG)",
            "Mobile",
            "Internet & DTH",
        ),
        group("Food", "Groceries", "Dining out", "Food delivery"),
        group("Household", "Domestic help", "Household supplies", "Laundry"),
        group(
            "Transport",
            "Fuel",
            "Vehicle service",
            "Cabs & autos",
            "Public transport",
            "Parking & tolls",
        ),
        group("Health", "Consultations", "Medicines", "Lab tests", "Fitness"),
        group("Education", "School fees", "Courses & tuition", "Books"),
        group(
            "Shopping", "Clothing", "Electronics", "Home & furniture", "Personal care"
        ),
        group("Leisure", "Subscriptions", "Outings & movies", "Hobbies"),
        group("Travel", "Travel & holidays"),
        group(
            "Family & social",
            "Festivals",
            "Gifts given",
            "Weddings & functions",
            "Support to family",
            "Donations & religious",
        ),
        Node("Insurance premiums", role=Role.INSURANCE_PREMIUMS),
        group(
            "Finance costs",
            Node("Interest paid", role=Role.INTEREST_PAID),
            Node("Bank charges & fees", role=Role.BANK_CHARGES),
        ),
        group("Taxes", "Income tax", "Professional tax", role=Role.TAXES),
        Node("Uncategorised", role=Role.UNCATEGORISED),
    ),
    Type.EQUITY: group("Equity", Node("Opening Balances", role=Role.OPENING_BALANCES)),
}


ROLE_ABOUT: dict[Role, str] = {
    Role.OPENING_BALANCES: (
        "The other side of every Account's starting balance, so money you "
        "had before you started Folio still balances."
    ),
    Role.REALISED_GAINS: "Profit or loss booked when you sell an investment.",
    Role.INTEREST: ("Interest you earn: savings, FDs, RDs, EPF, PPF and bond coupons."),
    Role.DIVIDENDS: "Dividends, paid out or reinvested.",
    Role.REWARDS: (
        "Card rewards and cashback. Typing “cashback” in quick-add puts it here."
    ),
    Role.INTEREST_PAID: (
        "Interest on loans and card finance charges, unless a loan has its "
        "own interest Account."
    ),
    Role.BANK_CHARGES: (
        "Late, annual, processing, foreclosure and DP charges, GST on them, "
        "and NPS charges."
    ),
    Role.INSURANCE_PREMIUMS: (
        "Premiums for pure protection, such as health and term cover."
    ),
    Role.TAXES: (
        "A group: everything under it counts as tax (TDS, advance tax, "
        "professional tax), which Take-home leaves out."
    ),
    Role.UNCATEGORISED: (
        "Where quick-add and statement imports put what they can't place, "
        "for you to sort later."
    ),
}


def _account(
    node: Node, account_type: Type, parent: Account | None, name: str = ""
) -> Account:
    return Account.objects.create(
        name=name or node.name,
        account_type=account_type,
        parent=parent,
        is_group=node.is_group,
        role=node.role,
        asset_class=node.asset_class,
        emergency_fund_eligible=node.emergency_fund_eligible,
    )


def _create(node: Node, account_type: Type, parent: Account | None) -> None:
    account = _account(node, account_type, parent)
    for child in node.children:
        _create(child, account_type, account)


def seed() -> bool:
    """Create the seeded Chart of Accounts, unless there already is one.

    Returns:
        Whether it was created; an existing chart, edited or not, is left alone.
    """
    if Account.objects.exists():
        return False
    with transaction.atomic():
        for account_type, root in SEED.items():
            _create(root, account_type, None)
    return True


def seed_after_migrate(using: str, **kwargs: object) -> None:  # noqa: ARG001
    """Seed on first run, once the ledger's tables exist.

    Args:
        using: The database migrated.
        **kwargs: The rest of the signal's arguments (unused).
    """
    if Account._meta.db_table in connections[using].introspection.table_names():  # noqa: SLF001
        seed()


def root(account_type: Type) -> Account:
    """The top of an Account Type's tree.

    Returns:
        The root Account.
    """
    return Account.objects.get_or_create(
        parent=None,
        account_type=account_type,
        defaults={"name": SEED[account_type].name, "is_group": True},
    )[0]


@dataclass(frozen=True)
class Row:
    """An Account in its tree, with the groups above it (its root left out)."""

    account: Account
    ancestors: tuple[Account, ...]

    @property
    def depth(self) -> int:
        """How many groups down from the top of its tree."""
        return len(self.ancestors)

    @property
    def path(self) -> str:
        """Where it sits, such as `Finance costs > Interest paid`."""
        return SEP.join(a.name for a in (*self.ancestors, self.account))


def tree(account_type: Type) -> list[Row]:
    """An Account Type's tree below its root, each group before what's under it.

    Returns:
        The rows, siblings in name order.
    """
    top = root(account_type)
    under = defaultdict(list)
    accounts = Account.objects.filter(account_type=account_type)
    for account in accounts.prefetch_related("aliases"):
        under[account.parent_id].append(account)
    rows = []

    def visit(parent: Account, ancestors: tuple[Account, ...]) -> None:
        for account in under[parent.pk]:
            rows.append(Row(account, ancestors))
            visit(account, (*ancestors, account))

    visit(top, ())
    return rows


def groups(account_type: Type) -> list[tuple[Account, str]]:
    """An Account Type's groups, each named by its path from the top.

    Returns:
        Each group with its path, the top of the tree first.
    """
    top = root(account_type)
    return [(top, top.name)] + [
        (row.account, f"{top.name}{SEP}{row.path}")
        for row in tree(account_type)
        if row.account.is_group
    ]


def groups_to_move_to(account: Account) -> list[tuple[Account, str]]:
    """The groups an Account can move under: its type's, not itself or below it.

    Returns:
        Each group with its path, the top of the tree first.
    """
    below = {
        row.account for row in tree(account.account_type) if account in row.ancestors
    }
    return [
        (group, path)
        for group, path in groups(account.account_type)
        if group != account and group not in below
    ]


def _seeded(role: Role) -> tuple[Type, Node]:
    return next(
        (account_type, node)
        for account_type, top in SEED.items()
        for node in top.walk()
        if node.role == role
    )


def account_for(role: Role) -> Account:
    """The Account that holds a role, recreated if it was deleted.

    Returns:
        The Account.
    """
    if account := Account.objects.filter(role=role).first():
        return account
    account_type, node = _seeded(role)
    top = root(account_type)
    name, n = node.name, 1
    # The seeded name may now belong to another Account at the top of the tree.
    while top.children.filter(name__iexact=name).exists():
        n += 1
        name = f"{node.name} {n}"
    return _account(node, account_type, top, name)


def candidates(role: Role) -> QuerySet[Account]:
    """The Accounts a role could be pointed at: its type and shape, and free.

    Returns:
        The Accounts, including the one holding it now.
    """
    account_type, node = _seeded(role)
    return Account.objects.filter(
        Q(role="") | Q(role=role),
        account_type=account_type,
        is_group=node.is_group,
        parent__isnull=False,
    )


@transaction.atomic
def repoint(role: Role, account: Account) -> None:
    """Move a role to another Account; the old one keeps everything else.

    Raises:
        ValueError: The Account doesn't fit the role.
    """
    if not candidates(role).filter(pk=account.pk).exists():
        msg = f"{account} doesn't fit the {Role(role).label} role."
        raise ValueError(msg)
    # One at a time, so simple-history records each change.
    for old in Account.objects.filter(role=role).exclude(pk=account.pk):
        old.role = ""
        old.save()
    account.role = role
    account.save()
