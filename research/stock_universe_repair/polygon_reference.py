"""Polygon reference-data source for the stock-universe repair (Track 1: identifier/delisting map).

Scope is dictated by the provisioned Polygon plan (probed 2026-07-11):
  WORKS: /v3/reference/tickers (incl. active=false -> delisted, with delisted_utc + composite_figi),
         /v3/reference/splits, /v3/reference/dividends.
  BLOCKED (403 NOT_AUTHORIZED on this plan): /v2/aggs price bars. So this layer supplies the
  survivorship-complete IDENTIFIER + DELISTING + corporate-action metadata, NOT prices. The ~150
  dead names' OHLCV (repair Track 3 price half) still needs a Polygon price-tier upgrade or FactSet.

This is ADDITIVE to the concurrent repair project — it does not edit id_map.csv / PLAN.md /
continuity_audit.py. It writes: polygon_raw/*.json (cached pages), delisting_map.csv (auto-completed
delist dates + FIGI for the ever-S&P members missing from the panel).

Run: .venv/bin/python research/stock_universe_repair/polygon_reference.py
Idempotent: cached pages are reused; re-run is free.
"""
from __future__ import annotations
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]   # HERE = alpha-lab/research/stock_universe_repair -> ROOT = alpha-lab
RAW = HERE / "polygon_raw"
RAW.mkdir(exist_ok=True)
CHANGES = ROOT / "data" / "raw" / "sp500_pit_changes.parquet"
PANEL = ROOT / "research" / "hunt2026" / "panel_2005.parquet"


def _key() -> str:
    env = dict(l.split("=", 1) for l in (ROOT / ".env").read_text().splitlines() if "=" in l)
    return env["POLYGON_API_KEY"]


def _get(url: str, tries: int = 5) -> dict:
    for a in range(tries):
        try:
            return json.loads(urllib.request.urlopen(url, timeout=30).read())
        except urllib.error.HTTPError as e:
            if e.code == 429:                      # rate limited -> back off (free tier ~5/min)
                time.sleep(15 * (a + 1)); continue
            raise
    raise RuntimeError(f"gave up after {tries} tries: {url}")


def fetch_delisted(max_pages: int = 80) -> pd.DataFrame:
    """Paginate all delisted US stocks (cached per page). Returns ticker/delisted_utc/figi/name."""
    key = _key()
    url = (f"https://api.polygon.io/v3/reference/tickers?market=stocks&active=false"
           f"&limit=1000&sort=ticker&order=asc&apiKey={key}")
    rows, page = [], 0
    while url and page < max_pages:
        cache = RAW / f"delisted_{page:03d}.json"
        if cache.exists():
            d = json.loads(cache.read_text())
        else:
            d = _get(url)
            cache.write_text(json.dumps(d))
            time.sleep(3)                          # polite spacing for the rate limit
        rows += d.get("results", [])
        nxt = d.get("next_url")
        url = f"{nxt}&apiKey={key}" if nxt else None
        page += 1
    df = pd.DataFrame([{"ticker": r.get("ticker"), "delisted_utc": r.get("delisted_utc"),
                        "composite_figi": r.get("composite_figi"), "name": r.get("name")}
                       for r in rows])
    return df.drop_duplicates("ticker")


def ever_members() -> set:
    ch = pd.read_parquet(CHANGES)
    out = set()
    for m in ch["members"]:
        out |= set(m)
    return out


def panel_tickers() -> set:
    p = pd.read_parquet(PANEL)
    cols = p["close"].columns if isinstance(p.columns, pd.MultiIndex) else p.columns
    return set(cols)


def build_map() -> pd.DataFrame:
    ever, have = ever_members(), panel_tickers()
    missing = sorted(ever - have)
    delisted = fetch_delisted().set_index("ticker")
    recs = []
    for t in missing:
        hit = delisted.loc[t] if t in delisted.index else None
        recs.append({
            "ticker": t,
            "delisted_utc": (hit["delisted_utc"][:10] if hit is not None and pd.notna(hit["delisted_utc"]) else None),
            "composite_figi": (hit["composite_figi"] if hit is not None else None),
            "polygon_name": (hit["name"] if hit is not None else None),
            "polygon_found": hit is not None,
        })
    out = pd.DataFrame(recs)
    out.to_csv(HERE / "delisting_map.csv", index=False)
    return out


if __name__ == "__main__":
    m = build_map()
    found = int(m["polygon_found"].sum())
    dated = int(m["delisted_utc"].notna().sum())
    figi = int(m["composite_figi"].notna().sum())
    print(f"ever-S&P members missing from panel: {len(m)}")
    print(f"  matched in Polygon delisted set: {found}  ({100*found/len(m):.0f}%)")
    print(f"  with delist date: {dated}   with FIGI permanent id: {figi}")
    print("wrote delisting_map.csv")
    # self-check: a known delisting resolves
    aaba = m[m["ticker"] == "AABA"]
    assert aaba.empty or aaba.iloc[0]["delisted_utc"] == "2019-10-07", aaba.to_dict("records")
    print("self-check OK (AABA delist date)" if not aaba.empty else "note: AABA not in missing set")
