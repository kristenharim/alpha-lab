"""Successor / rename resolution for the 175 ever-S&P members Polygon left unmatched.

IDENTIFIER + CORPORATE-EVENT REPAIR ONLY — NOT a price-panel repair. It builds a NEW additive
CANDIDATE file (`rename_candidates.csv`); it never edits the frozen panel or the curated `id_map.csv`
(cross-checked, not overwritten). It does NOT join predecessor↔successor price series and does NOT
assume economic continuity unless a same-security rename is supported (per authorization restrictions).

Sources (each kept separate in the `sources` field; robots for StockAnalysis checked = general
access allowed, but it is used only as a documented MANUAL cross-check, not scraped here):
  - curated_id_map        : research/stock_universe_repair/id_map.csv (authoritative hand curation)
  - polygon_reference     : the cached delisted-ticker set (name / delisted_utc / composite_figi),
                            matched after conservative normalization (bankruptcy 'Q', share-class, warrant)
  - sec_company_tickers   : SEC current ticker→CIK/name (successor CIK; reuse flagged, not assumed)
NOTE: SEC offers no delisted-ticker→CIK lookup, so `old_cik` is usually blank → manual review.

Run: .venv/bin/python research/stock_universe_repair/resolve_renames.py
"""
from __future__ import annotations
import json
import urllib.request
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RAW = HERE / "polygon_raw"
UA = {"User-Agent": "alpha-lab research (kris10harim@gmail.com)"}


def load_polygon_delisted() -> dict:
    """ticker -> {name, delisted_utc, composite_figi} from the cached reference pull."""
    out = {}
    for p in sorted(RAW.glob("delisted_*.json")):
        for r in json.loads(p.read_text()).get("results", []):
            out[r.get("ticker")] = {"name": r.get("name"), "delisted_utc": (r.get("delisted_utc") or "")[:10],
                                    "figi": r.get("composite_figi")}
    return out


def sec_current_tickers() -> dict:
    """current TICKER -> (cik, name) from SEC (cached)."""
    cache = HERE / "sec_company_tickers.json"
    if cache.exists():
        data = json.loads(cache.read_text())
    else:
        data = json.loads(urllib.request.urlopen(
            urllib.request.Request("https://www.sec.gov/files/company_tickers.json", headers=UA)).read())
        cache.write_text(json.dumps(data))
    return {v["ticker"]: (v["cik_str"], v["title"]) for v in data.values()}


def normalize_variants(t: str) -> list[str]:
    """Conservative ticker variants to probe against the Polygon delisted set."""
    v = {t}
    if len(t) > 1 and t.endswith("Q"):
        v.add(t[:-1])                 # bankruptcy Q-suffix: AAMRQ -> AAMR
    for sep in (".", "-"):
        if sep in t:
            v.add(t.split(sep)[0])    # share-class / warrant base: AFS-A -> AFS
    v.add(t.replace("-", "."))        # dash<->dot share-class form
    return [x for x in v if x]


def classify_event(t: str, id_action: str | None) -> tuple[str, str]:
    """Return (event_type, event_basis). event_basis distinguishes AUTHORITATIVE event evidence
    (curated id_map / SEC former-name) from a PATTERN_CANDIDATE inferred only from ticker syntax.
    Ticker syntax NEVER by itself proves the event: a 'Q' suffix indicates bankruptcy *proceedings*,
    not liquidation or successor treatment; class/punctuation notation does not prove a share-class
    conversion. These are candidates for manual verification, not determinations."""
    if id_action:
        ev = {"rename": "rename", "acquire": "acquisition", "merge": "acquisition",
              "delist": "uncertain", "spinoff": "spinoff"}.get(id_action, id_action)
        return ev, "sourced:id_map"
    if len(t) > 1 and t.endswith("Q"):
        return "bankruptcy_proceedings?", "pattern_candidate"   # Q-suffix — proceedings, not proven liquidation
    if any(s in t for s in (".WS", ".WT", ".U", "+")):
        return "share-class/warrant?", "pattern_candidate"      # punctuation — not proven conversion
    if any(t.endswith(sfx) for sfx in ("-A", "-B", ".A", ".B", "-P")):
        return "share-class?", "pattern_candidate"
    return "uncertain", "unresolved"


# price_continuity_valid is FALSE for every row unless the SAME continuing security is positively
# verified with effective dates + supporting evidence. No row in this 175-name set meets that bar,
# so all are False. Pattern syntax and identifier presence do NOT establish continuity.
def continuity(event_basis: str) -> bool:
    return False


