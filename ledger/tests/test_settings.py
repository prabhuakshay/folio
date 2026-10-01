import pytest
from django.urls import reverse
from django.utils.html import escape

from ledger import chart
from ledger.chart import SEP
from ledger.models import Account
from signin.tests import add_authenticator, verify

Role = Account.Role


@pytest.fixture
def signed_in(client, django_user_model):
    owner = django_user_model.objects.create_user("akshay")
    client.force_login(owner)
    verify(client, add_authenticator(owner))
    return client


def named(name):
    return Account.objects.get(name=name)


def edit(client, account, **data):
    fields = {
        "name": account.name,
        "parent": account.parent_id,
        "aliases": ", ".join(a.word for a in account.aliases.all()),
        **({"is_group": "on"} if account.is_group else {}),
        **data,
    }
    fields = {k: v for k, v in fields.items() if v is not None}
    return client.post(reverse("chart_account", args=[account.pk]), fields)


@pytest.mark.django_db
def test_settings_shows_the_chart_row(signed_in):
    text = signed_in.get(reverse("settings")).text

    assert f'href="{reverse("chart")}"' in text
    assert "Your books" in text


@pytest.mark.django_db
def tab(client, name=None):
    return client.get(reverse("chart"), {"tab": name} if name else {}).text


@pytest.mark.django_db
def test_the_chart_opens_on_the_expense_tree(signed_in):
    text = tab(signed_in)

    assert reverse("chart_account", args=[named("Groceries").pk]) in text
    assert reverse("chart_account", args=[named("Food").pk]) in text
    assert "Gross salary" not in text
    assert 'aria-current="page">Expenses<' in text


@pytest.mark.django_db
def test_the_income_tab_shows_the_income_tree(signed_in):
    text = tab(signed_in, "income")

    assert reverse("chart_account", args=[named("Gross salary").pk]) in text
    assert "Groceries" not in text


@pytest.mark.django_db
@pytest.mark.parametrize("name", [None, "income", "roles", "nonsense"])
def test_no_tab_offers_asset_liability_or_equity_accounts(signed_in, name):
    text = tab(signed_in, name)

    for hidden in ["Bank & Cash", "Credit Cards", "Opening Balances", "Expenses"]:
        assert reverse("chart_account", args=[named(hidden).pk]) not in text
    assert "Bank &amp; Cash" not in text


@pytest.mark.django_db
def test_the_roles_tab_lists_every_role_with_its_account(signed_in):
    text = tab(signed_in, "roles")

    for role in Role:
        assert reverse("chart_role", args=[role]) in text
    assert f"Finance costs{SEP}Interest paid" in text


@pytest.mark.django_db
def test_the_roles_tab_explains_every_role(signed_in):
    text = tab(signed_in, "roles")

    for role in Role:
        assert text.count(escape(chart.ROLE_ABOUT[role])) == 2  # row and sheet


@pytest.mark.django_db
def test_the_chart_says_where_what_you_own_and_owe_lives(signed_in):
    assert "from the Accounts tab" in tab(signed_in)


@pytest.mark.django_db
def test_an_accounts_screen_explains_its_role(signed_in):
    account = named("Uncategorised")

    text = signed_in.get(reverse("chart_account", args=[account.pk])).text

    assert (
        "Uncategorised</span>: " + escape(chart.ROLE_ABOUT[Role.UNCATEGORISED]) in text
    )


@pytest.mark.django_db
def test_a_refused_role_reopens_its_sheet_on_the_roles_tab(signed_in):
    response = signed_in.post(
        reverse("chart_role", args=[Role.TAXES]), {"account": named("Groceries").pk}
    )

    assert 'aria-current="page">Roles<' in response.text


@pytest.mark.django_db
def test_repointing_returns_to_the_roles_tab(signed_in):
    response = signed_in.post(
        reverse("chart_role", args=[Role.UNCATEGORISED]),
        {"account": named("Rent").pk},
    )

    assert response.url == reverse("chart") + "?tab=roles"


@pytest.mark.django_db
def test_the_chart_unfolds_the_group_it_is_asked_to(signed_in):
    food = named("Food")

    folded = " ".join(tab(signed_in).split())
    unfolded = " ".join(signed_in.get(reverse("chart"), {"open": food.pk}).text.split())

    assert '<details class="group/g" open>' not in folded
    assert unfolded.count('<details class="group/g" open>') == 1


