"""Editing the Chart of Accounts."""

from django import forms
from django.db import transaction

from ledger import chart
from ledger.models import Account, Alias, key


class AccountForm(forms.ModelForm):
    """Rename an Account, move it, make it a group or not, and set its aliases."""

    aliases = forms.CharField(required=False, max_length=500)

    class Meta:
        model = Account
        fields = ["name", "parent", "is_group"]

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.groups = self.allowed_groups()
        parent = self.fields["parent"]
        parent.required = True
        parent.queryset = Account.objects.filter(pk__in=[g.pk for g, _ in self.groups])
        if self.instance.pk:
            self.fields["aliases"].initial = ", ".join(
                a.word for a in self.instance.aliases.all()
            )

    def allowed_groups(self) -> list[tuple[Account, str]]:
        """The groups this Account can sit under.

        Returns:
            Each group with its path.
        """
        return chart.groups_to_move_to(self.instance)

    def clean_is_group(self) -> bool:
        """Refuse a change of shape that a role or the Accounts under it rule out.

        Returns:
            Whether it is a group.

        Raises:
            ValidationError: The change isn't possible.
        """
        is_group = self.cleaned_data["is_group"]
        account = self.instance
        if not account.pk or is_group == account.is_group:
            return is_group
        if account.role:
            shape = "a group" if account.is_group else "an Account, not a group"
            msg = f"The {account.get_role_display()} role needs {shape}."
            raise forms.ValidationError(msg)
        if account.children.exists():
            msg = "Move the Accounts under it elsewhere first."
            raise forms.ValidationError(msg)
        return is_group

    def clean_aliases(self) -> list[str]:
        """Split the typed list into words, each once whatever its case or spacing.

        Returns:
            The words.

        Raises:
            ValidationError: A word is too long.
        """
        words = {}
        for typed in self.cleaned_data["aliases"].split(","):
            word = " ".join(typed.split())
            if len(word) > Alias._meta.get_field("word").max_length:  # noqa: SLF001
                msg = f"“{word}” is too long for an alias."
                raise forms.ValidationError(msg)
            if word:
                words.setdefault(key(word), word)
        return list(words.values())

    @transaction.atomic
    def save(self) -> Account:
        """Save the Account and make its aliases the words given.

        Returns:
            The Account.
        """
        account = super().save()
        words = {key(w): w for w in self.cleaned_data["aliases"]}
        # One at a time, so simple-history records each change.
        for alias in account.aliases.all():
            if words.pop(key(alias.word), None) is None:
                alias.delete()
        for word in words.values():
            account.aliases.create(word=word)
        return account


class NewAccountForm(AccountForm):
    """Add an Income or Expense Account, or a group, under a group."""

    def allowed_groups(self) -> list[tuple[Account, str]]:
        """Any Income or Expense group.

        Returns:
            Each group with its path.
        """
        return chart.groups(Account.Type.INCOME) + chart.groups(Account.Type.EXPENSE)

    def clean(self) -> dict:
        """Give the new Account its group's type.

        Returns:
            The cleaned data.
        """
        cleaned = super().clean()
        if parent := cleaned.get("parent"):
            self.instance.account_type = parent.account_type
        return cleaned


class RoleForm(forms.Form):
    """The Account a role moves to."""

    account = forms.ModelChoiceField(queryset=Account.objects.none())

    def __init__(self, role: Account.Role, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.fields["account"].queryset = chart.candidates(role)
        self.fields["account"].error_messages["invalid_choice"] = (
            f"That Account can't hold the {role.label} role."
        )
