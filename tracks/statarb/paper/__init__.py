"""Stage-5 paper book for residual reversion (HYP-005).

Forward-trades the Avellaneda-Lee residual signal on the live S&P 500 via Alpaca
paper to resolve the survivorship bracket (~1.7 robust core vs ~2.5 PIT upper
bound). Survivorship-immune by construction: you hold current members forward, so
a name that delists at a loss is booked, not omitted.

Design: docs/superpowers/specs/2026-07-07-paper-book-residual-reversion-design.md
(in the quant.rim vault). Runs entirely on FakeBroker today; AlpacaBroker + the
parity gate are added before the first live run.
"""
