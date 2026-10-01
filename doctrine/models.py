"""Doctrine thresholds you've changed from their defaults."""

from django.db import models
from simple_history.models import HistoricalRecords


class Threshold(models.Model):
    """A threshold's value, kept only once you change it from its default."""

    class Key(models.TextChoices):
        EMI_GRACE_PERIOD = "emi_grace_period", "EMI grace period"
        STARTER_FUND = "starter_fund", "Starter fund"
        LIFE_COVER_MULTIPLE = "life_cover_multiple", "Life cover multiple"
        HEALTH_COVER_FLOOR = "health_cover_floor", "Health cover floor"
        HIGH_INTEREST_RATE = "high_interest_rate", "High-interest rate"
        EMERGENCY_FUND = "emergency_fund", "Emergency Fund"
        EMI_CAP = "emi_cap", "EMI cap"
        SAVINGS_RATE_TARGET = "savings_rate_target", "Savings-rate target"
        GENERAL_INFLATION = "general_inflation", "General inflation"
        MEDICAL_INFLATION = "medical_inflation", "Medical inflation"
        SAFE_WITHDRAWAL_RATE = "safe_withdrawal_rate", "Safe Withdrawal Rate"
        DECUMULATION_EQUITY = "decumulation_equity", "Decumulation equity"

    key = models.CharField(max_length=32, choices=Key, unique=True)
    value = models.DecimalField(max_digits=16, decimal_places=4)

    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"{self.get_key_display()}: {self.value}"
