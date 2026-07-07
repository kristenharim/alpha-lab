"""Live Alpaca **paper** adapter — the one piece that touches keys + network, built last.

Behind the same `Broker` interface, so nothing upstream changes: the nightly loop cannot tell it from
`FakeBroker`. Hardcodes the paper endpoint and asserts at runtime it is not the live URL. Keys come from
the env (`ALPACA_API_KEY_ID` / `ALPACA_API_SECRET_KEY`), never committed.

The `TradingClient` is INJECTED (not built in __init__) so the adapter is unit-tested with a mock, no
network, no keys — matching the repo rule that tests never touch the network. `alpaca_paper_broker()`
is the factory that wires the real client from env for the live runner.
"""
import os

from core.broker.base import Broker

PAPER_URL = "https://paper-api.alpaca.markets"


class AlpacaBroker(Broker):
    def __init__(self, trading_client, price_fn):
        """trading_client: an alpaca-py TradingClient (paper). price_fn: ticker -> latest price."""
        self._tc = trading_client
        self._price = price_fn
        self._seen: set = set()     # order ids already drained by fills()

    def submit_targets(self, targets: dict[str, float]) -> None:
        from alpaca.trading.enums import OrderSide, TimeInForce
        from alpaca.trading.requests import MarketOrderRequest
        held = {p.symbol: float(p.qty) for p in self._tc.get_all_positions()}
        for sym in set(held) | set(targets):
            if self.asset_status(sym) != "tradable":     # can't trade a halted/delisted name out
                continue
            price = self._price(sym)
            if not price:
                continue
            cur = held.get(sym, 0.0)
            target_qty = round(targets.get(sym, 0.0) / price)   # whole shares (shorts can't be fractional)
            delta = target_qty - cur
            if delta == 0:
                continue
            self._tc.submit_order(MarketOrderRequest(
                symbol=sym, qty=abs(delta),
                side=OrderSide.BUY if delta > 0 else OrderSide.SELL,
                time_in_force=TimeInForce.DAY))

    def positions(self) -> dict[str, dict]:
        return {p.symbol: {"qty": float(p.qty),
                           "avg_entry_price": float(p.avg_entry_price),
                           "side": str(getattr(p.side, "value", p.side))}
                for p in self._tc.get_all_positions()}

    def fills(self) -> list[dict]:
        from alpaca.trading.enums import QueryOrderStatus
        from alpaca.trading.requests import GetOrdersRequest
        orders = self._tc.get_orders(filter=GetOrdersRequest(status=QueryOrderStatus.CLOSED, limit=500))
        out = []
        for o in orders:
            if o.id in self._seen:
                continue
            self._seen.add(o.id)
            if o.filled_qty and float(o.filled_qty) > 0:
                out.append({"ticker": o.symbol,
                            "side": str(getattr(o.side, "value", o.side)),
                            "qty": float(o.filled_qty),
                            "fill_price": float(o.filled_avg_price) if o.filled_avg_price else None})
        return out

    def asset_status(self, ticker: str) -> str:
        try:
            a = self._tc.get_asset(ticker)
        except Exception:
            return "delisted"       # not found / API error -> treat as gone (reconcile still guards)
        if getattr(a, "tradable", False):
            return "tradable"
        status = str(getattr(a, "status", "")).lower()
        return "halted" if status.endswith("active") else "delisted"   # active-but-untradable = halt


def snapshot_price_fn(data_client, symbols: list[str]):
    """Build a dict-backed price_fn from one Alpaca latest-trade snapshot (one call, not per name)."""
    from alpaca.data.requests import StockLatestTradeRequest
    snap = data_client.get_stock_latest_trade(StockLatestTradeRequest(symbol_or_symbols=symbols))
    prices = {sym: float(trade.price) for sym, trade in snap.items()}
    return lambda t: prices.get(t)


def alpaca_paper_broker(price_fn):
    """Construct the live paper broker from env keys, asserting paper (never live)."""
    key, secret = os.environ.get("ALPACA_API_KEY_ID"), os.environ.get("ALPACA_API_SECRET_KEY")
    if not key or not secret:
        raise RuntimeError("set ALPACA_API_KEY_ID and ALPACA_API_SECRET_KEY (paper keys) in the env")
    from alpaca.trading.client import TradingClient
    tc = TradingClient(key, secret, paper=True)
    base = str(getattr(tc, "_base_url", PAPER_URL))
    assert "paper" in base, f"refusing to trade: broker base url is not paper ({base})"
    return AlpacaBroker(tc, price_fn)
