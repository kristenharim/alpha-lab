"""Asset-growth contrarian signal (Cooper, Gulen & Schill 2008).

Year-over-year total-asset growth is a CONTRARIAN cross-sectional signal: low-asset-
growth firms outperform high-growth firms (~20%/yr spread in the paper). So the score
is the NEGATIVE of asset growth — low growth ranks high (long), high growth ranks low
(short). Low turnover (annual), so it survives costs (Novy-Marx & Velikov).

Directly answers the "does highest YoY growth predict returns" question: it predicts
NEGATIVE returns — see [[LIT — Does highest YoY growth predict returns]].
"""
import pandas as pd


def asset_growth(assets: pd.DataFrame) -> pd.DataFrame:
    """YoY growth of total assets, per ticker. Input: annual assets (date x ticker),
    typically sparse because firms have different fiscal-year-ends. Growth is computed
    per company on its OWN consecutive reports (not panel-row adjacency), so it is not
    polluted by other firms' report dates. Each firm's first report has no prior → NaN.
    """
    if assets.empty:
        raise ValueError("assets frame is empty")
    cols = {c: assets[c].dropna().sort_index().pct_change() for c in assets.columns}
    return pd.DataFrame(cols).sort_index().dropna(how="all")


def growth_score(growth: pd.DataFrame) -> pd.DataFrame:
    """Contrarian score = -asset_growth. Low growth -> high score -> long side."""
    return -growth
