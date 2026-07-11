"""Render the alpha-lab project overview to a self-contained dashboard.html.

The Stage of each track is auto-pulled from its tracks/<name>/STATE.md so it never
goes stale; verdicts and headlines are curated here (STATE.md prose isn't machine-
structured enough to scrape reliably). Edit TRACKS below after a session, re-run.

Usage: .venv/bin/python scripts/build_dashboard.py   (stdlib only, no venv needed)
"""
import html
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER_LIVE = ROOT / "artifacts" / "statarb" / "paper" / "live"

# curated per-track summary. `dir` = tracks/<dir>/STATE.md to read the live Stage from
# (None → use `stage` literal, e.g. the vault-only outbreak test). verdict drives colour.
TRACKS = [
    # ponytail: dir=None (curated stage), not "statarb" — that STATE.md header only tracks the
    # dead pairs method (Stage 1); the alive residual method is Stage 3. Two methods, one header
    # can't scrape it. Update the STATE.md header and this can point back at the file.
    dict(id="005", name="StatArb residual reversion", source="Structural · forced liquidity flows",
         dir=None, stage="Stage 5", verdict="alive", featured=True,
         headline="Avellaneda-Lee residual mean-reversion on the S&P 500, net 10bps. "
                  "Sharpe 2.67 baseline → 2.50 point-in-time → ~1.7 robust core. Survived 7 "
                  "skeptical audits. Now trading live on Alpaca paper (Stage 5) — the one "
                  "forward test immune to survivorship. Live book below."),
    dict(id="001", name="PEAD drift", source="Behavioral · underreaction",
         dir="pead", stage="Stage 1", verdict="promising",
         headline="+8.45% 60-day drift, textbook shape — but survivorship + no costs yet. Stage 3 next."),
    dict(id="002", name="Outbreak overreaction", source="Behavioral · overreaction",
         dir=None, stage="Tested v1", verdict="decaying",
         headline="Clear pre-2020, roughly gone by 2024. Needs an XBI-adjusted v2."),
    dict(id="003", name="LLM headline sentiment", source="Informational · slow processing",
         dir="llm_sentiment", stage="Stage 0", verdict="blocked",
         headline="Pipeline built + tested. Waiting on a news source + API key, and Stage-0 sign-off."),
    dict(id="004", name="GKX signal rotation", source="Behavioral · factor momentum",
         dir="gkx", stage="Stage 4", verdict="dead", verdict_label="Dead-for-me",
         headline="Rotation 0.78 and PC-timing 0.27 Sharpe — both lose to 2.10 just holding "
                  "every anomaly equally. Timing the factor zoo loses to diversification."),
    dict(id="006", name="Asset-growth contrarian", source="Behavioral · glamour",
         dir="asset_growth", stage="Stage 1", verdict="flat",
         headline="Corrected Sharpe ~0.01, and confirmed not a hidden size/sector tilt. "
                  "No premium this era."),
]

# verdict -> (left-accent, badge-bg, badge-text, default label)
VERDICT = {
    "alive":     ("var(--success)",       "var(--bg-success)", "var(--success)", "Alive"),
    "promising": ("var(--accent)",        "var(--bg-accent)",  "var(--accent)",  "Promising"),
    "decaying":  ("var(--warning)",       "var(--bg-warning)", "var(--warning)", "Decaying"),
    "flat":      ("var(--border)",        "var(--chip)",       "var(--muted)",   "Flat"),
    "dead":      ("var(--border)",        "var(--chip)",       "var(--muted)",   "Dead-for-me"),
    "blocked":   ("var(--border-strong)", "var(--chip)",       "var(--muted)",   "Blocked"),
}

STAGES = ["Hypothesis", "Data", "Replicate", "OOS + robust", "Verdict", "Paper trade"]


def live_stage(track):
    """Pull `**Stage:** N` from the track's STATE.md; fall back to the curated literal."""
    if not track["dir"]:
        return track["stage"]
    p = ROOT / "tracks" / track["dir"] / "STATE.md"
    if not p.exists():
        return track["stage"]
    m = re.search(r"\*\*Stage:\*\*\s*([0-9](?:\s*.\s*[0-9])?)", p.read_text())
    return f"Stage {m.group(1)}" if m else track["stage"]


