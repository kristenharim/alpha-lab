"""Broker seam: one interface, two implementations.

The paper book talks only to `Broker`. `FakeBroker` fulfills the contract
in memory (every test + `--dry-run` runs on it, no network); `AlpacaBroker`
(built last) is the only piece that touches keys/live data. Because the rest
of the system depends on the interface, not the vendor, "tests never touch the
network" is free.
"""
from abc import ABC, abstractmethod


class Broker(ABC):
    """What the nightly loop needs a broker to do. Four verbs, nothing more."""

    @abstractmethod
    def submit_targets(self, targets: dict[str, float]) -> None:
        """Move current holdings toward the FULL target book `{ticker: dollars}`
        (signed: +long, -short). Any held name absent from `targets` is an exit
        (target 0)."""

    @abstractmethod
    def positions(self) -> dict[str, dict]:
        """Current holdings: {ticker: {qty, avg_entry_price, side}}."""

    @abstractmethod
    def fills(self) -> list[dict]:
        """Fills since the previous call (drains). [{ticker, side, qty, fill_price}]."""

    @abstractmethod
    def asset_status(self, ticker: str) -> str:
        """'tradable' | 'halted' | 'delisted' — the input reconcile's terminal-event
        logic keys on."""


class FakeBroker(Broker):
    """In-memory broker. Fills are naive (instant, complete, at the mark price) but
    honor `asset_status`, so the dead-name paths the experiment turns on are testable.

    ponytail: naive fills, no slippage/partials. Add a slippage arg only when a test
    demands realism — the reconcile fixtures need tradability, not microstructure.
    """

    def __init__(self, prices: dict[str, float]):
        self.prices = dict(prices)          # mark price per ticker
        self._positions: dict[str, dict] = {}   # ticker -> {qty, avg_entry_price}
        self._new_fills: list[dict] = []        # drained by fills()
        self._status: dict[str, str] = {}       # ticker -> status (default 'tradable')

    # ---- the fill policy ----------------------------------------------------
    def submit_targets(self, targets: dict[str, float]) -> None:
        """Fill toward `targets`. Union held + target names so a held name absent
        from the book is an exit (target 0). Turn target dollars into a share count,
        diff against current qty, and book the delta ONLY if it's nonzero AND the
        name is tradable — a delisted/halted name can't be traded out, so its stale
        position stays (exactly the dead-name path the experiment turns on)."""
        for ticker in set(self._positions) | set(targets):
            price = self.prices.get(ticker)
            if price is None or self.asset_status(ticker) != "tradable":
                continue
            cur = self._positions.get(ticker, {"qty": 0.0})["qty"]
            target_qty = targets.get(ticker, 0.0) / price
            delta = target_qty - cur
            if delta != 0:
                self._apply_fill(ticker, delta, price)

    # ---- given (bookkeeping, not the decision) ------------------------------
    def _apply_fill(self, ticker: str, delta_qty: float, price: float) -> None:
        """Update the position for one fill and record it. Handles the fiddly
        average-entry-price math (weighted add on same side, reset on a sign flip)."""
        pos = self._positions.get(ticker, {"qty": 0.0, "avg_entry_price": 0.0})
        cur = pos["qty"]
        new = cur + delta_qty
        if cur == 0 or (cur > 0) == (delta_qty > 0):        # open or add same side
            pos["avg_entry_price"] = (
                abs(cur) * pos["avg_entry_price"] + abs(delta_qty) * price
            ) / (abs(cur) + abs(delta_qty))
        elif new != 0 and (new > 0) != (cur > 0):            # reduced through zero -> flipped
            pos["avg_entry_price"] = price
        # else: reducing the same side -> keep the existing avg entry
        pos["qty"] = new
        if new == 0:
            self._positions.pop(ticker, None)
        else:
            self._positions[ticker] = pos
        self._new_fills.append({
            "ticker": ticker,
            "side": "buy" if delta_qty > 0 else "sell",
            "qty": abs(delta_qty),
            "fill_price": price,
        })

    def positions(self) -> dict[str, dict]:
        return {
            t: {"qty": p["qty"], "avg_entry_price": p["avg_entry_price"],
                "side": "long" if p["qty"] > 0 else "short"}
            for t, p in self._positions.items()
        }

    def fills(self) -> list[dict]:
        out, self._new_fills = self._new_fills, []
        return out

    def asset_status(self, ticker: str) -> str:
        return self._status.get(ticker, "tradable")

    def set_status(self, ticker: str, status: str) -> None:
        """Test hook: mark a name halted/delisted so the skip path can be exercised."""
        self._status[ticker] = status
