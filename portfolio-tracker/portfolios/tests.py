import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from .models import Holding, Portfolio, Transaction

# The exact documents the React app sends, so these tests break if the UI's
# query and the schema drift apart.
PORTFOLIOS_QUERY = """
  query Portfolios {
    portfolios {
      id
      name
      totalValue
      holdings {
        id
        ticker
        currentPrice
        shares
        value
        transactions { id type shares price date }
      }
    }
  }
"""

ADD_TRANSACTION = """
  mutation AddTransaction($holdingId: Int!, $type: String!, $shares: Float!, $price: Float!) {
    addTransaction(holdingId: $holdingId, type: $type, shares: $shares, price: $price) { id }
  }
"""

UPDATE_TRANSACTION = """
  mutation UpdateTransaction($id: Int!, $type: String!, $shares: Float!, $price: Float!) {
    updateTransaction(id: $id, type: $type, shares: $shares, price: $price) { id shares }
  }
"""

DELETE_TRANSACTION = """
  mutation DeleteTransaction($id: Int!) { deleteTransaction(id: $id) }
"""


class GraphQLTestCase(TestCase):
    def graphql(self, query, **variables):
        response = self.client.post(
            "/graphql/",
            data=json.dumps({"query": query, "variables": variables}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        return json.loads(response.content)

    def first_holding(self):
        """Read the holding back through the API the way the UI sees it."""
        body = self.graphql(PORTFOLIOS_QUERY)
        self.assertIsNone(body.get("errors"))
        return body["data"]["portfolios"][0], body["data"]["portfolios"][0]["holdings"][0]


class DerivedTotalsTests(GraphQLTestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="kavya", password="pw")
        self.portfolio = Portfolio.objects.create(name="Retirement", owner=self.user)
        self.holding = Holding.objects.create(
            ticker="AAPL", current_price=Decimal("180.00"), portfolio=self.portfolio
        )
        self.client.force_login(self.user)

    def test_shares_sum_buys_and_subtract_sells(self):
        Transaction.objects.create(
            holding=self.holding, type="BUY", shares=10, price=150
        )
        Transaction.objects.create(holding=self.holding, type="BUY", shares=5, price=170)
        Transaction.objects.create(
            holding=self.holding, type="SELL", shares=3, price=190
        )

        self.assertEqual(self.holding.total_shares, Decimal("12"))
        # 12 shares x $180 current price
        self.assertEqual(self.holding.market_value, Decimal("2160.00"))
        self.assertEqual(self.portfolio.total_value, Decimal("2160.00"))

    def test_holding_with_no_transactions_is_zero_not_an_error(self):
        self.assertEqual(self.holding.total_shares, Decimal("0"))
        self.assertEqual(self.holding.market_value, Decimal("0"))
        self.assertEqual(self.portfolio.total_value, Decimal("0"))

    def test_api_exposes_derived_shares_value_and_total(self):
        Transaction.objects.create(
            holding=self.holding, type="BUY", shares=10, price=150
        )

        portfolio, holding = self.first_holding()
        self.assertEqual(Decimal(holding["shares"]), Decimal("10"))
        self.assertEqual(Decimal(holding["value"]), Decimal("1800.00"))
        self.assertEqual(Decimal(portfolio["totalValue"]), Decimal("1800.00"))

    def test_totals_sum_across_multiple_holdings(self):
        Transaction.objects.create(
            holding=self.holding, type="BUY", shares=10, price=150
        )
        other = Holding.objects.create(
            ticker="MSFT", current_price=Decimal("400.00"), portfolio=self.portfolio
        )
        Transaction.objects.create(holding=other, type="BUY", shares=2, price=380)

        # 10 x 180 + 2 x 400
        self.assertEqual(self.portfolio.total_value, Decimal("2600.00"))


class AddTransactionLoopTests(GraphQLTestCase):
    """The read/write loop the form drives: add, then re-read the numbers."""

    def setUp(self):
        self.user = User.objects.create_user(username="kavya", password="pw")
        self.portfolio = Portfolio.objects.create(name="Retirement", owner=self.user)
        self.holding = Holding.objects.create(
            ticker="AAPL", current_price=Decimal("180.00"), portfolio=self.portfolio
        )
        Transaction.objects.create(
            holding=self.holding, type="BUY", shares=10, price=150
        )
        self.client.force_login(self.user)

    def test_adding_a_transaction_ticks_up_count_shares_and_value(self):
        _, before = self.first_holding()
        self.assertEqual(len(before["transactions"]), 1)
        self.assertEqual(Decimal(before["shares"]), Decimal("10"))

        body = self.graphql(
            ADD_TRANSACTION, holdingId=int(self.holding.id), type="BUY", shares=7.0, price=195.0
        )
        self.assertIsNone(body.get("errors"))

        portfolio, after = self.first_holding()
        self.assertEqual(len(after["transactions"]), 2)
        self.assertEqual(Decimal(after["shares"]), Decimal("17"))
        # 17 x 180
        self.assertEqual(Decimal(after["value"]), Decimal("3060.00"))
        self.assertEqual(Decimal(portfolio["totalValue"]), Decimal("3060.00"))

    def test_selling_reduces_the_derived_share_count(self):
        self.graphql(
            ADD_TRANSACTION, holdingId=int(self.holding.id), type="SELL", shares=4.0, price=200.0
        )

        _, after = self.first_holding()
        self.assertEqual(Decimal(after["shares"]), Decimal("6"))

    def test_history_is_newest_first(self):
        self.graphql(
            ADD_TRANSACTION, holdingId=int(self.holding.id), type="SELL", shares=1.0, price=200.0
        )

        _, holding = self.first_holding()
        self.assertEqual(holding["transactions"][0]["type"], "SELL")

    def test_rejects_zero_or_negative_shares(self):
        body = self.graphql(
            ADD_TRANSACTION, holdingId=int(self.holding.id), type="BUY", shares=0.0, price=195.0
        )
        self.assertIsNotNone(body.get("errors"))
        self.assertEqual(Transaction.objects.count(), 1)

    def test_rejects_an_unknown_transaction_type(self):
        body = self.graphql(
            ADD_TRANSACTION, holdingId=int(self.holding.id), type="GIFT", shares=1.0, price=1.0
        )
        self.assertIsNotNone(body.get("errors"))
        self.assertEqual(Transaction.objects.count(), 1)


class EditAndDeleteTests(GraphQLTestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="kavya", password="pw")
        self.portfolio = Portfolio.objects.create(name="Retirement", owner=self.user)
        self.holding = Holding.objects.create(
            ticker="AAPL", current_price=Decimal("180.00"), portfolio=self.portfolio
        )
        self.transaction = Transaction.objects.create(
            holding=self.holding, type="BUY", shares=10, price=150
        )
        self.client.force_login(self.user)

    def test_editing_shares_updates_the_derived_total(self):
        body = self.graphql(
            UPDATE_TRANSACTION,
            id=int(self.transaction.id),
            type="BUY",
            shares=25.0,
            price=150.0,
        )
        self.assertIsNone(body.get("errors"))

        _, holding = self.first_holding()
        self.assertEqual(Decimal(holding["shares"]), Decimal("25"))
        self.assertEqual(Decimal(holding["value"]), Decimal("4500.00"))

    def test_flipping_the_only_buy_to_a_sell_is_rejected(self):
        """Would leave -10 shares, so the edit must not land."""
        body = self.graphql(
            UPDATE_TRANSACTION,
            id=int(self.transaction.id),
            type="SELL",
            shares=10.0,
            price=150.0,
        )
        self.assertIsNotNone(body.get("errors"))

        _, holding = self.first_holding()
        self.assertEqual(Decimal(holding["shares"]), Decimal("10"))
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.type, "BUY")

    def test_deleting_removes_it_from_the_count_and_totals(self):
        body = self.graphql(DELETE_TRANSACTION, id=int(self.transaction.id))
        self.assertIsNone(body.get("errors"))
        self.assertTrue(body["data"]["deleteTransaction"])

        _, holding = self.first_holding()
        self.assertEqual(len(holding["transactions"]), 0)
        self.assertEqual(Decimal(holding["shares"]), Decimal("0"))
        self.assertEqual(Decimal(holding["value"]), Decimal("0"))


class OversellGuardTests(GraphQLTestCase):
    """A holding's derived share count must never go negative, by any route."""

    def setUp(self):
        self.user = User.objects.create_user(username="kavya", password="pw")
        self.portfolio = Portfolio.objects.create(name="Retirement", owner=self.user)
        self.holding = Holding.objects.create(
            ticker="AAPL", current_price=Decimal("180.00"), portfolio=self.portfolio
        )
        self.buy = Transaction.objects.create(
            holding=self.holding, type="BUY", shares=10, price=150
        )
        self.client.force_login(self.user)

    def assert_still_ten_shares(self):
        _, holding = self.first_holding()
        self.assertEqual(Decimal(holding["shares"]), Decimal("10"))

    def test_selling_more_than_held_is_rejected_and_rolled_back(self):
        body = self.graphql(
            ADD_TRANSACTION,
            holdingId=int(self.holding.id),
            type="SELL",
            shares=50.0,
            price=200.0,
        )
        self.assertIsNotNone(body.get("errors"))
        self.assertIn("cannot sell more shares", body["errors"][0]["message"])

        # The rejected SELL must not have been written.
        self.assertEqual(Transaction.objects.count(), 1)
        self.assert_still_ten_shares()

    def test_selling_exactly_what_is_held_is_allowed(self):
        body = self.graphql(
            ADD_TRANSACTION,
            holdingId=int(self.holding.id),
            type="SELL",
            shares=10.0,
            price=200.0,
        )
        self.assertIsNone(body.get("errors"))

        _, holding = self.first_holding()
        self.assertEqual(Decimal(holding["shares"]), Decimal("0"))

    def test_partial_sell_still_works(self):
        body = self.graphql(
            ADD_TRANSACTION,
            holdingId=int(self.holding.id),
            type="SELL",
            shares=4.0,
            price=200.0,
        )
        self.assertIsNone(body.get("errors"))

        _, holding = self.first_holding()
        self.assertEqual(Decimal(holding["shares"]), Decimal("6"))

    def test_editing_a_sell_beyond_the_holding_is_rejected(self):
        sell = Transaction.objects.create(
            holding=self.holding, type="SELL", shares=4, price=200
        )

        body = self.graphql(
            UPDATE_TRANSACTION,
            id=int(sell.id),
            type="SELL",
            shares=99.0,
            price=200.0,
        )
        self.assertIsNotNone(body.get("errors"))

        sell.refresh_from_db()
        self.assertEqual(sell.shares, Decimal("4.0000"))
        _, holding = self.first_holding()
        self.assertEqual(Decimal(holding["shares"]), Decimal("6"))

    def test_editing_a_buy_below_what_later_sells_consumed_is_rejected(self):
        Transaction.objects.create(
            holding=self.holding, type="SELL", shares=8, price=200
        )

        # Dropping the buy from 10 to 2 would leave -6.
        body = self.graphql(
            UPDATE_TRANSACTION,
            id=int(self.buy.id),
            type="BUY",
            shares=2.0,
            price=150.0,
        )
        self.assertIsNotNone(body.get("errors"))

        self.buy.refresh_from_db()
        self.assertEqual(self.buy.shares, Decimal("10.0000"))

    def test_deleting_a_buy_a_sell_relies_on_is_rejected(self):
        Transaction.objects.create(
            holding=self.holding, type="SELL", shares=8, price=200
        )

        body = self.graphql(DELETE_TRANSACTION, id=int(self.buy.id))
        self.assertIsNotNone(body.get("errors"))
        self.assertEqual(Transaction.objects.count(), 2)

    def test_deleting_a_buy_is_fine_when_nothing_depends_on_it(self):
        body = self.graphql(DELETE_TRANSACTION, id=int(self.buy.id))
        self.assertIsNone(body.get("errors"))
        self.assertEqual(Transaction.objects.count(), 0)

    def test_deleting_the_sell_first_then_the_buy_works(self):
        sell = Transaction.objects.create(
            holding=self.holding, type="SELL", shares=8, price=200
        )

        self.assertIsNone(self.graphql(DELETE_TRANSACTION, id=int(sell.id)).get("errors"))
        self.assertIsNone(
            self.graphql(DELETE_TRANSACTION, id=int(self.buy.id)).get("errors")
        )
        self.assertEqual(Transaction.objects.count(), 0)

    def test_sells_across_two_holdings_do_not_interfere(self):
        other = Holding.objects.create(
            ticker="MSFT", current_price=Decimal("400.00"), portfolio=self.portfolio
        )

        # MSFT owns nothing, so any sell against it fails...
        body = self.graphql(
            ADD_TRANSACTION, holdingId=int(other.id), type="SELL", shares=1.0, price=400.0
        )
        self.assertIsNotNone(body.get("errors"))

        # ...while AAPL's own balance is untouched and still sellable.
        body = self.graphql(
            ADD_TRANSACTION,
            holdingId=int(self.holding.id),
            type="SELL",
            shares=3.0,
            price=200.0,
        )
        self.assertIsNone(body.get("errors"))


class AuthorizationTests(GraphQLTestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="kavya", password="pw")
        self.other = User.objects.create_user(username="someone-else", password="pw")
        self.portfolio = Portfolio.objects.create(name="Retirement", owner=self.owner)
        self.holding = Holding.objects.create(
            ticker="AAPL", current_price=Decimal("180.00"), portfolio=self.portfolio
        )
        self.transaction = Transaction.objects.create(
            holding=self.holding, type="BUY", shares=10, price=150
        )

    def test_anonymous_sees_no_portfolios_and_no_user(self):
        body = self.graphql("{ me { username } portfolios { id } }")
        self.assertIsNone(body["data"]["me"])
        self.assertEqual(body["data"]["portfolios"], [])

    def test_anonymous_cannot_add_a_transaction(self):
        body = self.graphql(
            ADD_TRANSACTION, holdingId=int(self.holding.id), type="BUY", shares=1.0, price=1.0
        )
        self.assertIsNotNone(body.get("errors"))
        self.assertEqual(Transaction.objects.count(), 1)

    def test_login_and_logout_flip_the_gate(self):
        body = self.graphql(
            """
            mutation Login($username: String!, $password: String!) {
              login(username: $username, password: $password) { username }
            }
            """,
            username="kavya",
            password="pw",
        )
        self.assertEqual(body["data"]["login"]["username"], "kavya")

        body = self.graphql("{ me { username } portfolios { name } }")
        self.assertEqual(body["data"]["me"]["username"], "kavya")
        self.assertEqual(len(body["data"]["portfolios"]), 1)

        self.graphql("mutation { logout }")
        body = self.graphql("{ me { username } portfolios { name } }")
        self.assertIsNone(body["data"]["me"])
        self.assertEqual(body["data"]["portfolios"], [])

    def test_bad_password_does_not_log_you_in(self):
        body = self.graphql(
            """
            mutation Login($username: String!, $password: String!) {
              login(username: $username, password: $password) { username }
            }
            """,
            username="kavya",
            password="nope",
        )
        self.assertIsNone(body["data"]["login"])

    def test_another_user_cannot_see_or_touch_your_holdings(self):
        self.client.force_login(self.other)

        body = self.graphql(PORTFOLIOS_QUERY)
        self.assertEqual(body["data"]["portfolios"], [])

        body = self.graphql(
            ADD_TRANSACTION, holdingId=int(self.holding.id), type="BUY", shares=1.0, price=1.0
        )
        self.assertIsNotNone(body.get("errors"))

        body = self.graphql(DELETE_TRANSACTION, id=int(self.transaction.id))
        self.assertIsNotNone(body.get("errors"))
        self.assertEqual(Transaction.objects.count(), 1)
