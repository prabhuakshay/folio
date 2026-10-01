"""Editing a Doctrine threshold."""

from django import forms


class ThresholdForm(forms.Form):
    """A threshold's new value. Any number is allowed, in its band or not."""

    value = forms.DecimalField(max_digits=16, decimal_places=4)
