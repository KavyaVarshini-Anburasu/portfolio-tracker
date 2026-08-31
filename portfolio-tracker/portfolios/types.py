from decimal import Decimal

import strawberry
import strawberry_django
from strawberry import auto
from django.contrib.auth.models import User as DjangoUser
from . import models


@strawberry_django.type(DjangoUser)
class User:
    id: auto
    username: auto


@strawberry_django.type(models.Transaction)
class Transaction:
    id: auto
    type: auto
    shares: auto
    price: auto
    date: auto


@strawberry_django.type(models.Holding)
class Holding:
    id: auto
    ticker: auto
    current_price: auto

    @strawberry.field
    def transactions(root: models.Holding) -> list[Transaction]:
        """Newest first, so the history table reads top-down.

        Sorted in Python rather than with order_by: .all() may be served from
        the query's prefetch cache, and tacking order_by onto a cached related
        manager silently re-queries (or ignores the ordering entirely).
        """
        return sorted(
            root.transactions.all(),
            key=lambda transaction: (transaction.date, transaction.id),
            reverse=True,
        )

    @strawberry.field
    def shares(root: models.Holding) -> Decimal:
        """Derived from transactions, not stored on the holding."""
        return root.total_shares

    @strawberry.field
    def value(root: models.Holding) -> Decimal:
        return root.market_value


@strawberry_django.type(models.Portfolio)
class Portfolio:
    id: auto
    name: auto
    holdings: list[Holding]

    @strawberry.field
    def total_value(root: models.Portfolio) -> Decimal:
        return root.total_value
