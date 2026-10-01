"""Settings > Chart of Accounts: the Income and Expense tree, and the Roles."""

from typing import TYPE_CHECKING

from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from ledger import chart
from ledger.forms import AccountForm, NewAccountForm, RoleForm
from ledger.models import Account

if TYPE_CHECKING:
    from django.http import HttpRequest

Role = Account.Role
Type = Account.Type

EDITED_HERE = (Type.INCOME, Type.EXPENSE)
TABS = {Type.INCOME: "Income", Type.EXPENSE: "Expenses", "roles": "Roles"}


def _role_row(
    role: Role,
    account: Account | None,
    paths: dict[int, str],
    refused: RoleForm | None,
) -> dict:
    candidates = [(a.pk, paths[a.pk]) for a in chart.candidates(role)]
    return {
        "role": role,
        "about": chart.ROLE_ABOUT[role],
        "account": account,
        "path": paths[account.pk] if account else "",
        "candidates": sorted(candidates, key=lambda c: c[1].lower()),
        "errors": refused.errors["account"] if refused else [],
    }


def _folded(rows: list[chart.Row]) -> list[dict]:
    # Each top-level row with everything below it, so a group folds as one.
    items = []
    for row in rows:
        if row.depth == 0:
            items.append({"row": row, "under": []})
        else:
            items[-1]["under"].append(row)
    return items


def chart_screen(
    request: HttpRequest, refused: RoleForm | None = None, role: str = ""
) -> HttpResponse:
    """One tab of the chart: the Income tree, the Expense tree or the Roles.

    Args:
        request: The incoming request; `tab` picks `income`, `expense` (the
            default) or `roles`.
        refused: A role's form that was refused, to show again.
        role: The role `refused` was for, whose sheet opens on load.

    Returns:
        The screen.
    """
    tab = "roles" if refused else request.GET.get("tab", Type.EXPENSE)
    if tab not in TABS:
        tab = Type.EXPENSE
    context = {
        "tab": "home",
        "back": "settings",
        "title": "Chart of Accounts",
        "tabs": TABS,
        "current": tab,
    }
    if tab == "roles":
        paths = {row.account.pk: row.path for t in Type for row in chart.tree(Type(t))}
        holders = {a.role: a for a in Account.objects.exclude(role="")}
        context["roles"] = [
            _role_row(r, holders.get(r), paths, refused if r == role else None)
            for r in Role
        ]
        context["open"] = role
    else:
        context["top"] = chart.root(Type(tab))
        context["unfolded"] = request.GET.get("open", "")
        context["items"] = _folded(chart.tree(Type(tab)))
    return render(request, "ledger/chart.html", context)


def _saved(account: Account) -> HttpResponse:
    # The sheet's form was posted by htmx, which follows this to the chart,
    # back on the Account's tab with its group unfolded.
    top = account
    while top.parent.parent_id:
        top = top.parent
    url = f"{reverse('chart')}?tab={account.account_type}&open={top.pk}"
    return HttpResponse(status=204, headers={"HX-Location": url})


def account_sheet(request: HttpRequest, pk: int) -> HttpResponse:
    """Rename an Income or Expense Account, move it, and set its aliases.

    Args:
        request: The incoming request.
        pk: The Account.

    Returns:
        The sheet's form, or an empty response that reloads the chart once
        saved.
    """
    account = get_object_or_404(
        Account, pk=pk, account_type__in=EDITED_HERE, parent__isnull=False
    )
    # Read before the form, which puts a refused name on the Account.
    title = account.name
    form = AccountForm(request.POST or None, instance=account)
    if request.method == "POST" and form.is_valid():
        return _saved(form.save())
    return render(
        request,
        "ledger/account_sheet.html",
        {
            "title": title,
            "account": account,
            "role_about": chart.ROLE_ABOUT.get(account.role, ""),
            "form": form,
        },
    )


def new_account_sheet(request: HttpRequest) -> HttpResponse:
    """Add an Income or Expense Account or group.

    Args:
        request: The incoming request; `under` names the group to start in.

    Returns:
        The sheet's form, or an empty response that reloads the chart once
        saved.
    """
    form = NewAccountForm(
        request.POST or None, initial={"parent": request.GET.get("under")}
    )
    if request.method == "POST" and form.is_valid():
        return _saved(form.save())
    return render(
        request, "ledger/account_sheet.html", {"form": form, "title": "New Account"}
    )


@require_POST
def repoint_role(request: HttpRequest, role: str) -> HttpResponse:
    """Point a role at another Account.

    Args:
        request: The incoming request.
        role: Which role.

    Returns:
        A redirect to the chart, or the chart with the role's sheet reopened.

    Raises:
        Http404: There is no such role.
    """
    try:
        role = Role(role)
    except ValueError:
        raise Http404 from None
    form = RoleForm(role, request.POST)
    if not form.is_valid():
        return chart_screen(request, form, role)
    chart.repoint(role, form.cleaned_data["account"])
    return redirect(f"{reverse('chart')}?tab=roles")