def esc(s):
    return html.escape(str(s))


def _read_jsonl(p):
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def _sparkline(vals, w=680, h=56, pad=4):
    """Inline SVG polyline of the NAV curve. preserveAspectRatio=none so it stretches to the panel."""
    lo, hi = min(vals), max(vals)
    rng = (hi - lo) or 1e-9
    n = len(vals)
    pts = " ".join(
        f"{pad + (w - 2 * pad) * (i / (n - 1) if n > 1 else 0):.1f},"
        f"{pad + (h - 2 * pad) * (1 - (v - lo) / rng):.1f}"
        for i, v in enumerate(vals)
    )
    color = "var(--success)" if vals[-1] >= vals[0] else "var(--warning)"
    return (f'<svg viewBox="0 0 {w} {h}" preserveAspectRatio="none" class="spark">'
            f'<polyline fill="none" stroke="{color}" stroke-width="1.5" '
            f'points="{pts}"/></svg>')


def paper_stats(live_dir=PAPER_LIVE):
    """Reduce the committed live ledgers to the numbers the panel shows. Returns None if no book yet.
    NAV = cumulative product of daily net returns; day P&L = last day's net; holdings = latest targets."""
    nav_rows = _read_jsonl(live_dir / "daily_nav.jsonl")
    if not nav_rows:
        return None
    # ledger is append-only, so a re-run can duplicate a date — keep the last row per date and
    # sort, else sessions inflate and that day's return double-compounds into the NAV curve.
    by_date = {r["date"]: r for r in nav_rows}          # later row for a date wins
    nav_rows = [by_date[d] for d in sorted(by_date)]
    nav, cum = [], 1.0
    for r in nav_rows:
        cum *= 1.0 + float(r.get("net", 0.0))
        nav.append(cum)
    last = nav_rows[-1]
    tgt = _read_jsonl(live_dir / "targets.jsonl")
    holdings = []
    if tgt:
        as_of = max(r["date"] for r in tgt)
        rows = sorted((r for r in tgt if r["date"] == as_of),
                      key=lambda r: abs(float(r.get("target_weight", 0.0))), reverse=True)
        holdings = [(r["ticker"], "long" if float(r["target_weight"]) > 0 else "short")
                    for r in rows[:8]]
    return dict(nav=nav, days=len(nav_rows), day_pnl=float(last.get("net", 0.0)),
                cum_return=nav[-1] - 1.0, n_pos=int(last.get("n_pos", 0)),
                as_of=last.get("date", ""), holdings=holdings)


def paper_panel():
    """The live-paper-book panel, baked in at build time from the committed ledgers (no keys, no
    client-side API). Empty string if the book hasn't traded yet, so the page still builds."""
    s = paper_stats()
    if not s:
        return ""
    pnl_c = "var(--success)" if s["day_pnl"] >= 0 else "var(--warning)"
    cum_c = "var(--success)" if s["cum_return"] >= 0 else "var(--warning)"
    holds = "".join(
        f'<span class="hold" style="color:{"var(--success)" if d == "long" else "var(--warning)"}">'
        f'{esc(t)}<em>{d[0].upper()}</em></span>'
        for t, d in s["holdings"]
    )
    return f"""
  <div class="lbl">Live paper book — HYP-005 forward test · Alpaca paper · as of {esc(s['as_of'])}</div>
  <div class="card paper">
    <div class="pstats">
      <div class="pstat"><div class="l">Sessions</div><div class="v">{s['days']}</div></div>
      <div class="pstat"><div class="l">Cumulative</div>
        <div class="v" style="color:{cum_c}">{s['cum_return'] * 100:+.2f}%</div></div>
      <div class="pstat"><div class="l">Last day</div>
        <div class="v" style="color:{pnl_c}">{s['day_pnl'] * 100:+.2f}%</div></div>
      <div class="pstat"><div class="l">Positions</div><div class="v">{s['n_pos']}</div></div>
    </div>
    {_sparkline(s['nav'])}
    <div class="holds">{holds}</div>
    <p class="headline">Market-neutral residual-reversion book, staged pre-open nightly by a GitHub
      Actions cron. Paper only — a forward test, not a track record. Bracket Sharpe is noisy until
      ~12 months accrue. <a href="reports/statarb_paper_live_tearsheet.html">Live QuantStats
      tearsheet →</a> (accrues; full report at 20 sessions).</p>
  </div>"""


