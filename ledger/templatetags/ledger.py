"""Template helpers for the ledger."""

from django import template

from ledger.models import Account

register = template.Library()


@register.simple_tag
def chart_summary() -> str:
    """How big the Income and Expense tree is, for Settings' row.

    Returns:
        A line such as `68 Income and Expense Accounts`.
    """
    count = Account.objects.filter(
        account_type__in=[Account.Type.INCOME, Account.Type.EXPENSE],
        parent__isnull=False,
    ).count()
    return f"{count} Income and Expense Accounts"
