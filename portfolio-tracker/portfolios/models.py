from decimal import Decimal

from django.db import models

class Portfolio(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="portfolios",
    )

    def __str__(self):
        return self.name

    @property
    def total_value(self):
        """Sum of every holding's market value. Derived, never stored."""
        return sum(
            (holding.market_value for holding in self.holdings.all()),
            Decimal("0"),
        )

class Holding(models.Model):
    ticker = models.CharField(max_length=10)
    current_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    portfolio = models.ForeignKey(
        "Portfolio",
        on_delete=models.CASCADE,
        related_name="holdings",
    )

    def __str__(self):
        return f"{self.ticker} ({self.portfolio.name})"

    @property
    def total_shares(self):
        """Shares owned, summed from transactions: buys add, sells subtract."""
        total = Decimal("0")
        for transaction in self.transactions.all():
            if transaction.type == Transaction.SELL:
                total -= transaction.shares
            else:
                total += transaction.shares
        return total

    @property
    def market_value(self):
        """Shares owned x the current price."""
        return self.total_shares * self.current_price

class Transaction(models.Model):
    BUY = "BUY"
    SELL = "SELL"
    TYPE_CHOICES = [(BUY, "Buy"), (SELL, "Sell")]

    type = models.CharField(max_length=4, choices=TYPE_CHOICES)
    shares = models.DecimalField(max_digits=12, decimal_places=4)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    holding = models.ForeignKey(
        "Holding",
        on_delete=models.CASCADE,
        related_name="transactions",
    )

    def __str__(self):
        return f"{self.type} {self.shares} {self.holding.ticker}"