def build():
    dm = pd.read_csv(HERE / "delisting_map.csv")
    unmatched = dm[~dm["polygon_found"]]["ticker"].tolist()          # the 175
    idmap = pd.read_csv(HERE / "id_map.csv").set_index("old_ticker")
    poly = load_polygon_delisted()
    cur = sec_current_tickers()

    rows = []
    for t in unmatched:
        src, succ, eff, pred_name, succ_name = [], None, None, None, None
        old_cik = new_cik = figi = None
        id_action = None
        # 1) curated id_map (authoritative; cross-check, never overwrite)
        if t in idmap.index:
            r = idmap.loc[t]
            id_action = str(r.get("action")) if pd.notna(r.get("action")) else None
            succ = r.get("successor_ticker") if pd.notna(r.get("successor_ticker")) else None
            eff = str(r.get("effective_date"))[:10] if pd.notna(r.get("effective_date")) else None
            pred_name = str(r.get("note")) if pd.notna(r.get("note")) else None
            src.append("curated_id_map")
        # 2) polygon reference via conservative normalization
        for v in normalize_variants(t):
            if v in poly:
                pred_name = pred_name or poly[v]["name"]
                eff = eff or (poly[v]["delisted_utc"] or None)
                figi = figi or poly[v]["figi"]
                src.append(f"polygon_reference:{v}")
                break
        # 3) SEC current-ticker map — successor CIK if successor is a current ticker; flag reuse
        if succ and succ in cur:
            new_cik, succ_name = f"{cur[succ][0]:010d}", cur[succ][1]
            src.append("sec_company_tickers:successor")
        if t in cur:                      # historical ticker is a CURRENT ticker -> possible reuse/rename
            src.append("sec_company_tickers:ticker-active(reuse?)")

        event, ebasis = classify_event(t, id_action)
        # identifier-evidence confidence (FIGI/CIK/curated) is SEPARATE from the event determination.
        id_conf = "high" if "curated_id_map" in src else ("medium" if any("polygon" in s for s in src) else ("low" if src else "uncertain"))
        rows.append({
            "historical_ticker": t, "proposed_successor_ticker": succ,
            "predecessor_name": pred_name, "successor_name": succ_name,
            "effective_date": eff,
            "event_type": event, "event_basis": ebasis,   # pattern_candidate = inferred from ticker syntax only
            "old_cik": old_cik, "new_cik": new_cik, "figi": figi,
            "sources": ";".join(src) if src else "none",
            "identifier_confidence": id_conf,              # confidence in the ID evidence, NOT the event type
            "price_continuity_valid": False,               # False unless same-security positively verified w/ dates+evidence
            "manual_review_required": True,                # every row — no continuity positively verified
        })
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "rename_candidates.csv", index=False)
    return out


# Categories are CANDIDATE buckets. Anything from event_basis=pattern_candidate is a candidate for
# manual verification, not an authoritative determination. A row lands in the VERIFIED rename bucket
# only with sourced evidence AND positively-verified continuity (none in this set).
CATEGORIES = {
    "verified_rename_same_security": lambda r: str(r["event_basis"]).startswith("sourced") and r["event_type"] == "rename" and r["price_continuity_valid"] is True,
    "share_class_pattern_candidate": lambda r: str(r["event_type"]).startswith("share-class"),
    "acquisition_old_terminated": lambda r: r["event_type"] == "acquisition",
    "bankruptcy_proceedings_pattern_candidate": lambda r: str(r["event_type"]).startswith("bankruptcy"),
    "relisting_reorg": lambda r: r["event_type"] in ("relisting", "spinoff"),
    "unresolved": lambda r: r["event_type"] == "uncertain",
}

if __name__ == "__main__":
    df = build()
    print(f"unmatched names processed: {len(df)}")
    print(f"any source found: {(df['sources'] != 'none').sum()} | manual_review_required: {df['manual_review_required'].sum()}")
    print("\ncategory counts:")
    counted = pd.Series(0, index=list(CATEGORIES))
    for _, r in df.iterrows():
        for name, fn in CATEGORIES.items():
            if fn(r):
                counted[name] += 1
                break
    for k, v in counted.items():
        print(f"  {k:42s} {v}")
    print(f"  {'TOTAL':42s} {counted.sum()}")
    # self-checks enforcing the labeling rules:
    assert (df["price_continuity_valid"] == False).all(), "continuity must be False for every row"
    pc = df[df["event_basis"] == "pattern_candidate"]
    assert pc["event_type"].str.contains(r"\?").all(), "pattern_candidate events must carry the '?' marker"
    assert df["manual_review_required"].all(), "every row must require manual review"
    print(f"\nself-check OK: continuity=False all rows; {len(pc)} pattern_candidate rows marked; all manual_review")
    print("wrote rename_candidates.csv")