def card(track, featured=False):
    accent, badge_bg, badge_fg, default_label = VERDICT[track["verdict"]]
    label = track.get("verdict_label", default_label)
    stage = live_stage(track)
    border = "2px solid var(--accent)" if featured else f"border-left:3px solid {accent}"
    style = (f"border:{border};" if featured
             else f"border:.5px solid var(--border);{border};")
    name_size = "16px" if featured else "14px"
    return f"""
    <div class="card" style="{style}">
      <div class="card-head">
        <div>
          <span style="font-weight:500;font-size:{name_size}">HYP-{esc(track['id'])} · {esc(track['name'])}</span>
          <div class="src">{esc(track['source'])}</div>
        </div>
        <div class="tags">
          <span class="pill">{esc(stage)}</span>
          <span class="badge" style="background:{badge_bg};color:{badge_fg}">{esc(label)}</span>
        </div>
      </div>
      <p class="headline">{esc(track['headline'])}</p>
    </div>"""


def build():
    featured = next(t for t in TRACKS if t.get("featured"))
    rest = [t for t in TRACKS if not t.get("featured")]

    live = sum(t["verdict"] == "alive" for t in TRACKS)
    deadflat = sum(t["verdict"] in ("dead", "flat", "decaying") for t in TRACKS)
    inprog = sum(t["verdict"] in ("promising", "blocked") for t in TRACKS)

    stage_spine = "".join(
        f'<div class="step"><div class="rail" style="{"background:var(--accent)" if i==5 else ""}"></div>'
        f'<div class="snum" style="{"color:var(--accent)" if i==5 else ""}">{i}</div>'
        f'<div class="slbl">{esc(s)}</div></div>'
        for i, s in enumerate(STAGES)
    )
    rest_cards = "".join(card(t) for t in rest)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    return TEMPLATE.format(
        live=live, deadflat=deadflat, inprog=inprog,
        spine=stage_spine, featured=card(featured, featured=True),
        paper=paper_panel(), cards=rest_cards, stamp=stamp,
    )


TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>alpha-lab — project overview</title>
<style>
:root{{
  --page:#faf9f7; --card:#ffffff; --chip:#f2f1ee;
  --text:#1a1a19; --secondary:#6b6a67; --muted:#9a9895;
  --border:#e6e4e0; --border-strong:#c9c6c1;
  --accent:#2f6dd0; --bg-accent:#e9f0fb;
  --success:#1c7f4b; --bg-success:#e7f4ec;
  --warning:#946a1c; --bg-warning:#f8f0dd;
  --mono:ui-monospace,SFMono-Regular,Menlo,monospace;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
}}
@media (prefers-color-scheme:dark){{
  :root{{
    --page:#1c1b19; --card:#26241f; --chip:#2f2d28;
    --text:#ecebe8; --secondary:#a8a6a1; --muted:#7c7a75;
    --border:#3a3833; --border-strong:#524f49;
    --accent:#7aa9ee; --bg-accent:#20304a;
    --success:#5fc389; --bg-success:#1d3527;
    --warning:#d8ab5c; --bg-warning:#3a2f18;
  }}
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--page);color:var(--text);font-family:var(--sans);
  line-height:1.6;font-size:15px;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:760px;margin:0 auto;padding:2.2rem 1.4rem 3rem}}
h1{{font-size:24px;font-weight:500;margin:0}}
.sub{{color:var(--secondary);margin:.35rem 0 1.6rem}}
.metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:1.8rem}}
.metric{{background:var(--chip);border-radius:8px;padding:.85rem 1rem}}
.metric .l{{font-size:13px;color:var(--secondary)}}
.metric .v{{font-size:24px;font-weight:500;margin-top:2px}}
.lbl{{font-size:13px;color:var(--secondary);margin-bottom:8px}}
.spine{{display:grid;grid-template-columns:repeat(6,1fr);gap:6px;margin-bottom:1.9rem}}
.step{{text-align:center}}
.rail{{height:4px;background:var(--border-strong);border-radius:2px;margin-bottom:6px}}
.snum{{font-size:12px;font-weight:500}}
.slbl{{font-size:11px;color:var(--muted);line-height:1.3}}
.card{{background:var(--card);border-radius:12px;padding:1rem 1.2rem;margin-bottom:1rem}}
.card-head{{display:flex;justify-content:space-between;align-items:flex-start;gap:8px;flex-wrap:wrap}}
.src{{font-size:12px;color:var(--secondary);margin-top:2px}}
.tags{{display:flex;gap:6px}}
.pill{{font-size:12px;padding:3px 9px;border-radius:8px;background:var(--chip);
  color:var(--secondary);white-space:nowrap}}
