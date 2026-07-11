# vix_panic_buyer

Liquidity-provision returns concentrate after volatility spikes (Nagel; Hameed-Mian
JFQA 2015; Dai-Medhat-Novy-Marx-Rizova): the other side is levered and risk-managed
players (vol-target funds, margin-called accounts, dealers) forced to de-gross into
the spike, leaving elevated forward returns for anyone with pre-committed dry powder
and tolerance for early drawdown. Rather than harvesting this cross-sectionally at
10 bps/name (the dead statarb expression, ~5%/yr in costs), this expresses the same
information once at the index level: a permanent 1.5x SPY book that steps up to 2.0x
while VIX sits above 1.5x its trailing 60d median (relative spike, regime-proof) and
steps back down below 1.1x. A full spike cycle costs ~2 bps round-trip on the 0.5x
add. Falsifier: if forward SPY returns following relative VIX spikes stop exceeding
unconditional returns (i.e. the 2.0x add underperforms the 1.5x base net of its vol
drag over several spike cycles), the panic premium is arbitraged away or spikes have
become continuation signals, and the trigger should be removed.
