"""Terminal-event disambiguation — the survivorship SENSOR (highest-risk unit).

A false `delisted` injects a fake dead-name loss and *manufactures* the very signal
we're testing for — so every rule here is conservative and ambiguity NEVER
auto-books a dead-name loss (→ quarantine, flagged for human review). See the
disambiguation table in the spec; this is that table as code.

`classify` returns (reason, keep): keep=True means mark-to-last, do NOT book a
close (the position survives to the next run).
"""
from dataclasses import dataclass, field

HALT_MAX_DAYS = 5   # a transient halt resolves within K trading days; longer → quarantine

# reasons that book a close (keep=False)
CLOSE_REASONS = {"delisted", "corporate_action", "corporate_action_follow", "gap_stop"}
# the subset that are live "dead-name" events feeding the survivorship resolver
DEAD_NAME_REASONS = {"delisted", "corporate_action", "gap_stop"}


@dataclass
class Reconciler:
    """Stateful only in the per-ticker halt-day counter (needs memory across runs to
    tell a transient halt from a stuck one)."""
    halt_days: dict = field(default_factory=dict)

    def classify(self, ticker: str, status: str, *, in_index: bool = True,
                 successor: str | None = None, event: dict | None = None,
                 open_price: float | None = None, deep_floor: float | None = None,
                 entry_side: str = "long") -> tuple[str, bool]:
        """status: 'tradable'|'halted'|'delisted' (from broker.asset_status).
        event: optional corporate-action dict, e.g. {'type': 'merger_cash'} or
        {'type': 'symbol_change'}. Precedence: a known corporate action is
        unambiguous, so it's resolved before the tradability ladder."""
        # 1. corporate action with an authoritative feed → unambiguous
        if event:
            etype = event.get("type")
            if etype == "symbol_change" and successor:
                self.halt_days.pop(ticker, None)
                return "corporate_action_follow", False   # migrate position; NOT a dead name
            if etype in ("merger_cash", "acquisition_cash"):
                self.halt_days.pop(ticker, None)
                return "corporate_action", False          # book close at deal terms

        # 2. tradable → still open, unless a held long gapped through the deep-dip floor
        if status == "tradable":
            self.halt_days.pop(ticker, None)
            if (entry_side == "long" and open_price is not None
                    and deep_floor is not None and open_price < deep_floor):
                return "gap_stop", False
            return "still_open", True

        # 3. halted → transient (mark, keep) up to K days, then guardrail
        if status == "halted":
            days = self.halt_days.get(ticker, 0) + 1
            self.halt_days[ticker] = days
            if in_index and days <= HALT_MAX_DAYS:
                return "halt", True
            return "quarantine", True

        # 4. delisted → dead name ONLY if it's also out of the index with no successor;
        #    anything short of that certainty quarantines rather than book a false loss
        if status == "delisted":
            if not in_index and not successor:
                self.halt_days.pop(ticker, None)
                return "delisted", False
            return "quarantine", True

        return "quarantine", True     # unknown status → guardrail