.badge{{font-size:12px;padding:3px 10px;border-radius:8px;white-space:nowrap}}
.headline{{margin:8px 0 0;font-size:13.5px;color:var(--secondary)}}
.paper{{border:.5px solid var(--border);border-left:3px solid var(--success)}}
.pstats{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:.9rem}}
.pstat .l{{font-size:12px;color:var(--secondary)}}
.pstat .v{{font-size:22px;font-weight:500;margin-top:2px;font-family:var(--mono)}}
.spark{{width:100%;height:56px;display:block;margin:.2rem 0 .7rem}}
.holds{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:.2rem}}
.hold{{font-size:12px;font-family:var(--mono);padding:3px 8px;border-radius:7px;
  background:var(--chip)}}
.hold em{{font-style:normal;opacity:.6;margin-left:3px;font-size:10px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1rem;margin:0 0 1.5rem}}
.grid .card{{margin-bottom:0}}
.legend{{display:flex;gap:16px;flex-wrap:wrap;font-size:12px;color:var(--secondary);margin-bottom:1.9rem}}
.dot{{width:9px;height:9px;border-radius:50%;display:inline-block;vertical-align:1px;margin-right:5px}}
.rooms{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px;margin-bottom:1.6rem}}
.room{{background:var(--chip);border-radius:8px;padding:.8rem 1rem}}
.room .l{{font-size:12px;color:var(--muted)}}
.room .v{{font-size:13px;margin-top:3px;font-family:var(--mono);word-break:break-all}}
.foot{{font-size:12px;color:var(--muted);border-top:.5px solid var(--border);padding-top:1rem}}
</style></head>
<body><div class="wrap">
  <h1>alpha-lab</h1>
  <p class="sub">Personal signal-research lab — reproduce a published edge, attack it honestly,
    keep the dead ones. Paper only.</p>

  <div class="metrics">
    <div class="metric"><div class="l">Hypotheses</div><div class="v">6</div></div>
    <div class="metric"><div class="l">Live signal</div><div class="v" style="color:var(--success)">{live}</div></div>
    <div class="metric"><div class="l">Dead / flat</div><div class="v">{deadflat}</div></div>
    <div class="metric"><div class="l">In progress</div><div class="v">{inprog}</div></div>
  </div>

  <div class="lbl">The framework — every idea walks this gate</div>
  <div class="spine">{spine}</div>

  {featured}
  {paper}

  <div class="grid">{cards}</div>

  <div class="legend">
    <span><span class="dot" style="background:var(--success)"></span>Alive</span>
    <span><span class="dot" style="background:var(--accent)"></span>Promising</span>
    <span><span class="dot" style="background:var(--warning)"></span>Decaying</span>
    <span><span class="dot" style="background:var(--muted)"></span>Dead / flat</span>
    <span><span class="dot" style="background:var(--border-strong)"></span>Blocked</span>
  </div>

  <div class="lbl">Where it all lives — three rooms, not one folder</div>
  <div class="rooms">
    <div class="room"><div class="l">Code + backtests</div><div class="v">~/projects/alpha-lab</div></div>
    <div class="room"><div class="l">Research journal</div><div class="v">vault / trading-lab</div></div>
    <div class="room"><div class="l">Design spec</div><div class="v">quant.rim/docs/specs</div></div>
  </div>

  <div class="foot">Generated {stamp} by scripts/build_dashboard.py · stages read live from each
    track's STATE.md · re-run after a session to refresh.</div>
</div></body></html>
"""


def main():
    out = ROOT / "dashboard.html"
    out.write_text(build(), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