@pytest.mark.django_db
def test_adding_returns_to_the_new_accounts_group(signed_in):
    response = add(signed_in, name="Bonus 2", parent=named("Salary").pk)

    assert response.headers["HX-Location"] == (
        f"{reverse('chart')}?tab=income&open={named('Salary').pk}"
    )


@pytest.mark.django_db
def test_rename(signed_in):
    groceries = named("Groceries")

    response = edit(signed_in, groceries, name="Kirana")

    assert response.status_code == 204
    food = named("Food")
    assert response.headers["HX-Location"] == (
        f"{reverse('chart')}?tab=expense&open={food.pk}"
    )
    groceries.refresh_from_db()
    assert groceries.name == "Kirana"


@pytest.mark.django_db
def test_a_name_taken_in_the_same_group_is_refused(signed_in):
    response = edit(signed_in, named("Groceries"), name="dining out")

    assert response.status_code == 200
    assert "Another Account in this group has this name." in response.text
    assert ">Groceries</h2>" in response.text
    assert Account.objects.filter(name="Groceries").exists()


@pytest.mark.django_db
def test_move_under_another_group(signed_in):
    gifts = named("Gifts given")

    edit(signed_in, gifts, parent=named("Shopping").pk)

    gifts.refresh_from_db()
    assert gifts.parent == named("Shopping")


@pytest.mark.django_db
def test_move_a_group_to_the_top_of_its_tree_and_another_under_it(signed_in):
    travel = named("Travel")

    edit(signed_in, travel, parent=named("Expenses").pk)
    edit(signed_in, named("Food"), parent=travel.pk)

    assert named("Food").parent == travel


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("account", "parent"),
    [
        ("Groceries", "Salary"),  # another type
        ("Groceries", "Rent"),  # a leaf
        ("Food", "Food"),  # itself
    ],
)
def test_a_move_that_doesnt_fit_is_refused(signed_in, account, parent):
    moving = named(account)
    before = moving.parent

    response = edit(signed_in, moving, parent=named(parent).pk)

    assert response.status_code == 200
    moving.refresh_from_db()
    assert moving.parent == before


@pytest.mark.django_db
def test_a_group_cant_move_under_an_account_below_it(signed_in):
    finance = named("Finance costs")
    loans = finance.add_child("Loans interest", is_group=True)

    response = edit(signed_in, finance, parent=loans.pk)

    assert response.status_code == 200
    finance.refresh_from_db()
    assert finance.parent == named("Expenses")


@pytest.mark.django_db
def test_aliases_are_set_from_a_list_of_words(signed_in):
    dining = named("Dining out")

    edit(signed_in, dining, aliases="eating out,  restaurant , Eating Out,eatingout")

    assert [a.word for a in dining.aliases.all()] == ["eating out", "restaurant"]
    assert list(Account.objects.answering("restaurant")) == [dining]

    edit(signed_in, dining, aliases="restaurant")

    assert [a.word for a in dining.aliases.all()] == ["restaurant"]
    assert dining.aliases.get().history.count() == 1


@pytest.mark.django_db
def test_the_edit_screen_shows_the_account(signed_in):
    dining = named("Dining out")
    dining.aliases.create(word="eating out")

    text = signed_in.get(reverse("chart_account", args=[dining.pk])).text

    assert 'value="Dining out"' in text
    assert 'value="eating out"' in text


@pytest.mark.django_db
@pytest.mark.parametrize("name", ["Expenses", "Bank & Cash", "Opening Balances"])
def test_only_the_income_and_expense_tree_is_edited_here(signed_in, name):
    account = named(name)

    assert signed_in.get(reverse("chart_account", args=[account.pk])).status_code == 404


@pytest.mark.django_db
def test_repoint_a_role(signed_in):
    home_loan = named("Finance costs").add_child("Home loan interest")

    response = signed_in.post(
        reverse("chart_role", args=[Role.INTEREST_PAID]), {"account": home_loan.pk}
    )

    assert response.status_code == 302
    assert chart.account_for(Role.INTEREST_PAID) == home_loan


@pytest.mark.django_db
def test_a_role_cant_be_pointed_where_it_doesnt_fit(signed_in):
    response = signed_in.post(
        reverse("chart_role", args=[Role.TAXES]), {"account": named("Groceries").pk}
    )

    assert response.status_code == 200
    assert "data-open" in response.text
    assert chart.account_for(Role.TAXES) == named("Taxes")


