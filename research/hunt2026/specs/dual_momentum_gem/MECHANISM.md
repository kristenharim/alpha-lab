# dual_momentum_gem

Cross-sectional momentum across asset-class ETFs (SPY/QQQ/EFA) combined with an
absolute-momentum regime gate (winner's 12-month total return must beat BIL's, else
rotate to TLT), winner held at 1.5x. The counterparties are benchmark-anchored
institutional allocators who rebalance against 3-12 month trends and under-react to
regime shifts; the edge persists post-publication (Antonacci 2014, MOP 2012) because
harvesting it requires tolerating multi-quarter tracking error to the S&P, which
mandate-constrained institutions structurally cannot do. Falsifier: a forward year
where the 12-month gate whipsaws — a sharp crash plus V-recovery inside the lookback
window — costing 10-15% versus buy-and-hold, or the selected equity leg persistently
lagging SPY while the gate stays risk-on (post-publication decay exceeding the
McLean-Pontiff halving already priced into expectations).
