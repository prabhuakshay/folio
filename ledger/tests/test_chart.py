import pytest
from django.core.management import call_command

from ledger import chart
from ledger.models import Account, AssetClass

Role = Account.Role
Type = Account.Type


def named(name, account_type=None):
    accounts = Account.objects.filter(name=name)
    if account_type:
        accounts = accounts.filter(account_type=account_type)
    return accounts.get()


def children(name, account_type=None):
    return [a.name for a in named(name, account_type).children.all()]


@pytest.mark.django_db
def test_the_chart_is_seeded_on_first_run():
    roots = Account.objects.filter(parent=None)

    assert {(a.name, a.account_type) for a in roots} == {
        ("Assets", Type.ASSET),
        ("Liabilities", Type.LIABILITY),
        ("Equity", Type.EQUITY),
        ("Income", Type.INCOME),
        ("Expenses", Type.EXPENSE),
    }
    assert all(a.is_group for a in roots)
    assert children("Finance costs") == ["Bank charges & fees", "Interest paid"]
    assert "Card EMIs" in children("Liabilities")
    assert children("Travel") == ["Travel & holidays"]


@pytest.mark.django_db
def test_asset_and_liability_groups_start_empty():
    groups = Account.objects.filter(
        account_type__in=[Type.ASSET, Type.LIABILITY]
    ).exclude(parent=None)

    assert groups.count() == 15
    assert all(g.is_group and not g.children.exists() for g in groups)


@pytest.mark.django_db
def test_every_account_sits_under_a_group_of_its_own_type():
    for account in Account.objects.exclude(parent=None):
        assert account.parent.is_group
        assert account.parent.account_type == account.account_type


@pytest.mark.django_db
def test_seeding_again_leaves_an_edited_chart_alone():
    groceries = named("Groceries")
    groceries.name = "Kirana"
    groceries.save()

    call_command("seed_chart")

    assert not Account.objects.filter(name="Groceries").exists()


@pytest.mark.django_db
def test_seeding_on_demand_fills_an_empty_chart():
    while Account.objects.exists():
        Account.objects.filter(children=None).delete()

    call_command("seed_chart")

    assert named("Groceries").parent == named("Food")


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("group", "asset_class", "eligible"),
    [
        ("Bank & Cash", AssetClass.CASH, True),
        ("Deposits", AssetClass.DEBT, False),
        ("Gold & Silver", AssetClass.GOLD_SILVER, False),
        ("Property", AssetClass.REAL_ESTATE, False),
        ("Receivables", "", False),
    ],
)
def test_a_new_leaf_takes_its_asset_groups_defaults(group, asset_class, eligible):
    leaf = named(group).add_child("Something")

    assert leaf.account_type == Type.ASSET
    assert not leaf.is_group
    assert leaf.asset_class == asset_class
    assert leaf.emergency_fund_eligible is eligible


@pytest.mark.django_db
def test_a_new_leaf_can_override_its_groups_defaults():
    leaf = named("Bank & Cash").add_child(
        "Old locker", asset_class="", emergency_fund_eligible=False
    )

    assert leaf.asset_class == ""
    assert not leaf.emergency_fund_eligible


@pytest.mark.django_db
def test_a_leaf_has_nothing_under_it():
    with pytest.raises(ValueError, match="leaf"):
        named("Groceries").add_child("Vegetables")


@pytest.mark.django_db
def test_all_ten_roles_are_seeded_each_on_one_account():
    assert {a.role: a.name for a in Account.objects.exclude(role="")} == {
        Role.OPENING_BALANCES: "Opening Balances",
        Role.REALISED_GAINS: "Realised Gains",
        Role.INTEREST: "Interest",
        Role.DIVIDENDS: "Dividends",
        Role.REWARDS: "Rewards & cashback",
        Role.INTEREST_PAID: "Interest paid",
        Role.BANK_CHARGES: "Bank charges & fees",
        Role.INSURANCE_PREMIUMS: "Insurance premiums",
        Role.TAXES: "Taxes",
        Role.UNCATEGORISED: "Uncategorised",
    }