@pytest.mark.django_db
def test_a_deleted_roles_account_shows_until_it_is_needed(signed_in):
    named("Uncategorised").delete()

    text = tab(signed_in, "roles")

    assert "Folio makes a new one when next needed" in text
    assert not Account.objects.filter(role=Role.UNCATEGORISED).exists()


@pytest.mark.django_db
def test_edits_are_audited_with_who_made_them(signed_in):
    groceries = named("Groceries")

    edit(signed_in, groceries, name="Kirana")

    assert groceries.history.latest().history_user.username == "akshay"


def add(client, **data):
    return client.post(reverse("chart_new"), {"aliases": "", **data})


@pytest.mark.django_db
def test_add_an_account_under_a_group(signed_in):
    response = add(
        signed_in,
        name="Home loan interest",
        parent=named("Finance costs").pk,
        aliases="hl interest",
    )

    assert response.status_code == 204
    account = named("Home loan interest")
    assert account.parent == named("Finance costs")
    assert account.account_type == Account.Type.EXPENSE
    assert not account.is_group
    assert [a.word for a in account.aliases.all()] == ["hl interest"]


@pytest.mark.django_db
def test_add_a_group_at_the_top_of_income(signed_in):
    add(signed_in, name="Side projects", parent=named("Income").pk, is_group="on")

    account = named("Side projects")
    assert account.is_group
    assert account.account_type == Account.Type.INCOME
    assert account.parent == named("Income")


@pytest.mark.django_db
@pytest.mark.parametrize("parent", ["Groceries", "Bank & Cash", "Liabilities"])
def test_an_account_goes_only_under_an_income_or_expense_group(signed_in, parent):
    response = add(signed_in, name="Something", parent=named(parent).pk)

    assert response.status_code == 200
    assert not Account.objects.filter(name="Something").exists()


@pytest.mark.django_db
def test_a_new_account_needs_a_name_free_in_its_group(signed_in):
    response = add(signed_in, name="groceries", parent=named("Food").pk)

    assert "Another Account in this group has this name." in response.text
    assert Account.objects.filter(name__iexact="groceries").count() == 1


@pytest.mark.django_db
def test_add_starts_in_the_group_it_was_opened_from(signed_in):
    food = named("Food")

    text = signed_in.get(reverse("chart_new") + f"?under={food.pk}").text

    assert f'value="{food.pk}" selected' in " ".join(text.split())


@pytest.mark.django_db
def test_the_chart_and_a_groups_screen_offer_add(signed_in):
    food = named("Food")
    chart_text = tab(signed_in)
    group_text = signed_in.get(reverse("chart_account", args=[food.pk])).text
    leaf_text = signed_in.get(reverse("chart_account", args=[named("Rent").pk])).text

    new = reverse("chart_new")
    assert f"{new}?under={named('Expenses').pk}" in chart_text
    assert f"{new}?under={food.pk}" in chart_text
    assert f'hx-get="{reverse("chart_account", args=[food.pk])}"' in chart_text
    assert f"{new}?under={food.pk}" in group_text
    assert new not in leaf_text


@pytest.mark.django_db
def test_an_account_with_nothing_under_it_can_become_a_group(signed_in):
    pets = named("Expenses").add_child("Pets")

    edit(signed_in, pets, is_group="on")
    pets.refresh_from_db()
    assert pets.is_group

    edit(signed_in, pets, is_group=None)
    pets.refresh_from_db()
    assert not pets.is_group


@pytest.mark.django_db
def test_a_group_with_accounts_under_it_stays_a_group(signed_in):
    response = edit(signed_in, named("Food"), is_group=None)

    assert "Move the Accounts under it elsewhere first." in response.text
    assert named("Food").is_group


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("name", "is_group", "needs"),
    [("Uncategorised", "on", "an Account, not a group"), ("Taxes", None, "a group")],
)
def test_a_role_keeps_its_accounts_shape(signed_in, name, is_group, needs):
    account = named(name)
    if name == "Taxes":
        account.children.all().delete()

    response = edit(signed_in, account, is_group=is_group)

    assert f"role needs {needs}." in response.text
    assert named(name).is_group is (name == "Taxes")
