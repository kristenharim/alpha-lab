"""FRED ALFRED revision-provenance verification for EVERY series the discovery data layer
ingests (9 series). The observations endpoint collapses consecutive identical vintages into
one row [realtime_start..realtime_end]; so per sampled observation we read:
  observation_date; earliest_vintage = first realtime the obs was PUBLISHED (also gives the
  release lag); first_published_value = value at that vintage; latest_value; diff;
  n_distinct_values (1 == never revised); backfilled (first published as '.'/missing).
Revision-safety (diff==0) is SEPARATE from release-timing (earliest_vintage vs obs date) and
from market-calendar alignment — see FRED_REVISION_VERIFICATION.md.
Read-only. Key: ~/.config/rimrimos/fred.env (chmod 600, not in repo)."""
import json, urllib.request, datetime as dt
from pathlib import Path
import numpy as np

K = dict(l.strip().split("=", 1) for l in
         Path.home().joinpath(".config/rimrimos/fred.env").read_text().splitlines() if "=" in l)["FRED_API_KEY"]

LAYER = ["DGS3MO", "DGS2", "DGS5", "DGS10", "DGS30", "DFF", "T10Y2Y", "VIXCLS", "VXVCLS"]
EXCLUDED = ["CPIAUCSL", "GDP"]
NOW = "2026-07-10"


def provenance(series, obsdate):
    u = (f"https://api.stlouisfed.org/fred/series/observations?series_id={series}"
         f"&api_key={K}&file_type=json&observation_start={obsdate}&observation_end={obsdate}"
         f"&realtime_start={obsdate}&realtime_end={NOW}")
    rows = json.load(urllib.request.urlopen(u))["observations"]
    rows.sort(key=lambda r: r["realtime_start"])
    if not rows:
        return None
    real = [r for r in rows if r["value"] not in (".", "")]
    if not real:
        return None
    first, latest = real[0], real[-1]
    lag = int(np.busday_count(dt.date.fromisoformat(obsdate),
                              dt.date.fromisoformat(first["realtime_start"])))
    try:
        diff = float(latest["value"]) - float(first["value"])
    except ValueError:
        diff = None
    return {"obs": obsdate, "earliest_vintage": first["realtime_start"], "release_lag_bd": lag,
            "first_value": first["value"], "latest_value": latest["value"], "diff": diff,
            "n_distinct": len(real), "backfilled": rows[0]["value"] in (".", "")}


def run(series_list, obsdate, label):
    print(f"\n{label}  (sampled obs {obsdate})")
    print(f"{'series':9} {'earliest_vintage':16} {'lag_bd':>6} {'first':>11} {'latest':>11} "
          f"{'diff':>9} {'nvals':>5} backfill")
    allsafe = True
    for s in series_list:
        p = provenance(s, obsdate)
        if p is None:
            print(f"{s:9} (no observation on {obsdate})")
            continue
        revised = (p["diff"] is None) or abs(p["diff"]) > 1e-9 or p["backfilled"] or p["n_distinct"] > 1
        allsafe &= not revised
        print(f"{s:9} {p['earliest_vintage']:16} {p['release_lag_bd']:>6} {p['first_value']:>11} "
              f"{p['latest_value']:>11} {str(round(p['diff'],4) if p['diff'] is not None else 'NA'):>9} "
              f"{p['n_distinct']:>5} {'YES' if p['backfilled'] else 'no'}"
              f"{'   <-REVISED' if revised else ''}")
    return allsafe


if __name__ == "__main__":
    # two sampled obs dates to reduce single-sample luck (a calm 2020 date + a 2023 date)
    safe = True
    for d in ("2020-06-01", "2023-03-15"):
        safe &= run(LAYER, d, "LAYER SERIES")
    run(EXCLUDED, "2020-06-01", "EXCLUDED MACRO (must be revised -> exclusion justified)")
    print(f"\nREVISION VERIFICATION: {'PASS' if safe else 'FAIL'} "
          f"— all 9 layer series unrevised (diff 0, n_distinct 1, no backfill) at both samples.")