@pytest.mark.django_db
def test_taxes_sits_on_a_group_and_every_other_role_on_a_leaf():
    for account in Account.objects.exclude(role=""):
        assert account.is_group is (account.role == Role.TAXES)
    assert children("Taxes") == ["Income tax", "Professional tax"]


@pytest.mark.django_db
def test_a_role_finds_its_account_whatever_its_name():
    interest = named("Interest", Type.INCOME)
    interest.name = "Interest earned"
    interest.save()

    assert chart.account_for(Role.INTEREST) == interest


@pytest.mark.django_db
def test_asking_for_a_role_whose_account_was_deleted_recreates_it():
    named("Uncategorised").delete()

    account = chart.account_for(Role.UNCATEGORISED)

    assert account.name == "Uncategorised"
    assert account.account_type == Type.EXPENSE
    assert account.parent == named("Expenses")
    assert not account.is_group
    assert chart.account_for(Role.UNCATEGORISED) == account


@pytest.mark.django_db
def test_a_role_recreated_where_its_name_is_taken_gets_a_free_one():
    uncategorised = named("Uncategorised")
    chart.repoint(Role.UNCATEGORISED, named("Food").add_child("Unsorted"))
    named("Unsorted").delete()

    account = chart.account_for(Role.UNCATEGORISED)

    assert account.name == "Uncategorised 2"
    assert account.parent == uncategorised.parent


@pytest.mark.django_db
def test_a_recreated_taxes_role_is_a_group():
    taxes = named("Taxes")
    taxes.children.all().delete()
    taxes.delete()

    assert chart.account_for(Role.TAXES).is_group


@pytest.mark.django_db
def test_repointing_a_role_moves_it_off_its_old_account():
    old = named("Interest paid")
    new = named("Finance costs").add_child("Home loan interest")

    chart.repoint(Role.INTEREST_PAID, new)

    old.refresh_from_db()
    assert old.role == ""
    assert chart.account_for(Role.INTEREST_PAID) == new


@pytest.mark.django_db
def test_a_role_can_go_on_any_free_account_of_its_type_and_shape():
    fits = chart.candidates(Role.INTEREST_PAID)

    assert named("Groceries") in fits
    assert named("Interest paid") in fits
    assert all(a.account_type == Type.EXPENSE and not a.is_group for a in fits)
    assert named("Income tax", Type.EXPENSE) in fits
    assert named("Taxes") in chart.candidates(Role.TAXES)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("role", "name"),
    [
        (Role.INTEREST_PAID, "Rental income"),  # another type
        (Role.TAXES, "Groceries"),  # a leaf, not a group
        (Role.UNCATEGORISED, "Food"),  # a group, not a leaf
        (Role.INTEREST_PAID, "Bank charges & fees"),  # holds another role
        (Role.OPENING_BALANCES, "Equity"),  # a root
    ],
)
def test_a_role_goes_only_where_it_fits(role, name):
    target = named(name)

    assert target not in chart.candidates(role)
    with pytest.raises(ValueError, match="fit"):
        chart.repoint(role, target)


@pytest.mark.django_db
def test_an_account_answers_to_its_name_and_aliases():
    hdfc = named("Bank & Cash").add_child("HDFC Savings")
    hdfc.aliases.create(word="hdfc")
    card = named("Credit Cards").add_child("HDFC Card")
    card.aliases.create(word="hdfc")
    card.aliases.create(word="card")

    assert list(Account.objects.answering("HDFC savings")) == [hdfc]
    assert list(Account.objects.answering(" hdfcsavings ")) == [hdfc]
    assert list(Account.objects.answering("CARD")) == [card]
    assert set(Account.objects.answering("hdfc")) == {hdfc, card}
    assert not Account.objects.answering("gpay").exists()


@pytest.mark.django_db
def test_accounts_and_aliases_are_audited():
    groceries = named("Groceries")
    groceries.name = "Kirana"
    groceries.save()
    groceries.aliases.create(word="veg")

    assert [h.name for h in groceries.history.order_by("history_date")] == [
        "Groceries",
        "Kirana",
    ]
    assert groceries.aliases.get().history.count() == 1
