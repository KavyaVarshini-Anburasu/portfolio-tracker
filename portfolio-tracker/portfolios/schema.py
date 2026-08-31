import strawberry
from typing import List, Optional
from strawberry.types import Info
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.db import transaction as db_transaction
from . import types
from . import models


def _require_user(info: Info):
    """Every portfolio read and write is scoped to the logged-in user."""
    user = info.context.request.user
    if not user.is_authenticated:
        raise Exception("Not authenticated")
    return user


def _holding_for_user(user, holding_id: int) -> models.Holding:
    try:
        return models.Holding.objects.get(id=holding_id, portfolio__owner=user)
    except models.Holding.DoesNotExist:
        raise Exception(f"No holding with id {holding_id}")


def _transaction_for_user(user, transaction_id: int) -> models.Transaction:
    try:
        return models.Transaction.objects.select_related("holding").get(
            id=transaction_id, holding__portfolio__owner=user
        )
    except models.Transaction.DoesNotExist:
        raise Exception(f"No transaction with id {transaction_id}")


def _guard_no_oversell(holding: models.Holding) -> None:
    """Reject any write that leaves a holding owing shares it never owned.

    Checked *after* the write inside an atomic block rather than predicting the
    result up front: the transaction list is the source of truth, so re-deriving
    the total is the only check that cannot drift from the derivation itself. It
    also covers every route to a negative balance at once - overselling, editing
    a buy down, flipping a buy to a sell, or deleting a buy a later sell relied
    on - instead of special-casing each one.
    """
    total = holding.total_shares
    if total < 0:
        raise Exception(
            f"That would leave {holding.ticker} at {total.normalize():f} shares. "
            "You cannot sell more shares than the holding owns."
        )


def _clean_type(value: str) -> str:
    cleaned = value.upper()
    if cleaned not in (models.Transaction.BUY, models.Transaction.SELL):
        raise Exception("Type must be BUY or SELL")
    return cleaned


def _clean_shares(value: float) -> float:
    if value <= 0:
        raise Exception("Shares must be greater than zero")
    return value


def _clean_price(value: float) -> float:
    if value < 0:
        raise Exception("Price cannot be negative")
    return value


@strawberry.type
class Query:
    @strawberry.field
    def portfolios(self, info: Info) -> List[types.Portfolio]:
        user = info.context.request.user
        if not user.is_authenticated:
            return []
        # Every derived total walks a holding's transactions, so pull them all in
        # one query instead of one per holding. Ordering is the Holding type's
        # job, not this query's.
        return models.Portfolio.objects.filter(owner=user).prefetch_related(
            "holdings__transactions"
        )

    @strawberry.field
    def me(self, info: Info) -> Optional[types.User]:
        user = info.context.request.user
        if user.is_authenticated:
            return user
        return None


@strawberry.type
class Mutation:
    @strawberry.mutation
    def add_transaction(
        self,
        info: Info,
        holding_id: int,
        type: str,
        shares: float,
        price: float,
    ) -> types.Transaction:
        user = _require_user(info)
        holding = _holding_for_user(user, holding_id)
        with db_transaction.atomic():
            transaction = models.Transaction.objects.create(
                holding=holding,
                type=_clean_type(type),
                shares=_clean_shares(shares),
                price=_clean_price(price),
            )
            _guard_no_oversell(holding)
            # The floats we just assigned are still floats in memory; re-read so
            # the response carries real Decimals.
            transaction.refresh_from_db()
        return transaction

    @strawberry.mutation
    def update_transaction(
        self,
        info: Info,
        id: int,
        type: Optional[str] = None,
        shares: Optional[float] = None,
        price: Optional[float] = None,
    ) -> types.Transaction:
        user = _require_user(info)
        transaction = _transaction_for_user(user, id)
        if type is not None:
            transaction.type = _clean_type(type)
        if shares is not None:
            transaction.shares = _clean_shares(shares)
        if price is not None:
            transaction.price = _clean_price(price)
        with db_transaction.atomic():
            transaction.save()
            _guard_no_oversell(transaction.holding)
            transaction.refresh_from_db()
        return transaction

    @strawberry.mutation
    def delete_transaction(self, info: Info, id: int) -> bool:
        user = _require_user(info)
        transaction = _transaction_for_user(user, id)
        with db_transaction.atomic():
            holding = transaction.holding
            transaction.delete()
            # Removing a buy can strand a later sell, so the same rule applies.
            _guard_no_oversell(holding)
        return True

    @strawberry.mutation
    def login(self, info: Info, username: str, password: str) -> Optional[types.User]:
        user = authenticate(info.context.request, username=username, password=password)
        if user is not None:
            django_login(info.context.request, user)
            return user
        return None

    @strawberry.mutation
    def logout(self, info: Info) -> bool:
        django_logout(info.context.request)
        return True


schema = strawberry.Schema(query=Query, mutation=Mutation)
